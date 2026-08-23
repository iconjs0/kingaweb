from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .config import Settings, get_settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str | None
    name: str | None


def verify_oidc_token(token: str, settings: Settings) -> Principal:
    if not settings.oidc_issuer or not settings.oidc_audience or not settings.oidc_jwks_url:
        raise HTTPException(status_code=503, detail="Identity provider is not configured")

    jwks = PyJWKClient(settings.oidc_jwks_url)
    signing_key = jwks.get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.oidc_audience,
        issuer=settings.oidc_issuer,
        options={"require": ["exp", "iat", "iss", "sub"]},
    )
    return Principal(subject=claims["sub"], email=claims.get("email"), name=claims.get("name"))


def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return verify_oidc_token(credentials.credentials, settings)
    except HTTPException:
        raise
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=401, detail="Invalid access token") from error
