# STEP 11: AI Agent

## Design

The AI Agent is implemented as a controlled workflow executor with auditable
tool steps.

The first production-safe workflow is `prepare_dashboard`:

1. `recommend_charts`
2. `generate_insights`
3. `save_dashboard`

Each run and each step is persisted. This gives the product a real agent
foundation without allowing arbitrary model-directed code execution.

## Backend

Added modules:

- `apps/api/app/schemas/agent.py`
- `apps/api/app/repositories/agent_runs.py`
- `apps/api/app/services/agent.py`
- `apps/api/app/api/v1/routes/agent.py`

Added endpoints:

- `POST /api/v1/datasets/{dataset_id}/agent-runs`
- `GET /api/v1/datasets/{dataset_id}/agent-runs`
- `GET /api/v1/agent-runs/{run_id}`

Supported objectives:

- `prepare_dashboard`
- `dashboard`
- `full_analysis`
- `queue_analysis`
- `refresh_analysis`

The first three run the chart, insight, and dashboard workflow. The latter two
queue a background analysis job through the STEP 10 job system.

## Database

Added migration:

- `infra/postgres/009_agent_runs.sql`

Tables:

- `agent_runs`
- `agent_steps`

Each step stores input, output, status, timing, and error message. This creates an
audit trail for later streaming, retries, approvals, and human-in-the-loop review.

## Frontend

Added:

- `apps/web/features/agent/components/agent-panel.tsx`
- agent API types and calls in `apps/web/features/datasets/dataset-api.ts`

The workspace now supports:

- running the `prepare_dashboard` agent.
- listing recent agent runs.
- seeing each audited tool step.
- invalidating charts, insights, and dashboards after a successful run.

## Why This Design

- Agent tools reuse existing service layer methods instead of duplicating product
  behavior.
- The workflow is deterministic and permission-checked before future model-driven
  planning is introduced.
- The database structure supports future streaming output, tool approvals, and
  resumable agent runs.
- Business code remains inside product services; the model provider boundary
  remains isolated in `AIService`.

## Next Step

STEP 12 will implement deployment:

- production environment variable checklist.
- Vercel frontend setup.
- Railway or Render backend setup.
- Docker deployment notes.
- migration and worker boot order.
