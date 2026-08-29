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

logger = logging.getLogger("patch_radar.adapters.hpe")

# HPE CSAF feeds follow the OASIS CSAF 2.0 standard, similar to Dell.
# HPE also publishes security bulletins with HPESB* identifiers.
_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}")
_VERSION_RE = re.compile(r"(?:v|version\s*)?([\d]+\.[\d]+(?:\.[\d]+)*)", re.IGNORECASE)
_SPP_VERSION_RE = re.compile(r"SPP\s*([\d.]+)", re.IGNORECASE)

# Product line classification from product names
_PRODUCT_CLASSIFIERS = {
    "ProLiant DL": ("ProLiant DL Series", "Server"),
    "ProLiant ML": ("ProLiant ML Series", "Server"),
    "ProLiant BL": ("ProLiant BL Series", "Server"),
    "Synergy": ("Synergy", "Server"),
    "Apollo": ("Apollo", "Server"),
    "Edgeline": ("Edgeline", "Server"),
    "Nimble": ("Nimble Storage", "Storage"),
    "3PAR": ("3PAR StoreServ", "Storage"),
    "Primera": ("Primera", "Storage"),
    "Alletra": ("Alletra", "Storage"),
    "StoreOnce": ("StoreOnce", "Storage"),
    "MSA": ("MSA Storage", "Storage"),
    "iLO": ("Integrated Lights-Out", "Management"),
    "Aruba": ("Aruba Networks", "Networking"),
    "FlexFabric": ("FlexFabric", "Networking"),
    "BladeSystem": ("BladeSystem", "Server"),
    "Superdome": ("Superdome Flex", "Server"),
    "OneView": ("OneView", "Management"),
    "Agentless Management": ("AMS", "Management"),
}


def _classify_product(name: str) -> tuple[str, str]:
    """Return (product_family_name, category) for a product name."""
    for key, (family, category) in _PRODUCT_CLASSIFIERS.items():
        if key.lower() in name.lower():
            return family, category
    return "HPE Other", "Server"


class HPEAdapter(BaseAdapter):
    """Adapter for HPE security advisories and firmware feeds.

    Ingestion strategy:
    1. Fetch HPE's CSAF provider-metadata.json (same structure as Dell's
       CSAF 2.0 feed) for security advisories.
    2. For each CSAF advisory document, parse product_tree branches and
       vulnerabilities to extract model, component, version, CVEs, severity.
    3. Also fetch the SPP (Service Pack for ProLiant) catalog feed for
       firmware bundle metadata.
    4. Merge both sources into CanonicalPatch records.

    If the CSAF endpoint is unavailable, falls back to the legacy JSON
    security bulletins feed.
    """

    vendor_id = "hpe"

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.hpe_sdr_base_url

    async def fetch(self) -> list[CanonicalPatch]:
        patches: list[CanonicalPatch] = []
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "PatchRadar/1.0 (Security Vulnerability Aggregator)",
                "Accept": "application/json, application/xml, text/xml",
            },
        ) as client:
            # Strategy 1: Try CSAF feed (preferred, structured data)
            try:
                csaf_patches = await self._fetch_csaf(client)
                patches.extend(csaf_patches)
                logger.info("HPE CSAF: %d patches from CSAF feed", len(csaf_patches))
            except (httpx.HTTPError, Exception) as exc:
                logger.warning("HPE CSAF feed unavailable (%s); trying fallback", exc)

            # Strategy 2: Try legacy security bulletins JSON feed
            if not patches:
                try:
                    bulletin_patches = await self._fetch_bulletins_json(client)
                    patches.extend(bulletin_patches)
                    logger.info(
                        "HPE Bulletins: %d patches from JSON feed", len(bulletin_patches)
                    )
                except (httpx.HTTPError, Exception) as exc:
                    logger.warning("HPE JSON bulletin feed also unavailable (%s)", exc)

            # Strategy 3: Try SPP catalog XML for firmware bundles
            try:
                spp_patches = await self._fetch_spp_catalog(client)
                patches.extend(spp_patches)
                logger.info("HPE SPP: %d patches from SPP catalog", len(spp_patches))
            except (httpx.HTTPError, Exception) as exc:
                logger.debug("HPE SPP catalog unavailable (%s); non-critical", exc)

        return patches

    async def _fetch_csaf(self, client: httpx.AsyncClient) -> list[CanonicalPatch]:
        """Fetch HPE's CSAF 2.0 provider metadata and walk the index."""
        resp = await client.get(f"{self.base_url}/csaf/provider-metadata.json")
        resp.raise_for_status()
        metadata = resp.json()

        urls: list[str] = []
        for dist in metadata.get("distributions", []):
            index_url = dist.get("rolling", {}).get("directory_url")
            if not index_url:
                continue
            idx_resp = await client.get(f"{index_url}/index.txt")
            if idx_resp.status_code == 200:
                urls.extend(
                    f"{index_url}/{line.strip()}"
                    for line in idx_resp.text.splitlines()
                    if line.strip().endswith(".json")
                )

        patches: list[CanonicalPatch] = []
        for doc_url in urls[:100]:  # Cap at 100 documents per run
            try:
                doc_resp = await client.get(doc_url)
                doc_resp.raise_for_status()
                doc = doc_resp.json()
                patches.extend(self._parse_csaf_document(doc))
            except (httpx.HTTPError, Exception):
                continue
        return patches

    def _parse_csaf_document(self, doc: dict) -> list[CanonicalPatch]:
        """Parse a CSAF 2.0 advisory document (same structure as Dell's)."""
        out: list[CanonicalPatch] = []

        tracking = doc.get("document", {}).get("tracking", {})
        release_date_str = tracking.get("current_release_date") or tracking.get(
            "initial_release_date"
        )
        try:
            release_dt = datetime.fromisoformat(
                release_date_str.replace("Z", "+00:00")
            ).date()
        except (TypeError, ValueError):
            release_dt = date.today()

        cves = [
            v.get("cve")
            for v in doc.get("vulnerabilities", [])
            if v.get("cve")
        ]

        max_score = 0.0
        for v in doc.get("vulnerabilities", []):
            for score_block in v.get("scores", []):
                cvss = score_block.get("cvss_v3", {}) or score_block.get(
                    "cvss_v4", {}
                )
                base_score = cvss.get("baseScore")
                if isinstance(base_score, (int, float)):
                    max_score = max(max_score, base_score)
        severity = map_severity(str(max_score)) if max_score else None

        advisory_url = ""
        refs = doc.get("document", {}).get("references", [])
        if refs:
            advisory_url = refs[0].get("url", "")

        for branch in doc.get("product_tree", {}).get("branches", []):
            model_name = branch.get("name", "Unknown")
            for product_branch in branch.get("branches", []):
                component_name = product_branch.get("name", "Firmware")
                for version_branch in product_branch.get("branches", []):
                    version_raw = version_branch.get("name")
                    if not version_raw:
                        continue
                    out.append(
                        CanonicalPatch(
                            vendor=self.vendor_id,
                            model=model_name,
                            component_type=component_name,
                            version_raw=version_raw,
                            version_normalized=normalize_version(
                                self.vendor_id, version_raw
                            ),
                            release_date=release_dt,
                            severity=severity,
                            cves=cves,
                            advisory_url=advisory_url,
                            download_url=None,
                            requires_entitlement=False,
                            checksum_sha256=None,
                            source_adapter="hpe_csaf",
                        )
                    )
        return out

    async def _fetch_bulletins_json(
        self, client: httpx.AsyncClient
    ) -> list[CanonicalPatch]:
        """Fallback: fetch the legacy JSON security bulletins feed."""
        resp = await client.get(f"{self.base_url}/feeds/security-bulletins.json")
        resp.raise_for_status()
        data = resp.json()
        return self._parse_bulletins_feed(data)

    def _parse_bulletins_feed(self, data: dict) -> list[CanonicalPatch]:
        """Parse HPE's legacy JSON bulletin feed."""
        out: list[CanonicalPatch] = []
        bulletins = data.get("bulletins", data.get("data", {}).get("bulletins", []))

        for entry in bulletins:
            release_str = entry.get("release_date") or entry.get(
                "publishDate", ""
            )
            try:
                release_dt = datetime.fromisoformat(release_str).date()
            except (TypeError, ValueError):
                try:
                    release_dt = datetime.strptime(release_str, "%Y-%m-%d").date()
                except (TypeError, ValueError):
                    release_dt = date.today()

            version_raw = (
                entry.get("spp_version")
                or entry.get("component_version")
                or entry.get("version")
                or "Unknown"
            )

            # Extract CVEs from the entry
            cves = entry.get("cves", [])
            if not cves and entry.get("cve_ids"):
                cves = entry["cve_ids"]
            if isinstance(cves, str):
                cves = _CVE_RE.findall(cves)

            model = (
                entry.get("product_line")
                or entry.get("product")
                or entry.get("platform", "ProLiant")
            )
            component_type = entry.get("component_type") or entry.get(
                "component", "Firmware"
            )

            out.append(
                CanonicalPatch(
                    vendor=self.vendor_id,
                    model=model,
                    component_type=component_type,
                    version_raw=version_raw,
                    version_normalized=normalize_version(self.vendor_id, version_raw),
                    release_date=release_dt,
                    severity=map_severity(entry.get("severity")),
                    cves=cves or [],
                    advisory_url=entry.get("advisory_url", entry.get("url", "")),
                    download_url=entry.get("download_url"),
                    requires_entitlement=entry.get("requires_entitlement", False),
                    checksum_sha256=entry.get("checksum_sha256"),
                    source_adapter="hpe_bulletins_json",
                )
            )
        return out

    async def _fetch_spp_catalog(
        self, client: httpx.AsyncClient
    ) -> list[CanonicalPatch]:
        """Fetch SPP (Service Pack for ProLiant) catalog XML for firmware
        bundle metadata. SPP catalogs list component firmware versions
        bundled in each SPP release."""
        resp = await client.get(f"{self.base_url}/spp/catalog.xml")
        resp.raise_for_status()
        return self._parse_spp_catalog(resp.text)

    def _parse_spp_catalog(self, xml_text: str) -> list[CanonicalPatch]:
        """Parse SPP XML catalog."""
        out: list[CanonicalPatch] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("HPE SPP catalog XML did not parse; skipping")
            return out

        # SPP catalogs vary in schema; handle common structures
        for package in root.findall(".//{*}SoftwareComponent") or root.findall(
            ".//SoftwareComponent"
        ):
            name = package.get("name", "")
            version_raw = package.get("version", "")
            release_date_str = package.get("releaseDate", "")

            if not version_raw:
                continue

            try:
                release_dt = datetime.strptime(release_date_str, "%Y-%m-%dT%H:%M:%S").date()
            except (TypeError, ValueError):
                try:
                    release_dt = datetime.strptime(release_date_str, "%Y-%m-%d").date()
                except (TypeError, ValueError):
                    release_dt = date.today()

            # Classify the component
            family, category = _classify_product(name)
            component_type = package.get("category", "Firmware")

            # Extract model from target elements if present
            model = "ProLiant"
            for target in package.findall(".//{*}Target") or package.findall(
                ".//Target"
            ):
                model = target.get("name", model)
                break

            download_url = None
            for file_elem in package.findall(".//{*}File") or package.findall(
                ".//File"
            ):
                download_url = file_elem.get("url")
                break

            checksum = None
            for file_elem in package.findall(".//{*}File") or package.findall(
                ".//File"
            ):
                checksum = file_elem.get("sha256") or file_elem.get("hash")
                break

            out.append(
                CanonicalPatch(
                    vendor=self.vendor_id,
                    model=model,
                    component_type=component_type,
                    version_raw=version_raw,
                    version_normalized=normalize_version(self.vendor_id, version_raw),
                    release_date=release_dt,
                    severity=None,  # SPP entries are firmware bundles, not advisories
                    cves=[],
                    advisory_url=f"https://support.hpe.com/hpesc/public/swd/detail/{name}",
                    download_url=download_url,
                    requires_entitlement=True,  # SPP downloads require HPE passport
                    checksum_sha256=checksum,
                    source_adapter="hpe_spp_catalog",
                )
            )
        return out
