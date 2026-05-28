# AI Data Analysis

[![CI](https://github.com/lll2777/AI-Data-Analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/lll2777/AI-Data-Analysis/actions/workflows/ci.yml)

Production-grade AI data analysis SaaS platform. Users upload CSV or Excel files,
then the platform cleans data, infers column types, generates charts, answers
questions with AI, produces business insights, saves dashboards, and prepares
analysis results for sharing.

## Product

- Upload CSV/Excel datasets through Supabase Storage.
- Parse, profile, and preview tabular data with pandas and numpy.
- Detect missing values, outliers, field types, correlations, and time-series ranges.
- Recommend charts through a deterministic chart service, with Recharts rendering.
- Ask dataset-grounded AI questions through the provider adapter layer.
- Generate business insights and save dashboards.
- Queue long-running jobs through Redis and Celery.
- Run a controlled AI Agent workflow that audits every tool step.

## Architecture

- `apps/web`: Next.js App Router, TypeScript, TailwindCSS, shadcn/ui, React Query, Zustand.
- `apps/api`: FastAPI, Pydantic, pandas, numpy, repository and service layers.
- `infra/postgres`: idempotent PostgreSQL schema migrations.
- `infra/supabase`: Supabase Storage policy SQL.
- `scripts`: migration, environment validation, and API smoke tooling.
- `docs`: architecture, delivery steps, deployment, and production runbooks.

AI calls are routed through `aiService`. Business code must not call model vendor
APIs directly. The default provider is Mimo with `mimo-v2-flash`, and the provider
boundary is ready for OpenAI, DeepSeek, Qwen, and Claude adapters.

## Quick Start

Use D drive cache paths on this workstation to avoid filling the C drive.

```powershell
$env:PATH = "D:\codex_project\tools\node-v24.16.0-win-x64;" + $env:PATH
$env:NPM_CONFIG_CACHE = "D:\codex_project\cache\npm"
npm ci
Copy-Item .env.example .env
python scripts/check_env.py --file .env --profile development
```

Start local infrastructure when Docker is available:

```powershell
docker compose up -d postgres redis
```

Run the backend in the existing conda environment:

```powershell
conda activate pytorch
Set-Location apps/api
uvicorn app.main:app --reload
```

Run the frontend:

```powershell
npm run dev
```

Use `samples/sales-demo.csv` for the first manual upload test.

## Verification

```powershell
python scripts/check_env.py --file .env.example --profile development --allow-placeholders
python scripts/check_env.py --file .env.production.example --profile production --allow-placeholders
conda run -n pytorch python scripts/smoke_api.py --local-testclient
conda run -n pytorch python scripts/apply_supabase_storage_policies.py
npm run format:check
npm run lint
npm run build
conda run -n pytorch python -m compileall apps/api/app scripts
```

## Deployment

Frontend deployment targets Vercel. Backend deployment targets Render or Railway.
PostgreSQL, Redis, Supabase Auth, Supabase Storage, and Mimo credentials must be
configured with production environment variables before live end-to-end testing.

See:

- [docs/step-12-deployment.md](docs/step-12-deployment.md)
- [docs/production-readiness.md](docs/production-readiness.md)
- [.env.production.example](.env.production.example)

## Delivery Docs

- [docs/step-01-architecture.md](docs/step-01-architecture.md)
- [docs/step-02-initialization.md](docs/step-02-initialization.md)
- [docs/step-03-authentication.md](docs/step-03-authentication.md)
- [docs/step-04-file-upload.md](docs/step-04-file-upload.md)
- [docs/step-05-csv-parsing.md](docs/step-05-csv-parsing.md)
- [docs/step-06-chart-generation.md](docs/step-06-chart-generation.md)
- [docs/step-07-ai-qa.md](docs/step-07-ai-qa.md)
- [docs/step-08-ai-insights.md](docs/step-08-ai-insights.md)
- [docs/step-09-dashboards.md](docs/step-09-dashboards.md)
- [docs/step-10-async-tasks.md](docs/step-10-async-tasks.md)
- [docs/step-11-ai-agent.md](docs/step-11-ai-agent.md)
- [docs/step-12-deployment.md](docs/step-12-deployment.md)

Long-running work context is kept in [AGENTS.md](AGENTS.md) and [MEMORY.md](MEMORY.md).
