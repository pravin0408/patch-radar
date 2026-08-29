# Security & InfoSec Controls

## 1. Egress & credential isolation

- Vendor API tokens (Cisco client credentials, Citrix OAuth, Dell API keys)
  are read from environment variables in this reference build
  (`app/config.py`), sourced from **HashiCorp Vault** or **AWS Secrets
  Manager** in production — never committed, never logged.
- Recommended rotation: every 90 days.
- Outbound adapter traffic should run through a dedicated egress proxy with
  IP allowlisting in production, both to prevent SSRF from a compromised
  adapter and to avoid tripping vendor rate limits.

## 2. Artifact integrity verification

- Where a vendor provides a SHA-256/SHA-512 checksum or a signed CSAF
  document, the ingestion worker verifies it (`normalizer.py::verify_checksum`)
  before the record is written to `patch_catalog`. Records that fail
  verification are dropped and logged, not silently published.

## 3. Data freshness SLA & circuit breaking

- Each vendor adapter runs every 4–6 hours (`scheduler.py`).
- Three consecutive adapter failures (HTTP 4xx/5xx, parse errors, checksum
  failures) flip that vendor's `vendors.status` to `DEGRADED` and fire an
  alert (Slack/PagerDuty webhook — interface defined in
  `app/adapters/base.py::AdapterResult`, not wired to a real endpoint in
  this build).
- `DEGRADED` vendors are still queryable but flagged in both the API
  (`GET /vendors`) and the dashboard, so stale data never masks a missed
  critical patch silently.

## 4. Access control

- Internal API: OAuth2 bearer token / mTLS.
- Two roles:
  - `SecurityAnalyst` — read/export only (`GET` routes)
  - `OpsAdmin` — can also configure connectors and trigger manual ingestion
    (`POST /ingest/{vendor}`)
- Enforced via a FastAPI dependency (`app/main.py::require_role`), stubbed in
  this build to always pass in dev mode — replace with real IdP/JWT
  validation before production use.

## 5. Secrets in this repo

`backend/.env.example` lists every required environment variable with a
placeholder value. **Never commit a real `.env`.** `.gitignore` already
excludes it.
