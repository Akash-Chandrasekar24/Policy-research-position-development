"""Research history: "have we answered a question like this before?"

Backed by Postgres + pgvector (see history/sql.py for the schema),
populated by both cli.session and web.manager after every finished run.
Entirely optional — every function that touches the database is guarded by
`is_enabled()` (True only when settings.DATABASE_URL is set), so the rest
of the system works identically whether or not this feature is configured.

    embeddings   local, free text embeddings (fastembed/ONNX) — no API key
    models       RunRecord, the shared result shape
    sql          the SQL strings, shared verbatim between db.py and async_db.py
    db           sync Postgres access, for the CLI
    async_db     async Postgres access (connection-pooled), for the web app
"""
from policy_orchestrator.history.embeddings import embed
from policy_orchestrator.history.models import RunRecord
from policy_orchestrator.history.prompts import build_refresh_task_text, build_task_text

__all__ = ["embed", "RunRecord", "build_refresh_task_text", "build_task_text"]
