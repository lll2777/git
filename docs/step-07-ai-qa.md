# STEP 7: AI Data Q&A

## Design

AI Q&A is implemented as dataset-grounded analysis, not generic chat.

The backend builds a compact context from:

- parsed dataset profile.
- preview rows.
- missing values, outliers, correlations, time-series metadata, and categorical aggregates.
- saved chart recommendation specs.
- recent conversation messages.

That context is sent through `AIService.chat()`, which delegates to the configured
provider adapter. Route and business code do not call a model vendor directly.

## Backend

Added modules:

- `apps/api/app/schemas/ai.py`
- `apps/api/app/repositories/ai_conversations.py`
- `apps/api/app/services/ai/dataset_qa.py`
- `apps/api/app/api/v1/routes/ai.py`

Added endpoint:

- `POST /api/v1/datasets/{dataset_id}/ai/chat`

The endpoint requires Supabase JWT auth. It only works after dataset parsing has
produced both a profile and preview.

## AI Provider

`MimoProvider` now implements an OpenAI-compatible chat completions request:

- base URL from `MIMO_BASE_URL`.
- API key from `MIMO_API_KEY`.
- model from `MIMO_MODEL`.

For the user's current MiMo subscription, use the OpenAI-compatible token-plan
endpoint:

```env
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5
```

Before testing through the browser, run:

```powershell
conda run -n pytorch python scripts/test_mimo_provider.py
```

- tools are passed through as function-calling tool definitions.

If `MIMO_API_KEY` is missing, the provider returns a safe explanatory response so
the application remains locally runnable.

## Database

Added migration:

- `infra/postgres/005_ai_conversations.sql`

Tables:

- `ai_conversations`
- `ai_messages`

Messages store role, content, provider, model, metadata, and timestamps. This is
enough for MVP Q&A and leaves room for future tool-call traces, streaming chunks,
and agent steps.

## Frontend

Added API types and call:

- `askDatasetQuestion` in `apps/web/features/datasets/dataset-api.ts`

Added UI:

- `apps/web/features/ai/components/dataset-question-panel.tsx`

The panel appears for the latest ready dataset and supports:

- empty state.
- loading state.
- toast feedback.
- persistent conversation id for follow-up questions.
- readable user/assistant message bubbles.

## Why This Design

- Dataset context is assembled server-side to avoid exposing raw storage access or
  duplicating analysis logic in the browser.
- Conversation persistence makes Q&A auditable and reusable for future dashboard
  copilot and report generation.
- Function-calling support is wired at the provider boundary now, while actual
  agentic tool execution remains reserved for STEP 11.
- Provider switching remains controlled by environment variables.

## Next Step

STEP 8 will implement AI insights:

- insight persistence schema.
- dataset insight generation endpoint.
- `aiService.generate_insight` use.
- insight cards in the dashboard workspace.
