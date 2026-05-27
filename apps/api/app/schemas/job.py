from typing import Any

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: str
    workspace_id: str
    dataset_id: str | None = None
    job_type: str
    status: str
    progress: int
    celery_task_id: str | None = None
    payload: dict[str, Any]
    result: dict[str, Any]
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
