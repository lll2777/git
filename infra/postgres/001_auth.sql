create table if not exists profiles (
  id uuid primary key,
  email text not null,
  display_name text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists workspaces (
  id uuid primary key,
  owner_id uuid not null references profiles(id),
  name text not null,
  slug text not null unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists workspace_members (
  workspace_id uuid not null references workspaces(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'member', 'viewer')),
  created_at timestamptz not null default now(),
  primary key (workspace_id, user_id)
);

create index if not exists idx_workspace_members_user_id on workspace_members(user_id);
create index if not exists idx_workspaces_owner_id on workspaces(owner_id);
