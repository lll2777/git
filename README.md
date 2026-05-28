# AI Data Analysis

Production-grade AI data analysis SaaS platform.

Users upload CSV or Excel files, then the platform cleans data, infers column types,
generates charts, answers questions with AI, produces business insights, saves
dashboards, and shares analysis results.

## Current Stage

STEP 1 is complete: architecture, data flow, database design, API design, project
structure, and roadmap are documented in:

- [docs/step-01-architecture.md](docs/step-01-architecture.md)

STEP 2 is complete and locally verified: project initialization details are documented in:

- [docs/step-02-initialization.md](docs/step-02-initialization.md)

STEP 3 is complete and locally verified without live Supabase credentials:

- [docs/step-03-authentication.md](docs/step-03-authentication.md)

STEP 4 is complete and locally verified without live Supabase credentials:

- [docs/step-04-file-upload.md](docs/step-04-file-upload.md)

STEP 5 is complete and locally verified without live Supabase credentials:

- [docs/step-05-csv-parsing.md](docs/step-05-csv-parsing.md)

STEP 6 is complete and locally verified without live Supabase credentials:

- [docs/step-06-chart-generation.md](docs/step-06-chart-generation.md)

STEP 7 is complete and locally verified without live Supabase credentials:

- [docs/step-07-ai-qa.md](docs/step-07-ai-qa.md)

STEP 8 is complete and locally verified without live Supabase credentials:

- [docs/step-08-ai-insights.md](docs/step-08-ai-insights.md)

STEP 9 is complete and locally verified without live Supabase credentials:

- [docs/step-09-dashboards.md](docs/step-09-dashboards.md)

STEP 10 is complete and locally verified without live Supabase credentials:

- [docs/step-10-async-tasks.md](docs/step-10-async-tasks.md)

STEP 11 is complete and locally verified without live Supabase credentials:

- [docs/step-11-ai-agent.md](docs/step-11-ai-agent.md)

STEP 12 is complete and locally verified:

- [docs/step-12-deployment.md](docs/step-12-deployment.md)

Long-running work context is kept in [AGENTS.md](AGENTS.md) and [MEMORY.md](MEMORY.md).

## Required Stack

- Frontend: Next.js App Router, TypeScript, TailwindCSS, shadcn/ui, React Query, Zustand
- Backend: FastAPI on local conda `pytorch` environment
- Database: PostgreSQL
- Auth: Supabase Auth
- Storage: Supabase Storage
- AI: Provider Adapter architecture, default provider `mimo`
- Charts: Recharts first, ECharts later
- Async: Redis and Celery
- Deploy: Vercel for frontend, Railway or Render for backend
