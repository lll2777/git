from typing import Any

from pydantic import BaseModel, EmailStr


class AuthUser(BaseModel):
    id: str
    email: EmailStr | None = None
    role: str | None = None
    claims: dict[str, Any]


class ProfileResponse(BaseModel):
    id: str
    email: EmailStr | str
    display_name: str | None = None
    avatar_url: str | None = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str
    role: str


class BootstrapRequest(BaseModel):
    display_name: str | None = None
    workspace_name: str | None = None


class AuthMeResponse(BaseModel):
    user: AuthUser
    profile: ProfileResponse | None = None
    workspaces: list[WorkspaceResponse] = []


class BootstrapResponse(BaseModel):
    profile: ProfileResponse
    workspace: WorkspaceResponse

