from __future__ import annotations

import logging
from datetime import date, datetime

import httpx

from app.adapters.base import BaseAdapter
from app.config import settings
from app.normalizer import map_severity, normalize_version
from app.schemas import CanonicalPatch

logger = logging.getLogger("patch_radar.adapters.paloalto")


class PaloAltoAdapter(BaseAdapter):
    """Adapter for Palo Alto Networks Security Advisories.
    
    Reads from the public JSON API provided by PAN PSIRT.
    """

    vendor_id = "paloalto"

    def __init__(self, api_url: str | None = None):
        self.api_url = api_url or settings.paloalto_api_url

    async def fetch(self) -> list[CanonicalPatch]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Modern PAN API requires User-Agent
                resp = await client.get(
                    self.api_url, 
                    headers={"User-Agent": "PatchRadar/1.0", "Accept": "application/json"}
                )
                resp.raise_for_status()
                data = resp.json()
                return self._parse_json(data)
            except httpx.HTTPError as exc:
                logger.warning("Palo Alto API unavailable (%s)", exc)
                return []

    def _parse_json(self, data: list | dict) -> list[CanonicalPatch]:
        out: list[CanonicalPatch] = []
        advisories = data if isinstance(data, list) else data.get("advisories", [])

        for adv in advisories:
            adv_id = adv.get("AdvisoryId", "")
            if not adv_id:
                continue

            date_str = adv.get("DateInitial") or adv.get("DateUpdated")
            try:
                release_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            except (TypeError, ValueError):
                release_dt = date.today()

            # Sometimes multiple PAN-OS versions are affected. This stub flattens it for simplicity.
            out.append(
                CanonicalPatch(
                    vendor=self.vendor_id,
                    model="PAN-OS",
                    component_type="Firewall OS",
                    version_raw=adv_id,
                    version_normalized=normalize_version(self.vendor_id, adv_id),
                    release_date=release_dt,
                    severity=map_severity(adv.get("Severity")),
                    cves=[adv.get("CVE")] if adv.get("CVE") else [],
                    advisory_url=f"https://security.paloaltonetworks.com/{adv_id}",
                    download_url="https://support.paloaltonetworks.com/",
                    requires_entitlement=True,
                    checksum_sha256=None,
                    source_adapter="paloalto_api",
                )
            )
        return out
