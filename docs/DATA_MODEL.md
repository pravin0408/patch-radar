# Unified Data Model

All vendor-specific schemas are normalized into one canonical model before
they touch the database.

## Canonical patch object (Python / Pydantic)

Defined in `backend/app/schemas.py` as `CanonicalPatch`:

```python
class CanonicalPatch(BaseModel):
    vendor: str                    # 'dell' | 'cisco' | 'netscaler' | 'hpe'
    model: str                     # e.g. 'PowerEdge R750'
    component_type: str            # 'BIOS' | 'iDRAC' | 'IOS-XE' | 'Firmware' | ...
    version_raw: str               # vendor's own version string
    version_normalized: str        # comparable/sortable representation
    release_date: date
    severity: str | None           # 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
    cves: list[str] = []
    advisory_url: str
    download_url: str | None = None
    requires_entitlement: bool = False
    checksum_sha256: str | None = None
    source_adapter: str
```

## PostgreSQL schema

See `backend/migrations/001_init.sql` for the full DDL. Summary:

- `vendors` — one row per vendor, plus a `status` column (`OK` / `DEGRADED`)
  used by the circuit breaker.
- `product_families` — vendor product lines (PowerEdge, Catalyst, NetScaler
  ADC, ProLiant, ...).
- `patch_catalog` — the canonical table. One row per (model, component,
  version). Indexed on `(vendor_id, model, is_latest)` and `release_date`.
- `ingestion_audit` — one row per adapter run (started_at, finished_at,
  records_ingested, status, error) for observability.

## Canonical JSON API response

```json
{
  "vendor": "Cisco",
  "product_family": "Catalyst",
  "model": "Catalyst 9300 Series",
  "component": "IOS-XE",
  "latest_release": {
    "version": "17.12.03",
    "release_date": "2026-06-15",
    "is_vendor_recommended": true,
    "severity_rating": "HIGH",
    "addressed_cves": ["CVE-2026-20150", "CVE-2026-20151"],
    "links": {
      "advisory": "https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-iosxe-vuln-2026",
      "download": "https://software.cisco.com/download/home/286315874/type/282046477/release/17.12.03",
      "requires_auth": true
    },
    "checksum_sha256": null
  }
}
```

## Version normalization

Vendors use incompatible schemes:

- Dell: `17.9.4a` (semver-ish, with trailing letter suffixes)
- Cisco: `17.12.03`
- NetScaler: `14.1-34.42` (release-build format)
- HPE: SPP bundle versions + per-component versions

`app/normalizer.py` implements `normalize_version(vendor, raw) -> str`,
producing a zero-padded, lexicographically-sortable string per vendor family
so `is_latest` can be computed with a simple `MAX()` per `(model,
component_type)` group rather than vendor-specific comparison code scattered
throughout the app.
