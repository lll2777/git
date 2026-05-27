import asyncio

from app.db.session import SessionLocal
from app.repositories.jobs import JobRepository
from app.schemas.auth import AuthUser
from app.services.datasets import DatasetService
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.datasets.analyze_dataset")
def analyze_dataset_task(job_id: str, dataset_id: str, user_id: str) -> dict[str, str]:
    session = SessionLocal()
    job_repository = JobRepository(session)
    try:
        job_repository.mark_running(job_id=job_id, progress=15)
        user = AuthUser(id=user_id, email=None, role=None, claims={})
        dataset = asyncio.run(
            DatasetService(session).analyze_dataset(
                user=user,
                dataset_id=dataset_id,
            ),
        )
        if dataset.status == "failed":
            job_repository.mark_failed(
                job_id=job_id,
                error_message=dataset.error_message or "Dataset analysis failed.",
            )
        else:
            job_repository.mark_succeeded(
                job_id=job_id,
                result={
                    "dataset_id": dataset.id,
                    "status": dataset.status,
                    "row_count": dataset.row_count,
                    "column_count": dataset.column_count,
                },
            )
        return {"dataset_id": dataset.id, "status": dataset.status}
    except Exception as exc:
        job_repository.mark_failed(job_id=job_id, error_message=str(exc))
        raise
    finally:
        session.close()
