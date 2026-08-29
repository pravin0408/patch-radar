from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CanonicalPatch(BaseModel):
    """The single normalized shape every vendor adapter must produce."""

    vendor: str  # 'dell' | 'cisco' | 'netscaler' | 'hpe' | 'vmware' | 'paloalto' | 'fortinet' | 'f5'
    model: str
    component_type: str
    version_raw: str
    version_normalized: str
    release_date: date
    severity: Optional[str] = None  # CRITICAL | HIGH | MEDIUM | LOW
    cves: list[str] = Field(default_factory=list)
    advisory_url: str
    download_url: Optional[str] = None
    requires_entitlement: bool = False
    checksum_sha256: Optional[str] = None
    source_adapter: str


class PatchOut(BaseModel):
    vendor: str
    model: str
    component_type: str
    version: str
    release_date: date
    severity: Optional[str]
    cves: list[str]
    advisory_url: str
    download_url: Optional[str]
    requires_entitlement: bool
    is_latest: bool
    is_recommended: bool


class PatchListResponse(BaseModel):
    count: int
    total: int = 0  # Total matching records (for pagination)
    limit: int = 50
    offset: int = 0
    results: list[PatchOut]


class VendorStatusOut(BaseModel):
    id: str
    display_name: str
    status: str
    last_success_at: Optional[datetime]
    consecutive_failures: int


class IngestResultOut(BaseModel):
    vendor: str
    status: str
    records_ingested: int
    error: Optional[str] = None


# --- Asset Inventory & Gap Report ---


class AssetEntry(BaseModel):
    """A single asset from a user's inventory."""
    vendor: str
    model: str
    component_type: str
    current_version: str


class AssetInventoryUpload(BaseModel):
    """Batch asset inventory upload."""
    assets: list[AssetEntry]


class GapReportEntry(BaseModel):
    """A single gap between an asset's current version and the latest patch."""
    vendor: str
    model: str
    component_type: str
    current_version: str
    latest_version: Optional[str]
    latest_release_date: Optional[date]
    severity: Optional[str]
    cves: list[str] = Field(default_factory=list)
    advisory_url: Optional[str]
    is_behind: bool
    versions_behind: int = 0


class GapReportResponse(BaseModel):
    total_assets: int
    assets_behind: int
    critical_gaps: int
    gaps: list[GapReportEntry]


# --- Auth ---


class TokenRequest(BaseModel):
    """Request body for dev token generation."""
    subject: str = "dev-user"
    role: str = "OpsAdmin"
    expires_in_seconds: int = 86400


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
