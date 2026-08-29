import hashlib
import re
from datetime import date

from app.normalizer import dedup, map_severity, normalize_version, verify_checksum
from app.schemas import CanonicalPatch


# ---------------------------------------------------------------------------
# Version normalization tests
# ---------------------------------------------------------------------------


def test_normalize_version_sorts_correctly_dell():
    v1 = normalize_version("dell", "1.9.4")
    v2 = normalize_version("dell", "1.14.2")
    assert v1 < v2  # 1.14.2 is newer than 1.9.4, must sort after it


def test_normalize_version_netscaler_build_format():
    v1 = normalize_version("netscaler", "13.1-9.60")
    v2 = normalize_version("netscaler", "14.1-34.42")
    assert v1 < v2


def test_normalize_version_netscaler_same_major():
    v1 = normalize_version("netscaler", "14.1-29.63")
    v2 = normalize_version("netscaler", "14.1-34.42")
    assert v1 < v2


def test_normalize_version_cisco():
    v1 = normalize_version("cisco", "17.9.4a")
    v2 = normalize_version("cisco", "17.12.03")
    assert v1 < v2


def test_normalize_version_hpe():
    v1 = normalize_version("hpe", "1.50")
    v2 = normalize_version("hpe", "1.62")
    assert v1 < v2


def test_normalize_version_strips_whitespace():
    v1 = normalize_version("dell", "  1.14.2  ")
    v2 = normalize_version("dell", "1.14.2")
    assert v1 == v2


def test_normalize_version_see_advisory_placeholder():
    """Placeholder versions should still normalize without error."""
    v = normalize_version("netscaler", "see-advisory")
    assert isinstance(v, str)
    assert len(v) > 0


# ---------------------------------------------------------------------------
# Severity mapping tests
# ---------------------------------------------------------------------------


def test_map_severity_from_label():
    assert map_severity("Critical") == "CRITICAL"
    assert map_severity("high") == "HIGH"
    assert map_severity("Medium") == "MEDIUM"
    assert map_severity("low") == "LOW"
    assert map_severity(None) is None


def test_map_severity_from_cvss_score():
    assert map_severity("9.8") == "CRITICAL"
    assert map_severity("7.5") == "HIGH"
    assert map_severity("5.0") == "MEDIUM"
    assert map_severity("2.1") == "LOW"


def test_map_severity_boundary_values():
    assert map_severity("9.0") == "CRITICAL"
    assert map_severity("7.0") == "HIGH"
    assert map_severity("4.0") == "MEDIUM"
    assert map_severity("3.9") == "LOW"
    assert map_severity("0.0") == "LOW"


def test_map_severity_unknown_string():
    assert map_severity("UNKNOWN") is None
    assert map_severity("moderate") is None


# ---------------------------------------------------------------------------
# Checksum verification tests
# ---------------------------------------------------------------------------


def test_verify_checksum_no_checksum_passes():
    assert verify_checksum(b"anything", None) is True


def test_verify_checksum_mismatch_fails():
    assert verify_checksum(b"hello world", "0" * 64) is False


def test_verify_checksum_match_passes():
    content = b"hello world"
    digest = hashlib.sha256(content).hexdigest()
    assert verify_checksum(content, digest) is True


def test_verify_checksum_case_insensitive():
    content = b"test data"
    digest = hashlib.sha256(content).hexdigest()
    assert verify_checksum(content, digest.upper()) is True


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------


def _patch(model="R750", version="1.0", vendor="dell", component="BIOS", severity=None):
    return CanonicalPatch(
        vendor=vendor,
        model=model,
        component_type=component,
        version_raw=version,
        version_normalized=normalize_version(vendor, version),
        release_date=date(2026, 1, 1),
        severity=severity,
        advisory_url="https://example.com",
        source_adapter="test",
    )


def test_dedup_collapses_duplicates():
    patches = [_patch(), _patch(), _patch(model="R650")]
    result = dedup(patches)
    assert len(result) == 2


def test_dedup_keeps_different_versions():
    patches = [_patch(version="1.0"), _patch(version="1.1"), _patch(version="1.2")]
    result = dedup(patches)
    assert len(result) == 3


def test_dedup_keeps_different_components():
    patches = [
        _patch(component="BIOS"),
        _patch(component="iDRAC"),
        _patch(component="NIC"),
    ]
    result = dedup(patches)
    assert len(result) == 3


def test_dedup_last_wins():
    p1 = _patch(severity="LOW")
    p2 = _patch(severity="HIGH")  # Same key, should win
    result = dedup([p1, p2])
    assert len(result) == 1
    assert result[0].severity == "HIGH"


def test_dedup_empty_list():
    assert dedup([]) == []


# ---------------------------------------------------------------------------
# NetScaler adapter parsing tests (unit-level)
# ---------------------------------------------------------------------------


def test_netscaler_build_regex():
    """Verify the build number regex pattern works on typical bulletin titles."""
    pattern = re.compile(r"(\d{2}\.\d)-(\d+\.\d+)")

    assert pattern.search("NetScaler ADC 14.1-34.42 Security Bulletin")
    assert pattern.search("Citrix ADC and Gateway 13.1-54.14 update")
    assert pattern.search("Version 13.0-92.31 patch")

    m = pattern.search("NetScaler ADC 14.1-34.42")
    assert m.group(1) == "14.1"
    assert m.group(2) == "34.42"


def test_netscaler_cve_regex():
    """Verify CVE extraction from text."""
    pattern = re.compile(r"CVE-\d{4}-\d{4,7}")

    text = "Fixes CVE-2026-12345 and CVE-2026-67890 in NetScaler ADC"
    cves = pattern.findall(text)
    assert len(cves) == 2
    assert "CVE-2026-12345" in cves
    assert "CVE-2026-67890" in cves


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_canonical_patch_defaults():
    p = CanonicalPatch(
        vendor="test",
        model="TestModel",
        component_type="Firmware",
        version_raw="1.0",
        version_normalized="000001.000000",
        release_date=date(2026, 1, 1),
        advisory_url="https://example.com",
        source_adapter="test",
    )
    assert p.cves == []
    assert p.download_url is None
    assert p.requires_entitlement is False
    assert p.checksum_sha256 is None
    assert p.severity is None


def test_canonical_patch_all_fields():
    p = CanonicalPatch(
        vendor="cisco",
        model="Catalyst 9300",
        component_type="IOS-XE",
        version_raw="17.12.03",
        version_normalized="000017.000012.000003",
        release_date=date(2026, 6, 15),
        severity="CRITICAL",
        cves=["CVE-2026-20150", "CVE-2026-20151"],
        advisory_url="https://sec.cloudapps.cisco.com/advisory",
        download_url="https://software.cisco.com/download",
        requires_entitlement=True,
        checksum_sha256="e3b0c44298fc1c149afbf4c8996fb924",
        source_adapter="cisco_openvuln",
    )
    assert p.severity == "CRITICAL"
    assert len(p.cves) == 2
    assert p.requires_entitlement is True
