from __future__ import annotations

import csv
import io
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import ADAPTERS
from app.auth import create_token, require_role
from app.cache import (
    cache_get,
    cache_invalidate_all,
    cache_set,
    check_rate_limit,
    close_redis,
)
from app.config import settings
from app.db import get_db
from app.ingestion import run_ingestion
from app.models import PatchCatalog, Vendor
from app.normalizer import normalize_version
from app.scheduler import start_scheduler, stop_scheduler
from app.schemas import (
    AssetInventoryUpload,
    GapReportEntry,
    GapReportResponse,
    IngestResultOut,
    PatchListResponse,
    PatchOut,
    TokenRequest,
    TokenResponse,
    VendorStatusOut,
)

logger = logging.getLogger("patch_radar.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()
    await close_redis()


app = FastAPI(
    title="Unified Hardware Patch & Advisory Radar",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Rate Limiting Middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply per-IP rate limiting to API endpoints."""
    if request.url.path.startswith("/api/"):
        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining = await check_rate_limit(
            f"api:{client_ip}",
            max_requests=settings.api_rate_limit_per_minute,
            window_seconds=60,
        )
        if not allowed:
            return StreamingResponse(
                iter([b'{"detail":"Rate limit exceeded. Try again later."}']),
                status_code=429,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": "60",
                    "X-RateLimit-Remaining": "0",
                },
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
    return await call_next(request)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Patches (read)
# ---------------------------------------------------------------------------


@app.get("/api/v1/patches", response_model=PatchListResponse)
async def list_patches(
    vendor: Optional[str] = None,
    model: Optional[str] = None,
    severity: Optional[str] = None,
    latest_only: bool = True,
    allow_stale: bool = True,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    # Check for DEGRADED vendors when latest_only is requested
    if latest_only and not allow_stale and vendor:
        vendor_row = (
            await db.execute(select(Vendor).where(Vendor.id == vendor))
        ).scalar_one_or_none()
        if vendor_row and vendor_row.status == "DEGRADED":
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Vendor '{vendor}' is DEGRADED ({vendor_row.consecutive_failures} "
                    f"consecutive failures). Data may be stale. "
                    f"Pass allow_stale=true to see cached data."
                ),
            )

    # Try cache
    cache_params = {
        "vendor": vendor, "model": model, "severity": severity,
        "latest_only": latest_only, "limit": limit, "offset": offset,
    }
    cached = await cache_get("patches", cache_params)
    if cached:
        return PatchListResponse(**json.loads(cached))

    # Query
    stmt = select(PatchCatalog)
    count_stmt = select(func.count(PatchCatalog.id))

    if vendor:
        stmt = stmt.where(PatchCatalog.vendor_id == vendor)
        count_stmt = count_stmt.where(PatchCatalog.vendor_id == vendor)
    if model:
        stmt = stmt.where(PatchCatalog.model.ilike(f"%{model}%"))
        count_stmt = count_stmt.where(PatchCatalog.model.ilike(f"%{model}%"))
    if severity:
        stmt = stmt.where(PatchCatalog.severity_level == severity.upper())
        count_stmt = count_stmt.where(PatchCatalog.severity_level == severity.upper())
    if latest_only:
        stmt = stmt.where(PatchCatalog.is_latest.is_(True))
        count_stmt = count_stmt.where(PatchCatalog.is_latest.is_(True))

    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(PatchCatalog.release_date.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()

    results = [
        PatchOut(
            vendor=row.vendor_id,
            model=row.model,
            component_type=row.component_type,
            version=row.version_raw,
            release_date=row.release_date,
            severity=row.severity_level,
            cves=row.cve_identifiers or [],
            advisory_url=row.advisory_url,
            download_url=row.download_url,
            requires_entitlement=row.requires_entitlement,
            is_latest=row.is_latest,
            is_recommended=row.is_recommended,
        )
        for row in rows
    ]

    response = PatchListResponse(
        count=len(results),
        total=total,
        limit=limit,
        offset=offset,
        results=results,
    )

    # Cache the response
    await cache_set("patches", cache_params, response.model_dump_json(), settings.cache_ttl_patches)

    return response


@app.get("/api/v1/patches/{vendor}/{model}/latest", response_model=PatchOut)
async def get_latest_for_model(vendor: str, model: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(PatchCatalog)
        .where(
            PatchCatalog.vendor_id == vendor,
            PatchCatalog.model == model,
            PatchCatalog.is_latest.is_(True),
        )
        .order_by(PatchCatalog.release_date.desc())
        .limit(1)
    )
    row = (await db.execute(stmt)).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="No matching patch record found")

    return PatchOut(
        vendor=row.vendor_id,
        model=row.model,
        component_type=row.component_type,
        version=row.version_raw,
        release_date=row.release_date,
        severity=row.severity_level,
        cves=row.cve_identifiers or [],
        advisory_url=row.advisory_url,
        download_url=row.download_url,
        requires_entitlement=row.requires_entitlement,
        is_latest=row.is_latest,
        is_recommended=row.is_recommended,
    )


# ---------------------------------------------------------------------------
# CSV Export (server-side)
# ---------------------------------------------------------------------------


@app.get("/api/v1/patches/export.csv")
async def export_patches_csv(
    vendor: Optional[str] = None,
    model: Optional[str] = None,
    severity: Optional[str] = None,
    latest_only: bool = True,
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_role("SecurityAnalyst")),
):
    """Server-side CSV export of patch data."""
    stmt = select(PatchCatalog)
    if vendor:
        stmt = stmt.where(PatchCatalog.vendor_id == vendor)
    if model:
        stmt = stmt.where(PatchCatalog.model.ilike(f"%{model}%"))
    if severity:
        stmt = stmt.where(PatchCatalog.severity_level == severity.upper())
    if latest_only:
        stmt = stmt.where(PatchCatalog.is_latest.is_(True))
    stmt = stmt.order_by(PatchCatalog.release_date.desc()).limit(5000)

    rows = (await db.execute(stmt)).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "vendor", "model", "component_type", "version", "release_date",
        "severity", "cves", "advisory_url", "download_url",
        "requires_entitlement", "is_latest", "is_recommended",
    ])
    for row in rows:
        writer.writerow([
            row.vendor_id,
            row.model,
            row.component_type,
            row.version_raw,
            row.release_date.isoformat(),
            row.severity_level or "",
            ";".join(row.cve_identifiers or []),
            row.advisory_url,
            row.download_url or "",
            row.requires_entitlement,
            row.is_latest,
            row.is_recommended,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=patch-radar-export.csv",
        },
    )


# ---------------------------------------------------------------------------
# Vendors
# ---------------------------------------------------------------------------


@app.get("/api/v1/vendors", response_model=list[VendorStatusOut])
async def list_vendor_status(db: AsyncSession = Depends(get_db)):
    # Try cache
    cached = await cache_get("vendors", {"all": True})
    if cached:
        return json.loads(cached)

    rows = (await db.execute(select(Vendor))).scalars().all()
    results = [
        VendorStatusOut(
            id=v.id,
            display_name=v.display_name,
            status=v.status,
            last_success_at=v.last_success_at,
            consecutive_failures=v.consecutive_failures,
        )
        for v in rows
    ]

    # Cache
    await cache_set(
        "vendors",
        {"all": True},
        json.dumps([r.model_dump(mode="json") for r in results]),
        settings.cache_ttl_vendors,
    )
    return results


# ---------------------------------------------------------------------------
# Ingestion (admin)
# ---------------------------------------------------------------------------


@app.post("/api/v1/ingest/{vendor}", response_model=IngestResultOut)
async def trigger_ingestion(
    vendor: str,
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_role("OpsAdmin")),
):
    if vendor not in ADAPTERS:
        raise HTTPException(status_code=404, detail=f"Unknown vendor '{vendor}'")
    return await run_ingestion(vendor, db)


# ---------------------------------------------------------------------------
# Asset Inventory & Gap Report
# ---------------------------------------------------------------------------


@app.post("/api/v1/inventory/gap-report", response_model=GapReportResponse)
async def generate_gap_report(
    upload: AssetInventoryUpload,
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_role("SecurityAnalyst")),
):
    """Upload an asset inventory and get a delta/gap report showing which
    assets are behind the latest available patches."""
    gaps: list[GapReportEntry] = []
    critical_count = 0

    for asset in upload.assets:
        # Find the latest patch for this asset's vendor/model/component
        stmt = (
            select(PatchCatalog)
            .where(
                PatchCatalog.vendor_id == asset.vendor,
                PatchCatalog.model == asset.model,
                PatchCatalog.component_type == asset.component_type,
                PatchCatalog.is_latest.is_(True),
            )
            .order_by(PatchCatalog.version_normalized.desc())
            .limit(1)
        )
        latest = (await db.execute(stmt)).scalars().first()

        if latest is None:
            gaps.append(
                GapReportEntry(
                    vendor=asset.vendor,
                    model=asset.model,
                    component_type=asset.component_type,
                    current_version=asset.current_version,
                    latest_version=None,
                    latest_release_date=None,
                    severity=None,
                    cves=[],
                    advisory_url=None,
                    is_behind=False,
                    versions_behind=0,
                )
            )
            continue

        current_norm = normalize_version(asset.vendor, asset.current_version)
        is_behind = current_norm < latest.version_normalized

        # Count how many versions are between current and latest
        versions_behind = 0
        if is_behind:
            count_stmt = (
                select(func.count(PatchCatalog.id))
                .where(
                    PatchCatalog.vendor_id == asset.vendor,
                    PatchCatalog.model == asset.model,
                    PatchCatalog.component_type == asset.component_type,
                    PatchCatalog.version_normalized > current_norm,
                )
            )
            versions_behind = (await db.execute(count_stmt)).scalar() or 0

        if is_behind and latest.severity_level in ("CRITICAL", "HIGH"):
            critical_count += 1

        gaps.append(
            GapReportEntry(
                vendor=asset.vendor,
                model=asset.model,
                component_type=asset.component_type,
                current_version=asset.current_version,
                latest_version=latest.version_raw,
                latest_release_date=latest.release_date,
                severity=latest.severity_level,
                cves=latest.cve_identifiers or [],
                advisory_url=latest.advisory_url,
                is_behind=is_behind,
                versions_behind=versions_behind,
            )
        )

    return GapReportResponse(
        total_assets=len(upload.assets),
        assets_behind=sum(1 for g in gaps if g.is_behind),
        critical_gaps=critical_count,
        gaps=gaps,
    )


# ---------------------------------------------------------------------------
# Auth (dev token generation)
# ---------------------------------------------------------------------------


@app.post("/api/v1/auth/token", response_model=TokenResponse)
async def generate_dev_token(req: TokenRequest):
    """Generate a JWT token for development/testing.
    Only available when AUTH_DISABLED=true."""
    if not settings.auth_disabled:
        raise HTTPException(
            status_code=403,
            detail="Token generation endpoint is only available in development mode",
        )
    token = create_token(req.subject, req.role, req.expires_in_seconds)
    return TokenResponse(
        access_token=token,
        expires_in=req.expires_in_seconds,
        role=req.role,
    )


# ---------------------------------------------------------------------------
# Cache Management (admin)
# ---------------------------------------------------------------------------


@app.post("/api/v1/admin/cache/flush")
async def flush_cache(_auth=Depends(require_role("OpsAdmin"))):
    """Flush all API cache entries."""
    deleted = await cache_invalidate_all()
    return {"flushed": deleted}
