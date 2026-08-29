from __future__ import annotations

import logging
from datetime import date, datetime

import httpx

from app.adapters.base import BaseAdapter
from app.config import settings
from app.normalizer import map_severity, normalize_version
from app.schemas import CanonicalPatch

logger = logging.getLogger("patch_radar.adapters.cisco")


class CiscoAdapter(BaseAdapter):
    """Adapter for Cisco's openVuln API (PSIRT advisories) using the
    OAuth2 client-credentials flow. Requires CISCO_CLIENT_ID /
    CISCO_CLIENT_SECRET (from a Cisco DevNet application).

    Docs: https://developer.cisco.com/docs/psirt/
    """

    vendor_id = "cisco"

    BASE_URL = "https://apix.cisco.com/security/advisories/v2"
    TOKEN_URL = "https://id.cisco.com/oauth2/default/v1/token"

    # openVuln queries advisories per product; extend this list as needed.
    PRODUCTS = ["IOS%20XE", "NX-OS", "FXOS", "IOS"]

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id or settings.cisco_client_id
        self.client_secret = client_secret or settings.cisco_client_secret

    async def fetch(self) -> list[CanonicalPatch]:
        if not self.client_id or not self.client_secret:
            logger.warning(
                "CISCO_CLIENT_ID/CISCO_CLIENT_SECRET not configured — "
                "skipping Cisco ingestion (returning empty result)."
            )
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            token = await self._get_access_token(client)
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

            patches: list[CanonicalPatch] = []
            for product in self.PRODUCTS:
                resp = await client.get(
                    f"{self.BASE_URL}/product?product={product}", headers=headers
                )
                resp.raise_for_status()
                advisories = resp.json().get("advisories", [])
                patches.extend(self._parse_advisories(advisories, product))
            return patches

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        resp = await client.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _parse_advisories(self, advisories: list[dict], product: str) -> list[CanonicalPatch]:
        out: list[CanonicalPatch] = []
        component = product.replace("%20", " ")

        for adv in advisories:
            release_str = adv.get("firstPublished") or adv.get("lastUpdated")
            try:
                release_dt = datetime.fromisoformat(release_str.replace("Z", "+00:00")).date()
            except (TypeError, ValueError):
                release_dt = date.today()

            first_fixed = adv.get("firstFixed") or []
            version_raw = first_fixed[0] if first_fixed else "Unknown"

            out.append(
                CanonicalPatch(
                    vendor=self.vendor_id,
                    model=f"{component} Enterprise",
                    component_type="Operating System",
                    version_raw=version_raw,
                    version_normalized=normalize_version(self.vendor_id, version_raw),
                    release_date=release_dt,
                    severity=map_severity(adv.get("sir")),
                    cves=adv.get("cves", []) or [],
                    advisory_url=adv.get("url", ""),
                    download_url="https://software.cisco.com/download/navigator.html",
                    requires_entitlement=True,
                    checksum_sha256=None,
                    source_adapter="cisco_openvuln",
                )
            )
        return out
