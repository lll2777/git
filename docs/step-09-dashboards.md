# STEP 9: Dashboards

## Design

Dashboard saving is implemented as an analysis snapshot over an existing dataset.
The MVP dashboard stores references to generated charts and insights instead of
duplicating their JSON payloads.

This keeps dashboards lightweight while allowing future features such as:

- chart editing.
- multiple dashboards per dataset.
- share links.
- layout editing.
- dashboard-level permissions.

## Backend

Added modules:

- `apps/api/app/schemas/dashboard.py`
- `apps/api/app/repositories/dashboards.py`
- `apps/api/app/services/dashboards.py`
- `apps/api/app/api/v1/routes/dashboards.py`

Added endpoints:

- `POST /api/v1/datasets/{dataset_id}/dashboards`
- `GET /api/v1/datasets/{dataset_id}/dashboards`
- `GET /api/v1/dashboards/{dashboard_id}`

The save endpoint creates a dashboard from all current charts and insights for a
dataset. The service validates workspace access through the dataset ownership
path before saving.

## Database

Added migration:

- `infra/postgres/007_dashboards.sql`

Tables:

- `dashboards`
- `dashboard_items`

`dashboard_items` stores ordered references to charts and insights. The layout is
stored on the dashboard as JSON with a version number and 12-column grid metadata.

## Frontend

Added:

- `apps/web/features/dashboards/components/dashboard-panel.tsx`
- dashboard API types and calls in `apps/web/features/datasets/dataset-api.ts`

The workspace now supports:

- saving the current dataset outputs as a dashboard.
- default dashboard title generation.
- saved dashboard list.
- loading and empty states.
- toast feedback.

## Why This Design

- It preserves a clean service/repository boundary.
- It avoids copying chart/insight payloads before the chart editor exists.
- It supports multiple dashboards per dataset from day one.
- It creates a stable foundation for STEP 12 sharing and deployment flows.

## Next Step

STEP 10 will implement async tasks:

- Redis/Celery worker configuration.
- task records and status transitions.
- long-running dataset analysis jobs.
- frontend task status states.
