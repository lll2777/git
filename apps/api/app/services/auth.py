from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.auth import AuthRepository
from app.schemas.auth import (
    AuthMeResponse,
    AuthUser,
    BootstrapRequest,
    BootstrapResponse,
)


class AuthService:
    def __init__(self, session: Session) -> None:
        self.repository = AuthRepository(session)

    def get_me(self, user: AuthUser) -> AuthMeResponse:
        try:
            return AuthMeResponse(
                user=user,
                profile=self.repository.get_profile(user.id),
                workspaces=self.repository.list_workspaces(user.id),
            )
        except SQLAlchemyError:
            return AuthMeResponse(user=user, profile=None, workspaces=[])

    def bootstrap(self, user: AuthUser, payload: BootstrapRequest) -> BootstrapResponse:
        profile, workspace = self.repository.bootstrap_user(user=user, payload=payload)
        return BootstrapResponse(profile=profile, workspace=workspace)

