import sys
from pathlib import Path

import jwt
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.config import Config


@pytest.fixture(autouse=True)
def use_secure_test_secret(monkeypatch):
    monkeypatch.setattr(Config, "SECRET_KEY", "unit-test-secret-key-with-at-least-32-characters")


def test_password_hash_verifies_only_the_original_password():
    password_hash = hash_password("FreshLink!123")

    assert password_hash != "FreshLink!123"
    assert verify_password("FreshLink!123", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_invalid_password_hash_is_rejected_safely():
    assert verify_password("FreshLink!123", "not-a-bcrypt-hash") is False


def test_access_token_contains_user_and_role():
    token = create_access_token(25, "admin")

    payload = decode_access_token(token)

    assert payload["sub"] == "25"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_tampered_access_token_is_rejected():
    token = create_access_token(25, "truck_provider")
    header, payload, signature = token.split(".")
    tampered_token = f"{header}.{payload}.invalid-signature"

    assert decode_access_token(tampered_token) is None


def test_expired_access_token_is_rejected():
    expired_token = jwt.encode(
        {"sub": "25", "role": "hub_operator", "exp": 0},
        Config.SECRET_KEY,
        algorithm="HS256",
    )

    assert decode_access_token(expired_token) is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
