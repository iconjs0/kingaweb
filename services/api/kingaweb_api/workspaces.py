import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import Principal, get_current_principal
from .database import get_db
from .models import Asset, Membership, User, Workspace

router = APIRouter(prefix="/v1", tags=["Workspaces"])
PrincipalDep = Annotated[Principal, Depends(get_current_principal)]
DatabaseDep = Annotated[Session, Depends(get_db)]


class WorkspaceSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    role: str
    asset_count: int


class AssetSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hostname: str
    status: str


@router.get("/workspaces", response_model=list[WorkspaceSummary])
def list_workspaces(principal: PrincipalDep, db: DatabaseDep) -> list[WorkspaceSummary]:
    rows = db.execute(
        select(Workspace, Membership)
        .join(Membership, Membership.workspace_id == Workspace.id)
        .join(User, User.id == Membership.user_id)
        .where(User.oidc_subject == principal.subject)
        .order_by(Workspace.name)
    ).all()
    return [
        WorkspaceSummary(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            role=membership.role.value,
            asset_count=len(
                db.scalars(select(Asset).where(Asset.workspace_id == workspace.id)).all()
            ),
        )
        for workspace, membership in rows
    ]


@router.get("/workspaces/{workspace_id}/assets", response_model=list[AssetSummary])
def list_assets(
    workspace_id: uuid.UUID, principal: PrincipalDep, db: DatabaseDep
) -> list[AssetSummary]:
    membership = db.scalar(
        select(Membership)
        .join(User, User.id == Membership.user_id)
        .where(
            User.oidc_subject == principal.subject,
            Membership.workspace_id == workspace_id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return list(db.scalars(select(Asset).where(Asset.workspace_id == workspace_id)).all())
