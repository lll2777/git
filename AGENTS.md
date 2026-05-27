# Agent Operating Notes

This repository is an AI data analysis SaaS platform. Treat it as a production
startup project and a portfolio-grade full-stack system.

## User Mandates

- Work step by step. Do not generate the whole product at once.
- Current sequence:
  1. Architecture and planning.
  2. Project initialization.
  3. Authentication.
  4. File upload.
  5. CSV parsing.
  6. Automatic charts.
  7. AI Q&A.
  8. AI insights.
  9. Dashboards.
  10. Async tasks.
  11. AI Agent.
  12. Deployment.
- Every completed work session should update this file and `MEMORY.md` when needed.
- Every completed work session should commit and push changes to GitHub when there
  are repository changes.
- The user clarified that this file must be named `AGENTS.md`.
- The user's C drive has limited free space. Prefer D drive locations for dependency
  downloads, package caches, generated artifacts, Docker volumes, datasets, and other
  space-heavy operations whenever possible.

## Required Stack

- Frontend: Next.js latest stable with App Router, TypeScript, TailwindCSS,
  shadcn/ui, React Query, Zustand.
- Backend: FastAPI running in the existing conda `pytorch` environment.
- Do not create a Python venv.
- Do not force-upgrade Python.
- Database: PostgreSQL.
- Auth: Supabase Auth.
- Storage: Supabase Storage.
- AI: Provider Adapter architecture. Default provider is Mimo with model
  `mimo-v2-flash`.
- Charts: Recharts first, ECharts later.
- Async: Redis and Celery.
- Deploy: Vercel for frontend, Railway or Render for backend.

## AI Architecture Rules

- Business code must never call vendor model APIs directly.
- All AI calls go through `aiService`.
- `aiService` selects a provider from environment variables.
- Required provider interface:
  - `chat`
  - `analyze_data`
  - `generate_insight`
  - `generate_chart_config`
- Implement `MimoProvider` first.
- Reserve providers for OpenAI, DeepSeek, Qwen, and Claude.

## Local Environment Facts

- Repository path: `D:\codex_project\git`
- Git remote: `https://github.com/lll2777/git.git`
- Current backend Python environment: conda env `pytorch`
- Detected Python version in `pytorch`: `Python 3.10.20`
- `gh` CLI is not installed.
- Current shell cannot run `node` or `npm`; Node.js must be installed or exposed in
  PATH before STEP 2 frontend initialization.
- Use D drive paths for large local assets and caches where possible.
- PowerShell 7 is available and can be used for complex commands when it behaves
  better than Windows PowerShell.
- A portable Node.js LTS runtime was placed on the D drive:
  `D:\codex_project\tools\node-v24.16.0-win-x64`.
- Prefer `D:\codex_project\cache\npm` for npm cache and
  `D:\codex_project\cache\pip` for pip cache.

## Current Status

- STEP 1 is complete.
- STEP 2 scaffold is implemented and locally verified.
- Architecture documentation lives in `docs/step-01-architecture.md`.
- Initialization documentation lives in `docs/step-02-initialization.md`.
- Next task is STEP 3: implement Supabase authentication.
