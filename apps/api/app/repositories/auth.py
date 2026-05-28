from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.records import normalize_record, normalize_records
from app.schemas.auth import AuthUser, BootstrapRequest, ProfileResponse, WorkspaceResponse


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_profile(self, user_id: str) -> ProfileResponse | None:
        row = self.session.execute(
            text(
                """
                select id, email, display_name, avatar_url
                from profiles
                where id = :user_id
                """,
            ),
            {"user_id": user_id},
        ).mappings().first()
        if not row:
            return None
        return ProfileResponse(**normalize_record(row))

    def list_workspaces(self, user_id: str) -> list[WorkspaceResponse]:
        rows = self.session.execute(
            text(
                """
                select w.id, w.name, w.slug, wm.role
                from workspaces w
                join workspace_members wm on wm.workspace_id = w.id
                where wm.user_id = :user_id
                order by w.created_at asc
                """,
            ),
            {"user_id": user_id},
        ).mappings().all()
        return [WorkspaceResponse(**row) for row in normalize_records(rows)]

    def bootstrap_user(self, user: AuthUser, payload: BootstrapRequest) -> tuple[ProfileResponse, WorkspaceResponse]:
        display_name = payload.display_name or (user.email.split("@")[0] if user.email else "New user")
        workspace_name = payload.workspace_name or "My Workspace"
        workspace_id = str(uuid4())
        workspace_slug = f"workspace-{workspace_id[:8]}"

        self.session.execute(
            text(
                """
                insert into profiles (id, email, display_name, avatar_url)
                values (:id, :email, :display_name, :avatar_url)
                on conflict (id) do update set
                  email = excluded.email,
                  display_name = coalesce(profiles.display_name, excluded.display_name),
                  avatar_url = coalesce(profiles.avatar_url, excluded.avatar_url),
                  updated_at = now()
                """,
            ),
            {
                "id": user.id,
                "email": user.email or "",
                "display_name": display_name,
                "avatar_url": None,
            },
        )

        existing_workspace = self.session.execute(
            text(
                """
                select w.id, w.name, w.slug, wm.role
                from workspaces w
                join workspace_members wm on wm.workspace_id = w.id
                where wm.user_id = :user_id
                order by w.created_at asc
                limit 1
                """,
            ),
            {"user_id": user.id},
        ).mappings().first()

        if existing_workspace:
            self.session.commit()
            profile = self.get_profile(user.id)
            if profile is None:
                raise RuntimeError("Profile bootstrap failed.")
            return profile, WorkspaceResponse(**normalize_record(existing_workspace))

        self.session.execute(
            text(
                """
                insert into workspaces (id, owner_id, name, slug)
                values (:id, :owner_id, :name, :slug)
                """,
            ),
            {
                "id": workspace_id,
                "owner_id": user.id,
                "name": workspace_name,
                "slug": workspace_slug,
            },
        )
        self.session.execute(
            text(
                """
                insert into workspace_members (workspace_id, user_id, role)
                values (:workspace_id, :user_id, 'owner')
                on conflict (workspace_id, user_id) do nothing
                """,
            ),
            {
                "workspace_id": workspace_id,
                "user_id": user.id,
            },
        )
        self.session.commit()

        profile = self.get_profile(user.id)
        if profile is None:
            raise RuntimeError("Profile bootstrap failed.")
        return profile, WorkspaceResponse(
            id=workspace_id,
            name=workspace_name,
            slug=workspace_slug,
            role="owner",
        )
