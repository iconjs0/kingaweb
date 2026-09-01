import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from kingaweb_api.assets import (
    AssetCreate,
    create_asset,
    lookup_http_proof,
    normalize_hostname,
    renew_verification_challenge,
    verify_asset,
)
from kingaweb_api.auth import Principal
from kingaweb_api.models import (
    Asset,
    AssetStatus,
    Base,
    DomainVerification,
    Membership,
    User,
    VerificationAttempt,
    VerificationMethod,
    VerificationOutcome,
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


def test_http_file_verification_method_is_supported() -> None:
    request = AssetCreate(
        hostname="example.co.tz", verification_method=VerificationMethod.HTTP_FILE
    )
    assert request.verification_method == VerificationMethod.HTTP_FILE


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


def test_expired_challenge_can_be_renewed_with_a_new_token(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.OWNER)
    created = create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), principal, db)
    original = db.scalar(select(DomainVerification))
    assert original is not None
    original.created_at = datetime.now(UTC) - timedelta(minutes=2)
    original.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    renewed = renew_verification_challenge(
        workspace.id,
        created.id,
        AssetCreate(hostname=created.hostname, verification_method=VerificationMethod.HTTP_FILE),
        principal,
        db,
    )

    challenges = db.scalars(
        select(DomainVerification).order_by(DomainVerification.created_at)
    ).all()
    assert len(challenges) == 2
    assert renewed.verification_method == VerificationMethod.HTTP_FILE
    assert renewed.verification_value != created.verification_value
    assert challenges[-1].token_hash == hashlib.sha256(
        renewed.verification_value.removeprefix("kingaweb-verification=").encode()
    ).hexdigest()


def test_challenge_renewal_has_a_one_minute_cooldown(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.OWNER)
    created = create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), principal, db)

    with pytest.raises(HTTPException) as error:
        renew_verification_challenge(
            workspace.id,
            created.id,
            AssetCreate(hostname=created.hostname),
            principal,
            db,
        )

    assert error.value.status_code == 429


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
        workspace.id,
        created.id,
        principal,
        db,
        lambda name: [created.verification_value],
        lambda hostname: None,
    )

    asset = db.get(Asset, created.id)
    assert result.verified is True
    assert asset is not None
    assert asset.status == AssetStatus.VERIFIED
    assert asset.verified_at is not None
    attempt = db.scalar(select(VerificationAttempt))
    assert attempt is not None
    assert attempt.outcome == VerificationOutcome.VERIFIED


def test_wrong_or_unprefixed_dns_record_does_not_verify_asset(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.ANALYST)
    created = create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), principal, db)
    raw_token = created.verification_value.removeprefix("kingaweb-verification=")

    result = verify_asset(
        workspace.id,
        created.id,
        principal,
        db,
        lambda name: [raw_token, "wrong-value"],
        lambda hostname: None,
    )

    asset = db.get(Asset, created.id)
    assert result.verified is False
    assert asset is not None
    assert asset.status == AssetStatus.PENDING_VERIFICATION
    attempt = db.scalar(select(VerificationAttempt))
    assert attempt is not None
    assert attempt.outcome == VerificationOutcome.NOT_FOUND


def test_expired_dns_challenge_is_rejected(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.OWNER)
    created = create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), principal, db)
    verification = db.scalar(select(DomainVerification))
    assert verification is not None
    verification.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    with pytest.raises(HTTPException) as error:
        verify_asset(
            workspace.id, created.id, principal, db, lambda name: [], lambda hostname: None
        )

    assert error.value.status_code == 410
    attempt = db.scalar(select(VerificationAttempt))
    assert attempt is not None
    assert attempt.outcome == VerificationOutcome.EXPIRED


def test_verification_attempts_are_rate_limited_and_audited(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.OWNER)
    created = create_asset(workspace.id, AssetCreate(hostname="example.co.tz"), principal, db)

    for _ in range(5):
        result = verify_asset(
            workspace.id, created.id, principal, db, lambda name: [], lambda hostname: None
        )
        assert result.verified is False

    with pytest.raises(HTTPException) as error:
        verify_asset(
            workspace.id, created.id, principal, db, lambda name: [], lambda hostname: None
        )

    assert error.value.status_code == 429
    attempts = db.scalars(select(VerificationAttempt)).all()
    assert [attempt.outcome for attempt in attempts].count(VerificationOutcome.NOT_FOUND) == 5
    assert attempts[-1].outcome == VerificationOutcome.RATE_LIMITED


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
            lambda hostname: None,
        )

    assert error.value.status_code == 403


def test_matching_https_file_verifies_asset(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.OWNER)
    created = create_asset(
        workspace.id,
        AssetCreate(hostname="lab.example.com", verification_method=VerificationMethod.HTTP_FILE),
        principal,
        db,
    )

    result = verify_asset(
        workspace.id,
        created.id,
        principal,
        db,
        lambda name: [],
        lambda hostname: created.verification_value,
    )

    assert created.verification_name == (
        "https://lab.example.com/.well-known/kingaweb-verification.txt"
    )
    assert result.verified is True


@pytest.mark.skipif(
    os.getenv("KINGAWEB_RUN_LIVE_LAB_TEST") != "1",
    reason="Live Security Lab integration test is opt-in",
)
def test_live_security_lab_https_proof_verifies_asset(db: Session) -> None:
    workspace, principal = seed_member(db, WorkspaceRole.OWNER)
    proof_token = "kingaweb-security-lab-authorized-test"
    created = create_asset(
        workspace.id,
        AssetCreate(
            hostname="kingaweb-security-lab.cyberb008.chatgpt.site",
            verification_method=VerificationMethod.HTTP_FILE,
        ),
        principal,
        db,
    )
    verification = db.scalar(select(DomainVerification))
    assert verification is not None
    verification.token_hash = hashlib.sha256(proof_token.encode()).hexdigest()
    db.commit()

    result = verify_asset(
        workspace.id,
        created.id,
        principal,
        db,
        lambda name: [],
        lookup_http_proof,
    )

    assert result.verified is True
    assert result.status == AssetStatus.VERIFIED.value
