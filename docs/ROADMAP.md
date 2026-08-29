# Phased Implementation Roadmap

## Phase 1 — MVP & direct feeds (Weeks 1–3) — ✅ implemented in this repo

- PostgreSQL schema, Redis, FastAPI core backend
- Dell CSAF JSON parser (no auth required)
- Cisco openVuln API client via OAuth2
- `GET /api/v1/patches` endpoint with filtering

## Phase 2 — Webhooks, scrapers & complex vendors (Weeks 4–6) — 🚧 scaffolded

- Headless-browser scrapers (Playwright) for NetScaler and HPE SDR feeds where
  no clean JSON/CSAF source exists
- Version normalization engine hardening (vendor-specific edge cases)
- Automated link/SHA-256 integrity verifier wired into every adapter
- Webhook dispatcher wired to Slack/Teams/SIEM for `CRITICAL` releases

## Phase 3 — Dashboard & enterprise connectors (Weeks 7–9) — 🚧 scaffolded

- Full-text search + filtering in the Next.js UI
- CSV/JSON export
- Asset inventory upload → delta/gap report against the catalog
- RBAC-backed connector configuration UI

## What's in this repo today

| Item | Status |
|---|---|
| Postgres schema + migrations | ✅ |
| FastAPI backend + REST API | ✅ |
| Dell adapter | ✅ working |
| Cisco adapter | ✅ working (needs credentials) |
| NetScaler adapter | 🚧 stub, same interface |
| HPE adapter | 🚧 stub, same interface |
| Normalizer + dedup | ✅ |
| Scheduler | ✅ (APScheduler, swappable) |
| Webhook dispatcher | 🚧 interface only |
| Next.js dashboard | ✅ working table + filters |
| CSV export, inventory gap report | 🚧 not started |
