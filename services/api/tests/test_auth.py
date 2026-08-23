from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from kingaweb_api.auth import get_current_principal, verify_access_token
from kingaweb_api.config import Settings


def test_missing_bearer_credentials_are_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        get_current_principal(credentials=None, settings=Settings())

    assert error.value.status_code == 401


def test_unconfigured_identity_provider_fails_closed() -> None:
    with pytest.raises(HTTPException) as error:
        verify_access_token("eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ4In0.invalid", Settings())

    assert error.value.status_code == 503


def make_development_token(secret: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": "development|owner",
            "email": "owner@kingaweb.local",
            "iss": "kingaweb-local",
            "aud": "kingaweb-api",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        secret,
        algorithm="HS256",
    )


def test_development_token_is_accepted_only_in_development() -> None:
    secret = "a-local-secret-that-is-longer-than-thirty-two-bytes"
    token = make_development_token(secret)

    principal = verify_access_token(
        token, Settings(app_environment="development", dev_auth_secret=secret)
    )
    assert principal.subject == "development|owner"

    with pytest.raises(HTTPException) as error:
        verify_access_token(token, Settings(app_environment="production", dev_auth_secret=secret))
    assert error.value.status_code == 401
