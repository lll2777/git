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
