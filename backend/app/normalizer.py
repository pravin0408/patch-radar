"""Version normalization, checksum verification, and dedup logic.

Produces strict lexicographically-sortable strings per vendor based on
semantic version hierarchies, allowing safe MAX() evaluation in the database.
"""

from __future__ import annotations

import hashlib
import re

from app.schemas import CanonicalPatch


def _format_sortable(major: int, minor: int, build: int, patch: int, revision: str) -> str:
    """Format parsed tokens into a rigid 5-part string for safe DB sorting."""
    # Note: revision is usually a letter ('a', 'b') or empty. We pad it so empty sorts first.
    return f"{major:05d}.{minor:05d}.{build:05d}.{patch:05d}.{revision:4}"


def _parse_netscaler(raw: str) -> tuple[int, int, int, int, str]:
    """Parse NetScaler formats like '14.1-34.42' or '13.1-9.60'"""
    # Pattern: Major.Minor-Build.Patch
    match = re.match(r"(\d+)\.(\d+)-(\d+)\.(\d+)", raw)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)), ""
    return _parse_generic(raw)


def _parse_cisco(raw: str) -> tuple[int, int, int, int, str]:
    """Parse Cisco IOS-XE formats like '17.9.4a', '17.12.03', '17.9.4'"""
    # Pattern: Major.Minor.Patch[OptionalLetter]
    match = re.match(r"(\d+)\.(\d+)\.(\d+)([a-zA-Z]*)", raw)
    if match:
        patch_num = int(match.group(3))
        revision = match.group(4).lower()
        return int(match.group(1)), int(match.group(2)), patch_num, 0, revision
    return _parse_generic(raw)


def _parse_vmware(raw: str) -> tuple[int, int, int, int, str]:
    """Parse VMware formats like '8.0 U2d', '7.0.3', '8.0 U1'"""
    # Look for '8.0 U2d' format
    u_match = re.match(r"(\d+)\.(\d+)\s*U(\d+)([a-zA-Z]*)", raw, re.IGNORECASE)
    if u_match:
        return int(u_match.group(1)), int(u_match.group(2)), int(u_match.group(3)), 0, u_match.group(4).lower()
    
    # Look for '7.0.3' format
    dot_match = re.match(r"(\d+)\.(\d+)\.(\d+)([a-zA-Z]*)", raw)
    if dot_match:
        return int(dot_match.group(1)), int(dot_match.group(2)), int(dot_match.group(3)), 0, dot_match.group(4).lower()
    
    return _parse_generic(raw)


def _parse_generic(raw: str) -> tuple[int, int, int, int, str]:
    """Fallback parser: aggressively extract top 4 numbers in order."""
    numbers = [int(n) for n in re.findall(r"\d+", raw)]
    # Pad to at least 4 numbers
    while len(numbers) < 4:
        numbers.append(0)
    
    # Extract trailing letters if they exist at the very end
    letters = re.findall(r"[a-zA-Z]+", raw)
    revision = letters[-1].lower() if letters else ""
    
    return numbers[0], numbers[1], numbers[2], numbers[3], revision


def normalize_version(vendor: str, raw: str) -> str:
    """Public entrypoint. Routes version to the correct vendor semantic parser."""
    raw = raw.strip()
    
    # Placeholders bypass strict parsing
    if raw.lower() in ("see-advisory", "unknown", ""):
        return f"00000.00000.00000.00000.{raw[:4]}"

    if vendor == "netscaler":
        parsed = _parse_netscaler(raw)
    elif vendor == "cisco":
        parsed = _parse_cisco(raw)
    elif vendor == "vmware":
        parsed = _parse_vmware(raw)
    else:
        parsed = _parse_generic(raw)

    return _format_sortable(*parsed)


def verify_checksum(content: bytes, expected_sha256: str | None) -> bool:
    """Return True if no checksum was provided (nothing to verify) or if
    the computed SHA-256 matches."""
    if not expected_sha256:
        return True
    computed = hashlib.sha256(content).hexdigest()
    return computed.lower() == expected_sha256.lower()


def dedup(patches: list[CanonicalPatch]) -> list[CanonicalPatch]:
    """Collapse duplicate (vendor, model, component_type, version_normalized)
    records, keeping the most recently ingested one."""
    seen: dict[tuple[str, str, str, str], CanonicalPatch] = {}
    for p in patches:
        key = (p.vendor, p.model, p.component_type, p.version_normalized)
        seen[key] = p
    return list(seen.values())


SEVERITY_ORDER = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}


def map_severity(vendor_severity: str | None) -> str | None:
    """Normalize vendor-specific severity strings into our canonical set."""
    if not vendor_severity:
        return None
    s = vendor_severity.strip().upper()
    if s in SEVERITY_ORDER:
        return s
    
    try:
        score = float(vendor_severity)
        if score >= 9.0:
            return "CRITICAL"
        if score >= 7.0:
            return "HIGH"
        if score >= 4.0:
            return "MEDIUM"
        return "LOW"
    except ValueError:
        return None
