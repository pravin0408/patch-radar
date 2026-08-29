# Architecture

## Problem

Dell EMC, Cisco, NetScaler (Citrix/Cloud Software Group), and HPE each publish
patch/firmware/advisory data through different mechanisms (CSAF feeds, REST
APIs, RSS, HTML). There is no single upstream API. This system aggregates all
four into one canonical catalog with direct advisory/download links.

## Pattern: Event-Driven Adapter Pipeline

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                        INGESTION TIER (Adapters)                        │
 │   Dell CSAF/Catalog   Cisco PSIRT/Rec API   NetScaler CSAF/RSS   HPE SDR │
 └──────────┬────────────────┬────────────────────┬────────────────┬──────┘
            ▼                ▼                    ▼                ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                    NORMALIZATION & VALIDATION                           │
 │  SemVer/build normalizer · checksum verifier · CVE enrichment · dedup   │
 └──────────────────────────────────┬──────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                       STORAGE & EVENT BUS                               │
 │  PostgreSQL (catalog, inventory, audit) · Redis (cache/rate-limit)      │
 │  Scheduler (APScheduler in this build; Temporal/Celery are drop-in      │
 │  replacements — see SETUP.md)                                          │
 └──────────────────────────────────┬──────────────────────────────────────┘
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                        API & CONSUMPTION                                │
 │  FastAPI REST · Next.js dashboard · Webhook dispatcher (Slack/Jira/SIEM)│
 └─────────────────────────────────────────────────────────────────────────┘
```

## Why this pattern

- **Adapters are isolated.** Each vendor's quirks (auth, pagination, HTML vs
  JSON, rate limits) live in one file implementing a shared interface
  (`BaseAdapter.fetch() -> list[CanonicalPatch]`). A vendor outage or schema
  change never touches other adapters.
- **Normalization is centralized.** Vendors use incompatible version schemes
  (`17.9.4a` vs `14.1-29.63` vs semantic BIOS versions). One normalizer owns
  the comparison logic so "is this the latest patch" is answered consistently
  everywhere else in the system.
- **Storage is boring on purpose.** Postgres for durable catalog data,
  Redis for cache/rate-limiting. No exotic infra required to run this.
- **Scheduling is pluggable.** The reference implementation uses
  APScheduler for simplicity; the interface is intentionally thin so it can
  be swapped for Celery beat or Temporal workflows without touching adapter
  code.

## Component responsibilities

| Component | Responsibility |
|---|---|
| `app/adapters/*` | Fetch raw vendor data, map to `CanonicalPatch` |
| `app/normalizer.py` | Version normalization, dedup, severity mapping |
| `app/models.py` | SQLAlchemy ORM / table definitions |
| `app/db.py` | Engine/session management |
| `app/main.py` | FastAPI app, REST routes |
| `app/scheduler.py` | Periodic ingestion trigger (every N hours) |
| `frontend/` | Next.js dashboard consuming the REST API |

See `DATA_MODEL.md` for the exact schema and `API_SPEC.md` for the exact
endpoints.
