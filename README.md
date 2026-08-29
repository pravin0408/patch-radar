# Unified Hardware Patch & Advisory Radar

Aggregates patch, release-date, and direct advisory/download links across
**Dell EMC, Cisco, NetScaler (Citrix), and HPE** into one canonical catalog
and dashboard — no unified upstream vendor API required.

```
docs/       Design docs, written before implementation (start here)
backend/    FastAPI + PostgreSQL ingestion pipeline and REST API
frontend/   Next.js + Tailwind dashboard
```

## Quickstart

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db redis
psql "$DATABASE_URL" -f migrations/001_init.sql
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Full instructions: [`docs/SETUP.md`](./docs/SETUP.md).

## Status

Verified working in this build:
- ✅ Backend: 9/9 unit tests passing, FastAPI app imports and serves all
  routes, Dell CSAF adapter tested end-to-end against a sample advisory
- ✅ Frontend: type-checks clean, production build succeeds
  (`npm run build`)
- 🚧 NetScaler/HPE adapters are stubs (same interface, real HTTP calls,
  pending confirmed feed schemas) — see [`docs/ROADMAP.md`](./docs/ROADMAP.md)

## A note on the frontend dependency

`npm audit` flags the Next.js 14.2.x line broadly (the advisory range spans
9.x–16.x). The specific December 2025 RCE (CVE-2025-66478) and related RSC
CVEs affect the 15.x/16.x App Router deserialization path; 14.2.x was
confirmed not in the affected range at disclosure, and this project pins
the latest available 14.2.x patch release. A clean fix is a major-version
upgrade to Next 16, which involves App Router breaking changes — tracked as
follow-up work rather than done silently here.

See [`docs/README.md`](./docs/README.md) for the full documentation index.
