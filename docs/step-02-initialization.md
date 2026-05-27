# STEP 2 Initialization

## Design Intent

STEP 2 creates the runnable project foundation without implementing product
features ahead of schedule. The goal is to establish a production-shaped monorepo
that can grow into authentication, uploads, parsing, charts, AI chat, insights,
dashboards, workers, and deployment.

This step deliberately focuses on:

- A strict frontend/backend split.
- D-drive-first local tooling and caches because the C drive has limited space.
- The existing conda `pytorch` backend environment.
- A backend service boundary for future business logic.
- An AI provider adapter boundary before any concrete AI feature is implemented.
- Docker configuration for PostgreSQL and Redis, even though Docker is not currently
  installed in the local shell.

## What Was Added

### Monorepo

```text
apps/web      Next.js App Router frontend
apps/api      FastAPI backend
packages      Shared internal packages
infra         Docker assets
docs          Architecture and step records
```

### Frontend

- Next.js `16.2.6`.
- React `19.2.6`.
- TypeScript.
- TailwindCSS.
- shadcn-compatible `Button` primitive.
- React Query and Zustand dependencies.
- Recharts dependency.
- Supabase client dependency.
- ESLint flat config for Next 16 and ESLint 9.
- A production-style dark SaaS workspace shell as the first screen.

### Backend

- FastAPI app factory.
- `/api/v1/health` endpoint.
- Pydantic settings with environment-variable aliases.
- Structured logging setup.
- CORS configuration.
- AI service boundary.
- `AIProvider` interface.
- `MimoProvider` placeholder adapter.
- Provider factory driven by `AI_PROVIDER`.

The concrete Mimo HTTP transport is intentionally deferred to STEP 7, after official
Mimo API details are verified. The important architectural rule is already enforced:
business code will call `AIService`, not vendor SDKs directly.

### Infrastructure

- `.env.example`.
- PostgreSQL and Redis `docker-compose.yml`.
- Dockerfiles for backend and frontend.
- Git hygiene files:
  - `.gitignore`
  - `.gitattributes`
  - `.editorconfig`
  - Husky pre-commit hook
- npm lockfile for deterministic frontend installs.

## Local Environment

Detected backend environment:

```text
conda env: pytorch
Python: 3.10.20
```

Node/npm:

```text
Node: D:\codex_project\tools\node-v24.16.0-win-x64\node.exe
npm: 11.13.0
npm cache: D:\codex_project\cache\npm
```

Python dependency install:

- `conda install` was attempted first, as requested.
- conda downloads failed with SSL EOF errors.
- Missing packages were then installed into the existing `pytorch` conda environment
  using pip with cache at `D:\codex_project\cache\pip`.
- No Python virtual environment was created.

Docker:

- Docker config files are present.
- Local `docker` command is not currently available in PATH, so Docker services were
  not started during this step.

## Validation

Backend:

```text
GET /api/v1/health -> 200 {"status":"ok","service":"api"}
```

Frontend:

```text
npm run lint -> passed
npm run build -> passed
Browser verification at http://127.0.0.1:3000 -> rendered successfully
```

Security check:

- `npm audit --omit=dev` reports a moderate `postcss` advisory through Next's
  internal dependency tree.
- `npm audit fix --force` was not used because npm proposes an incompatible downgrade
  to an old Next major version.
- npm `overrides` were tested, but Next currently pins its nested PostCSS dependency
  in a way that was not replaced by the override in this workspace.
- Decision: keep latest stable Next.js, document the upstream advisory, and revisit
  when a patched stable Next release is available.

## How To Run

Backend:

```powershell
conda activate pytorch
cd D:\codex_project\git\apps\api
uvicorn app.main:app --reload
```

Frontend:

```powershell
$env:PATH = "D:\codex_project\tools\node-v24.16.0-win-x64;" + $env:PATH
$env:NPM_CONFIG_CACHE = "D:\codex_project\cache\npm"
cd D:\codex_project\git
npm run dev
```

Local URLs:

- Frontend: `http://127.0.0.1:3000`
- Backend health: `http://127.0.0.1:8000/api/v1/health`

## Why This Design

The monorepo keeps product code, shared types, infrastructure, and documentation in
one reviewable unit while preserving deployable frontend/backend boundaries. The
backend starts with service and provider layers so future data analysis, dashboard,
and AI features land in the right places instead of accumulating route-level
business logic. The frontend starts with reusable UI and state management foundations
instead of one-off page code.

This keeps the MVP small enough to ship while still looking like a system that can
grow into multi-tenant SaaS, background processing, AI agents, and deployment.

## Next Step

STEP 3 is authentication:

- Supabase client setup.
- Login/register screens.
- Session-aware app shell.
- Backend JWT verification.
- Profile bootstrap.
- Default workspace bootstrap.
