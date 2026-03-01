-- 1. Enable the pgvector extension
create extension if not exists vector;

-- 2. Create the table for structured methods
create table if not exists lab_methods (
  id uuid primary key default gen_random_uuid(),
  method_name text,
  preparation text,
  calibration text,
  measurement text,
  spectro_setup text,
  file_source text,
  embedding vector(1024), -- Summary embedding for the entire method
  metadata jsonb,
  created_at timestamp with time zone default now()
);

-- 3. Create search function
create or replace function match_methods (
  query_embedding vector(1024),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  method_name text,
  preparation text,
  calibration text,
  measurement text,
  spectro_setup text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    m.id,
    m.method_name,
    m.preparation,
    m.calibration,
    m.measurement,
    m.spectro_setup,
    1 - (m.embedding <=> query_embedding) as similarity
  from lab_methods m
  where 1 - (m.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
end;
$$;
