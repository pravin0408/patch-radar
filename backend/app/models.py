from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String(32), primary_key=True)
    display_name = Column(String(100), nullable=False)
    advisory_portal_url = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="OK")
    consecutive_failures = Column(Integer, nullable=False, default=0)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    patches = relationship("PatchCatalog", back_populates="vendor")


class ProductFamily(Base):
    __tablename__ = "product_families"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(String(32), ForeignKey("vendors.id"))
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)


class PatchCatalog(Base):
    __tablename__ = "patch_catalog"
    __table_args__ = (
        UniqueConstraint(
            "vendor_id", "model", "component_type", "version_normalized",
            name="uq_patch_identity",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(String(32), ForeignKey("vendors.id"), nullable=False)
    product_family_id = Column(UUID(as_uuid=True), ForeignKey("product_families.id"), nullable=True)

    model = Column(String(100), nullable=False)
    component_type = Column(String(50), nullable=False)

    version_raw = Column(String(100), nullable=False)
    version_normalized = Column(String(100), nullable=False)
    is_latest = Column(Boolean, default=False)
    is_recommended = Column(Boolean, default=False)

    release_date = Column(Date, nullable=False)
    severity_level = Column(String(20), nullable=True)
    cve_identifiers = Column(ARRAY(String), default=list)
    advisory_url = Column(Text, nullable=False)
    download_url = Column(Text, nullable=True)
    requires_entitlement = Column(Boolean, default=False)
    checksum_sha256 = Column(String(64), nullable=True)

    ingested_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    source_adapter = Column(String(50), nullable=False)

    vendor = relationship("Vendor", back_populates="patches")


class IngestionAudit(Base):
    __tablename__ = "ingestion_audit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(String(32), ForeignKey("vendors.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="RUNNING")
    records_ingested = Column(Integer, default=0)
    error = Column(Text, nullable=True)
