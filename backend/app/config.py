from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://patch_radar:patch_radar@localhost:5432/patch_radar"
    redis_url: str = "redis://localhost:6379/0"

    cisco_client_id: str | None = None
    cisco_client_secret: str | None = None

    dell_csaf_base_url: str = "https://www.dell.com/support/security/csaf"
    hpe_sdr_base_url: str = "https://support.hpe.com/hpesc/public/sdr"
    netscaler_bulletin_rss_url: str = "https://support.citrix.com/csaf/rss"

    # Additional Enterprise Vendor Feeds (Phase 3)
    vmware_advisories_url: str = "https://www.vmware.com/security/advisories.xml"
    paloalto_api_url: str = "https://security.paloaltonetworks.com/api/v1/advisories"
    fortinet_rss_url: str = "https://fortiguard.fortinet.com/rss/ir.xml"
    
    ingestion_interval_hours: int = 6
    auth_disabled: bool = True

    # JWT auth (used when AUTH_DISABLED=false)
    jwt_secret: str = "change-me-in-production-use-a-real-secret"

    # Webhook targets (leave empty to disable)
    webhook_slack_url: str = ""
    webhook_teams_url: str = ""
    webhook_generic_url: str = ""
    webhook_pagerduty_key: str = ""

    # Cache TTL (seconds)
    cache_ttl_patches: int = 300  # 5 minutes
    cache_ttl_vendors: int = 60   # 1 minute

    # Rate limiting
    api_rate_limit_per_minute: int = 120


settings = Settings()
