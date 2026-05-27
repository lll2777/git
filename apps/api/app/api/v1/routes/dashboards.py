from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.schemas.auth import AuthUser
from app.schemas.dashboard import (
    DashboardCreateRequest,
    DashboardListResponse,
    DashboardResponse,
)
from app.services.dashboards import DashboardService

router = APIRouter()


@router.post("/datasets/{dataset_id}/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def save_dataset_dashboard(
    dataset_id: str,
    payload: DashboardCreateRequest,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DashboardResponse:
    try:
        return DashboardService(session).save_from_dataset(
            user=current_user,
            dataset_id=dataset_id,
            payload=payload,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for dashboard saving.",
        ) from exc


@router.get("/datasets/{dataset_id}/dashboards", response_model=DashboardListResponse)
async def list_dataset_dashboards(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DashboardListResponse:
    try:
        return DashboardService(session).list_for_dataset(
            user=current_user,
            dataset_id=dataset_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for dashboard lookup.",
        ) from exc


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DashboardResponse:
    try:
        return DashboardService(session).get_dashboard(
            user=current_user,
            dashboard_id=dashboard_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for dashboard lookup.",
        ) from exc
