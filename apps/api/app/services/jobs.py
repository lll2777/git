from fastapi import HTTPException, status
from kombu.exceptions import KombuError
from sqlalchemy.orm import Session

from app.repositories.datasets import DatasetRepository
from app.repositories.jobs import JobRepository
from app.schemas.auth import AuthUser
from app.schemas.job import JobListResponse, JobResponse
from app.tasks.datasets import analyze_dataset_task


class JobService:
    def __init__(self, session: Session) -> None:
        self.dataset_repository = DatasetRepository(session)
        self.job_repository = JobRepository(session)

    def enqueue_dataset_analysis(self, *, user: AuthUser, dataset_id: str) -> JobResponse:
        dataset = self.dataset_repository.get_dataset_for_user(
            dataset_id=dataset_id,
            user_id=user.id,
        )
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset was not found.",
            )

        if dataset.status not in {"uploaded", "failed", "ready"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dataset must be uploaded before background analysis.",
            )

        job = self.job_repository.create_job(
            workspace_id=dataset.workspace_id,
            dataset_id=dataset.id,
            job_type="dataset_analysis",
            payload={"dataset_id": dataset.id, "requested_by": user.id},
        )

        try:
            async_result = analyze_dataset_task.delay(job.id, dataset.id, user.id)
        except KombuError as exc:
            failed = self.job_repository.mark_failed(
                job_id=job.id,
                error_message="Redis/Celery broker is unavailable.",
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis/Celery broker is unavailable.",
            ) from exc
        except Exception as exc:
            self.job_repository.mark_failed(job_id=job.id, error_message=str(exc))
            raise

        return self.job_repository.set_celery_task_id(
            job_id=job.id,
            celery_task_id=async_result.id,
        )

    def list_dataset_jobs(self, *, user: AuthUser, dataset_id: str) -> JobListResponse:
        dataset = self.dataset_repository.get_dataset_for_user(
            dataset_id=dataset_id,
            user_id=user.id,
        )
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset was not found.",
            )
        return JobListResponse(
            jobs=self.job_repository.list_for_dataset(
                dataset_id=dataset_id,
                user_id=user.id,
            ),
        )

    def get_job(self, *, user: AuthUser, job_id: str) -> JobResponse:
        job = self.job_repository.get_for_user(job_id=job_id, user_id=user.id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job was not found.",
            )
        return job
