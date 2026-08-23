import pytest
from fastapi import HTTPException

from kingaweb_api.auth import get_current_principal, verify_oidc_token
from kingaweb_api.config import Settings


def test_missing_bearer_credentials_are_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        get_current_principal(credentials=None, settings=Settings())

    assert error.value.status_code == 401


def test_unconfigured_identity_provider_fails_closed() -> None:
    with pytest.raises(HTTPException) as error:
        verify_oidc_token("not-a-token", Settings())

    assert error.value.status_code == 503
