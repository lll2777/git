# STEP 10: Async Tasks

## Design

Async task support is implemented with Redis and Celery while preserving the
existing synchronous dataset analysis endpoint.

The platform now has two analysis paths:

- `POST /api/v1/datasets/{dataset_id}/analyze` remains synchronous for local MVP
  development and small files.
- `POST /api/v1/datasets/{dataset_id}/analysis-jobs` creates a job record and
  queues a Celery task for background analysis.

This avoids breaking the current upload flow when a developer has not started a
worker yet, while creating the production path required for larger files and
long-running AI workflows.

## Backend

Added modules:

- `apps/api/app/schemas/job.py`
- `apps/api/app/repositories/jobs.py`
- `apps/api/app/services/jobs.py`
- `apps/api/app/api/v1/routes/jobs.py`
- `apps/api/app/tasks/celery_app.py`
- `apps/api/app/tasks/datasets.py`

Added endpoints:

- `POST /api/v1/datasets/{dataset_id}/analysis-jobs`
- `GET /api/v1/datasets/{dataset_id}/jobs`
- `GET /api/v1/jobs/{job_id}`

Job states:

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`

If Redis/Celery is unavailable during enqueue, the API returns `503` and records a
failed job with a clear error message.

## Database

Added migration:

- `infra/postgres/008_jobs.sql`

The `jobs` table stores workspace ownership, dataset association, job type,
status, progress, Celery task id, payload, result, and error details.

## Worker

Celery app:

```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=info -Q analysis
```

Local backend still uses the conda `pytorch` environment:

```bash
conda activate pytorch
uvicorn app.main:app --reload
```

Docker Compose now includes:

- PostgreSQL
- Redis
- `api-worker`

Large Docker volumes continue to use `DATA_DIR`, which should point to the D
drive on this machine.

## Frontend

Added:

- `apps/web/features/jobs/components/analysis-job-panel.tsx`
- job API types and calls in `apps/web/features/datasets/dataset-api.ts`

The workspace now supports:

- queueing a background analysis job.
- listing recent dataset jobs.
- polling queued/running jobs.
- progress bars.
- failed job error display.

## Why This Design

- The worker reuses the existing `DatasetService.analyze_dataset` path, avoiding
  duplicate parsing logic.
- Jobs are persisted independently of Celery backend state, so UI status survives
  restarts and can later drive WebSocket updates.
- The synchronous path remains useful for fast local iteration and avoids forcing
  Redis on every developer action.

## Next Step

STEP 11 will implement the AI Agent:

- agent workflow state.
- structured tool execution.
- dataset, chart, insight, and dashboard tools.
- agent run records.
- preparation for streaming output.
