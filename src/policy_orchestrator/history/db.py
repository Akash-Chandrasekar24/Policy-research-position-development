"""Sync Postgres access for the CLI (policy_orchestrator.cli.session).

Every function here is a no-op-friendly wrapper: if DATABASE_URL isn't set,
`is_enabled()` returns False and callers are expected to skip history
lookups/writes entirely rather than call connect() — this feature is
additive, not required for the rest of the system to work.

NOTE ON VERIFICATION: this module is written against the documented
psycopg3 + pgvector.psycopg APIs (verified via introspection of the
installed packages) but has not been exercised against a live Postgres
instance — there wasn't one available to test against when this was
written. Treat the first real run as the actual integration test.
"""
import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from policy_orchestrator.history.models import RunRecord
from policy_orchestrator.history.sql import CREATE_EXTENSION_SQL, FIND_SIMILAR_SQL, INSERT_RUN_SQL, SCHEMA_SQL
from policy_orchestrator.settings import DATABASE_URL


def is_enabled() -> bool:
    return bool(DATABASE_URL)


def connect() -> psycopg.Connection:
    """Open a connection with the schema ensured and the vector type registered.

    Ordering matters: the `vector` extension must exist server-side before
    register_vector() can look up its type OID (it raises
    psycopg.ProgrammingError otherwise), so CREATE EXTENSION runs first,
    on its own, ahead of everything else.
    """
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set — the research-history feature is disabled. "
            "Set it to a Postgres connection string (e.g. from Supabase or Neon's "
            "free tier) to enable it."
        )
    conn = psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row)
    conn.execute(CREATE_EXTENSION_SQL)
    register_vector(conn)
    conn.execute(SCHEMA_SQL)
    return conn


def insert_run(conn: psycopg.Connection, record: RunRecord, embedding: list[float]) -> None:
    conn.execute(
        INSERT_RUN_SQL,
        {
            "id": record.id,
            "question": record.question,
            "embedding": Vector(embedding),
            "topic": record.topic,
            "status": record.status,
            "approval_status": record.approval_status,
            "draft_position": record.draft_position,
            "confidence": record.confidence,
            "memory_store_path": record.memory_store_path,
            "output_dir": record.output_dir,
        },
    )


def find_similar(conn: psycopg.Connection, embedding: list[float], threshold: float) -> RunRecord | None:
    row = conn.execute(FIND_SIMILAR_SQL, {"embedding": Vector(embedding)}).fetchone()
    if row is None or row["similarity"] < threshold:
        return None
    return RunRecord(**row)
