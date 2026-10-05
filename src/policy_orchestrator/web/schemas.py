"""Pydantic request/response models for the web API."""
from pydantic import BaseModel, Field


class RefreshContext(BaseModel):
    """The prior run a "check for updates" request is refreshing.

    Sent back by the frontend exactly as received from GET /api/similar —
    the server doesn't re-fetch it by id, avoiding a second DB round trip
    and keeping the manager's RunRecord construction in one place.
    """
    question: str
    topic: str | None = None
    approval_status: str
    draft_position: str | None = None
    created_at: str | None = None  # ISO 8601; parsed back to datetime server-side


class StartRunRequest(BaseModel):
    question: str = Field(min_length=8, max_length=4000)
    refresh_context: RefreshContext | None = None


class StartRunResponse(BaseModel):
    run_id: str


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    notes: str | None = Field(default=None, max_length=4000)


class ConfigResponse(BaseModel):
    configured: bool
    subagents: list[dict]
    history_configured: bool
    message: str | None = None


class SimilarRunResponse(BaseModel):
    match: dict | None
