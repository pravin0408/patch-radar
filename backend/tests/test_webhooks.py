"""Tests for webhook formatting functions (unit-level, no HTTP)."""
from datetime import date

from app.schemas import CanonicalPatch
from app.webhooks import _format_generic, _format_pagerduty, _format_slack, _format_teams


def _make_patch(severity="CRITICAL", cves=None):
    return CanonicalPatch(
        vendor="cisco",
        model="Catalyst 9300",
        component_type="IOS-XE",
        version_raw="17.12.03",
        version_normalized="000017.000012.000003",
        release_date=date(2026, 6, 15),
        severity=severity,
        cves=cves or ["CVE-2026-20150"],
        advisory_url="https://example.com/advisory",
        source_adapter="test",
    )


def test_format_slack_structure():
    patches = [_make_patch()]
    payload = _format_slack("cisco", patches)
    assert "blocks" in payload
    assert len(payload["blocks"]) >= 2  # header + summary + patch details


def test_format_slack_caps_at_10():
    patches = [_make_patch() for _ in range(15)]
    payload = _format_slack("cisco", patches)
    # Should have header + summary + 10 details + overflow message = 13
    assert len(payload["blocks"]) == 13


def test_format_teams_structure():
    patches = [_make_patch()]
    payload = _format_teams("cisco", patches)
    assert payload["@type"] == "MessageCard"
    assert "sections" in payload
    assert len(payload["sections"][0]["facts"]) == 1


def test_format_pagerduty_structure():
    patches = [_make_patch()]
    payload = _format_pagerduty("cisco", patches, "test-routing-key")
    assert payload["routing_key"] == "test-routing-key"
    assert payload["event_action"] == "trigger"
    assert payload["payload"]["severity"] == "critical"
    assert "cisco" in payload["payload"]["summary"].lower()


def test_format_generic_structure():
    patches = [_make_patch(), _make_patch(severity="HIGH")]
    payload = _format_generic("cisco", patches)
    assert payload["event"] == "patch_radar.critical_patches"
    assert payload["vendor"] == "cisco"
    assert payload["patch_count"] == 2
    assert len(payload["patches"]) == 2
    assert payload["patches"][0]["model"] == "Catalyst 9300"


def test_format_generic_includes_all_fields():
    patch = _make_patch(cves=["CVE-2026-001", "CVE-2026-002"])
    payload = _format_generic("cisco", [patch])
    p = payload["patches"][0]
    assert p["version"] == "17.12.03"
    assert p["severity"] == "CRITICAL"
    assert len(p["cves"]) == 2
    assert p["advisory_url"] == "https://example.com/advisory"
    assert p["release_date"] == "2026-06-15"
