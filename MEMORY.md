# Project Memory

## 2026-05-27

- Initialized the repository at `D:\codex_project\git`.
- Pushed initial empty commit to `https://github.com/lll2777/git`.
- User defined the product as a production-grade AI data analysis SaaS platform.
- Required workflow is step-based. Do not skip ahead.
- Completed STEP 1 by documenting:
  - System architecture.
  - Technical architecture.
  - Data flow.
  - Database schema.
  - API design.
  - Project directory structure.
  - Development roadmap.
- Created `AGENTS.md` so future Codex sessions can recover the project rules.
- Confirmed local backend environment:
  - `conda 25.5.1`
  - conda env `pytorch`
  - Python `3.10.20`
- Confirmed current local blocker for STEP 2:
  - `node` fails with access denied from the Codex app bundled path.
  - `npm` is not available in PATH.
- User clarified:
  - Use `AGENTS.md`, not `agent.md`.
  - C drive space is limited. Prefer D drive for downloads, dependency caches,
    generated artifacts, Docker volumes, datasets, and other large operations.
  - PowerShell 7 is available and may be preferred for complex local commands.
- STEP 2 progress:
  - Downloaded portable Node.js `v24.16.0` to `D:\codex_project\tools`.
  - npm cache is configured at `D:\codex_project\cache\npm`.
  - pip cache is configured at `D:\codex_project\cache\pip`.
  - `conda install` for backend packages hit SSL EOF errors, so missing backend
    dependencies were installed into the existing `pytorch` environment with pip.
  - Added monorepo scaffold with `apps/web`, `apps/api`, `packages`, `infra`, and
    Docker configuration.
  - Added FastAPI health check and AI provider adapter skeleton.
  - Added Next.js App Router frontend shell.
  - Verified backend health endpoint and frontend render locally.
  - Docker CLI is not currently available in PATH.
  - `npm audit --omit=dev` reports a moderate advisory in Next's nested PostCSS
    dependency. Do not run `npm audit fix --force` because it suggests a breaking
    downgrade to Next 9. Recheck after the next stable Next release.
  - Local commits exist for STEP 1 and STEP 2, but `git push` to GitHub failed
    repeatedly because connections to `github.com:443` and the GitHub connector
    backend were reset or unavailable. Run `git push` from `D:\codex_project\git`
    when network connectivity recovers.
- STEP 3 progress:
  - Added Supabase SSR/browser client setup.
  - Added global `AuthProvider`, React Query provider, and Sonner toasts.
  - Added `/login`, `/register`, and `/auth/callback`.
  - Added FastAPI Supabase JWT verification with JWKS first and legacy JWT secret
    compatibility.
  - Added `/api/v1/auth/me` and `/api/v1/auth/bootstrap`.
  - Added PostgreSQL auth migration at `infra/postgres/001_auth.sql`.
  - Full sign-in requires real Supabase env values.
  - Local STEP 3 commit exists, but this agent's `git push` failed because
    `github.com:443` connections timed out or reset. Manual push may be needed again.
- STEP 4 progress:
  - Added dataset upload session, confirm upload, and list endpoints.
  - Added dataset repository/service/schema layers.
  - Added dataset migration at `infra/postgres/002_datasets.sql`.
  - Added Supabase Storage bucket/policy SQL at `infra/supabase/storage-policies.sql`.
  - Added homepage dataset upload card with file validation, loading states, toasts,
    and recent dataset empty/skeleton/list states.
  - Upload flow uses Supabase browser client direct upload. No service role key is
    exposed to the frontend.
  - Full upload validation requires real Supabase env values and database migrations.
  - STEP 4 should be committed locally; remote push is deferred because GitHub
    connectivity is currently unavailable from this environment.
- STEP 5 progress:
  - Added Supabase Storage downloader for backend analysis.
  - Added pandas profiler for CSV/Excel parsing, preview rows, type inference,
    missing values, outliers, correlations, time-series ranges, and categorical
    aggregates.
  - Added analysis endpoints: analyze, preview, and profile.
  - Added analysis persistence migration at `infra/postgres/003_dataset_analysis.sql`.
  - Frontend upload flow now triggers analysis after upload confirmation and can show
    parsed preview/profile for ready datasets.
- STEP 6 progress:
  - Added chart recommendation endpoints for listing and generating dataset charts.
  - Added deterministic chart recommender for bar, line, and scatter charts using
    persisted dataset profile and preview data.
  - Added chart persistence migration at `infra/postgres/004_charts.sql`.
  - Added Recharts frontend renderer with loading, empty state, and toast feedback.
  - User asked that future sessions try pushing from Codex first before asking for
    manual push.
- STEP 7 progress:
  - Added dataset-grounded AI Q&A endpoint at
    `/api/v1/datasets/{dataset_id}/ai/chat`.
  - Added `ai_conversations` and `ai_messages` migration at
    `infra/postgres/005_ai_conversations.sql`.
  - Implemented server-side dataset context assembly from profile, preview, and
    chart recommendations.
  - Implemented Mimo chat completions transport with configurable `MIMO_BASE_URL`.
  - Added frontend AI Q&A panel with conversation state, loading state, empty state,
    and toasts.
- User renamed the GitHub repository and visible project name to `AI Data Analysis`.
  The confirmed remote URL is `https://github.com/lll2777/AI-Data-Analysis.git`.
- STEP 8 progress:
  - Added insight endpoints for listing and generating dataset insights.
  - Added deterministic insight generation for dataset size, missing values,
    outliers, strong correlations, and time-series readiness.
  - Wired AI insight generation through `AIService.generate_insight`.
  - Added insight persistence migration at `infra/postgres/006_insights.sql`.
  - Added frontend business insight cards with loading, empty state, severity, and
    source/provider tags.
- STEP 9 progress:
  - Added dashboard endpoints for saving and listing dataset dashboards.
  - Added dashboard persistence migration at `infra/postgres/007_dashboards.sql`.
  - Dashboard MVP stores ordered references to generated charts and insights via
    `dashboard_items`.
  - Added frontend dashboard panel with save action, saved list, empty state,
    loading state, and toasts.
- STEP 10 progress:
  - Added Redis/Celery async task infrastructure.
  - Added job endpoints for queueing dataset analysis, listing dataset jobs, and
    reading a single job.
  - Added job persistence migration at `infra/postgres/008_jobs.sql`.
  - Added Celery app and dataset analysis task that reuses `DatasetService`.
  - Added Docker Compose `api-worker` service.
  - Added frontend background jobs panel with queue action, polling, progress, and
    error states.
- STEP 11 progress:
  - Added controlled AI Agent workflow endpoints for running and listing agent runs.
  - Added agent persistence migration at `infra/postgres/009_agent_runs.sql`.
  - Agent runs save audited tool steps with input, output, status, timing, and
    errors.
  - Default `prepare_dashboard` workflow executes chart recommendation, insight
    generation, and dashboard saving through existing services.
  - Added frontend AI Agent panel with run action and step audit display.
- STEP 12 progress:
  - Added deployment runbook at `docs/step-12-deployment.md`.
  - Added `vercel.json`, `render.yaml`, and `.env.production.example`.
  - Added idempotent PostgreSQL migration runner at
    `scripts/apply_postgres_migrations.py`.
  - Updated API Docker image to include migrations and scripts.
  - Updated web Dockerfile to use the renamed `@ai-data-analysis/web` workspace.
- Production readiness progress:
  - Added GitHub Actions CI for env template validation, formatting, frontend lint,
    backend compile, local API smoke testing, and frontend build.
  - Added `scripts/check_env.py` for development and production environment file
    validation.
  - Added `scripts/smoke_api.py` for FastAPI health smoke checks through either a
    running server or local TestClient.
  - Added `docs/production-readiness.md` and `samples/sales-demo.csv`.
  - Expanded `README.md` into a project entry point with product, architecture,
    quick start, verification, deployment, and documentation sections.
- Local live-credential setup progress:
  - Created local `.env` from `.env.example`.
  - User filled Supabase URL, publishable/anon key, service role key, and JWT
    secret locally without exposing secrets in chat.
  - `conda run -n pytorch python scripts/check_env.py --file .env --profile development`
    passed after Supabase values were filled.
  - Restarted local backend and frontend with the new environment.
  - Backend is reachable at `http://127.0.0.1:8000`; `/api/v1/health` returned
    `{"status":"ok","service":"api"}`.
  - Frontend is reachable at `http://localhost:3000`.
  - Current remaining local E2E blockers are database migration against Supabase
    Postgres, Supabase Storage policies, and optional Redis/Mimo credentials.
  - A hydration warning was observed when the in-app browser translated visible
    text; this appears browser-translation related, not a backend/API failure.
  - First Supabase Postgres migration attempt failed with password authentication
    for user `postgres`. The local `DATABASE_URL` parsed as a Supabase direct
    connection, but the password segment still looked like a placeholder rather
    than the real database password.
  - User corrected the local Supabase database password in `.env`.
  - `scripts/apply_postgres_migrations.py` successfully applied migrations
    `001_auth.sql` through `009_agent_runs.sql` against Supabase Postgres.
  - Added idempotent `scripts/apply_supabase_storage_policies.py`.
  - Updated `infra/supabase/storage-policies.sql` so repeated runs drop and
    recreate the four dataset object policies safely.
  - Supabase Storage bucket/policy application completed successfully and was
    verified by rerunning the policy script.
  - Restarted local backend and frontend again. Backend health and frontend HTTP
    checks passed after database and storage setup.
  - Register page initially showed missing `NEXT_PUBLIC_SUPABASE_URL` /
    `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` because Next.js runs from the
    `apps/web` workspace and does not read the repository root `.env` for public
    browser variables.
  - Created ignored local file `apps/web/.env.local` by syncing only public
    `NEXT_PUBLIC_*` values from root `.env`, then restarted the frontend. The
    register page no longer rendered the missing-env warning.
  - User successfully completed browser login through Supabase Auth.
  - Upload initially returned API 503. Root causes investigated:
    - Backend config loaded only the current working directory `.env`; when API was
      started from `apps/api`, it did not read the repository root `.env`.
    - Fixed `apps/api/app/core/config.py` to read both repository root `.env` and
      API-local `.env`.
    - Supabase/psycopg returns UUID columns as Python `UUID` objects, while API
      response schemas expect strings. Added `apps/api/app/repositories/records.py`
      and normalized repository records before constructing response models.
    - Created the user's application workspace locally through the repository
      bootstrap path after the browser login had created the Supabase Auth user.
    - Multiple old `uvicorn --reload` processes were left running on port 8000,
      causing the browser to keep hitting stale API code/config. Cleaned them and
      restarted a single non-reload API process for stable local E2E testing.
  - Local synthetic-token HTTP diagnostics then showed:
    - `GET /api/v1/datasets` returned 200.
    - `POST /api/v1/datasets/upload-session` returned 201.
  - Browser upload later returned API 401. The verifier was updated to try Supabase
    JWKS first and legacy `SUPABASE_JWT_SECRET` fallback second, but the real
    browser request still returned 401. Next session should continue from JWT
    diagnostics for the real Supabase browser token, not from DB/storage setup.
  - Follow-up upload diagnostics found the intermittent 401 was most likely caused
    by frontend components reusing `session.access_token` instead of asking
    Supabase for the latest session before API calls.
  - Added `getAccessToken()` to the frontend auth provider and changed upload,
    dataset listing, preview/profile, charts, insights, AI Q&A, dashboards, jobs,
    and agent calls to fetch a fresh token immediately before protected API calls.
  - Improved API error messages in the frontend so 401/503 and other common status
    codes show actionable Chinese messages instead of raw English status text.
  - Added a latest dataset status panel so successful uploads, pending parsing,
    and failed analyses all produce visible feedback instead of only ready datasets
    rendering downstream panels.
  - Updated backend dataset analysis failure handling so unexpected exceptions save
    a non-empty error message on failed dataset rows.
  - User clarified the website UI should be Chinese. Frontend metadata, landing
    page, auth pages, upload flow, dataset status, charts, AI Q&A, insights,
    dashboards, jobs, and agent panels were translated to Chinese while preserving
    API enums and code identifiers.
  - Browser verification confirmed `http://localhost:3000/` renders the Chinese
    title and core upload copy.
  - User has not filled the large-model API key yet. This does not block upload,
    parsing, deterministic chart recommendations, or dashboard persistence, but
    AI Q&A, AI insights, and AI agent AI-backed steps may fail or degrade until
    `MIMO_API_KEY` and related model environment variables are configured.
  - After a browser screenshot showed `Invalid Supabase access token`, the frontend
    auth provider was hardened again:
    - `getAccessToken()` now refreshes near-expiry sessions, validates the token
      with Supabase Auth, retries one refresh on validation failure, and clears the
      local session if the token remains invalid.
    - The upload card now shows the logged-in email and a Chinese "退出" button so
      stale login state is visible and easy to clear.
    - Browser verification after reload showed the invalid local session was
      cleared and the page returned to a clear logged-out state without the invalid
      token toast.
  - User then confirmed two remaining local issues:
    - After login, the homepage still showed the left-side login/create-account
      buttons even though the upload card showed the account email.
    - Upload still returned "Invalid Supabase access token".
  - Fixed the homepage by extracting the left hero into a client-side
    `WorkspaceHero` component that reads `useAuth()` and replaces login buttons
    with a logged-in status pill once a Supabase session exists.
  - Hardened backend authentication by making `get_current_user` async and adding
    a Supabase Auth `/auth/v1/user` validation fallback. The API now tries local
    JWKS/legacy secret verification first, then asks Supabase Auth to validate the
    browser access token when local verification rejects it. This handles real
    Supabase token signing/config variants during local development.
  - User later confirmed the CSV import path works: the dataset can be uploaded,
    parsed, typed, previewed, and recommended charts are rendered in the browser.
    Screenshot showed parsed fields such as `date: datetime`, `region: category`,
    `channel: category`, `revenue: integer`, and `cost: integer`, plus generated
    bar/line/scatter recommendations.
  - Next session can continue from post-import product hardening rather than
    re-debugging upload/auth, unless the issue reappears after a restart.
  - User requested richer visualization and Chinese chart text. Chart work added:
    - Backend deterministic recommendations now produce up to 10 charts from the
      same dataset, including bar, horizontal bar, pie/donut, line, area,
      composed, and scatter chart configs.
    - Backend chart titles and common field labels are localized to Chinese for
      common fields such as date, region, channel, revenue, and cost.
    - Frontend Recharts renderer now supports the added chart types, Chinese chart
      type labels, Chinese/legacy-title fallback localization, Chinese tooltip
      formatting, and an explicit Chinese font stack to reduce garbled text risk.
    - Local recommender smoke check against the sales demo shape returned 10 chart
      configs with Chinese titles.
    - Backend was restarted after the change so local "生成图表" uses the updated
      recommender.
    - In-app browser verification was attempted but the browser reported
      `net::ERR_BLOCKED_BY_CLIENT` for `http://localhost:3000`; rely on local
      browser/manual visual check for this one.
  - User uploaded `heart_disease_uci` and analysis failed with
    `numpy boolean subtract, the '-' operator, is not supported`. Root cause was
    pandas/numpy boolean data entering numeric quantile/correlation-style analysis.
  - Dataset profiler was hardened:
    - Numeric analysis now coerces numeric columns to `float64` before quantile,
      outlier, correlation, and categorical aggregate calculations.
    - Boolean columns remain typed as `boolean` and no longer enter boolean
      percentile/subtraction paths.
    - Time-series detection now parses only true datetime columns or columns with
      date/time-like names, preventing ordinary integer columns such as age from
      being interpreted as 1970 timestamps.
  - Local reproduction with bool + numeric heart-like columns now completes
    analysis successfully, and backend was restarted after the fix.
  - User reported the right workspace column was too narrow for the richer chart
    grid. Homepage layout now uses a client-side resizable split view:
    - Default right panel width is 60% on desktop.
    - Users can drag the vertical separator between 42% and 78%.
    - The selected width is persisted in localStorage.
    - Mobile keeps the original stacked layout.
  - Upload-to-analysis workspace UX was improved:
    - Recent datasets are now selectable instead of passive rows.
    - Upload success selects the newly analyzed dataset and shows a clearer
      success toast.
    - Preview, charts, AI Q&A, insights, dashboards, async jobs, and Agent panels
      now follow the selected ready dataset instead of silently using the first
      ready dataset.
    - Failed or uploaded datasets show a clear locked analysis notice and a
      "重新分析" action where the backend supports rerunning analysis.
  - User shared current MiMo subscription details. Defaults were aligned to the
    OpenAI-compatible subscription endpoint and available model list:
    - `MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1`
    - `MIMO_MODEL=mimo-v2.5`
    - Added `scripts/test_mimo_provider.py` for live connectivity checks after
      the user fills `MIMO_API_KEY` locally.
  - User filled the local `.env` MiMo settings. The key was verified only in
    masked form, with prefix `tp-css...` and suffix `7w1b`; do not print or commit
    the full key. The backend was restarted in the `pytorch` environment, health
    check passed at `/api/v1/health`, and `scripts/test_mimo_provider.py` returned
    `mimo provider ok` against `mimo-v2.5`.
  - User tested AI Q&A and saw "I could not generate an answer." Root cause:
    MiMo returned an OpenAI-style `tool_calls` response with empty `content` when
    dataset Q&A sent tools, but the backend did not execute the tool call and
    make a follow-up model request. The fix added tool-call follow-up handling in
    dataset Q&A, keeps final answers in Chinese, and added a unittest for
    OpenAI-compatible tool-result message construction.
  - User confirmed the local large-model API key is configured. Live MiMo
    connectivity was verified against `https://token-plan-cn.xiaomimimo.com/v1`
    with `mimo-v2.5`; the script returned `mimo provider ok`, a Chinese response,
    and token usage metadata. Later repeat runs in the same session failed at the
    connection layer with `httpx.ConnectError`, so treat live MiMo connectivity as
    configured but currently network/proxy-flaky. Do not expose or commit the key.
  - Local testing found that `.env` starts with a UTF-8 BOM. `scripts/check_env.py`
    now reads env files with `utf-8-sig`, and `scripts/test_check_env.py` covers
    BOM-compatible parsing.
  - Do not expose or commit local secrets. Local ignored files now include root
    `.env` and `apps/web/.env.local`.

## Architecture Decisions

- Monorepo with `apps/web`, `apps/api`, `packages`, `infra`, `docs`, and `scripts`.
- Supabase Auth handles authentication.
- Supabase Storage holds uploaded files.
- PostgreSQL stores metadata, inferred profiles, dashboards, charts, insights, jobs,
  AI conversations, share links, and audit logs.
- FastAPI backend uses service and repository layers.
- AI provider boundary is mandatory:
  - Routes call services.
  - Services call `aiService`.
  - `aiService` calls provider adapters.
- Default AI provider is Mimo:
  - `AI_PROVIDER=mimo`
  - `MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1`
  - `MIMO_MODEL=mimo-v2.5`
- Initial deterministic analysis should use pandas and numpy before invoking AI.
- Redis and Celery will handle long-running analysis and AI jobs.
