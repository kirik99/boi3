-- Hybrid RAG Schema with FRIDA (1536 dims) and BM25 support

-- 1. Ensure vector extension is enabled
create extension if not exists vector;

-- 2. Create the hybrid knowledge base table
create table if not exists knowledge_base_hybrid (
  id uuid primary key default gen_random_uuid(),
  file_path text not null,
  content text not null,
  context_summary text,
  path_content_embedding vector(1536), -- Combined file_path + content
  context_embedding vector(1536),      -- LLM-generated context
  bm25_weights jsonb,                  -- Store term frequencies or BM25 scores
  metadata jsonb default '{}'::jsonb,
  created_at timestamp with time zone default now()
);

-- 3. Create indices for faster vector search
create index on knowledge_base_hybrid using hnsw (path_content_embedding vector_cosine_ops);
create index on knowledge_base_hybrid using hnsw (context_embedding vector_cosine_ops);

-- 4. Hybrid search function (placeholder for RRF logic or simple combined score)
-- Note: Real hybrid search often combines vector similarity and full-text search.
-- Supabase also supports full-text search on the 'content' column.

create or replace function match_hybrid_chunks (
  query_path_embedding vector(1536),
  query_context_embedding vector(1536),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  file_path text,
  content text,
  context_summary text,
  path_similarity float,
  context_similarity float,
  combined_similarity float
)
language plpgsql
as $$
begin
  return query
  select
    kb.id,
    kb.file_path,
    kb.content,
    kb.context_summary,
    1 - (kb.path_content_embedding <=> query_path_embedding) as path_similarity,
    1 - (kb.context_embedding <=> query_context_embedding) as context_similarity,
    (
      (1 - (kb.path_content_embedding <=> query_path_embedding)) * 0.5 + 
      (1 - (kb.context_embedding <=> query_context_embedding)) * 0.5
    ) as combined_similarity
  from knowledge_base_hybrid kb
  where 
    (1 - (kb.path_content_embedding <=> query_path_embedding)) > match_threshold
    OR
    (1 - (kb.context_embedding <=> query_context_embedding)) > match_threshold
  order by combined_similarity desc
  limit match_count;
end;
$$;
