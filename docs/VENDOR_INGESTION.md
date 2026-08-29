# Vendor Ingestion Strategy

| Vendor | Primary source | Fallback | Auth | Data extracted |
|---|---|---|---|---|
| **Dell EMC** | Dell CSAF 2.0 feed (`/support/security/csaf/`) & Dell Catalog XML (`ftp.dell.com/catalog/`) | TechDirect / OpenManage Enterprise API | Public CSAF; mTLS for enterprise APIs | Model, component firmware version, release date, fix advisory URL, SHA256 |
| **Cisco** | openVuln API (`api.cisco.com/security/advisories`) | Suggested Releases API, DevNet RSS | OAuth2 client-credentials (Cisco DevNet) | OS (IOS/IOS-XE/NX-OS/FXOS), recommended release, release date, mitigation link |
| **NetScaler (Citrix)** | Cloud Software Group CSAF / Security Bulletins RSS | NetScaler release-notes scraping, NITRO API build check | Public RSS; headless browser for HTML fallback | Build number (e.g. `14.1-34.42`), release date, critical CVEs, download link |
| **HPE** | HPE Software Delivery Repository (SDR) JSON/XML feeds | HPE Support Center CSAF / SPP catalog | Public SDR; token-gated for entitlement-only SPPs | Component firmware, SPP bundle version, release date, advisory URL |

## Adapter contract

Every adapter implements the same interface (`backend/app/adapters/base.py`):

```python
class BaseAdapter(ABC):
    vendor_id: str

    async def fetch(self) -> list[CanonicalPatch]:
        """Return normalized patch records for this vendor."""
```

This means:
- The scheduler and normalizer never need vendor-specific logic.
- Adding a fifth vendor is "write one adapter file," not "touch the pipeline."
- Each adapter can fail independently — a Cisco outage does not block Dell
  ingestion.

## Per-adapter notes (this build)

- **Dell (`adapters/dell.py`)** — implemented against the public CSAF feed.
  No credentials required, so this is the reference/happy-path adapter.
- **Cisco (`adapters/cisco.py`)** — implemented against openVuln with the
  OAuth2 client-credentials flow. Requires `CISCO_CLIENT_ID` /
  `CISCO_CLIENT_SECRET` env vars (see `SETUP.md`). Falls back to an empty
  result with a logged warning if credentials are absent, so the rest of the
  system still runs in dev.
- **NetScaler (`adapters/netscaler.py`)** — stubbed. RSS/CSAF parsing is
  straightforward (see `_parse_rss` stub); HTML scraping fallback intentionally
  left as a TODO since it needs a headless browser dependency (Playwright)
  that's a separate infra decision (see `ROADMAP.md` Phase 2).
- **HPE (`adapters/hpe.py`)** — stubbed the same way, pending SDR feed URL
  and entitlement-token handling for gated SPPs.

## Freshness & circuit breaking

- Each adapter is scheduled independently, every 4–6 hours (`scheduler.py`).
- If an adapter raises 3 consecutive failures (HTTP 4xx/5xx or parse errors),
  the vendor's data is flagged `DEGRADED` in `vendors.status` rather than
  silently serving stale data (see `SECURITY.md` §3).
