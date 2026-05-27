create table if not exists datasets (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  owner_id uuid not null references profiles(id),
  name text not null,
  status text not null check (status in ('created', 'uploaded', 'processing', 'ready', 'failed')),
  row_count integer,
  column_count integer,
  storage_bucket text,
  storage_path text,
  original_filename text,
  content_type text,
  size_bytes bigint,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_datasets_workspace_created_at on datasets(workspace_id, created_at desc);
create index if not exists idx_datasets_owner_created_at on datasets(owner_id, created_at desc);
create index if not exists idx_datasets_status on datasets(status);
