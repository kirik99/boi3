-- Supabase SQL: Add vector search support
-- Run this in Supabase Dashboard → SQL Editor

-- 1. Enable pgvector extension
create extension if not exists vector;

-- 2. Add embedding column (384 dimensions for all-MiniLM-L6-v2)
alter table documents 
add column if not exists embedding vector(384);

-- 3. Create index for fast similarity search
create index if not exists documents_embedding_idx 
on documents using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- 4. Verify the column was added
select column_name, data_type 
from information_schema.columns 
where table_name = 'documents';
