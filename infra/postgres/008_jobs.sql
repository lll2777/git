create extension if not exists pgcrypto;

create table if not exists jobs (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  dataset_id uuid references datasets(id) on delete cascade,
  job_type text not null check (job_type in ('dataset_analysis', 'chart_generation', 'insight_generation', 'dashboard_export')),
  status text not null default 'queued' check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
  progress integer not null default 0 check (progress >= 0 and progress <= 100),
  celery_task_id text,
  payload jsonb not null default '{}'::jsonb,
  result jsonb not null default '{}'::jsonb,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_jobs_workspace_id on jobs(workspace_id);
create index if not exists idx_jobs_dataset_id on jobs(dataset_id);
create index if not exists idx_jobs_status on jobs(status);
create index if not exists idx_jobs_celery_task_id on jobs(celery_task_id);
