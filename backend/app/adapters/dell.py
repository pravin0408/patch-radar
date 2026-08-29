from __future__ import annotations

from datetime import date, datetime

import httpx

from app.adapters.base import BaseAdapter
from app.config import settings
from app.normalizer import map_severity, normalize_version
from app.schemas import CanonicalPatch


class DellAdapter(BaseAdapter):
    """Adapter for Dell's public CSAF 2.0 security advisory feed.

    No authentication required, which makes this the reference / happy-path
    adapter for the pipeline. CSAF documents are structured JSON, so this
    is a straightforward field mapping rather than a scraper.

    CSAF 2.0 spec: https://oasis-open.github.io/csaf-documentation/
    """

    vendor_id = "dell"

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.dell_csaf_base_url

    async def fetch(self) -> list[CanonicalPatch]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            index = await self._fetch_index(client)
            patches: list[CanonicalPatch] = []
            for doc_url in index:
                try:
                    doc = await self._fetch_csaf_document(client, doc_url)
                except httpx.HTTPError:
                    # One bad advisory shouldn't take down the whole run.
                    continue
                patches.extend(self._parse_csaf_document(doc))
            return patches

    async def _fetch_index(self, client: httpx.AsyncClient) -> list[str]:
        """Fetch the CSAF provider metadata / rolling index and return a
        list of individual advisory document URLs."""
        resp = await client.get(f"{self.base_url}/provider-metadata.json")
        resp.raise_for_status()
        metadata = resp.json()
        # CSAF provider-metadata.json points at one or more "distributions",
        # each with a rolling index of advisory document URLs.
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
        return urls

    async def _fetch_csaf_document(self, client: httpx.AsyncClient, url: str) -> dict:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()

    def _parse_csaf_document(self, doc: dict) -> list[CanonicalPatch]:
        """Map one CSAF advisory document to zero or more CanonicalPatch
        records (one per affected product/version combination)."""
        out: list[CanonicalPatch] = []

        tracking = doc.get("document", {}).get("tracking", {})
        release_date_str = tracking.get("current_release_date") or tracking.get("initial_release_date")
        try:
            release_dt = datetime.fromisoformat(release_date_str.replace("Z", "+00:00")).date()
        except (TypeError, ValueError):
            release_dt = date.today()

        cves = [
            v.get("cve")
            for v in doc.get("vulnerabilities", [])
            if v.get("cve")
        ]

        # CSAF severity comes from CVSS scores attached to vulnerabilities.
        max_score = 0.0
        for v in doc.get("vulnerabilities", []):
            for score_block in v.get("scores", []):
                cvss = score_block.get("cvss_v3", {}) or score_block.get("cvss_v4", {})
                base_score = cvss.get("baseScore")
                if isinstance(base_score, (int, float)):
                    max_score = max(max_score, base_score)
        severity = map_severity(str(max_score)) if max_score else None

        advisory_url = doc.get("document", {}).get("references", [{}])[0].get("url", "")

        for branch in doc.get("product_tree", {}).get("branches", []):
            model = branch.get("name", "Unknown Model")
            for product in branch.get("branches", []):
                for version_branch in product.get("branches", []):
                    version_raw = version_branch.get("name")
                    if not version_raw:
                        continue
                    out.append(
                        CanonicalPatch(
                            vendor=self.vendor_id,
                            model=model,
                            component_type=product.get("name", "Firmware"),
                            version_raw=version_raw,
                            version_normalized=normalize_version(self.vendor_id, version_raw),
                            release_date=release_dt,
                            severity=severity,
                            cves=cves,
                            advisory_url=advisory_url,
                            download_url=None,
                            requires_entitlement=False,
                            checksum_sha256=None,
                            source_adapter="dell_csaf",
                        )
                    )
        return out
