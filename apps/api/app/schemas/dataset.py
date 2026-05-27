from typing import Any

from pydantic import BaseModel, Field


class DatasetResponse(BaseModel):
    id: str
    workspace_id: str
    owner_id: str
    name: str
    status: str
    row_count: int | None = None
    column_count: int | None = None
    storage_bucket: str | None = None
    storage_path: str | None = None
    original_filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    error_message: str | None = None


class UploadSessionRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)
    workspace_id: str | None = None


class UploadTarget(BaseModel):
    bucket: str
    path: str
    strategy: str = "supabase_client_upload"


class UploadSessionResponse(BaseModel):
    dataset: DatasetResponse
    upload: UploadTarget


class ConfirmUploadRequest(BaseModel):
    size_bytes: int | None = Field(default=None, gt=0)
    content_type: str | None = None


class DatasetListResponse(BaseModel):
    datasets: list[DatasetResponse]


class DatasetColumnProfile(BaseModel):
    name: str
    original_name: str
    data_type: str
    semantic_type: str | None = None
    nullable: bool
    missing_count: int
    unique_count: int | None = None
    min_value: str | None = None
    max_value: str | None = None
    mean_value: float | None = None
    median_value: float | None = None
    stddev_value: float | None = None
    profile: dict[str, Any] = {}


class DatasetProfileResponse(BaseModel):
    dataset: DatasetResponse
    columns: list[DatasetColumnProfile]
    summary: dict[str, Any]
    missing_values: dict[str, Any]
    outliers: dict[str, Any]
    correlations: dict[str, Any]
    time_series: dict[str, Any]
    categorical_aggregates: dict[str, Any]


class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int

