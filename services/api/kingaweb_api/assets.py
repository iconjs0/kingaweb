import hashlib
import ipaddress
import secrets
import socket
import ssl
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Protocol

import dns.exception
import dns.resolver
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import Principal, get_current_principal
from .database import get_db
from .models import (
    Asset,
    AssetStatus,
    DomainVerification,
    Membership,
    User,
    VerificationAttempt,
    VerificationMethod,
    VerificationOutcome,
    WorkspaceRole,
)
from .network import resolve_public_addresses

router = APIRouter(prefix="/v1/workspaces/{workspace_id}/assets", tags=["Assets"])
WRITE_ROLES = {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.ANALYST}
VERIFICATION_ATTEMPT_LIMIT = 5
VERIFICATION_ATTEMPT_WINDOW = timedelta(minutes=10)
PrincipalDep = Annotated[Principal, Depends(get_current_principal)]
DatabaseDep = Annotated[Session, Depends(get_db)]


class TxtLookup(Protocol):
    def __call__(self, name: str) -> list[str]: ...


def lookup_txt_records(name: str) -> list[str]:
    resolver = dns.resolver.Resolver(configure=True)
    resolver.timeout = 2
    resolver.lifetime = 4
    try:
        answers = resolver.resolve(name, "TXT", search=False)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        return []
    except dns.exception.Timeout:
        return []
    return [b"".join(answer.strings).decode("utf-8") for answer in answers]


def get_txt_lookup() -> TxtLookup:
    return lookup_txt_records


TxtLookupDep = Annotated[TxtLookup, Depends(get_txt_lookup)]


class HttpProofLookup(Protocol):
    def __call__(self, hostname: str) -> str | None: ...


def lookup_http_proof(hostname: str) -> str | None:
    context = ssl.create_default_context()
    for address in resolve_public_addresses(hostname):
        try:
            with socket.create_connection((address, 443), timeout=4) as connection:
                connection.settimeout(6)
                with context.wrap_socket(connection, server_hostname=hostname) as secure:
                    request = (
                        "GET /.well-known/kingaweb-verification.txt HTTP/1.1\r\n"
                        f"Host: {hostname}\r\nUser-Agent: KingaWeb-Verifier/0.1\r\n"
                        "Accept: text/plain\r\nConnection: close\r\n\r\n"
                    )
                    secure.sendall(request.encode("ascii"))
                    response = bytearray()
                    while len(response) < 8192:
                        chunk = secure.recv(2048)
                        if not chunk:
                            break
                        response.extend(chunk)
                    header, separator, body = bytes(response).partition(b"\r\n\r\n")
                    if not separator or not header.startswith(b"HTTP/1.1 200"):
                        continue
                    return body[:4096].decode("utf-8").strip()
        except (OSError, ssl.SSLError, UnicodeError):
            continue
    return None


def get_http_proof_lookup() -> HttpProofLookup:
    return lookup_http_proof


HttpProofLookupDep = Annotated[HttpProofLookup, Depends(get_http_proof_lookup)]


def normalize_hostname(value: str) -> str:
    candidate = value.strip().lower().rstrip(".")
    if "://" in candidate or "/" in candidate or not candidate:
        raise ValueError("Enter a hostname without a scheme, path or port")
    try:
        ascii_hostname = candidate.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise ValueError("Hostname is not valid") from error
    labels = ascii_hostname.split(".")
    try:
        ipaddress.ip_address(ascii_hostname)
    except ValueError:
        pass
    else:
        raise ValueError("IP addresses cannot be registered as domain assets")
    if len(ascii_hostname) > 253 or len(labels) < 2:
        raise ValueError("Enter a registrable public hostname")
    invalid_edges = any(
        not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
        for label in labels
    )
    if invalid_edges:
        raise ValueError("Hostname is not valid")
    invalid_characters = any(
        not all(character.isalnum() or character == "-" for character in label) for label in labels
    )
    if invalid_characters:
        raise ValueError("Hostname is not valid")
    return ascii_hostname


class AssetCreate(BaseModel):
    hostname: str = Field(min_length=3, max_length=253)
    verification_method: VerificationMethod = VerificationMethod.DNS_TXT

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, value: str) -> str:
        return normalize_hostname(value)


class AssetCreated(BaseModel):
    id: uuid.UUID
    hostname: str
    status: str
    verification_method: VerificationMethod
    verification_name: str
    verification_value: str
    expires_at: datetime


class AssetVerificationResult(BaseModel):
    verified: bool
    status: str
    detail: str
    verified_at: datetime | None = None


def issue_verification_challenge(
    asset: Asset, method: VerificationMethod, db: Session
) -> AssetCreated:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(hours=24)
    verification = DomainVerification(
        asset=asset,
        method=method,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        expires_at=expires_at,
    )
    db.add(verification)
    db.commit()
    verification_name = (
        f"_kingaweb-verification.{asset.hostname}"
        if method == VerificationMethod.DNS_TXT
        else f"https://{asset.hostname}/.well-known/kingaweb-verification.txt"
    )
    return AssetCreated(
        id=asset.id,
        hostname=asset.hostname,
        status=asset.status.value,
        verification_method=method,
        verification_name=verification_name,
        verification_value=f"kingaweb-verification={token}",
        expires_at=expires_at,
    )


def require_workspace_member(
    db: Session, workspace_id: uuid.UUID, principal: Principal, allowed_roles: set[WorkspaceRole]
) -> tuple[User, Membership]:
    row = db.execute(
        select(User, Membership)
        .join(Membership, Membership.user_id == User.id)
        .where(
            User.oidc_subject == principal.subject,
            Membership.workspace_id == workspace_id,
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    user, membership = row
    if membership.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Insufficient workspace permission")
    return user, membership


@router.post("", response_model=AssetCreated, status_code=status.HTTP_201_CREATED)
def create_asset(
    workspace_id: uuid.UUID,
    request: AssetCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> AssetCreated:
    user, _ = require_workspace_member(db, workspace_id, principal, WRITE_ROLES)
    asset = Asset(workspace_id=workspace_id, hostname=request.hostname, created_by_user_id=user.id)
    db.add(asset)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Asset already exists in this workspace"
        ) from error
    return issue_verification_challenge(asset, request.verification_method, db)


@router.post("/{asset_id}/verification-challenge", response_model=AssetCreated)
def renew_verification_challenge(
    workspace_id: uuid.UUID,
    asset_id: uuid.UUID,
    request: AssetCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> AssetCreated:
    require_workspace_member(db, workspace_id, principal, WRITE_ROLES)
    asset = db.scalar(select(Asset).where(Asset.id == asset_id, Asset.workspace_id == workspace_id))
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.status == AssetStatus.VERIFIED:
        raise HTTPException(status_code=409, detail="Verified assets do not need a new challenge")
    if request.hostname != asset.hostname:
        raise HTTPException(status_code=400, detail="Challenge hostname does not match the asset")
    latest = db.scalar(
        select(DomainVerification)
        .where(DomainVerification.asset_id == asset.id)
        .order_by(DomainVerification.created_at.desc())
    )
    if latest is not None:
        created_at = latest.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        if created_at > datetime.now(UTC) - timedelta(minutes=1):
            raise HTTPException(
                status_code=429,
                detail="Wait one minute before generating another verification challenge.",
                headers={"Retry-After": "60"},
            )
    return issue_verification_challenge(asset, request.verification_method, db)


@router.post("/{asset_id}/verify", response_model=AssetVerificationResult)
def verify_asset(
    workspace_id: uuid.UUID,
    asset_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
    txt_lookup: TxtLookupDep,
    http_proof_lookup: HttpProofLookupDep,
) -> AssetVerificationResult:
    user, _ = require_workspace_member(db, workspace_id, principal, WRITE_ROLES)
    asset = db.scalar(select(Asset).where(Asset.id == asset_id, Asset.workspace_id == workspace_id))
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.status == AssetStatus.VERIFIED:
        return AssetVerificationResult(
            verified=True,
            status=asset.status.value,
            detail="Domain ownership was already verified",
            verified_at=asset.verified_at,
        )

    verification = db.scalar(
        select(DomainVerification)
        .where(
            DomainVerification.asset_id == asset.id,
            DomainVerification.verified_at.is_(None),
        )
        .order_by(DomainVerification.created_at.desc())
    )
    if verification is None:
        raise HTTPException(status_code=409, detail="No active verification challenge")
    window_started_at = datetime.now(UTC) - VERIFICATION_ATTEMPT_WINDOW
    recent_attempts = db.scalar(
        select(func.count(VerificationAttempt.id)).where(
            VerificationAttempt.verification_id == verification.id,
            VerificationAttempt.created_at >= window_started_at,
            VerificationAttempt.outcome != VerificationOutcome.RATE_LIMITED,
        )
    ) or 0
    if recent_attempts >= VERIFICATION_ATTEMPT_LIMIT:
        db.add(
            VerificationAttempt(
                verification_id=verification.id,
                requested_by_user_id=user.id,
                outcome=VerificationOutcome.RATE_LIMITED,
            )
        )
        db.commit()
        raise HTTPException(
            status_code=429,
            detail="Too many verification attempts. Try again in 10 minutes.",
            headers={"Retry-After": "600"},
        )
    expires_at = verification.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        db.add(
            VerificationAttempt(
                verification_id=verification.id,
                requested_by_user_id=user.id,
                outcome=VerificationOutcome.EXPIRED,
            )
        )
        db.commit()
        raise HTTPException(status_code=410, detail="Verification challenge has expired")

    records = (
        txt_lookup(f"_kingaweb-verification.{asset.hostname}")
        if verification.method == VerificationMethod.DNS_TXT
        else [http_proof_lookup(asset.hostname) or ""]
    )
    matched = any(
        record.startswith("kingaweb-verification=")
        and secrets.compare_digest(
            hashlib.sha256(record.removeprefix("kingaweb-verification=").encode()).hexdigest(),
            verification.token_hash,
        )
        for record in records
    )
    if not matched:
        db.add(
            VerificationAttempt(
                verification_id=verification.id,
                requested_by_user_id=user.id,
                outcome=VerificationOutcome.NOT_FOUND,
            )
        )
        db.commit()
        return AssetVerificationResult(
            verified=False,
            status=asset.status.value,
            detail=(
                "Matching DNS TXT record was not found yet"
                if verification.method == VerificationMethod.DNS_TXT
                else "Matching HTTPS verification file was not found yet"
            ),
        )

    verified_at = datetime.now(UTC)
    verification.verified_at = verified_at
    asset.verified_at = verified_at
    asset.status = AssetStatus.VERIFIED
    db.add(
        VerificationAttempt(
            verification_id=verification.id,
            requested_by_user_id=user.id,
            outcome=VerificationOutcome.VERIFIED,
        )
    )
    db.commit()
    return AssetVerificationResult(
        verified=True,
        status=asset.status.value,
        detail="Domain ownership verified",
        verified_at=verified_at,
    )
