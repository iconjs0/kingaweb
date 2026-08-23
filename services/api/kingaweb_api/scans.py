import ipaddress
import socket
import uuid
from datetime import UTC, datetime
from typing import Annotated, Protocol

import httpx
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
    resolve_public_addresses(hostname)
    try:
        with httpx.Client(
            follow_redirects=False,
            timeout=httpx.Timeout(6, connect=4),
            headers={"User-Agent": "KingaWeb-Baseline-Scanner/0.1"},
        ) as client:
            with client.stream("GET", f"https://{hostname}/") as response:
                return ProbeResult(status_code=response.status_code, headers=dict(response.headers))
    except (httpx.HTTPError, OSError) as error:
        raise ValueError("HTTPS connection failed") from error


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
    findings: list[FindingResponse]


def serialize_scan(scan: ScanRun) -> ScanResponse:
    return ScanResponse(
        id=scan.id,
        status=scan.status.value,
        score=scan.score,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
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
