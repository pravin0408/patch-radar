from __future__ import annotations

import logging
from datetime import date

import httpx

from app.adapters.base import BaseAdapter
from app.normalizer import normalize_version
from app.schemas import CanonicalPatch

logger = logging.getLogger("patch_radar.adapters.f5")


class F5Adapter(BaseAdapter):
    """Adapter for F5 Networks (BIG-IP).
    
    F5 doesn't provide a cleanly structured public RSS/JSON for all security advisories
    in a unified way without an account. This is a placeholder stub that will be expanded 
    in future enterprise iterations to connect to the MYF5 API.
    """

    vendor_id = "f5"

    async def fetch(self) -> list[CanonicalPatch]:
        # Without an authenticated API endpoint, we will return an empty list here to 
        # demonstrate standard handling until Phase 4 (auth'd enterprise connectors).
        logger.debug("F5 adapter executing (stub mode)")
        return []

