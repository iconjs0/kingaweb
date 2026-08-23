import argparse
import secrets

from sqlalchemy import select

from .database import SessionLocal
from .models import Membership, User, Workspace, WorkspaceRole


def seed_development(subject: str, email: str, workspace_name: str) -> None:
    slug = workspace_name.strip().lower().replace(" ", "-")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.oidc_subject == subject))
        if user is None:
            user = User(oidc_subject=subject, email=email, display_name="Development Owner")
            db.add(user)

        workspace = db.scalar(select(Workspace).where(Workspace.slug == slug))
        if workspace is None:
            workspace = Workspace(name=workspace_name, slug=slug)
            db.add(workspace)

        db.flush()
        membership = db.scalar(
            select(Membership).where(
                Membership.workspace_id == workspace.id,
                Membership.user_id == user.id,
            )
        )
        if membership is None:
            db.add(
                Membership(
                    workspace_id=workspace.id,
                    user_id=user.id,
                    role=WorkspaceRole.OWNER,
                )
            )
        db.commit()
        print(f"Development workspace ready: {workspace.name} ({workspace.id})")
        print(f"OIDC subject: {user.oidc_subject}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed an idempotent KingaWeb development workspace"
    )
    parser.add_argument("--subject", default=f"development|{secrets.token_hex(8)}")
    parser.add_argument("--email", default="owner@kingaweb.local")
    parser.add_argument("--workspace", default="KingaWeb Development")
    args = parser.parse_args()
    seed_development(args.subject, args.email, args.workspace)


if __name__ == "__main__":
    main()
