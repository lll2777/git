from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.schemas.auth import AuthMeResponse, AuthUser, BootstrapRequest, BootstrapResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth")


@router.get("/me", response_model=AuthMeResponse)
async def get_me(
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AuthMeResponse:
    return AuthService(session).get_me(current_user)


@router.post("/bootstrap", response_model=BootstrapResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_user(
    payload: BootstrapRequest,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> BootstrapResponse:
    try:
        return AuthService(session).bootstrap(current_user, payload)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for profile bootstrap.",
        ) from exc

