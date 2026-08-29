# Frontend — Unified Hardware Patch & Advisory Radar

Next.js (App Router) + Tailwind dashboard, consuming the backend REST API.

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ UNIFIED HARDWARE PATCH & ADVISORY RADAR              [Export] [API]  │
├──────────────────────────────────────────────────────────────────────┤
│ Filter: [Vendor ▼] [Severity ▼] [Search model...]                    │
├──────────┬────────────────┬───────────┬──────────┬──────────┬───────┤
│ Vendor   │ Model          │ Component │ Version  │ Released │ Sev.  │ Links
├──────────┼────────────────┼───────────┼──────────┼──────────┼───────┤
│ Dell     │ PowerEdge R750 │ BIOS      │ 1.14.2   │ Jun 2026 │ HIGH  │ ↗
│ Cisco    │ Catalyst 9300  │ IOS-XE    │ 17.12.03 │ Jun 2026 │ CRIT  │ ↗
└──────────┴────────────────┴───────────┴──────────┴──────────┴───────┘
```

## Component structure

- `app/page.tsx` — page shell, fetches `/api/v1/patches`, holds filter state
- `components/PatchTable.tsx` — renders the table, severity badges, link icons
- `components/FilterBar.tsx` — vendor/severity/search controls
- `components/VendorStatusBadge.tsx` — shows `OK`/`DEGRADED` per vendor,
  backed by `GET /vendors`

## Data fetching

Client-side fetch to the FastAPI backend (`NEXT_PUBLIC_API_BASE_URL`,
default `http://localhost:8000/api/v1`). Server components can be used later
for SSR/caching once the backend is behind a stable internal hostname.

## Styling

Tailwind utility classes; severity badges color-coded
(`CRITICAL`=red, `HIGH`=orange, `MEDIUM`=yellow, `LOW`=gray).

## Not yet built (Phase 3)

- CSV/JSON export button (backend route not yet added)
- Asset inventory upload + gap report
- Webhook configuration UI
