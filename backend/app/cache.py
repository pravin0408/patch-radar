"""Redis-backed caching and rate-limiting layer.

Provides:
- Response caching for API endpoints (TTL-based, auto-invalidated on ingestion)
- Rate limiting for outbound adapter requests to avoid vendor rate-limit blocks
- Rate limiting for inbound API requests
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import timedelta
from functools import wraps
from typing import Any, Callable

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger("patch_radar.cache")

_pool: aioredis.Redis | None = None

# Key prefixes
CACHE_PREFIX = "pr:cache:"
RATE_LIMIT_PREFIX = "pr:rl:"
VENDOR_LOCK_PREFIX = "pr:lock:"


async def get_redis() -> aioredis.Redis:
    """Return a shared async Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def close_redis() -> None:
    """Shutdown the Redis pool gracefully."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


def _cache_key(namespace: str, params: dict[str, Any]) -> str:
    """Build a deterministic cache key from a namespace + query params."""
    sorted_params = json.dumps(params, sort_keys=True, default=str)
    h = hashlib.md5(sorted_params.encode()).hexdigest()
    return f"{CACHE_PREFIX}{namespace}:{h}"


async def cache_get(namespace: str, params: dict[str, Any]) -> str | None:
    """Fetch a cached JSON string. Returns None on miss."""
    try:
        r = await get_redis()
        key = _cache_key(namespace, params)
        return await r.get(key)
    except Exception as exc:
        logger.debug("Redis cache_get failed (non-fatal): %s", exc)
        return None


async def cache_set(
    namespace: str,
    params: dict[str, Any],
    value: str,
    ttl_seconds: int = 300,
) -> None:
    """Store a JSON string in cache with TTL."""
    try:
        r = await get_redis()
        key = _cache_key(namespace, params)
        await r.setex(key, ttl_seconds, value)
    except Exception as exc:
        logger.debug("Redis cache_set failed (non-fatal): %s", exc)


async def cache_invalidate_namespace(namespace: str) -> int:
    """Invalidate all cache entries for a namespace (e.g., after ingestion).
    Returns count of deleted keys."""
    try:
        r = await get_redis()
        pattern = f"{CACHE_PREFIX}{namespace}:*"
        keys = []
        async for key in r.scan_iter(match=pattern, count=100):
            keys.append(key)
        if keys:
            return await r.delete(*keys)
        return 0
    except Exception as exc:
        logger.debug("Redis cache_invalidate failed (non-fatal): %s", exc)
        return 0


async def cache_invalidate_all() -> int:
    """Flush all Patch Radar cache entries."""
    try:
        r = await get_redis()
        keys = []
        async for key in r.scan_iter(match=f"{CACHE_PREFIX}*", count=100):
            keys.append(key)
        if keys:
            return await r.delete(*keys)
        return 0
    except Exception as exc:
        logger.debug("Redis cache_invalidate_all failed (non-fatal): %s", exc)
        return 0


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------


async def check_rate_limit(
    identifier: str,
    max_requests: int = 60,
    window_seconds: int = 60,
) -> tuple[bool, int]:
    """Sliding-window rate limiter.

    Returns (allowed: bool, remaining: int)."""
    try:
        r = await get_redis()
        key = f"{RATE_LIMIT_PREFIX}{identifier}"
        current = await r.incr(key)
        if current == 1:
            await r.expire(key, window_seconds)
        remaining = max(0, max_requests - current)
        return current <= max_requests, remaining
    except Exception as exc:
        logger.debug("Redis rate_limit check failed (non-fatal, allowing): %s", exc)
        return True, max_requests


async def adapter_rate_limit(vendor_id: str) -> bool:
    """Check if we can make another outbound request for this vendor.
    Limits to 30 requests per minute per vendor to avoid getting blocked."""
    allowed, _ = await check_rate_limit(
        f"adapter:{vendor_id}", max_requests=30, window_seconds=60
    )
    return allowed


# ---------------------------------------------------------------------------
# Distributed Locking (prevent concurrent ingestion for same vendor)
# ---------------------------------------------------------------------------


async def acquire_ingestion_lock(vendor_id: str, ttl_seconds: int = 600) -> bool:
    """Try to acquire a distributed lock for a vendor ingestion run.
    Returns True if lock was acquired."""
    try:
        r = await get_redis()
        key = f"{VENDOR_LOCK_PREFIX}{vendor_id}"
        acquired = await r.set(key, "locked", ex=ttl_seconds, nx=True)
        return acquired is not None
    except Exception as exc:
        logger.debug("Redis lock acquire failed (non-fatal, allowing): %s", exc)
        return True


async def release_ingestion_lock(vendor_id: str) -> None:
    """Release the distributed lock for a vendor."""
    try:
        r = await get_redis()
        key = f"{VENDOR_LOCK_PREFIX}{vendor_id}"
        await r.delete(key)
    except Exception as exc:
        logger.debug("Redis lock release failed (non-fatal): %s", exc)
