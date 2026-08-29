from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime

import httpx

from app.adapters.base import BaseAdapter
from app.config import settings
from app.normalizer import map_severity, normalize_version
from app.schemas import CanonicalPatch

logger = logging.getLogger("patch_radar.adapters.vmware")

_VMSA_RE = re.compile(r"VMSA-\d{4}-\d{4}")
_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}")


class VMwareAdapter(BaseAdapter):
    """Adapter for VMware (Broadcom) Security Advisories (VMSA).
    
    Reads from the public VMSA XML/RSS feed. 
    Notes: VMware advisories typically bundle multiple product updates
    under a single VMSA ID. This stub adapter parses the high-level
    advisory from the RSS feed.
    """

    vendor_id = "vmware"

    def __init__(self, rss_url: str | None = None):
        self.rss_url = rss_url or settings.vmware_advisories_url

    async def fetch(self) -> list[CanonicalPatch]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(self.rss_url)
                resp.raise_for_status()
                return self._parse_rss(resp.text)
            except httpx.HTTPError as exc:
                logger.warning("VMware RSS feed unavailable (%s)", exc)
                return []

    def _parse_rss(self, xml_text: str) -> list[CanonicalPatch]:
        out: list[CanonicalPatch] = []
        try:
            # RSS typically has <rss> or xmlns.
            # Using basic string search to handle namespaces safely
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("VMware RSS failed XML parsing")
            return out

        # Accommodate Atom or RSS
        items = root.findall(".//item") or root.findall(". //*{http://www.w3.org/2005/Atom}entry")
        
        for item in items:
            title = ""
            link = ""
            pub_date = ""

            # Try RSS format
            if item.find("title") is not None:
                title = item.findtext("title") or ""
                link = item.findtext("link") or ""
                pubDate_elem = item.find("pubDate")
                if pubDate_elem is not None:
                    pub_date = pubDate_elem.text or ""
            
            # Atom format fallback
            if not title:
                title_elem = item.find("{http://www.w3.org/2005/Atom}title")
                title = title_elem.text if title_elem is not None else ""
                
                link_elem = item.find("{http://www.w3.org/2005/Atom}link")
                link = link_elem.attrib.get("href", "") if link_elem is not None else ""
                
                updated_elem = item.find("{http://www.w3.org/2005/Atom}updated")
                pub_date = updated_elem.text if updated_elem is not None else ""

            if not title:
                continue

            # Attempt to parse date
            release_dt = date.today()
            if pub_date:
                try:
                    if "T" in pub_date: # ISO format
                        release_dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00")).date()
                    else: # RSS format
                        release_dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").date()
                except ValueError:
                    pass

            vmsa_match = _VMSA_RE.search(title)
            vmsa_id = vmsa_match.group(0) if vmsa_match else "Unknown"

            severity = None
            if "critical" in title.lower():
                severity = "CRITICAL"
            elif "important" in title.lower() or "high" in title.lower():
                severity = "HIGH"
            elif "moderate" in title.lower():
                severity = "MEDIUM"

            out.append(
                CanonicalPatch(
                    vendor=self.vendor_id,
                    model="vSphere / ESXi / vCenter",
                    component_type="Hypervisor",
                    version_raw=vmsa_id,
                    version_normalized=normalize_version(self.vendor_id, vmsa_id),
                    release_date=release_dt,
                    severity=severity,
                    cves=_CVE_RE.findall(title),
                    advisory_url=link,
                    download_url=None,
                    requires_entitlement=True, # Need customer connect
                    checksum_sha256=None,
                    source_adapter="vmware_rss",
                )
            )
        return out
