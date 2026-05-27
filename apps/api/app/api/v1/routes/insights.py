from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.schemas.auth import AuthUser
from app.schemas.insight import InsightGenerationResponse, InsightListResponse
from app.services.insights import InsightService

router = APIRouter(prefix="/datasets/{dataset_id}/insights")


@router.post("/generate", response_model=InsightGenerationResponse)
async def generate_insights(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> InsightGenerationResponse:
    try:
        return await InsightService(session).generate_insights(
            user=current_user,
            dataset_id=dataset_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for insight generation.",
        ) from exc


@router.get("", response_model=InsightListResponse)
async def list_insights(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> InsightListResponse:
    try:
        return InsightService(session).list_insights(
            user=current_user,
            dataset_id=dataset_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for insight lookup.",
        ) from exc
