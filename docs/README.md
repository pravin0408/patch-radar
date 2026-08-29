# Unified Hardware Patch & Advisory Radar — Development Docs

This directory contains the full design documentation for the system, written
**before** implementation, so that engineering, security, and frontend work
can proceed from a single agreed-upon spec.

## Reading order

1. [`ARCHITECTURE.md`](./ARCHITECTURE.md) — system overview, component responsibilities, data flow
2. [`VENDOR_INGESTION.md`](./VENDOR_INGESTION.md) — per-vendor source, auth, and extraction details
3. [`DATA_MODEL.md`](./DATA_MODEL.md) — canonical schema (SQL + JSON) all adapters normalize into
4. [`API_SPEC.md`](./API_SPEC.md) — REST endpoints exposed by the backend
5. [`SECURITY.md`](./SECURITY.md) — credential handling, integrity checks, access control
6. [`FRONTEND.md`](./FRONTEND.md) — dashboard UX and component structure
7. [`ROADMAP.md`](./ROADMAP.md) — phased delivery plan
8. [`SETUP.md`](./SETUP.md) — how to run the system locally

## Scope of this build

This repository implements **Phase 1 + scaffolding for Phase 2/3** of the
roadmap:

- ✅ Postgres schema + FastAPI backend, fully wired
- ✅ Dell CSAF adapter (real HTTP client, no auth required)
- ✅ Cisco openVuln adapter (OAuth2 client-credentials flow)
- ✅ Normalizer + dedup engine
- ✅ `GET /api/v1/patches` query API with filtering
- 🚧 NetScaler & HPE adapters — stubbed with the same interface, ready to fill
  in scraper/SDR logic (Phase 2)
- 🚧 Webhook dispatcher — interface defined, not wired to Slack/Jira yet
- 🚧 Next.js dashboard — working page scaffold with table, filters, and API
  client; not a pixel-polished production UI

Everything is structured so each 🚧 item is a self-contained follow-up task.
