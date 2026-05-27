create extension if not exists pgcrypto;

create table if not exists ai_conversations (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  dataset_id uuid not null references datasets(id) on delete cascade,
  owner_id uuid not null,
  title text not null,
  status text not null default 'active' check (status in ('active', 'archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists ai_messages (
  id uuid primary key,
  conversation_id uuid not null references ai_conversations(id) on delete cascade,
  role text not null check (role in ('system', 'user', 'assistant', 'tool')),
  content text not null,
  provider text,
  model text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_ai_conversations_dataset_id on ai_conversations(dataset_id);
create index if not exists idx_ai_conversations_workspace_id on ai_conversations(workspace_id);
create index if not exists idx_ai_messages_conversation_id on ai_messages(conversation_id);
