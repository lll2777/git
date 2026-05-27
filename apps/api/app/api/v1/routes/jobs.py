from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.schemas.auth import AuthUser
from app.schemas.job import JobListResponse, JobResponse
from app.services.jobs import JobService

router = APIRouter()


@router.post("/datasets/{dataset_id}/analysis-jobs", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_dataset_analysis(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobResponse:
    try:
        return JobService(session).enqueue_dataset_analysis(
            user=current_user,
            dataset_id=dataset_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for job creation.",
        ) from exc


@router.get("/datasets/{dataset_id}/jobs", response_model=JobListResponse)
async def list_dataset_jobs(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobListResponse:
    try:
        return JobService(session).list_dataset_jobs(
            user=current_user,
            dataset_id=dataset_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for job lookup.",
        ) from exc


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobResponse:
    try:
        return JobService(session).get_job(user=current_user, job_id=job_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for job lookup.",
        ) from exc
