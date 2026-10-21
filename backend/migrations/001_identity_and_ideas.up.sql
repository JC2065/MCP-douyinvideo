create extension if not exists pgcrypto;

create table users (
  id uuid primary key default gen_random_uuid(),
  status text not null default 'active' check (status in ('active','disabled')),
  display_name varchar(60) not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table user_identities (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references users(id) on delete cascade,
  provider text not null check (provider in ('wechat-mini','wechat-app','phone','email','oidc')),
  subject text not null, union_subject text, created_at timestamptz not null default now(), last_used_at timestamptz,
  unique(provider,subject)
);
create index user_identities_user_idx on user_identities(user_id);

create table sessions (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references users(id) on delete cascade,
  device_id varchar(100) not null, client_type text not null check (client_type in ('wechat-mini','web','app')),
  refresh_token_hash text not null unique, expires_at timestamptz not null, revoked_at timestamptz, last_seen_at timestamptz not null default now(), created_at timestamptz not null default now()
);
create index sessions_active_user_idx on sessions(user_id,expires_at) where revoked_at is null;

create table ideas (
  id uuid primary key, user_id uuid not null references users(id) on delete cascade, version integer not null default 1 check (version>0),
  text varchar(4000) not null check (length(btrim(text)) between 1 and 4000), tags text[] not null default '{}',
  source_type text not null default 'manual' check (source_type in ('manual','hotspot','learning_case','review')),
  source_ref text, source_snapshot jsonb not null default '{}', target_project_id uuid, occurred_at timestamptz,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), deleted_at timestamptz
);
create index ideas_user_updated_idx on ideas(user_id,updated_at desc,id desc) where deleted_at is null;
create index ideas_user_deleted_idx on ideas(user_id,deleted_at) where deleted_at is not null;

create table change_log (
  cursor bigint generated always as identity primary key, user_id uuid not null references users(id) on delete cascade,
  entity_type text not null, entity_id uuid not null, entity_version integer not null check (entity_version>0),
  operation text not null check (operation in ('upsert','delete')), changed_at timestamptz not null default now()
);
create index change_log_user_cursor_idx on change_log(user_id,cursor);

create table idempotency_keys (
  user_id uuid not null references users(id) on delete cascade, resource text not null, action text not null,
  key varchar(120) not null, request_hash char(64) not null, response_code integer, response_body jsonb,
  created_at timestamptz not null default now(), expires_at timestamptz not null,
  primary key(user_id,resource,action,key)
);
create index idempotency_expiry_idx on idempotency_keys(expires_at);

alter table ideas enable row level security;
alter table ideas force row level security;
create policy ideas_owner on ideas using (user_id=nullif(current_setting('app.user_id',true),'')::uuid) with check (user_id=nullif(current_setting('app.user_id',true),'')::uuid);
alter table change_log enable row level security;
alter table change_log force row level security;
create policy change_log_owner on change_log using (user_id=nullif(current_setting('app.user_id',true),'')::uuid) with check (user_id=nullif(current_setting('app.user_id',true),'')::uuid);
alter table idempotency_keys enable row level security;
alter table idempotency_keys force row level security;
create policy idempotency_owner on idempotency_keys using (user_id=nullif(current_setting('app.user_id',true),'')::uuid) with check (user_id=nullif(current_setting('app.user_id',true),'')::uuid);
