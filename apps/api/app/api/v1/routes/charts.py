from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.schemas.auth import AuthUser
from app.schemas.chart import ChartRecommendationResponse
from app.services.charts.service import ChartService

router = APIRouter(prefix="/datasets/{dataset_id}/charts")


@router.post("/recommend", response_model=ChartRecommendationResponse, status_code=status.HTTP_201_CREATED)
async def recommend_charts(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ChartRecommendationResponse:
    try:
        return ChartService(session).recommend_charts(user=current_user, dataset_id=dataset_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for chart recommendation.",
        ) from exc


@router.get("", response_model=ChartRecommendationResponse)
async def list_charts(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ChartRecommendationResponse:
    try:
        return ChartService(session).list_charts(user=current_user, dataset_id=dataset_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for chart lookup.",
        ) from exc

