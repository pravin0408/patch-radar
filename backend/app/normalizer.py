"""Version normalization, checksum verification, and dedup logic.

Each vendor uses an incompatible version scheme. This module produces a
zero-padded, lexicographically-sortable string per vendor so `is_latest`
can be computed with a simple MAX() per (model, component_type) group,
instead of scattering vendor-specific comparison logic throughout the app.
"""

from __future__ import annotations

import hashlib
import re

from app.schemas import CanonicalPatch

_NUMERIC_RUN = re.compile(r"\d+")


def _zero_pad_numeric_parts(raw: str, width: int = 6) -> str:
    """Replace every run of digits with a zero-padded version, keep
    separators/letters as-is, so string comparison == numeric comparison.

    '17.9.4a'      -> '000017.000009.000004a'
    '14.1-34.42'   -> '000014.000001-000034.000042'
    '17.12.03'     -> '000017.000012.000003'
    """
    return _NUMERIC_RUN.sub(lambda m: m.group(0).zfill(width), raw)


def normalize_version(vendor: str, raw: str) -> str:
    """Public entrypoint. Vendor-specific quirks can be special-cased here
    without touching callers."""
    raw = raw.strip()
    if vendor == "netscaler":
        # NetScaler build numbers look like '14.1-34.42' (release-build).
        # Normalize the separator so it sorts the same as dotted versions.
        raw = raw.replace("-", ".")
    return _zero_pad_numeric_parts(raw)


def verify_checksum(content: bytes, expected_sha256: str | None) -> bool:
    """Return True if no checksum was provided (nothing to verify) or if
    the computed SHA-256 matches. Callers should drop records that fail
    this check rather than publish them."""
    if not expected_sha256:
        return True
    computed = hashlib.sha256(content).hexdigest()
    return computed.lower() == expected_sha256.lower()


def dedup(patches: list[CanonicalPatch]) -> list[CanonicalPatch]:
    """Collapse duplicate (vendor, model, component_type, version_normalized)
    records, keeping the most recently ingested one (last wins — adapters
    should already order results newest-first where possible)."""
    seen: dict[tuple[str, str, str, str], CanonicalPatch] = {}
    for p in patches:
        key = (p.vendor, p.model, p.component_type, p.version_normalized)
        seen[key] = p
    return list(seen.values())


SEVERITY_ORDER = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}


def map_severity(vendor_severity: str | None) -> str | None:
    """Normalize vendor-specific severity strings (e.g. Cisco's 'sir' field
    uses 'Critical'/'High'/..., others may use CVSS bands) into our
    canonical uppercase set."""
    if not vendor_severity:
        return None
    s = vendor_severity.strip().upper()
    if s in SEVERITY_ORDER:
        return s
    # Fallback: try to bucket a numeric CVSS score if one sneaks in.
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
