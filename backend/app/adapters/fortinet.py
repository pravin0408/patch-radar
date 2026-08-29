from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime

import httpx

from app.adapters.base import BaseAdapter
from app.config import settings
from app.normalizer import normalize_version
from app.schemas import CanonicalPatch

logger = logging.getLogger("patch_radar.adapters.fortinet")

_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}")


class FortinetAdapter(BaseAdapter):
    """Adapter for Fortinet PSIRT (FortiGuard) security advisories.
    
    Reads from the public RSS feed.
    """

    vendor_id = "fortinet"

    def __init__(self, rss_url: str | None = None):
        self.rss_url = rss_url or settings.fortinet_rss_url

    async def fetch(self) -> list[CanonicalPatch]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(self.rss_url)
                resp.raise_for_status()
                return self._parse_rss(resp.text)
            except httpx.HTTPError as exc:
                logger.warning("Fortinet RSS feed unavailable (%s)", exc)
                return []

    def _parse_rss(self, xml_text: str) -> list[CanonicalPatch]:
        out: list[CanonicalPatch] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("Fortinet RSS failed XML parsing")
            return out

        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            desc = (item.findtext("description") or "").strip()

            if not title:
                continue

            try:
                release_dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").date()
            except ValueError:
                release_dt = date.today()

            # Fortinet titles look like "FortiOS - Buffer overflow in xyz"
            model = "FortiOS"
            if "FortiClient" in title:
                model = "FortiClient"
            elif "FortiManager" in title:
                model = "FortiManager"
            elif "FortiAnalyzer" in title:
                model = "FortiAnalyzer"
            elif "-" in title:
                model = title.split("-")[0].strip()

            severity = None
            if "Critical" in desc or "Critical" in title:
                severity = "CRITICAL"
            elif "High" in desc or "High" in title:
                severity = "HIGH"
            elif "Medium" in desc or "Medium" in title:
                severity = "MEDIUM"

            # Use FG-IR-xx-xxx identifier if present in the link as version_raw
            ir_match = re.search(r"FG-IR-\d{2}-\d{3}", link)
            version_raw = ir_match.group(0) if ir_match else "Unknown"

            out.append(
                CanonicalPatch(
                    vendor=self.vendor_id,
                    model=model,
                    component_type="Security OS",
                    version_raw=version_raw,
                    version_normalized=normalize_version(self.vendor_id, version_raw),
                    release_date=release_dt,
                    severity=severity,
                    cves=_CVE_RE.findall(title + " " + desc),
                    advisory_url=link,
                    download_url=None,
                    requires_entitlement=True,
                    checksum_sha256=None,
                    source_adapter="fortinet_rss",
                )
            )
        return out
