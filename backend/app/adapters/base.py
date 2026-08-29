from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.schemas import CanonicalPatch

logger = logging.getLogger("patch_radar.adapters")


@dataclass
class AdapterResult:
    """Wraps an adapter run so the scheduler/circuit-breaker doesn't need
    to inspect exceptions directly — every adapter returns one of these,
    even on failure."""

    vendor: str
    patches: list[CanonicalPatch] = field(default_factory=list)
    success: bool = True
    error: str | None = None


class BaseAdapter(ABC):
    """Every vendor adapter implements this interface. The scheduler and
    normalizer never need vendor-specific logic — adding a new vendor is
    "write one adapter file," not "touch the pipeline."
    """

    vendor_id: str

    @abstractmethod
    async def fetch(self) -> list[CanonicalPatch]:
        """Return normalized patch records for this vendor. Raise on
        unrecoverable failure — `run()` below turns that into an
        AdapterResult so callers never need a try/except."""
        raise NotImplementedError

    async def run(self) -> AdapterResult:
        try:
            patches = await self.fetch()
            return AdapterResult(vendor=self.vendor_id, patches=patches, success=True)
        except Exception as exc:  # noqa: BLE001 - adapters must never crash the scheduler
            logger.exception("Adapter %s failed", self.vendor_id)
            return AdapterResult(vendor=self.vendor_id, success=False, error=str(exc))
