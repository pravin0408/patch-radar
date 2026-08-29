-- Unified Hardware Patch & Advisory Radar — initial schema

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Vendor registry, with circuit-breaker status
CREATE TABLE IF NOT EXISTS vendors (
    id VARCHAR(32) PRIMARY KEY,              -- 'dell' | 'hpe' | 'cisco' | 'netscaler'
    display_name VARCHAR(100) NOT NULL,
    advisory_portal_url TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OK', -- 'OK' | 'DEGRADED'
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    last_success_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_families (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id VARCHAR(32) REFERENCES vendors(id),
    name VARCHAR(100) NOT NULL,               -- 'PowerEdge', 'Catalyst', 'NetScaler ADC', 'ProLiant'
    category VARCHAR(50) NOT NULL             -- 'Server', 'Switch', 'ADC', 'Storage'
);

CREATE TABLE IF NOT EXISTS patch_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id VARCHAR(32) NOT NULL REFERENCES vendors(id),
    product_family_id UUID REFERENCES product_families(id),
    model VARCHAR(100) NOT NULL,
    component_type VARCHAR(50) NOT NULL,      -- 'BIOS', 'iDRAC', 'IOS-XE', 'Firmware', ...

    version_raw VARCHAR(100) NOT NULL,
    version_normalized VARCHAR(100) NOT NULL,
    is_latest BOOLEAN DEFAULT FALSE,
    is_recommended BOOLEAN DEFAULT FALSE,

    release_date DATE NOT NULL,
    severity_level VARCHAR(20),
    cve_identifiers TEXT[] DEFAULT '{}',
    advisory_url TEXT NOT NULL,
    download_url TEXT,
    requires_entitlement BOOLEAN DEFAULT FALSE,
    checksum_sha256 VARCHAR(64),

    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    source_adapter VARCHAR(50) NOT NULL,

    UNIQUE (vendor_id, model, component_type, version_normalized)
);

CREATE INDEX IF NOT EXISTS idx_patch_lookup ON patch_catalog (vendor_id, model, is_latest);
CREATE INDEX IF NOT EXISTS idx_patch_release_date ON patch_catalog (release_date DESC);
CREATE INDEX IF NOT EXISTS idx_patch_severity ON patch_catalog (severity_level);

CREATE TABLE IF NOT EXISTS ingestion_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id VARCHAR(32) NOT NULL REFERENCES vendors(id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING', -- RUNNING | SUCCESS | FAILED
    records_ingested INTEGER DEFAULT 0,
    error TEXT
);

-- Seed vendors
INSERT INTO vendors (id, display_name, advisory_portal_url) VALUES
    ('dell', 'Dell EMC', 'https://www.dell.com/support/security'),
    ('cisco', 'Cisco', 'https://sec.cloudapps.cisco.com/security/center/publicationListing.x'),
    ('netscaler', 'NetScaler (Citrix / Cloud Software Group)', 'https://support.citrix.com/csaf'),
    ('hpe', 'HPE', 'https://support.hpe.com/hpesc/public/km/securityBulletins')
ON CONFLICT (id) DO NOTHING;
