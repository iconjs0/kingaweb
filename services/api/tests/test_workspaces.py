from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from kingaweb_api.auth import Principal
from kingaweb_api.models import Base, Membership, User, Workspace, WorkspaceRole
from kingaweb_api.workspaces import list_workspaces


def test_workspace_listing_is_scoped_to_authenticated_subject() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        owner = User(oidc_subject="development|owner", email="owner@kingaweb.local")
        outsider = User(oidc_subject="development|outsider", email="outsider@kingaweb.local")
        workspace = Workspace(name="KingaWeb Development", slug="kingaweb-development")
        db.add_all([owner, outsider, workspace])
        db.flush()
        db.add(Membership(workspace_id=workspace.id, user_id=owner.id, role=WorkspaceRole.OWNER))
        db.commit()

        result = list_workspaces(
            Principal(subject=owner.oidc_subject, email=owner.email, name=None), db
        )
        hidden = list_workspaces(
            Principal(subject=outsider.oidc_subject, email=outsider.email, name=None), db
        )

    assert len(result) == 1
    assert result[0].role == "owner"
    assert result[0].asset_count == 0
    assert hidden == []
