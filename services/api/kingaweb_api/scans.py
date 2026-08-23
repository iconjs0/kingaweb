import ipaddress
import socket
import ssl
import uuid
from datetime import UTC, datetime
from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .assets import WRITE_ROLES, require_workspace_member
from .auth import Principal, get_current_principal
from .database import get_db
from .models import (
    Asset,
    AssetStatus,
    Finding,
    FindingSeverity,
    ScanRun,
    ScanStatus,
    WorkspaceRole,
)

router = APIRouter(prefix="/v1/workspaces/{workspace_id}/assets/{asset_id}/scans", tags=["Scans"])
PrincipalDep = Annotated[Principal, Depends(get_current_principal)]
DatabaseDep = Annotated[Session, Depends(get_db)]


class ProbeResult(BaseModel):
    status_code: int
    headers: dict[str, str]
    target_ip: str = "203.0.113.1"
    tls_version: str = "TLSv1.3"
    certificate_expires_at: datetime | None = None


class WebProbe(Protocol):
    def __call__(self, hostname: str) -> ProbeResult: ...


def resolve_public_addresses(hostname: str) -> list[str]:
    try:
        records = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise ValueError("Domain could not be resolved") from error
    addresses = sorted({record[4][0] for record in records})
    if not addresses:
        raise ValueError("Domain did not resolve to an address")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError("Domain resolves to a private or reserved network")
    return addresses


def probe_https(hostname: str) -> ProbeResult:
    addresses = resolve_public_addresses(hostname)
    context = ssl.create_default_context()
    last_error: OSError | None = None
    for address in addresses:
        try:
            with socket.create_connection((address, 443), timeout=4) as connection:
                connection.settimeout(6)
                with context.wrap_socket(connection, server_hostname=hostname) as secure:
                    request = (
                        f"GET / HTTP/1.1\r\nHost: {hostname}\r\n"
                        "User-Agent: KingaWeb-Baseline-Scanner/0.2\r\n"
                        "Accept: */*\r\nConnection: close\r\n\r\n"
                    )
                    secure.sendall(request.encode("ascii"))
                    response = bytearray()
                    while b"\r\n\r\n" not in response and len(response) < 65_536:
                        chunk = secure.recv(4096)
                        if not chunk:
                            break
                        response.extend(chunk)
                    status_code, headers = parse_http_headers(bytes(response))
                    certificate = secure.getpeercert()
                    expiry_text = certificate.get("notAfter")
                    expires_at = (
                        datetime.fromtimestamp(ssl.cert_time_to_seconds(expiry_text), UTC)
                        if isinstance(expiry_text, str)
                        else None
                    )
                    return ProbeResult(
                        status_code=status_code,
                        headers=headers,
                        target_ip=address,
                        tls_version=secure.version() or "unknown",
                        certificate_expires_at=expires_at,
                    )
        except (OSError, ssl.SSLError, ValueError) as error:
            last_error = error
    raise ValueError("HTTPS connection failed") from last_error


def parse_http_headers(response: bytes) -> tuple[int, dict[str, str]]:
    try:
        header_block = response.split(b"\r\n\r\n", 1)[0].decode("iso-8859-1")
        lines = header_block.split("\r\n")
        status_code = int(lines[0].split(" ", 2)[1])
        headers = {
            name.strip().lower(): value.strip()
            for line in lines[1:]
            if ":" in line
            for name, value in [line.split(":", 1)]
        }
    except (IndexError, ValueError, UnicodeError) as error:
        raise ValueError("HTTPS response headers were invalid") from error
    return status_code, headers


def get_web_probe() -> WebProbe:
    return probe_https


ProbeDep = Annotated[WebProbe, Depends(get_web_probe)]


CHECKS = (
    (
        "strict-transport-security",
        "hsts",
        FindingSeverity.HIGH,
        "HSTS is missing",
        "Enable Strict-Transport-Security with an appropriate max-age.",
    ),
    (
        "content-security-policy",
        "csp",
        FindingSeverity.HIGH,
        "Content Security Policy is missing",
        "Deploy a restrictive Content-Security-Policy and test it in report-only mode first.",
    ),
    (
        "x-content-type-options",
        "content_type",
        FindingSeverity.MEDIUM,
        "MIME sniffing protection is missing",
        "Return X-Content-Type-Options: nosniff.",
    ),
    (
        "x-frame-options",
        "clickjacking",
        FindingSeverity.MEDIUM,
        "Frame protection is missing",
        "Set frame-ancestors in CSP or return X-Frame-Options.",
    ),
    (
        "referrer-policy",
        "referrer",
        FindingSeverity.LOW,
        "Referrer policy is missing",
        "Return a privacy-preserving Referrer-Policy.",
    ),
    (
        "permissions-policy",
        "permissions",
        FindingSeverity.LOW,
        "Permissions policy is missing",
        "Restrict unused browser capabilities with Permissions-Policy.",
    ),
)


class FindingResponse(BaseModel):
    check_key: str
    severity: str
    title: str
    evidence: str
    remediation: str


class ScanResponse(BaseModel):
    id: uuid.UUID
    status: str
    score: int | None
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
    target_ip: str | None
    http_status: int | None
    tls_version: str | None
    certificate_expires_at: datetime | None
    findings: list[FindingResponse]


def serialize_scan(scan: ScanRun) -> ScanResponse:
    return ScanResponse(
        id=scan.id,
        status=scan.status.value,
        score=scan.score,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        target_ip=scan.target_ip,
        http_status=scan.http_status,
        tls_version=scan.tls_version,
        certificate_expires_at=scan.certificate_expires_at,
        findings=[
            FindingResponse(
                check_key=item.check_key,
                severity=item.severity.value,
                title=item.title,
                evidence=item.evidence,
                remediation=item.remediation,
            )
            for item in scan.findings
        ],
    )


@router.post("", response_model=ScanResponse)
def run_scan(
    workspace_id: uuid.UUID,
    asset_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
    probe: ProbeDep,
) -> ScanResponse:
    require_workspace_member(db, workspace_id, principal, WRITE_ROLES)
    asset = db.scalar(select(Asset).where(Asset.id == asset_id, Asset.workspace_id == workspace_id))
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.status != AssetStatus.VERIFIED:
        raise HTTPException(status_code=409, detail="Verify domain ownership before scanning")

    scan = ScanRun(asset_id=asset.id, status=ScanStatus.COMPLETED)
    db.add(scan)
    try:
        observation = probe(asset.hostname)
        scan.target_ip = observation.target_ip
        scan.http_status = observation.status_code
        scan.tls_version = observation.tls_version
        scan.certificate_expires_at = observation.certificate_expires_at
        missing = [check for check in CHECKS if check[0] not in observation.headers]
        deductions = {FindingSeverity.HIGH: 20, FindingSeverity.MEDIUM: 10, FindingSeverity.LOW: 5}
        scan.score = max(0, 100 - sum(deductions[check[2]] for check in missing))
        scan.findings = [
            Finding(
                check_key=check[1],
                severity=check[2],
                title=check[3],
                evidence=(
                    f"{check[0]} header was not present on HTTPS response "
                    f"{observation.status_code}."
                ),
                remediation=check[4],
            )
            for check in missing
        ]
        if observation.certificate_expires_at is not None:
            expires_at = observation.certificate_expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            days_remaining = (expires_at - datetime.now(UTC)).days
            if days_remaining <= 30:
                severity = FindingSeverity.HIGH if days_remaining <= 14 else FindingSeverity.MEDIUM
                scan.findings.append(
                    Finding(
                        check_key="certificate_expiry",
                        severity=severity,
                        title="TLS certificate expires soon"
                        if days_remaining >= 0
                        else "TLS certificate expired",
                        evidence=f"Certificate has {days_remaining} days remaining.",
                        remediation="Renew and deploy the certificate before service interruption.",
                    )
                )
                scan.score = max(
                    0, (scan.score or 0) - (20 if severity == FindingSeverity.HIGH else 10)
                )
    except ValueError as error:
        scan.status = ScanStatus.FAILED
        scan.error_message = str(error)
    scan.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(scan)
    return serialize_scan(scan)


@router.get("", response_model=list[ScanResponse])
def list_scans(
    workspace_id: uuid.UUID, asset_id: uuid.UUID, principal: PrincipalDep, db: DatabaseDep
) -> list[ScanResponse]:
    require_workspace_member(db, workspace_id, principal, set(WRITE_ROLES) | {WorkspaceRole.VIEWER})
    scans = db.scalars(
        select(ScanRun)
        .options(selectinload(ScanRun.findings))
        .join(Asset)
        .where(Asset.id == asset_id, Asset.workspace_id == workspace_id)
        .order_by(ScanRun.started_at.desc())
        .limit(20)
    ).all()
    return [serialize_scan(scan) for scan in scans]
