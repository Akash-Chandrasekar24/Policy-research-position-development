"""FastAPI application for the Policy Intelligence Orchestrator front end.

Routes:
    GET  /                                   the single-page UI
    GET  /static/...                         CSS / JS assets
    GET  /api/config                         whether policy-setup has been run
    GET  /api/similar                        semantic search over past runs (history feature)
    POST /api/runs                           start a new policy question
    GET  /api/runs/{run_id}                  status snapshot (for reconnects)
    GET  /api/runs/{run_id}/stream           live activity, SSE
    POST /api/runs/{run_id}/approvals/{id}   human approve/reject decision
    GET  /api/runs/{run_id}/outputs/{name}   download a generated output file

Run:
    uv run policy-web
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from policy_orchestrator.core import SUBAGENTS
from policy_orchestrator.history import RunRecord
from policy_orchestrator.web.manager import (
    ApprovalNotPendingError,
    OUTPUT_ROOT,
    RunNotFoundError,
    SessionManager,
)
from policy_orchestrator.web.schemas import (
    ApprovalDecisionRequest,
    ConfigResponse,
    SimilarRunResponse,
    StartRunRequest,
    StartRunResponse,
)

WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"


def _run_record_to_dict(record: RunRecord) -> dict:
    return {
        "id": record.id,
        "question": record.question,
        "topic": record.topic,
        "approval_status": record.approval_status,
        "draft_position": record.draft_position,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "similarity": record.similarity,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.manager = SessionManager()
    await app.state.manager.astart()
    yield
    await app.state.manager.aclose()


app = FastAPI(title="Policy Intelligence Orchestrator", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    return FileResponse(TEMPLATES_DIR / "index.html")


@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    configured = SessionManager.is_configured()
    return ConfigResponse(
        configured=configured,
        subagents=[{"key": s["key"], "name": s["name"]} for s in SUBAGENTS],
        history_configured=SessionManager.history_enabled(),
        message=None
        if configured
        else "Not provisioned yet — run `uv run policy-setup` first.",
    )


@app.get("/api/similar", response_model=SimilarRunResponse)
async def find_similar(question: str):
    manager: SessionManager = app.state.manager
    if not question.strip() or not manager.history_enabled():
        return SimilarRunResponse(match=None)
    match = await manager.find_similar_run(question)
    return SimilarRunResponse(match=_run_record_to_dict(match) if match else None)


@app.post("/api/runs", response_model=StartRunResponse, status_code=202)
async def start_run(body: StartRunRequest):
    manager: SessionManager = app.state.manager
    if not manager.is_configured():
        raise HTTPException(
            status_code=409,
            detail="Not provisioned yet — run `uv run policy-setup` first.",
        )

    refresh_context = None
    if body.refresh_context is not None:
        rc = body.refresh_context
        refresh_context = RunRecord(
            id="",  # not used by build_refresh_task_text
            question=rc.question,
            topic=rc.topic,
            status="completed",
            approval_status=rc.approval_status,
            draft_position=rc.draft_position,
            confidence=None,
            memory_store_path=None,
            output_dir=None,
            created_at=datetime.fromisoformat(rc.created_at) if rc.created_at else None,
        )

    run = manager.start_run(body.question, refresh_context=refresh_context)
    return StartRunResponse(run_id=run.id)


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    manager: SessionManager = app.state.manager
    try:
        run = manager.get_run(run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "id": run.id,
        "question": run.question,
        "status": run.status,
        "console_url": run.console_url,
        "pending_approvals": [
            {
                "request_id": p.request_id,
                "policy_topic": p.policy_topic,
                "policy_question": p.policy_question,
                "draft_position": p.draft_position,
                "summary": p.summary,
            }
            for p in run.pending_approvals.values()
            if not p.future.done()
        ],
        "outputs": run.outputs,
    }


@app.get("/api/runs/{run_id}/stream")
async def stream_run(run_id: str):
    manager: SessionManager = app.state.manager
    try:
        manager.get_run(run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail="run not found")
    return EventSourceResponse(manager.stream_events(run_id))


@app.post("/api/runs/{run_id}/approvals/{request_id}")
async def submit_approval(run_id: str, request_id: str, body: ApprovalDecisionRequest):
    manager: SessionManager = app.state.manager
    if not body.approved and not (body.notes and body.notes.strip()):
        raise HTTPException(status_code=422, detail="notes are required when rejecting a draft position")
    try:
        await manager.resolve_approval(run_id, request_id, body.approved, body.notes)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail="run not found")
    except ApprovalNotPendingError:
        raise HTTPException(status_code=409, detail="no pending approval with that request_id")
    return {"ok": True}


@app.get("/api/runs/{run_id}/outputs/{filename}")
async def download_output(run_id: str, filename: str):
    manager: SessionManager = app.state.manager
    try:
        manager.get_run(run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail="run not found")

    safe_name = os.path.basename(filename)
    if not safe_name or safe_name in (".", ".."):
        raise HTTPException(status_code=400, detail="invalid filename")

    path = OUTPUT_ROOT / run_id / safe_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="output not found")
    return FileResponse(path, filename=safe_name)


def main() -> None:
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("policy_orchestrator.web.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
