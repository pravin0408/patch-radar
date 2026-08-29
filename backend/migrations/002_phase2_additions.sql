-- Phase 2 schema additions: additional indexes and webhook/cache support tables

-- Full-text search index on model column for dashboard search
CREATE INDEX IF NOT EXISTS idx_patch_model_search ON patch_catalog USING gin (to_tsvector('english', model));

-- Index for gap report queries
CREATE INDEX IF NOT EXISTS idx_patch_latest_lookup ON patch_catalog (vendor_id, model, component_type, is_latest)
    WHERE is_latest = TRUE;

-- Index for product family lookup
CREATE INDEX IF NOT EXISTS idx_product_family_vendor ON product_families (vendor_id);

-- Webhook delivery audit log
CREATE TABLE IF NOT EXISTS webhook_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id VARCHAR(32) NOT NULL REFERENCES vendors(id),
    target_type VARCHAR(20) NOT NULL,                -- 'slack' | 'teams' | 'pagerduty' | 'generic'
    patch_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'SENT',      -- 'SENT' | 'FAILED'
    error TEXT,
    dispatched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_webhook_audit_vendor ON webhook_audit (vendor_id, dispatched_at DESC);
