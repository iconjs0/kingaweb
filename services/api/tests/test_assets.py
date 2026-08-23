import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from kingaweb_api.assets import AssetCreate, create_asset, normalize_hostname, verify_asset
from kingaweb_api.auth import Principal
from kingaweb_api.models import (
    Asset,
    AssetStatus,
    Base,
    DomainVerification,
    Membership,
    User,
    VerificationMethod,
    Workspace,
    WorkspaceRole,
)


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session


def seed_member(db: Session, role: WorkspaceRole) -> tuple[Workspace, Principal]:
    user = User(oidc_subject="oidc|member", email="member@example.com")
    workspace = Workspace(name="Mwangaza", slug=f"mwangaza-{uuid.uuid4().hex[:8]}")
    db.add_all([user, workspace])
    db.flush()
    db.add(Membership(workspace_id=workspace.id, user_id=user.id, role=role))
    db.commit()
    return workspace, Principal(subject=user.oidc_subject, email=user.email, name=None)


def test_hostname_normalization_and_ip_rejection() -> None:
    assert normalize_hostname("  Mwangaza.CO.TZ. ") == "mwangaza.co.tz"
    with pytest.raises(ValueError, match="IP addresses"):
        normalize_hostname("127.0.0.1")
    with pytest.raises(ValueError, match="without a scheme"):
        normalize_hostname("https://example.com/path")


def test_unsupported_verification_method_is_rejected() -> None:
    with pytest.raises(ValueError, match="Only DNS TXT"):
        AssetCreate(hostname="example.co.tz", verification_method=VerificationMethod.HTTP_FILE)


def test_analyst_can_create_asset_and_plaintext_token_is_not_stored(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.ANALYST)

    result = create_asset(workspace.id, AssetCreate(hostname="Mwangaza.CO.TZ"), principal, db)

    verification = db.scalar(select(DomainVerification))
    assert result.hostname == "mwangaza.co.tz"
    assert result.verification_name == "_kingaweb-verification.mwangaza.co.tz"
    token = result.verification_value.removeprefix("kingaweb-verification=")
    assert verification is not None
    assert verification.token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert token not in verification.token_hash


def test_viewer_cannot_create_asset(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.VIEWER)

    with pytest.raises(HTTPException) as error:
        create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), principal, db)

    assert error.value.status_code == 403


def test_non_member_receives_not_found(db: Session) -> None:
    workspace, _ = seed_member(db, WorkspaceRole.OWNER)
    outsider = Principal(subject="oidc|outsider", email="outsider@example.com", name=None)

    with pytest.raises(HTTPException) as error:
        create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), outsider, db)

    assert error.value.status_code == 404


def test_matching_dns_record_verifies_asset(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.OWNER)
    created = create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), principal, db)

    result = verify_asset(
        workspace.id, created.id, principal, db, lambda name: [created.verification_value]
    )

    asset = db.get(Asset, created.id)
    assert result.verified is True
    assert asset is not None
    assert asset.status == AssetStatus.VERIFIED
    assert asset.verified_at is not None


def test_wrong_or_unprefixed_dns_record_does_not_verify_asset(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.ANALYST)
    created = create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), principal, db)
    raw_token = created.verification_value.removeprefix("kingaweb-verification=")

    result = verify_asset(
        workspace.id, created.id, principal, db, lambda name: [raw_token, "wrong-value"]
    )

    asset = db.get(Asset, created.id)
    assert result.verified is False
    assert asset is not None
    assert asset.status == AssetStatus.PENDING_VERIFICATION


def test_expired_dns_challenge_is_rejected(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.OWNER)
    created = create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), principal, db)
    verification = db.scalar(select(DomainVerification))
    assert verification is not None
    verification.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    with pytest.raises(HTTPException) as error:
        verify_asset(workspace.id, created.id, principal, db, lambda name: [])

    assert error.value.status_code == 410


def test_viewer_cannot_verify_asset(db: Session) -> None:
    workspace, owner = seed_member(db, WorkspaceRole.OWNER)
    created = create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), owner, db)
    viewer = User(oidc_subject="oidc|viewer", email="viewer@example.com")
    db.add(viewer)
    db.flush()
    db.add(Membership(workspace_id=workspace.id, user_id=viewer.id, role=WorkspaceRole.VIEWER))
    db.commit()

    with pytest.raises(HTTPException) as error:
        verify_asset(
            workspace.id,
            created.id,
            Principal(subject=viewer.oidc_subject, email=viewer.email, name=None),
            db,
            lambda name: [created.verification_value],
        )

    assert error.value.status_code == 403
