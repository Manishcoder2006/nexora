import pytest
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token


def test_settings_load():
    assert settings.PROJECT_NAME == "Nexora — AI Employee Platform"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ALGORITHM == "HS256"


def test_password_hashing():
    raw_password = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_creation_and_decoding():
    subject = "user_12345"
    token = create_access_token(subject=subject)
    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded["sub"] == subject
