"""Tests for the JWT auth module."""
import time

import pytest

from app.auth import create_token, verify_token


def test_create_and_verify_token():
    token = create_token("test-user", "OpsAdmin", expires_in_seconds=3600)
    payload = verify_token(token)
    assert payload["sub"] == "test-user"
    assert payload["role"] == "OpsAdmin"
    assert payload["exp"] > time.time()


def test_verify_token_expired():
    token = create_token("test-user", "OpsAdmin", expires_in_seconds=-1)
    with pytest.raises(Exception):
        verify_token(token)


def test_verify_token_invalid_signature():
    token = create_token("test-user", "OpsAdmin")
    # Corrupt the signature
    parts = token.split(".")
    parts[2] = "invalid_signature_here"
    corrupted = ".".join(parts)
    with pytest.raises(Exception):
        verify_token(corrupted)


def test_verify_token_invalid_format():
    with pytest.raises(Exception):
        verify_token("not.a.valid.token.at.all")


def test_create_token_different_roles():
    admin_token = create_token("admin", "OpsAdmin")
    analyst_token = create_token("analyst", "SecurityAnalyst")

    admin_payload = verify_token(admin_token)
    analyst_payload = verify_token(analyst_token)

    assert admin_payload["role"] == "OpsAdmin"
    assert analyst_payload["role"] == "SecurityAnalyst"
