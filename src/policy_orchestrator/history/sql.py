"""SQL shared verbatim between db.py (sync, CLI) and async_db.py (web) —
kept in one place so the two never drift.

Requires pgvector (`CREATE EXTENSION vector`) — available out of the box on
Supabase and Neon's free tiers as of this writing; confirm at signup since
free-tier feature sets change. The HNSW index is optional at a single
office's realistic data volume (a sequential scan over a few hundred rows
is instant either way) but costs nothing to have for when that stops being
true.
"""

CREATE_EXTENSION_SQL = "CREATE EXTENSION IF NOT EXISTS vector"

# CREATE_EXTENSION_SQL must run — and, on a real connection, be followed by
# pgvector.psycopg.register_vector(conn) — BEFORE this: register_vector()
# looks up the `vector` type's OID server-side, which fails with
# psycopg.ProgrammingError if the extension doesn't exist yet. See
# db.connect() / async_db.connect().
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    id                 TEXT PRIMARY KEY,
    question           TEXT NOT NULL,
    question_embedding vector(384) NOT NULL,
    topic              TEXT,
    status             TEXT NOT NULL,
    approval_status    TEXT NOT NULL DEFAULT 'draft',
    draft_position     TEXT,
    confidence         TEXT,
    memory_store_path  TEXT,
    output_dir         TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS runs_embedding_idx
    ON runs USING hnsw (question_embedding vector_cosine_ops);
"""

INSERT_RUN_SQL = """
INSERT INTO runs (
    id, question, question_embedding, topic, status, approval_status,
    draft_position, confidence, memory_store_path, output_dir, completed_at
)
VALUES (%(id)s, %(question)s, %(embedding)s, %(topic)s, %(status)s, %(approval_status)s,
        %(draft_position)s, %(confidence)s, %(memory_store_path)s, %(output_dir)s, now())
ON CONFLICT (id) DO UPDATE SET
    status = EXCLUDED.status,
    approval_status = EXCLUDED.approval_status,
    draft_position = EXCLUDED.draft_position,
    confidence = EXCLUDED.confidence,
    memory_store_path = EXCLUDED.memory_store_path,
    output_dir = EXCLUDED.output_dir,
    completed_at = now()
"""

# `1 - (a <=> b)` converts pgvector's cosine *distance* operator into cosine
# *similarity* (both vectors are pre-normalized by the embedding model, but
# the conversion holds regardless). Only rows with status='completed' are
# eligible matches — a run that errored out has nothing usable to return.
FIND_SIMILAR_SQL = """
SELECT id, question, topic, status, approval_status, draft_position, confidence,
       memory_store_path, output_dir, created_at, completed_at,
       1 - (question_embedding <=> %(embedding)s) AS similarity
FROM runs
WHERE status = 'completed'
ORDER BY question_embedding <=> %(embedding)s
LIMIT 1
"""
