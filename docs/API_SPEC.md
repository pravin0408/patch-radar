# API Specification

Base URL (local dev): `http://localhost:8000/api/v1`

## `GET /patches`

List patch catalog entries with optional filters.

**Query params**

| Param | Type | Description |
|---|---|---|
| `vendor` | string | `dell`, `cisco`, `netscaler`, `hpe` |
| `model` | string | Substring match on model name |
| `severity` | string | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `latest_only` | bool | Default `true` — only return `is_latest` rows |
| `limit` | int | Default 50, max 500 |
| `offset` | int | Pagination offset |

**Response** `200 OK`

```json
{
  "count": 4,
  "results": [
    {
      "vendor": "dell",
      "model": "PowerEdge R750",
      "component_type": "BIOS",
      "version": "1.14.2",
      "release_date": "2026-06-01",
      "severity": "HIGH",
      "cves": ["CVE-2026-1234"],
      "advisory_url": "https://...",
      "download_url": "https://...",
      "requires_entitlement": false
    }
  ]
}
```

## `GET /patches/{vendor}/{model}/latest`

Return the single latest record for a given vendor + model.

## `GET /vendors`

Return vendor status (`OK` / `DEGRADED`) and last successful ingestion time —
backs the dashboard's freshness indicator.

## `POST /ingest/{vendor}`

Manually trigger an out-of-band ingestion run for one vendor (used for
testing adapters and for on-demand refresh from the dashboard). Protected —
requires `OpsAdmin` role (see `SECURITY.md`).

## `GET /healthz`

Liveness probe. No auth required.

## Errors

Standard FastAPI/Pydantic validation errors (`422`) for bad query params;
`404` for unknown vendor/model; `503` if the requested vendor is currently
`DEGRADED` and `latest_only=true` would otherwise silently serve stale data
(caller can pass `allow_stale=true` to override).

## Auth

Internal API is protected by an OAuth2 bearer token (or mTLS in production).
In this reference build, auth is stubbed as a FastAPI dependency
(`app/main.py::get_current_user`) that can be swapped for a real IdP
integration without touching route logic.
