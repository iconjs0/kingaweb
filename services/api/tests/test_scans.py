import socket
import uuid

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
from kingaweb_api.scans import ProbeResult, resolve_public_addresses, run_scan


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
