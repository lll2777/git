# Production Readiness

## What Is Ready

- Monorepo with Next.js frontend and FastAPI backend.
- Supabase Auth and Storage integration points.
- PostgreSQL schema migrations.
- CSV/Excel parsing and profiling.
- Chart recommendations.
- AI Q&A through provider adapter architecture.
- AI insights.
- Dashboard saving.
- Redis/Celery background jobs.
- Controlled AI Agent workflow.
- Vercel and Render deployment templates.
- CI for formatting, linting, backend compile, API smoke, and frontend build.

## What Still Needs Real Credentials

- Supabase project URL and keys.
- Supabase JWT secret.
- Supabase service role key.
- Supabase Storage bucket and policies.
- PostgreSQL database URL.
- Redis URL.
- Mimo API key.
- Vercel project environment variables.
- Render or Railway backend environment variables.

## Local Readiness Commands

```bash
python scripts/check_env.py --file .env --profile development
conda run -n pytorch python scripts/smoke_api.py --local-testclient
conda run -n pytorch python scripts/apply_supabase_storage_policies.py
npm run format:check
npm run lint
npm run build
conda run -n pytorch python -m compileall apps/api/app scripts
```

## Manual End-to-End Checklist

1. Apply migrations with `python scripts/apply_postgres_migrations.py`.
2. Apply Supabase storage policies with
   `python scripts/apply_supabase_storage_policies.py`.
3. Start API with `conda activate pytorch` then `uvicorn app.main:app --reload`.
4. Start frontend with `npm run dev`.
5. Sign up or sign in.
6. Upload `samples/sales-demo.csv`.
7. Confirm parsed preview and profile.
8. Generate charts.
9. Ask an AI question.
10. Generate insights.
11. Save dashboard.
12. Queue a background analysis job with Redis/Celery running.
13. Run the AI Agent.

## Suggested Next Hardening Work

- Add backend unit tests for repositories and services.
- Add frontend component tests for upload, charts, insights, jobs, and agent panels.
- Add Playwright E2E with seeded Supabase test credentials.
- Add request IDs and structured JSON logs.
- Add rate limits on upload, AI, and agent endpoints.
- Add billing, RBAC, share links, and audit logs from the roadmap.
