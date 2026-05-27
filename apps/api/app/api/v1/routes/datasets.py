from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.schemas.auth import AuthUser
from app.schemas.dataset import (
    ConfirmUploadRequest,
    DatasetListResponse,
    DatasetPreviewResponse,
    DatasetProfileResponse,
    DatasetResponse,
    UploadSessionRequest,
    UploadSessionResponse,
)
from app.services.datasets import DatasetService

router = APIRouter(prefix="/datasets")


@router.post("/upload-session", response_model=UploadSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_upload_session(
    payload: UploadSessionRequest,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> UploadSessionResponse:
    try:
        return DatasetService(session).create_upload_session(current_user, payload)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for dataset upload session creation.",
        ) from exc


@router.post("/{dataset_id}/confirm-upload", response_model=DatasetResponse)
async def confirm_upload(
    dataset_id: str,
    payload: ConfirmUploadRequest,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DatasetResponse:
    try:
        return DatasetService(session).confirm_upload(
            user=current_user,
            dataset_id=dataset_id,
            payload=payload,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for dataset upload confirmation.",
        ) from exc


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    workspace_id: str | None = Query(default=None),
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DatasetListResponse:
    try:
        return DatasetService(session).list_datasets(
            user=current_user,
            workspace_id=workspace_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for dataset listing.",
        ) from exc


@router.post("/{dataset_id}/analyze", response_model=DatasetResponse)
async def analyze_dataset(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DatasetResponse:
    try:
        return await DatasetService(session).analyze_dataset(
            user=current_user,
            dataset_id=dataset_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for dataset analysis.",
        ) from exc


@router.get("/{dataset_id}/profile", response_model=DatasetProfileResponse)
async def get_profile(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DatasetProfileResponse:
    try:
        return DatasetService(session).get_profile(
            user=current_user,
            dataset_id=dataset_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for dataset profile lookup.",
        ) from exc


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def get_preview(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DatasetPreviewResponse:
    try:
        return DatasetService(session).get_preview(
            user=current_user,
            dataset_id=dataset_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for dataset preview lookup.",
        ) from exc
