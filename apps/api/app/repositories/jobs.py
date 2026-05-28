import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.records import normalize_record, normalize_records
from app.schemas.job import JobResponse


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_job(
        self,
        *,
        workspace_id: str,
        dataset_id: str | None,
        job_type: str,
        payload: dict[str, Any],
    ) -> JobResponse:
        row = self.session.execute(
            text(
                """
                insert into jobs (
                  id,
                  workspace_id,
                  dataset_id,
                  job_type,
                  status,
                  progress,
                  payload,
                  result
                )
                values (
                  gen_random_uuid(),
                  :workspace_id,
                  :dataset_id,
                  :job_type,
                  'queued',
                  0,
                  cast(:payload as jsonb),
                  '{}'::jsonb
                )
                returning
                  id,
                  workspace_id,
                  dataset_id,
                  job_type,
                  status,
                  progress,
                  celery_task_id,
                  payload,
                  result,
                  error_message,
                  created_at::text as created_at,
                  updated_at::text as updated_at
                """,
            ),
            {
                "workspace_id": workspace_id,
                "dataset_id": dataset_id,
                "job_type": job_type,
                "payload": json.dumps(payload),
            },
        ).mappings().one()
        self.session.commit()
        return JobResponse(**normalize_record(row))

    def set_celery_task_id(self, *, job_id: str, celery_task_id: str) -> JobResponse:
        return self._update_job(
            job_id=job_id,
            status="queued",
            progress=5,
            celery_task_id=celery_task_id,
        )

    def mark_running(self, *, job_id: str, progress: int = 10) -> JobResponse:
        return self._update_job(job_id=job_id, status="running", progress=progress)

    def mark_succeeded(
        self,
        *,
        job_id: str,
        result: dict[str, Any] | None = None,
    ) -> JobResponse:
        return self._update_job(
            job_id=job_id,
            status="succeeded",
            progress=100,
            result=result or {},
            error_message=None,
        )

    def mark_failed(self, *, job_id: str, error_message: str) -> JobResponse:
        return self._update_job(
            job_id=job_id,
            status="failed",
            error_message=error_message[:1000],
        )

    def get_for_user(self, *, job_id: str, user_id: str) -> JobResponse | None:
        row = self.session.execute(
            text(
                """
                select
                  j.id,
                  j.workspace_id,
                  j.dataset_id,
                  j.job_type,
                  j.status,
                  j.progress,
                  j.celery_task_id,
                  j.payload,
                  j.result,
                  j.error_message,
                  j.created_at::text as created_at,
                  j.updated_at::text as updated_at
                from jobs j
                join workspace_members wm on wm.workspace_id = j.workspace_id
                where j.id = :job_id and wm.user_id = :user_id
                limit 1
                """,
            ),
            {"job_id": job_id, "user_id": user_id},
        ).mappings().first()
        return JobResponse(**normalize_record(row)) if row else None

    def list_for_dataset(self, *, dataset_id: str, user_id: str) -> list[JobResponse]:
        rows = self.session.execute(
            text(
                """
                select
                  j.id,
                  j.workspace_id,
                  j.dataset_id,
                  j.job_type,
                  j.status,
                  j.progress,
                  j.celery_task_id,
                  j.payload,
                  j.result,
                  j.error_message,
                  j.created_at::text as created_at,
                  j.updated_at::text as updated_at
                from jobs j
                join datasets d on d.id = j.dataset_id
                join workspace_members wm on wm.workspace_id = d.workspace_id
                where j.dataset_id = :dataset_id and wm.user_id = :user_id
                order by j.created_at desc
                limit 20
                """,
            ),
            {"dataset_id": dataset_id, "user_id": user_id},
        ).mappings().all()
        return [JobResponse(**row) for row in normalize_records(rows)]

    def _update_job(
        self,
        *,
        job_id: str,
        status: str,
        progress: int | None = None,
        celery_task_id: str | None = None,
        result: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> JobResponse:
        row = self.session.execute(
            text(
                """
                update jobs
                set
                  status = :status,
                  progress = coalesce(:progress, progress),
                  celery_task_id = coalesce(:celery_task_id, celery_task_id),
                  result = coalesce(cast(:result as jsonb), result),
                  error_message = :error_message,
                  updated_at = now()
                where id = :job_id
                returning
                  id,
                  workspace_id,
                  dataset_id,
                  job_type,
                  status,
                  progress,
                  celery_task_id,
                  payload,
                  result,
                  error_message,
                  created_at::text as created_at,
                  updated_at::text as updated_at
                """,
            ),
            {
                "job_id": job_id,
                "status": status,
                "progress": progress,
                "celery_task_id": celery_task_id,
                "result": json.dumps(result) if result is not None else None,
                "error_message": error_message,
            },
        ).mappings().one()
        self.session.commit()
        return JobResponse(**normalize_record(row))
