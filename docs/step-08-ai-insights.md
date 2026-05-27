# STEP 8: AI Insights

## Design

Insight generation combines deterministic analysis with AI interpretation.

The deterministic layer uses persisted profile data to produce immediately
useful insights about:

- dataset size.
- missing values.
- outliers.
- strong correlations.
- time-series readiness.

The AI layer then calls `AIService.generate_insight()` with the same dataset
context and chart specs. Business code still does not call a vendor SDK directly.

This gives the product a reliable baseline even when `MIMO_API_KEY` is not
configured, while preserving the provider adapter architecture for live AI output.

## Backend

Added modules:

- `apps/api/app/schemas/insight.py`
- `apps/api/app/repositories/insights.py`
- `apps/api/app/services/insights.py`
- `apps/api/app/api/v1/routes/insights.py`

Added endpoints:

- `GET /api/v1/datasets/{dataset_id}/insights`
- `POST /api/v1/datasets/{dataset_id}/insights/generate`

Generation requires a parsed dataset profile and preview. The service loads saved
chart recommendations to provide richer chart-aware context to the AI provider.

## Database

Added migration:

- `infra/postgres/006_insights.sql`

The `insights` table stores:

- dataset and workspace ownership.
- title and summary.
- insight type.
- severity.
- evidence JSON.
- provider/model metadata.
- source: `deterministic`, `ai`, or `user`.

## AI Provider

`MimoProvider.generate_insight()` now asks the provider for structured JSON:

```json
{
  "insights": [
    {
      "title": "...",
      "summary": "...",
      "insight_type": "business",
      "severity": "info",
      "evidence": {}
    }
  ]
}
```

The service validates and normalizes provider output before saving it.

## Frontend

Added:

- `apps/web/features/insights/components/insight-panel.tsx`
- insight API types and calls in `apps/web/features/datasets/dataset-api.ts`

The workspace now shows business insight cards for the latest ready dataset with:

- empty state.
- loading skeleton.
- toast feedback.
- severity badge.
- source/provider tags.

## Naming Update

The visible product name is now `AI Data Analysis`, matching the renamed GitHub
repository and project name.

## Next Step

STEP 9 will implement dashboards:

- dashboard persistence.
- saved chart layouts.
- saved insight associations.
- dashboard list/detail routes.
- frontend dashboard workspace.
