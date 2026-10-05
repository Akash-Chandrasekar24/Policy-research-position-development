"""Async session orchestration for the web front end.

This is the web equivalent of policy_orchestrator.cli.session (the CLI runtime),
rewritten around asyncio so the human-approval step suspends only the one
background task waiting on it — not the whole process — while the FastAPI
server keeps serving other requests (other runs, the SSE stream itself,
static assets) concurrently.

Each policy question submitted via the API becomes a `RunState`, driven by
a background asyncio task (`_drive`). Browser tabs subscribe to a run's
event history via Server-Sent Events; `request_human_approval` calls create
a `PendingApproval` whose `asyncio.Future` is resolved by the
POST /api/runs/{id}/approvals/{request_id} endpoint — that's the entire
human-in-the-loop mechanism.

If DATABASE_URL is configured (see policy_orchestrator.history),
find_similar_run() answers "have we researched something like this
before?" and every completed run is saved via history.async_db.insert_run
at the end of _drive(). With no DATABASE_URL, both are no-ops and behavior
is identical to before the history feature existed.
"""
import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field

from anthropic import AsyncAnthropic

from policy_orchestrator.cli.session import build_resources
from policy_orchestrator.history import RunRecord, build_refresh_task_text, build_task_text, embed
from policy_orchestrator.history import async_db as history_db
from policy_orchestrator.settings import BETA_HEADER, OUTPUT_DIR as OUTPUT_ROOT, SIMILARITY_THRESHOLD, STATE_FILE
from policy_orchestrator.tools import build_position_record

# Terminal statuses: once a run reaches one of these, its history is fixed
# and stream_events() can skip subscribing altogether (nothing more to come).
_TERMINAL_STATUSES = {"completed", "error"}


@dataclass
class PendingApproval:
    request_id: str
    tool_use_id: str
    policy_topic: str
    policy_question: str
    draft_position: str
    summary: str
    future: "asyncio.Future[dict]" = field(default_factory=asyncio.Future)


@dataclass
class RunState:
    id: str
    question: str
    status: str = "starting"  # starting|running|awaiting_approval|completed|error
    created_at: float = field(default_factory=time.time)
    history: list[dict] = field(default_factory=list)
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    pending_approvals: dict[str, PendingApproval] = field(default_factory=dict)
    approved_topics: dict[str, dict] = field(default_factory=dict)
    outputs: list[dict] = field(default_factory=list)
    managed_session_id: str | None = None
    console_url: str | None = None
    # Populated as the run progresses, purely for the history row written at
    # the end — has no bearing on the approval gate itself.
    topic: str | None = None
    approval_status: str = "draft"
    memory_store_path: str | None = None


class RunNotFoundError(KeyError):
    pass


class ApprovalNotPendingError(KeyError):
    pass


class SessionManager:
    """Owns the shared AsyncAnthropic client and every in-flight run.

    In-memory only — runs and their history (the live activity log, not the
    research-history database) are lost on server restart. That's an
    acceptable trade-off for a single-office tool; if this needs to survive
    restarts later, persist RunState (minus the live asyncio.Future
    objects) to disk or a small database.
    """

    def __init__(self):
        self._client = AsyncAnthropic()
        self._runs: dict[str, RunState] = {}
        self._history_pool = None  # set in astart() if history_db.is_enabled()

    # -- lifecycle -----------------------------------------------------------

    async def astart(self) -> None:
        """Call once from FastAPI's lifespan, after construction."""
        if history_db.is_enabled():
            self._history_pool = history_db.create_pool()
            await self._history_pool.open()

    async def aclose(self) -> None:
        if self._history_pool is not None:
            await self._history_pool.close()
        await self._client.close()

    # -- configuration ---------------------------------------------------------

    @staticmethod
    def is_configured() -> bool:
        return STATE_FILE.exists()

    @staticmethod
    def load_state() -> dict:
        return json.loads(STATE_FILE.read_text())

    @staticmethod
    def history_enabled() -> bool:
        return history_db.is_enabled()

    # -- research history --------------------------------------------------

    async def find_similar_run(self, question: str) -> RunRecord | None:
        """Embeds `question` and returns the closest past completed run
        above SIMILARITY_THRESHOLD, or None if disabled / no close match.

        Embedding runs in a thread executor — fastembed's ONNX inference is
        synchronous, CPU-bound code and would otherwise block the event
        loop for the ~10-50ms it takes.
        """
        if self._history_pool is None:
            return None
        loop = asyncio.get_running_loop()
        vector = await loop.run_in_executor(None, embed, question)
        return await history_db.find_similar(self._history_pool, vector, SIMILARITY_THRESHOLD)

    # -- run management --------------------------------------------------------

    def start_run(self, question: str, refresh_context: RunRecord | None = None) -> RunState:
        run = RunState(id=uuid.uuid4().hex[:12], question=question)
        self._runs[run.id] = run
        asyncio.create_task(self._drive(run, refresh_context))
        return run

    def get_run(self, run_id: str) -> RunState:
        run = self._runs.get(run_id)
        if run is None:
            raise RunNotFoundError(run_id)
        return run

    async def resolve_approval(
        self, run_id: str, request_id: str, approved: bool, notes: str | None
    ) -> None:
        run = self.get_run(run_id)
        pending = run.pending_approvals.get(request_id)
        if pending is None or pending.future.done():
            raise ApprovalNotPendingError(request_id)
        pending.future.set_result({"approved": approved, "notes": notes})

    async def stream_events(self, run_id: str):
        """Async generator of {"event": ..., "data": ...} dicts for SSE.

        Replays history first (covers a page refresh / late subscriber),
        then tails live events until the run reaches a terminal state.
        """
        run = self.get_run(run_id)

        for event in run.history:
            yield {"event": event["type"], "data": json.dumps(event)}

        if run.status in _TERMINAL_STATUSES:
            return

        queue: asyncio.Queue = asyncio.Queue()
        run.subscribers.append(queue)
        try:
            while True:
                event = await queue.get()
                yield {"event": event["type"], "data": json.dumps(event)}
                if event["type"] == "done":
                    break
        finally:
            run.subscribers.remove(queue)

    # -- internals ---------------------------------------------------------

    async def _emit(self, run: RunState, event: dict) -> None:
        run.history.append(event)
        for queue in list(run.subscribers):
            await queue.put(event)

    async def _drive(self, run: RunState, refresh_context: RunRecord | None) -> None:
        if not self.is_configured():
            run.status = "error"
            await self._emit(
                run,
                {
                    "type": "error",
                    "message": (
                        f"{STATE_FILE} not found. Run `uv run policy-setup` "
                        f"first to provision the agents, memory stores, and "
                        f"environment."
                    ),
                },
            )
            await self._emit(run, {"type": "done", "status": "error"})
            return

        state = self.load_state()
        orchestrator = state["orchestrator"]
        position_register_store_id = state["memory_stores"]["position_register"]["id"]

        try:
            session = await self._client.beta.sessions.create(
                agent={
                    "type": "agent",
                    "id": orchestrator["id"],
                    "version": orchestrator["version"],
                },
                environment_id=state["environment_id"],
                title=f"Policy Intelligence session ({run.id})",
                resources=build_resources(state),
            )
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            run.status = "error"
            await self._emit(run, {"type": "error", "message": str(exc)})
            await self._emit(run, {"type": "done", "status": "error"})
            return

        run.managed_session_id = session.id
        run.console_url = (
            f"https://platform.claude.com/workspaces/default/sessions/{session.id}"
        )
        run.status = "running"
        await self._emit(
            run,
            {
                "type": "session_started",
                "session_id": session.id,
                "console_url": run.console_url,
            },
        )

        task_text = (
            build_refresh_task_text(run.question, refresh_context)
            if refresh_context is not None
            else build_task_text(run.question)
        )

        try:
            await self._run_event_loop(run, session.id, task_text, position_register_store_id)
        except Exception as exc:  # noqa: BLE001
            run.status = "error"
            await self._emit(run, {"type": "error", "message": str(exc)})
            await self._emit(run, {"type": "done", "status": "error"})
            return

        outputs = await self._download_outputs(run, session.id)
        run.outputs = outputs
        run.status = "completed"
        await self._save_to_history(run)
        await self._emit(run, {"type": "done", "status": "completed", "outputs": outputs})

    async def _save_to_history(self, run: RunState) -> None:
        if self._history_pool is None:
            return
        loop = asyncio.get_running_loop()
        vector = await loop.run_in_executor(None, embed, run.question)
        record = RunRecord(
            id=run.id,
            question=run.question,
            topic=run.topic,
            status="completed",
            approval_status=run.approval_status,
            draft_position=next(iter(run.approved_topics.values()), {}).get("draft_position")
            if run.approved_topics
            else None,
            confidence=None,  # not captured as a distinct structured field today
            memory_store_path=run.memory_store_path,
            output_dir=str(OUTPUT_ROOT / run.id),
        )
        await history_db.insert_run(self._history_pool, record, vector)

    async def _run_event_loop(
        self, run: RunState, session_id: str, task_text: str, position_register_store_id: str
    ) -> None:
        async with await self._client.beta.sessions.events.stream(session_id) as stream:
            await self._client.beta.sessions.events.send(
                session_id,
                events=[{"type": "user.message", "content": [{"type": "text", "text": task_text}]}],
            )

            async for event in stream:
                etype = event.type

                if etype == "agent.message":
                    for block in event.content:
                        text = getattr(block, "text", "")
                        if text:
                            await self._emit(run, {"type": "agent_message", "text": text})

                elif etype == "agent.tool_use":
                    await self._emit(run, {"type": "tool_use", "name": event.name})

                elif etype == "agent.custom_tool_use":
                    await self._handle_custom_tool(
                        run, session_id, event, position_register_store_id
                    )

                elif etype == "session.thread_created":
                    await self._emit(run, {"type": "thread_created", "agent_name": event.agent_name})

                elif etype == "session.thread_status_running":
                    await self._emit(run, {"type": "thread_running", "agent_name": event.agent_name})

                elif etype == "session.thread_status_idle":
                    await self._emit(run, {"type": "thread_idle", "agent_name": event.agent_name})

                elif etype in ("agent.thread_message_sent", "agent.thread_message_received"):
                    direction = "sent" if etype.endswith("_sent") else "received"
                    other = getattr(event, "to_agent_name", None) or getattr(
                        event, "from_agent_name", None
                    )
                    await self._emit(
                        run, {"type": "thread_message", "direction": direction, "agent_name": other}
                    )

                elif etype == "session.error":
                    await self._emit(run, {"type": "error", "message": str(getattr(event, "message", event))})

                elif etype == "session.status_terminated":
                    break

                elif etype == "session.status_idle":
                    stop = getattr(event, "stop_reason", None)
                    if stop is not None and getattr(stop, "type", None) == "requires_action":
                        continue
                    break

    async def _handle_custom_tool(
        self, run: RunState, session_id: str, event, position_register_store_id: str
    ) -> None:
        if event.name == "request_human_approval":
            await self._handle_request_human_approval(run, session_id, event)
        elif event.name == "register_approved_position":
            await self._handle_register_approved_position(
                run, session_id, event, position_register_store_id
            )
        else:
            await self._send_tool_result(
                session_id,
                event.id,
                json.dumps({"error": "unknown_tool", "name": event.name}),
                is_error=True,
            )

    async def _handle_request_human_approval(self, run: RunState, session_id: str, event) -> None:
        request_id = uuid.uuid4().hex[:10]
        pending = PendingApproval(
            request_id=request_id,
            tool_use_id=event.id,
            policy_topic=event.input.get("policy_topic", ""),
            policy_question=event.input.get("policy_question", ""),
            draft_position=event.input.get("draft_position", ""),
            summary=event.input.get("summary", ""),
        )
        run.pending_approvals[request_id] = pending
        run.status = "awaiting_approval"
        run.topic = pending.policy_topic
        await self._emit(
            run,
            {
                "type": "approval_requested",
                "request_id": request_id,
                "policy_topic": pending.policy_topic,
                "policy_question": pending.policy_question,
                "draft_position": pending.draft_position,
                "summary": pending.summary,
            },
        )

        decision = await pending.future  # suspends only this run's task
        run.status = "running"

        approved = bool(decision.get("approved"))
        notes = decision.get("notes")
        approver = "Tejasvi Surya / senior team (web approval)"
        run.approval_status = "approved" if approved else "rejected"

        if approved:
            run.approved_topics[pending.policy_topic] = {
                "policy_question": pending.policy_question,
                "draft_position": pending.draft_position,
                "approver": approver,
            }

        await self._emit(
            run, {"type": "approval_resolved", "request_id": request_id, "approved": approved}
        )

        result = json.dumps(
            {"approved": approved, "approver": approver if approved else None, "notes": notes or None}
        )
        await self._send_tool_result(session_id, event.id, result)

    async def _handle_register_approved_position(
        self, run: RunState, session_id: str, event, store_id: str
    ) -> None:
        topic = event.input.get("policy_topic", "")
        record = run.approved_topics.get(topic)
        if record is None:
            result = json.dumps(
                {
                    "error": "not_approved",
                    "message": (
                        f"No approved request_human_approval result found for "
                        f"topic '{topic}' in this run. Call request_human_approval "
                        f"first and wait for approved=true before registering."
                    ),
                }
            )
        else:
            path, content = build_position_record(event.input, record["approver"])
            try:
                memory = await self._client.beta.memory_stores.memories.create(
                    store_id, path=path, content=content
                )
                result = json.dumps({"status": "registered", "memory_id": memory.id, "path": path})
                run.memory_store_path = path
                await self._emit(
                    run, {"type": "position_registered", "path": path, "memory_id": memory.id}
                )
            except Exception as exc:  # noqa: BLE001
                result = json.dumps({"error": "write_failed", "message": str(exc)})

        await self._send_tool_result(session_id, event.id, result)

    async def _send_tool_result(
        self, session_id: str, tool_use_id: str, result_text: str, is_error: bool = False
    ) -> None:
        payload = {
            "type": "user.custom_tool_result",
            "custom_tool_use_id": tool_use_id,
            "content": [{"type": "text", "text": result_text}],
        }
        if is_error:
            payload["is_error"] = True
        await self._client.beta.sessions.events.send(session_id, events=[payload])

    async def _download_outputs(self, run: RunState, session_id: str) -> list[dict]:
        out_dir = OUTPUT_ROOT / run.id
        out_dir.mkdir(parents=True, exist_ok=True)

        outputs = []
        async for f in self._client.beta.files.list(scope_id=session_id, betas=[BETA_HEADER]):
            content = await self._client.beta.files.download(f.id)
            dest = out_dir / f.filename
            await content.write_to_file(dest)
            outputs.append({"filename": f.filename, "size_bytes": f.size_bytes})
        return outputs
