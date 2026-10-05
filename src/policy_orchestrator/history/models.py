"""Shared result shape for the sync (db.py) and async (async_db.py) history layers."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RunRecord:
    id: str
    question: str
    topic: str | None
    status: str
    approval_status: str  # draft | approved | rejected
    draft_position: str | None
    confidence: str | None
    memory_store_path: str | None
    output_dir: str | None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    similarity: float | None = None  # only set on find_similar() results
