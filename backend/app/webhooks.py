"""Webhook dispatcher for alerting on critical patch releases.

Supports:
- Slack (Incoming Webhooks / Block Kit)
- Microsoft Teams (Adaptive Cards via Power Automate / Webhook)
- Generic HTTP webhook (JSON POST)
- PagerDuty Events API v2

Dispatches are fire-and-forget with retry logic. Failed deliveries are
logged but do not block the ingestion pipeline.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.schemas import CanonicalPatch

logger = logging.getLogger("patch_radar.webhooks")


async def dispatch_new_patches(
    vendor_id: str,
    patches: list[CanonicalPatch],
    *,
    critical_only: bool = True,
) -> None:
    """Send notifications for newly ingested patches.

    By default only CRITICAL patches trigger webhooks. Set critical_only=False
    to alert on HIGH severity and above.
    """
    if not patches:
        return

    severity_threshold = {"CRITICAL"} if critical_only else {"CRITICAL", "HIGH"}
    notable = [p for p in patches if p.severity in severity_threshold]
    if not notable:
        return

    targets = _get_webhook_targets()
    if not targets:
        logger.debug("No webhook targets configured; skipping dispatch")
        return

    for target in targets:
        try:
            await _send_webhook(target, vendor_id, notable)
        except Exception as exc:
            logger.error(
                "Webhook dispatch to %s failed: %s", target["url"][:60], exc
            )


def _get_webhook_targets() -> list[dict[str, str]]:
    """Read configured webhook targets from settings."""
    targets: list[dict[str, str]] = []

    if settings.webhook_slack_url:
        targets.append({"type": "slack", "url": settings.webhook_slack_url})

    if settings.webhook_teams_url:
        targets.append({"type": "teams", "url": settings.webhook_teams_url})

    if settings.webhook_generic_url:
        targets.append({"type": "generic", "url": settings.webhook_generic_url})

    if settings.webhook_pagerduty_key:
        targets.append({
            "type": "pagerduty",
            "url": "https://events.pagerduty.com/v2/enqueue",
            "routing_key": settings.webhook_pagerduty_key,
        })

    return targets


async def _send_webhook(
    target: dict[str, str],
    vendor_id: str,
    patches: list[CanonicalPatch],
) -> None:
    """Route to the appropriate webhook formatter and send."""
    dispatch_type = target["type"]
    async with httpx.AsyncClient(timeout=15.0) as client:
        if dispatch_type == "slack":
            payload = _format_slack(vendor_id, patches)
        elif dispatch_type == "teams":
            payload = _format_teams(vendor_id, patches)
        elif dispatch_type == "pagerduty":
            payload = _format_pagerduty(
                vendor_id, patches, target.get("routing_key", "")
            )
        else:
            payload = _format_generic(vendor_id, patches)

        resp = await client.post(
            target["url"],
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        logger.info(
            "Webhook dispatched to %s (%d patches, status %d)",
            dispatch_type, len(patches), resp.status_code,
        )


def _format_slack(vendor_id: str, patches: list[CanonicalPatch]) -> dict[str, Any]:
    """Format a Slack Block Kit message."""
    patch_lines = []
    for p in patches[:10]:  # Cap at 10 to avoid message size limits
        cve_str = ", ".join(p.cves[:3]) or "N/A"
        patch_lines.append(
            f"*{p.model}* / {p.component_type} `{p.version_raw}` "
            f"({p.severity}) - {cve_str}\n"
            f"<{p.advisory_url}|View Advisory>"
        )

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Patch Radar Alert: {vendor_id.upper()}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{len(patches)}* critical patch(es) detected during "
                    f"the latest {vendor_id} ingestion run."
                ),
            },
        },
    ]
    for line in patch_lines:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": line},
        })
    if len(patches) > 10:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"_...and {len(patches) - 10} more. View all in the dashboard._",
            },
        })

    return {"blocks": blocks}


def _format_teams(vendor_id: str, patches: list[CanonicalPatch]) -> dict[str, Any]:
    """Format a Microsoft Teams Adaptive Card."""
    facts = []
    for p in patches[:10]:
        facts.append({
            "name": f"{p.model} / {p.component_type}",
            "value": f"{p.version_raw} ({p.severity}) - {', '.join(p.cves[:3]) or 'N/A'}",
        })

    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "themeColor": "FF0000",
        "summary": f"Patch Radar: {len(patches)} critical patches from {vendor_id}",
        "sections": [
            {
                "activityTitle": f"Patch Radar Alert: {vendor_id.upper()}",
                "activitySubtitle": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "facts": facts,
                "markdown": True,
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "Open Dashboard",
                "targets": [{"os": "default", "uri": "http://localhost:3000"}],
            }
        ],
    }


def _format_pagerduty(
    vendor_id: str,
    patches: list[CanonicalPatch],
    routing_key: str,
) -> dict[str, Any]:
    """Format a PagerDuty Events API v2 payload."""
    cve_summary = []
    for p in patches[:5]:
        cve_summary.append(f"{p.model}: {p.version_raw} ({', '.join(p.cves[:2])})")

    return {
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": (
                f"Patch Radar: {len(patches)} critical patch(es) from "
                f"{vendor_id.upper()}"
            ),
            "severity": "critical",
            "source": "patch-radar",
            "component": vendor_id,
            "group": "infrastructure-patches",
            "class": "security-advisory",
            "custom_details": {
                "vendor": vendor_id,
                "patch_count": len(patches),
                "top_patches": cve_summary,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    }


def _format_generic(vendor_id: str, patches: list[CanonicalPatch]) -> dict[str, Any]:
    """Format a generic JSON webhook payload."""
    return {
        "event": "patch_radar.critical_patches",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vendor": vendor_id,
        "patch_count": len(patches),
        "patches": [
            {
                "model": p.model,
                "component": p.component_type,
                "version": p.version_raw,
                "severity": p.severity,
                "cves": p.cves,
                "advisory_url": p.advisory_url,
                "download_url": p.download_url,
                "release_date": p.release_date.isoformat(),
            }
            for p in patches
        ],
    }
