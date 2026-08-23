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


def principal_from_claims(claims: dict[str, object]) -> Principal:
    return Principal(
        subject=str(claims["sub"]),
        email=str(claims["email"]) if claims.get("email") else None,
        name=str(claims["name"]) if claims.get("name") else None,
    )


def verify_access_token(token: str, settings: Settings) -> Principal:
    algorithm = jwt.get_unverified_header(token).get("alg")
    if algorithm == "HS256":
        if settings.app_environment != "development" or not settings.dev_auth_secret:
            raise HTTPException(status_code=401, detail="Development authentication is disabled")
        if len(settings.dev_auth_secret) < 32:
            raise HTTPException(
                status_code=503, detail="Development authentication is misconfigured"
            )
        claims = jwt.decode(
            token,
            settings.dev_auth_secret,
            algorithms=["HS256"],
            audience="kingaweb-api",
            issuer="kingaweb-local",
            options={"require": ["exp", "iat", "iss", "sub"]},
        )
        return principal_from_claims(claims)

    if algorithm != "RS256":
        raise HTTPException(status_code=401, detail="Unsupported access token algorithm")
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
    return principal_from_claims(claims)


def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return verify_access_token(credentials.credentials, settings)
    except HTTPException:
        raise
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=401, detail="Invalid access token") from error
