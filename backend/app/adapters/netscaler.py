from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from html.parser import HTMLParser

import httpx

from app.adapters.base import BaseAdapter
from app.config import settings
from app.normalizer import map_severity, normalize_version
from app.schemas import CanonicalPatch

logger = logging.getLogger("patch_radar.adapters.netscaler")

# Patterns for extracting structured data from bulletin titles and HTML pages.
# NetScaler build numbers follow the format: <major>.<minor>-<release>.<build>
# e.g., "14.1-34.42", "13.1-54.14", "13.0-92.31"
_BUILD_RE = re.compile(r"(\d{2}\.\d)-(\d+\.\d+)")
# CVE identifiers in text
_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}")
# NetScaler product model extraction from titles
_MODEL_RE = re.compile(
    r"(NetScaler\s+(?:ADC|Gateway|SD-WAN|Console|Agent|Application Delivery Management))",
    re.IGNORECASE,
)
# Severity from bulletin title or body (Citrix uses these labels)
_SEVERITY_RE = re.compile(
    r"\b(Critical|High|Medium|Low)\b(?:\s+[Ss]everity)?", re.IGNORECASE
)


class _BulletinHTMLParser(HTMLParser):
    """Lightweight HTML parser that extracts version/build numbers, CVEs,
    severity, and download links from a Citrix security bulletin page
    without requiring a headless browser."""

    def __init__(self):
        super().__init__()
        self.builds: list[str] = []
        self.cves: list[str] = []
        self.severity: str | None = None
        self.download_links: list[str] = []
        self._in_body = False
        self._text_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag == "body":
            self._in_body = True
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href and ("download" in href.lower() or "dl.dod.cyber.mil" in href):
                self.download_links.append(href)

    def handle_data(self, data: str):
        if self._in_body:
            self._text_buffer.append(data)

    def close(self):
        super().close()
        full_text = " ".join(self._text_buffer)
        # Extract build numbers
        for m in _BUILD_RE.finditer(full_text):
            build = f"{m.group(1)}-{m.group(2)}"
            if build not in self.builds:
                self.builds.append(build)
        # Extract CVEs
        for m in _CVE_RE.finditer(full_text):
            cve = m.group(0)
            if cve not in self.cves:
                self.cves.append(cve)
        # Extract severity (first match wins)
        sev_match = _SEVERITY_RE.search(full_text)
        if sev_match:
            self.severity = sev_match.group(1)


class NetScalerAdapter(BaseAdapter):
    """Adapter for Cloud Software Group (Citrix) NetScaler security
    bulletins.

    Ingestion strategy:
    1. Fetch the public security bulletins RSS feed.
    2. For each RSS item, extract what we can from the title (build number,
       severity, product model).
    3. Follow each bulletin link and parse the HTML page to extract:
       - All affected/fixed build numbers
       - CVE identifiers
       - Severity rating
       - Download links (where available)
    4. Emit one CanonicalPatch per distinct build number found.
    """

    vendor_id = "netscaler"

    # Maximum number of bulletin pages to fetch per run to avoid rate-limiting
    MAX_BULLETIN_FETCHES = 50

    def __init__(self, rss_url: str | None = None):
        self.rss_url = rss_url or settings.netscaler_bulletin_rss_url

    async def fetch(self) -> list[CanonicalPatch]:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "PatchRadar/1.0 (Security Vulnerability Aggregator)"
            },
        ) as client:
            resp = await client.get(self.rss_url)
            resp.raise_for_status()
            items = self._parse_rss(resp.text)

            patches: list[CanonicalPatch] = []
            fetched = 0
            for item in items:
                if fetched >= self.MAX_BULLETIN_FETCHES:
                    break
                if item.get("link"):
                    try:
                        detail = await self._fetch_bulletin_detail(client, item["link"])
                        patches.extend(self._merge_item_with_detail(item, detail))
                        fetched += 1
                    except (httpx.HTTPError, Exception) as exc:
                        logger.debug(
                            "Failed to fetch bulletin detail %s: %s",
                            item["link"], exc,
                        )
                        # Fall back to RSS-only data
                        patches.extend(self._patches_from_rss_item(item))
                else:
                    patches.extend(self._patches_from_rss_item(item))
            return patches

    def _parse_rss(self, xml_text: str) -> list[dict]:
        """Parse RSS XML and return a list of dicts with title, link,
        release_date, and any data extractable from the title."""
        out: list[dict] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("NetScaler RSS feed did not parse as XML; skipping this run")
            return out

        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()

            try:
                release_dt = datetime.strptime(
                    pub_date, "%a, %d %b %Y %H:%M:%S %z"
                ).date()
            except ValueError:
                release_dt = date.today()

            # Pre-extract what we can from the RSS title
            build_match = _BUILD_RE.search(title)
            model_match = _MODEL_RE.search(title)
            severity_match = _SEVERITY_RE.search(title)
            cves_in_title = _CVE_RE.findall(title)

            out.append({
                "title": title,
                "link": link,
                "release_date": release_dt,
                "build_from_title": f"{build_match.group(1)}-{build_match.group(2)}" if build_match else None,
                "model_from_title": model_match.group(1) if model_match else "NetScaler ADC",
                "severity_from_title": severity_match.group(1) if severity_match else None,
                "cves_from_title": cves_in_title,
            })
        return out

    async def _fetch_bulletin_detail(
        self, client: httpx.AsyncClient, url: str
    ) -> _BulletinHTMLParser:
        """Fetch a bulletin page and parse it for build numbers, CVEs, etc."""
        resp = await client.get(url)
        resp.raise_for_status()
        parser = _BulletinHTMLParser()
        parser.feed(resp.text)
        parser.close()
        return parser

    def _merge_item_with_detail(
        self, item: dict, detail: _BulletinHTMLParser
    ) -> list[CanonicalPatch]:
        """Combine RSS item metadata with HTML-scraped detail to produce
        one CanonicalPatch per distinct build number."""
        # Use builds from HTML, fall back to title-extracted build
        builds = detail.builds or (
            [item["build_from_title"]] if item["build_from_title"] else ["see-advisory"]
        )
        # Merge CVEs from title and HTML
        all_cves = list(dict.fromkeys(item.get("cves_from_title", []) + detail.cves))
        # Severity: prefer HTML detail, then title
        severity = map_severity(detail.severity or item.get("severity_from_title"))
        model = item.get("model_from_title", "NetScaler ADC")
        download_url = detail.download_links[0] if detail.download_links else None

        patches: list[CanonicalPatch] = []
        for build in builds:
            patches.append(
                CanonicalPatch(
                    vendor=self.vendor_id,
                    model=model,
                    component_type="Firmware",
                    version_raw=build,
                    version_normalized=normalize_version(self.vendor_id, build),
                    release_date=item["release_date"],
                    severity=severity,
                    cves=all_cves,
                    advisory_url=item["link"],
                    download_url=download_url,
                    requires_entitlement=False,
                    checksum_sha256=None,
                    source_adapter="netscaler_rss_html",
                )
            )
        return patches

    def _patches_from_rss_item(self, item: dict) -> list[CanonicalPatch]:
        """Fallback: produce a CanonicalPatch from RSS-only data when the
        bulletin page is unreachable."""
        version_raw = item.get("build_from_title") or "see-advisory"
        return [
            CanonicalPatch(
                vendor=self.vendor_id,
                model=item.get("model_from_title", "NetScaler ADC"),
                component_type="Firmware",
                version_raw=version_raw,
                version_normalized=normalize_version(self.vendor_id, version_raw),
                release_date=item["release_date"],
                severity=map_severity(item.get("severity_from_title")),
                cves=item.get("cves_from_title", []),
                advisory_url=item.get("link", ""),
                download_url=None,
                requires_entitlement=False,
                checksum_sha256=None,
                source_adapter="netscaler_rss_fallback",
            )
        ]
