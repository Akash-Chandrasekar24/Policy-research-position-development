"""Async Postgres access for the web app (policy_orchestrator.web.manager).

Mirrors db.py's logic exactly (same SQL, from history/sql.py) but through
psycopg_pool.AsyncConnectionPool, since the web app is a long-running
process serving concurrent runs rather than a one-shot CLI invocation.

NOTE ON VERIFICATION: written against the documented psycopg3 / psycopg_pool
/ pgvector.psycopg APIs (verified via introspection of the installed
packages), but not exercised against a live Postgres instance — there
wasn't one available to test against when this was written.
"""
import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector, register_vector_async
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from policy_orchestrator.history.models import RunRecord
from policy_orchestrator.history.sql import CREATE_EXTENSION_SQL, FIND_SIMILAR_SQL, INSERT_RUN_SQL, SCHEMA_SQL
from policy_orchestrator.settings import DATABASE_URL


def is_enabled() -> bool:
    return bool(DATABASE_URL)


def _ensure_schema_once() -> None:
    """Runs once, synchronously, before the pool opens.

    CREATE EXTENSION must happen — and be visible — before register_vector()
    can look up the `vector` type's OID; doing this as a single blocking
    call at startup is simpler than threading an async equivalent through
    for something that only ever runs once per process lifetime.
    """
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    try:
        conn.execute(CREATE_EXTENSION_SQL)
        register_vector(conn)
        conn.execute(SCHEMA_SQL)
    finally:
        conn.close()


async def _configure_connection(conn: psycopg.AsyncConnection) -> None:
    await register_vector_async(conn)


def create_pool() -> AsyncConnectionPool:
    """Build the pool (not yet open — caller awaits .open() or uses `async with`).

    Call from FastAPI's lifespan startup; see web/manager.py SessionManager.
    """
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set — the research-history feature is disabled."
        )
    _ensure_schema_once()
    return AsyncConnectionPool(
        DATABASE_URL,
        min_size=1,
        max_size=5,
        open=False,
        configure=_configure_connection,
        kwargs={"row_factory": dict_row},
    )


async def insert_run(pool: AsyncConnectionPool, record: RunRecord, embedding: list[float]) -> None:
    async with pool.connection() as conn:
        await conn.execute(
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


async def find_similar(
    pool: AsyncConnectionPool, embedding: list[float], threshold: float
) -> RunRecord | None:
    async with pool.connection() as conn:
        cur = await conn.execute(FIND_SIMILAR_SQL, {"embedding": Vector(embedding)})
        row = await cur.fetchone()
    if row is None or row["similarity"] < threshold:
        return None
    return RunRecord(**row)
