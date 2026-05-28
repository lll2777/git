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
    DatasetPreviewResponse,
    DatasetProfileResponse,
    DatasetResponse,
    UploadSessionRequest,
    UploadSessionResponse,
    UploadTarget,
)
from app.services.analysis.profiler import DatasetProfiler
from app.services.storage import SupabaseStorageClient

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

    async def analyze_dataset(self, *, user: AuthUser, dataset_id: str) -> DatasetResponse:
        dataset = self.repository.get_dataset_for_user(dataset_id=dataset_id, user_id=user.id)
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset was not found.",
            )

        if dataset.status not in {"uploaded", "failed", "ready"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dataset must be uploaded before analysis.",
            )

        if not dataset.storage_bucket or not dataset.storage_path or not dataset.original_filename:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dataset storage metadata is incomplete.",
            )

        self.repository.mark_processing(dataset_id=dataset_id)

        try:
            content = await SupabaseStorageClient().download_object(
                bucket=dataset.storage_bucket,
                path=dataset.storage_path,
            )
            analysis = DatasetProfiler().analyze(
                content=content,
                filename=dataset.original_filename,
            )
            return self.repository.save_analysis(
                dataset_id=dataset_id,
                row_count=analysis.row_count,
                column_count=analysis.column_count,
                columns=analysis.columns,
                preview_columns=analysis.preview_columns,
                preview_rows=analysis.preview_rows,
                summary=analysis.summary,
                missing_values=analysis.missing_values,
                outliers=analysis.outliers,
                correlations=analysis.correlations,
                time_series=analysis.time_series,
                categorical_aggregates=analysis.categorical_aggregates,
            )
        except HTTPException:
            self.repository.mark_failed(
                dataset_id=dataset_id,
                error_message="Storage download failed during dataset analysis.",
            )
            raise
        except Exception as exc:
            message = str(exc) or exc.__class__.__name__
            failed = self.repository.mark_failed(dataset_id=dataset_id, error_message=message)
            if failed is not None:
                return failed
            raise

    def get_profile(self, *, user: AuthUser, dataset_id: str) -> DatasetProfileResponse:
        profile = self.repository.get_profile(dataset_id=dataset_id, user_id=user.id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset profile was not found.",
            )
        return profile

    def get_preview(self, *, user: AuthUser, dataset_id: str) -> DatasetPreviewResponse:
        preview = self.repository.get_preview(dataset_id=dataset_id, user_id=user.id)
        if preview is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset preview was not found.",
            )
        return preview

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
