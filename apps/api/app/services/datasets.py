from pathlib import Path
from re import sub
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.datasets import DatasetRepository
from app.schemas.auth import AuthUser
from app.schemas.dataset import (
    ConfirmUploadRequest,
    DatasetListResponse,
    DatasetResponse,
    UploadSessionRequest,
    UploadSessionResponse,
    UploadTarget,
)

ALLOWED_EXTENSIONS = {".csv", ".xls", ".xlsx"}
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/octet-stream",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class DatasetService:
    def __init__(self, session: Session) -> None:
        self.repository = DatasetRepository(session)
        self.settings = get_settings()

    def create_upload_session(
        self,
        user: AuthUser,
        payload: UploadSessionRequest,
    ) -> UploadSessionResponse:
        self._validate_file(payload)

        workspace_id = payload.workspace_id or self.repository.get_default_workspace_id(user.id)
        if not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Create a workspace before uploading datasets.",
            )

        if not self.repository.user_can_access_workspace(user.id, workspace_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this workspace.",
            )

        dataset_id = str(uuid4())
        safe_filename = self._safe_filename(payload.filename)
        storage_path = f"{workspace_id}/{user.id}/{dataset_id}/{safe_filename}"

        dataset = self.repository.create_dataset(
            dataset_id=dataset_id,
            workspace_id=workspace_id,
            owner_id=user.id,
            name=Path(payload.filename).stem,
            bucket=self.settings.supabase_storage_bucket,
            path=storage_path,
            original_filename=payload.filename,
            content_type=payload.content_type,
            size_bytes=payload.size_bytes,
        )

        return UploadSessionResponse(
            dataset=dataset,
            upload=UploadTarget(
                bucket=self.settings.supabase_storage_bucket,
                path=storage_path,
            ),
        )

    def confirm_upload(
        self,
        *,
        user: AuthUser,
        dataset_id: str,
        payload: ConfirmUploadRequest,
    ) -> DatasetResponse:
        dataset = self.repository.confirm_upload(
            dataset_id=dataset_id,
            user_id=user.id,
            size_bytes=payload.size_bytes,
            content_type=payload.content_type,
        )
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset was not found.",
            )
        return dataset

    def list_datasets(self, *, user: AuthUser, workspace_id: str | None) -> DatasetListResponse:
        return DatasetListResponse(
            datasets=self.repository.list_datasets(
                user_id=user.id,
                workspace_id=workspace_id,
            ),
        )

    def _validate_file(self, payload: UploadSessionRequest) -> None:
        extension = Path(payload.filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only CSV and Excel files are supported.",
            )

        if payload.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported file content type.",
            )

        if payload.size_bytes > self.settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds the configured upload size limit.",
            )

    @staticmethod
    def _safe_filename(filename: str) -> str:
        path = Path(filename)
        stem = sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip(".-") or "dataset"
        suffix = path.suffix.lower()
        return f"{stem}{suffix}"
