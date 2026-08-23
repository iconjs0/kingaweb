import socket
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from kingaweb_api.auth import Principal
from kingaweb_api.models import (
    Asset,
    AssetStatus,
    Base,
    Finding,
    Membership,
    ScanRun,
    ScanStatus,
    User,
    Workspace,
    WorkspaceRole,
)
from kingaweb_api.network import resolve_public_addresses
from kingaweb_api.scans import ProbeResult, parse_http_headers, run_scan


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session


def seed_asset(
    db: Session, status: AssetStatus = AssetStatus.VERIFIED
) -> tuple[Workspace, Asset, Principal]:
    user = User(oidc_subject="oidc|owner", email="owner@example.com")
    workspace = Workspace(name="Kinga", slug=f"kinga-{uuid.uuid4().hex[:8]}")
    db.add_all([user, workspace])
    db.flush()
    asset = Asset(
        workspace_id=workspace.id,
        hostname="example.co.tz",
        status=status,
        created_by_user_id=user.id,
    )
    db.add_all(
        [
            Membership(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.OWNER),
            asset,
        ]
    )
    db.commit()
    return workspace, asset, Principal(subject=user.oidc_subject, email=user.email, name=None)


def test_scan_records_score_and_missing_header_evidence(db: Session) -> None:
    workspace, asset, principal = seed_asset(db)
    result = run_scan(
        workspace.id,
        asset.id,
        principal,
        db,
        lambda hostname: ProbeResult(
            status_code=200,
            headers={
                "strict-transport-security": "max-age=31536000",
                "x-content-type-options": "nosniff",
            },
        ),
    )

    assert result.status == "completed"
    assert result.score == 60
    assert {finding.check_key for finding in result.findings} == {
        "csp",
        "clickjacking",
        "referrer",
        "permissions",
    }
    assert db.scalar(select(ScanRun)) is not None
    assert len(db.scalars(select(Finding)).all()) == 4


def test_unverified_asset_cannot_be_scanned(db: Session) -> None:
    workspace, asset, principal = seed_asset(db, AssetStatus.PENDING_VERIFICATION)

    with pytest.raises(HTTPException) as error:
        run_scan(
            workspace.id,
            asset.id,
            principal,
            db,
            lambda hostname: ProbeResult(status_code=200, headers={}),
        )

    assert error.value.status_code == 409


def test_probe_failure_is_recorded_without_exposing_exception(db: Session) -> None:
    workspace, asset, principal = seed_asset(db)

    def unavailable(_hostname: str) -> ProbeResult:
        raise ValueError("HTTPS connection failed")

    result = run_scan(workspace.id, asset.id, principal, db, unavailable)

    assert result.status == ScanStatus.FAILED.value
    assert result.score is None
    assert result.error_message == "HTTPS connection failed"


def test_private_destination_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )

    with pytest.raises(ValueError, match="private or reserved"):
        resolve_public_addresses("internal.example")


def test_http_headers_are_parsed_without_reading_response_body() -> None:
    status, headers = parse_http_headers(
        b"HTTP/1.1 204 No Content\r\nX-Content-Type-Options: nosniff\r\n\r\nignored"
    )

    assert status == 204
    assert headers == {"x-content-type-options": "nosniff"}


def test_certificate_expiry_creates_high_severity_finding(db: Session) -> None:
    workspace, asset, principal = seed_asset(db)
    result = run_scan(
        workspace.id,
        asset.id,
        principal,
        db,
        lambda hostname: ProbeResult(
            status_code=200,
            headers={
                check: "present"
                for check in (
                    "strict-transport-security",
                    "content-security-policy",
                    "x-content-type-options",
                    "x-frame-options",
                    "referrer-policy",
                    "permissions-policy",
                )
            },
            target_ip="203.0.113.20",
            tls_version="TLSv1.3",
            certificate_expires_at=datetime.now(UTC) + timedelta(days=7),
        ),
    )

    assert result.score == 80
    assert result.target_ip == "203.0.113.20"
    assert result.tls_version == "TLSv1.3"
    assert result.findings[0].check_key == "certificate_expiry"
    assert result.findings[0].severity == "high"
