# STEP 6: Automatic Chart Generation

## Design

Automatic chart generation is implemented as a backend-owned recommendation
pipeline with a frontend renderer:

1. The backend reads the persisted dataset profile and preview generated in
   STEP 5.
2. A deterministic recommender selects chart candidates from field types:
   category + numeric columns produce bar charts, datetime + numeric columns
   produce line charts, and two numeric columns produce scatter charts.
3. Recommendations are stored in PostgreSQL as chart metadata and portable JSON
   configs.
4. The frontend reads saved chart configs and renders them with Recharts.

This keeps early recommendations explainable, fast, and testable. AI chart
decisioning will be layered in later through `aiService.generate_chart_config`
without changing route or persistence boundaries.

## Backend

Added modules:

- `apps/api/app/schemas/chart.py`
- `apps/api/app/repositories/charts.py`
- `apps/api/app/services/charts/recommender.py`
- `apps/api/app/services/charts/service.py`
- `apps/api/app/api/v1/routes/charts.py`

Added endpoints:

- `GET /api/v1/datasets/{dataset_id}/charts`
- `POST /api/v1/datasets/{dataset_id}/charts/recommend`

The route layer only handles HTTP concerns. `ChartService` enforces the dataset
profile dependency and delegates persistence to `ChartRepository`. Access control
is inherited from the dataset profile/preview lookup and from chart listing joins
against `workspace_members`.

## Database

Added migration:

- `infra/postgres/004_charts.sql`

The `charts` table stores:

- dataset association.
- optional dashboard association for STEP 9.
- chart type.
- renderer config.
- query spec explaining the fields and aggregation behind the chart.
- creator marker: `system`, `ai`, or `user`.

## Frontend

Added chart API types and calls in:

- `apps/web/features/datasets/dataset-api.ts`

Added Recharts rendering component:

- `apps/web/features/charts/components/chart-recommendations.tsx`

The upload workspace now shows chart recommendations for the latest ready
dataset. It includes loading skeletons, an empty state, toast feedback, and
renderer support for bar, line, and scatter charts.

## Why This Design

- The recommender is deterministic first, which makes it reliable for MVP users
  and easy to verify without burning model tokens.
- The chart config is stored as JSON so dashboards can reuse it without
  recomputing recommendations.
- The frontend does not infer chart decisions. It only renders validated backend
  configs, keeping product behavior consistent across clients.
- The route contract is already compatible with future AI recommendations through
  the provider adapter architecture.

## Next Step

STEP 7 will implement AI Q&A:

- conversation schema.
- protected chat endpoint.
- `aiService.chat` integration.
- Mimo provider request/response handling.
- dataset-aware question context from profile, preview, and generated charts.
