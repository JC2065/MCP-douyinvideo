create table media_assets (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references users(id) on delete cascade,
  sha256 char(64) not null, perceptual_hash varchar(128), asset_type text not null check (asset_type in ('source_video','audio','image','keyframe','subtitle','generated_clip','final_video')),
  source_kind text not null check (source_kind in ('upload','douyin','generated','derived')), source_url text, platform_asset_id text,
  storage_uri text not null, mime_type varchar(120), size_bytes bigint check (size_bytes is null or size_bytes>=0), duration_ms integer check (duration_ms is null or duration_ms>=0),
  width integer check (width is null or width>0), height integer check (height is null or height>0), rights_status text not null default 'user_asserted' check (rights_status in ('user_asserted','verified','restricted','unknown')),
  metadata jsonb not null default '{}', created_at timestamptz not null default now(), deleted_at timestamptz,
  unique(user_id,sha256)
);
create index media_assets_user_created_idx on media_assets(user_id,created_at desc) where deleted_at is null;

create table reference_analyses (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references users(id) on delete cascade, source_asset_id uuid not null references media_assets(id),
  version integer not null default 1 check (version>0), status text not null check (status in ('pending','running','succeeded','failed')),
  analyzer_version text not null, summary jsonb not null default '{}', transcript jsonb not null default '{}', evidence jsonb not null default '{}', confidence numeric(5,4) check (confidence is null or confidence between 0 and 1),
  error_code text, created_at timestamptz not null default now(), completed_at timestamptz, unique(source_asset_id,version)
);

create table video_shots (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references users(id) on delete cascade, analysis_id uuid not null references reference_analyses(id) on delete cascade,
  ordinal integer not null check (ordinal>=0), start_ms integer not null check (start_ms>=0), end_ms integer not null check (end_ms>start_ms),
  keyframe_asset_id uuid references media_assets(id), semantics jsonb not null default '{}', evidence jsonb not null default '{}', confidence numeric(5,4) check (confidence is null or confidence between 0 and 1),
  created_at timestamptz not null default now(), unique(analysis_id,ordinal)
);

create table storyboards (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references users(id) on delete cascade, analysis_id uuid references reference_analyses(id),
  version integer not null default 1 check (version>0), reference_mode text not null check (reference_mode in ('content-structure','visual-style','same-topic')),
  status text not null default 'draft' check (status in ('draft','approved','superseded')), payload jsonb not null default '{}', estimated_cost_cny numeric(12,4) not null default 0 check (estimated_cost_cny>=0),
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), unique(user_id,id,version)
);

create table generation_jobs (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references users(id) on delete cascade, storyboard_id uuid not null references storyboards(id), shot_id uuid references video_shots(id),
  provider text not null, model text not null, provider_task_id text, status text not null default 'draft' check (status in ('draft','queued','running','succeeded','failed','cancelled')),
  phase text not null default 'draft', request_snapshot jsonb not null default '{}', estimated_cost_cny numeric(12,4) not null default 0 check (estimated_cost_cny>=0), actual_cost_cny numeric(12,4) check (actual_cost_cny is null or actual_cost_cny>=0),
  error_code text, created_at timestamptz not null default now(), started_at timestamptz, completed_at timestamptz
);
create index generation_jobs_user_status_idx on generation_jobs(user_id,status,created_at desc);
create unique index generation_jobs_provider_task_idx on generation_jobs(provider,provider_task_id) where provider_task_id is not null;

create table video_artifacts (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references users(id) on delete cascade, generation_job_id uuid references generation_jobs(id), shot_id uuid references video_shots(id), media_asset_id uuid not null references media_assets(id),
  artifact_type text not null check (artifact_type in ('candidate','selected','final')), quality jsonb not null default '{}', lineage jsonb not null,
  created_at timestamptz not null default now(), unique(generation_job_id,media_asset_id)
);

create table creation_feedback (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references users(id) on delete cascade, storyboard_id uuid references storyboards(id), generation_job_id uuid references generation_jobs(id), shot_id uuid references video_shots(id),
  event_type text not null check (event_type in ('accepted','rejected','edited','regenerated','deleted')), reason text, payload jsonb not null default '{}',
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), deleted_at timestamptz
);
create index creation_feedback_user_created_idx on creation_feedback(user_id,created_at desc) where deleted_at is null;

do $$ declare table_name text; begin
  foreach table_name in array array['media_assets','reference_analyses','video_shots','storyboards','generation_jobs','video_artifacts','creation_feedback'] loop
    execute format('alter table %I enable row level security',table_name);
    execute format('alter table %I force row level security',table_name);
    execute format('create policy %I_owner on %I using (user_id=nullif(current_setting(''app.user_id'',true),'''')::uuid) with check (user_id=nullif(current_setting(''app.user_id'',true),'''')::uuid)',table_name,table_name);
  end loop;
end $$;
