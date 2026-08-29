"""JWT-based authentication and role-based access control (RBAC).

Supports:
- HS256 JWT tokens with role claims
- Two built-in roles: SecurityAnalyst (read-only), OpsAdmin (read + write)
- AUTH_DISABLED=true disables all checks for local development
- Token generation endpoint for development/testing
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Any

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

logger = logging.getLogger("patch_radar.auth")

# Role definitions
ROLES = {
    "SecurityAnalyst": {
        "description": "View and export patch data",
        "permissions": ["read:patches", "read:vendors", "export:csv"],
    },
    "OpsAdmin": {
        "description": "Configure connectors, trigger ingestion, manage system",
        "permissions": [
            "read:patches",
            "read:vendors",
            "export:csv",
            "write:ingest",
            "write:config",
            "write:inventory",
        ],
    },
}

_bearer_scheme = HTTPBearer(auto_error=False)


def _b64url_encode(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return urlsafe_b64decode(s)


def create_token(
    subject: str,
    role: str,
    expires_in_seconds: int = 86400,
) -> str:
    """Create a signed JWT token. Uses HS256 with the configured JWT_SECRET.
    This is for development and internal service-to-service auth.
    Production deployments should use an external IdP (Okta, Azure AD, etc.)."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in_seconds,
    }

    header_b64 = _b64url_encode(json.dumps(header).encode())
    payload_b64 = _b64url_encode(json.dumps(payload).encode())
    signing_input = f"{header_b64}.{payload_b64}"

    signature = hmac.new(
        settings.jwt_secret.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{signing_input}.{sig_b64}"


def verify_token(token: str) -> dict[str, Any]:
    """Verify and decode a JWT token. Returns the payload dict.
    Raises HTTPException on invalid/expired tokens."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}"

        expected_sig = hmac.new(
            settings.jwt_secret.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("Invalid signature")

        payload = json.loads(_b64url_decode(payload_b64))

        if payload.get("exp", 0) < time.time():
            raise ValueError("Token expired")

        return payload
    except (ValueError, json.JSONDecodeError, KeyError) as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc


def require_role(role: str):
    """FastAPI dependency that enforces role-based access control.

    When AUTH_DISABLED=true (default in dev), all requests pass through.
    When AUTH_DISABLED=false, requires a valid JWT Bearer token with the
    specified role (or a higher-privilege role).
    """

    async def _check(request: Request):
        if settings.auth_disabled:
            return {"sub": "dev-user", "role": "OpsAdmin"}

        credentials: HTTPAuthorizationCredentials | None = await _bearer_scheme(request)
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = verify_token(credentials.credentials)
        user_role = payload.get("role", "")

        # Check role hierarchy: OpsAdmin can do everything SecurityAnalyst can
        if role == "SecurityAnalyst" and user_role in ("SecurityAnalyst", "OpsAdmin"):
            return payload
        if role == "OpsAdmin" and user_role == "OpsAdmin":
            return payload

        raise HTTPException(
            status_code=403,
            detail=f"Role '{user_role}' does not have '{role}' access",
        )

    return _check
