-- Run this entire file in Supabase: SQL Editor -> New query.
-- The embedding size must match EMBEDDING_DIMENSIONS in .env.
create extension if not exists vector with schema extensions;

create table if not exists public.resume_chunks (
  id uuid primary key default gen_random_uuid(),
  source_file text not null,
  chunk_index integer not null,
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding extensions.vector(1536) not null,
  created_at timestamptz not null default now(),
  unique (source_file, chunk_index)
);

create index if not exists resume_chunks_embedding_hnsw
  on public.resume_chunks using hnsw (embedding vector_cosine_ops);

-- RPC is required because PostgREST does not expose pgvector distance operators.
create or replace function public.match_resume_chunks(
  query_embedding extensions.vector(1536),
  match_count integer default 12
)
returns table (
  id uuid,
  source_file text,
  chunk_index integer,
  content text,
  metadata jsonb,
  similarity double precision
)
language sql
stable
set search_path = public, extensions
as $$
  select
    rc.id, rc.source_file, rc.chunk_index, rc.content, rc.metadata,
    1 - (rc.embedding <=> query_embedding) as similarity
  from public.resume_chunks rc
  order by rc.embedding <=> query_embedding
  limit least(greatest(match_count, 1), 50);
$$;

-- This project is intended to call Supabase only from a trusted backend using
-- the service_role key. Do not put that key in a frontend application.

