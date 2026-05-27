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

