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
  - `MIMO_MODEL=mimo-v2-flash`
- Initial deterministic analysis should use pandas and numpy before invoking AI.
- Redis and Celery will handle long-running analysis and AI jobs.
