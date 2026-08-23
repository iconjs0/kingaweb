import hashlib
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from kingaweb_api.assets import AssetCreate, create_asset, normalize_hostname
from kingaweb_api.auth import Principal
from kingaweb_api.models import (
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
