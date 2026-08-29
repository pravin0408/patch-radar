from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import ADAPTERS
from app.adapters.base import AdapterResult
from app.cache import (
    acquire_ingestion_lock,
    cache_invalidate_namespace,
    release_ingestion_lock,
)
from app.models import IngestionAudit, PatchCatalog, ProductFamily, Vendor
from app.normalizer import dedup
from app.schemas import IngestResultOut
from app.webhooks import dispatch_new_patches

logger = logging.getLogger("patch_radar.ingestion")

FAILURE_THRESHOLD = 3

# Product family mapping for auto-population
_VENDOR_FAMILIES: dict[str, dict[str, tuple[str, str]]] = {
    "dell": {
        "PowerEdge": ("PowerEdge", "Server"),
        "iDRAC": ("PowerEdge", "Server"),
        "BIOS": ("PowerEdge", "Server"),
        "Storage": ("PowerStore", "Storage"),
        "Networking": ("Dell Networking", "Switch"),
    },
    "cisco": {
        "IOS XE": ("Catalyst", "Switch"),
        "IOS-XE": ("Catalyst", "Switch"),
        "NX-OS": ("Nexus", "Switch"),
        "FXOS": ("Firepower", "Firewall"),
        "IOS": ("IOS Devices", "Router"),
    },
    "netscaler": {
        "NetScaler ADC": ("NetScaler ADC", "ADC"),
        "NetScaler Gateway": ("NetScaler Gateway", "ADC"),
        "NetScaler SD-WAN": ("NetScaler SD-WAN", "Networking"),
    },
    "hpe": {
        "ProLiant": ("ProLiant", "Server"),
        "iLO": ("ProLiant", "Server"),
        "Synergy": ("Synergy", "Server"),
        "Nimble": ("Nimble Storage", "Storage"),
        "3PAR": ("3PAR StoreServ", "Storage"),
        "Alletra": ("Alletra", "Storage"),
    },
}


async def run_ingestion(vendor_id: str, db: AsyncSession) -> IngestResultOut:
    """Run one vendor's adapter, persist results, and update that vendor's
    circuit-breaker status. Never raises -- failures are captured in the
    returned IngestResultOut and in `vendors.status`."""
    if vendor_id not in ADAPTERS:
        return IngestResultOut(vendor=vendor_id, status="UNKNOWN_VENDOR", records_ingested=0)

    # Distributed lock: prevent concurrent ingestion for same vendor
    if not await acquire_ingestion_lock(vendor_id):
        return IngestResultOut(
            vendor=vendor_id,
            status="SKIPPED_LOCKED",
            records_ingested=0,
            error="Another ingestion run is in progress for this vendor",
        )

    audit = IngestionAudit(vendor_id=vendor_id, status="RUNNING")
    db.add(audit)
    await db.flush()

    try:
        adapter = ADAPTERS[vendor_id]()
        result: AdapterResult = await adapter.run()

        if result.success:
            patches = dedup(result.patches)
            await _upsert_patches(db, patches)
            await _recompute_is_latest(db, vendor_id)
            await _ensure_product_families(db, vendor_id, patches)
            await _mark_vendor_healthy(db, vendor_id)

            audit.status = "SUCCESS"
            audit.records_ingested = len(patches)
            audit.finished_at = datetime.utcnow()
            await db.commit()

            # Invalidate API cache for this vendor's data
            await cache_invalidate_namespace("patches")
            await cache_invalidate_namespace("vendors")

            # Dispatch webhook alerts for critical patches
            try:
                await dispatch_new_patches(vendor_id, patches)
            except Exception as exc:
                logger.warning("Webhook dispatch failed (non-blocking): %s", exc)

            return IngestResultOut(
                vendor=vendor_id, status="SUCCESS", records_ingested=len(patches)
            )

        await _mark_vendor_failure(db, vendor_id)
        audit.status = "FAILED"
        audit.error = result.error
        audit.finished_at = datetime.utcnow()
        await db.commit()

        return IngestResultOut(
            vendor=vendor_id, status="FAILED", records_ingested=0, error=result.error
        )
    finally:
        await release_ingestion_lock(vendor_id)


async def _upsert_patches(db: AsyncSession, patches) -> None:
    for p in patches:
        stmt = (
            pg_insert(PatchCatalog)
            .values(
                vendor_id=p.vendor,
                model=p.model,
                component_type=p.component_type,
                version_raw=p.version_raw,
                version_normalized=p.version_normalized,
                release_date=p.release_date,
                severity_level=p.severity,
                cve_identifiers=p.cves,
                advisory_url=p.advisory_url,
                download_url=p.download_url,
                requires_entitlement=p.requires_entitlement,
                checksum_sha256=p.checksum_sha256,
                source_adapter=p.source_adapter,
            )
            .on_conflict_do_update(
                index_elements=["vendor_id", "model", "component_type", "version_normalized"],
                set_=dict(
                    version_raw=p.version_raw,
                    release_date=p.release_date,
                    severity_level=p.severity,
                    cve_identifiers=p.cves,
                    advisory_url=p.advisory_url,
                    download_url=p.download_url,
                    requires_entitlement=p.requires_entitlement,
                    checksum_sha256=p.checksum_sha256,
                    ingested_at=datetime.utcnow(),
                    source_adapter=p.source_adapter,
                ),
            )
        )
        await db.execute(stmt)
    await db.flush()


async def _recompute_is_latest(db: AsyncSession, vendor_id: str) -> None:
    """Mark the highest version_normalized per (model, component_type) as
    is_latest=True, clearing the flag everywhere else for this vendor."""
    await db.execute(
        update(PatchCatalog).where(PatchCatalog.vendor_id == vendor_id).values(is_latest=False)
    )

    latest_ids_subq = (
        select(
            PatchCatalog.model,
            PatchCatalog.component_type,
        )
        .where(PatchCatalog.vendor_id == vendor_id)
        .group_by(PatchCatalog.model, PatchCatalog.component_type)
    )
    groups = (await db.execute(latest_ids_subq)).all()

    for model, component_type in groups:
        top = (
            select(PatchCatalog.id)
            .where(
                PatchCatalog.vendor_id == vendor_id,
                PatchCatalog.model == model,
                PatchCatalog.component_type == component_type,
            )
            .order_by(PatchCatalog.version_normalized.desc())
            .limit(1)
        )
        top_id = (await db.execute(top)).scalar_one_or_none()
        if top_id:
            await db.execute(
                update(PatchCatalog).where(PatchCatalog.id == top_id).values(is_latest=True)
            )
    await db.flush()


async def _ensure_product_families(
    db: AsyncSession, vendor_id: str, patches
) -> None:
    """Auto-populate product_families from ingested patches and link them."""
    families_config = _VENDOR_FAMILIES.get(vendor_id, {})
    existing = (
        await db.execute(
            select(ProductFamily).where(ProductFamily.vendor_id == vendor_id)
        )
    ).scalars().all()
    existing_names = {f.name for f in existing}
    name_to_id = {f.name: f.id for f in existing}

    for p in patches:
        family_name = None
        category = "Server"
        # Try to match by model or component
        for key, (fname, cat) in families_config.items():
            if key.lower() in p.model.lower() or key.lower() in p.component_type.lower():
                family_name = fname
                category = cat
                break
        if not family_name:
            family_name = p.model.split(" ")[0] if " " in p.model else p.model
            category = "Other"

        if family_name not in existing_names:
            pf = ProductFamily(
                vendor_id=vendor_id,
                name=family_name,
                category=category,
            )
            db.add(pf)
            await db.flush()
            existing_names.add(family_name)
            name_to_id[family_name] = pf.id

        # Link the patch to its product family
        if family_name in name_to_id:
            await db.execute(
                update(PatchCatalog)
                .where(
                    PatchCatalog.vendor_id == p.vendor,
                    PatchCatalog.model == p.model,
                    PatchCatalog.component_type == p.component_type,
                    PatchCatalog.version_normalized == p.version_normalized,
                )
                .values(product_family_id=name_to_id[family_name])
            )
    await db.flush()


async def _mark_vendor_healthy(db: AsyncSession, vendor_id: str) -> None:
    await db.execute(
        update(Vendor)
        .where(Vendor.id == vendor_id)
        .values(status="OK", consecutive_failures=0, last_success_at=datetime.utcnow())
    )


async def _mark_vendor_failure(db: AsyncSession, vendor_id: str) -> None:
    vendor = (await db.execute(select(Vendor).where(Vendor.id == vendor_id))).scalar_one_or_none()
    if vendor is None:
        return
    failures = vendor.consecutive_failures + 1
    new_status = "DEGRADED" if failures >= FAILURE_THRESHOLD else vendor.status
    await db.execute(
        update(Vendor)
        .where(Vendor.id == vendor_id)
        .values(consecutive_failures=failures, status=new_status)
    )
    await db.commit()
    if new_status == "DEGRADED":
        logger.error(
            "Vendor %s marked DEGRADED after %d consecutive ingestion failures",
            vendor_id, failures,
        )
