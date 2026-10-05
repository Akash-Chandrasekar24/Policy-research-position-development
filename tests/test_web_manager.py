"""SessionManager unit checks — no real Anthropic API calls.

AsyncAnthropic() constructs successfully even with no API key configured
(the key is only checked when a request is actually sent), so these tests
replace `manager._client` with a mock before any method that would send a
request. Async methods are exercised via asyncio.run() directly rather than
pytest-asyncio, which isn't a project dependency.
"""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from policy_orchestrator.web.manager import (
    ApprovalNotPendingError,
    PendingApproval,
    RunNotFoundError,
    RunState,
    SessionManager,
)


def test_is_configured_reflects_state_file(monkeypatch, tmp_path):
    state_file = tmp_path / "policy_state.json"
    monkeypatch.setattr("policy_orchestrator.web.manager.STATE_FILE", state_file)

    assert SessionManager.is_configured() is False

    state_file.write_text("{}")
    assert SessionManager.is_configured() is True


def test_history_enabled_reflects_database_url(monkeypatch):
    monkeypatch.setattr(
        "policy_orchestrator.web.manager.history_db.is_enabled", lambda: True
    )
    assert SessionManager.history_enabled() is True

    monkeypatch.setattr(
        "policy_orchestrator.web.manager.history_db.is_enabled", lambda: False
    )
    assert SessionManager.history_enabled() is False


def test_get_run_raises_for_unknown_id():
    manager = SessionManager()
    with pytest.raises(RunNotFoundError):
        manager.get_run("does-not-exist")


def test_find_similar_run_returns_none_when_history_disabled():
    manager = SessionManager()  # _history_pool stays None without astart()
    result = asyncio.run(manager.find_similar_run("some policy question"))
    assert result is None


def test_resolve_approval_raises_for_unknown_run():
    manager = SessionManager()
    with pytest.raises(RunNotFoundError):
        asyncio.run(manager.resolve_approval("nope", "req1", True, None))


def test_resolve_approval_raises_when_no_pending_approval_for_run():
    manager = SessionManager()
    run = RunState(id="run1", question="Q?")
    manager._runs["run1"] = run
    with pytest.raises(ApprovalNotPendingError):
        asyncio.run(manager.resolve_approval("run1", "req1", True, None))


def test_resolve_approval_raises_if_already_resolved():
    # PendingApproval's future must be created while a loop is running
    # (asyncio.Future() needs one on Windows' Proactor policy), so build it
    # inside the same asyncio.run() that resolves it.
    async def _flow():
        manager = SessionManager()
        run = RunState(id="run1", question="Q?")
        pending = PendingApproval(
            request_id="req1",
            tool_use_id="tu1",
            policy_topic="T",
            policy_question="Q",
            draft_position="D",
            summary="S",
        )
        pending.future.set_result({"approved": True, "notes": None})
        run.pending_approvals["req1"] = pending
        manager._runs["run1"] = run

        with pytest.raises(ApprovalNotPendingError):
            await manager.resolve_approval("run1", "req1", False, "changed my mind")

    asyncio.run(_flow())


def test_resolve_approval_sets_future_result():
    async def _flow():
        manager = SessionManager()
        run = RunState(id="run1", question="Q?")
        pending = PendingApproval(
            request_id="req1",
            tool_use_id="tu1",
            policy_topic="T",
            policy_question="Q",
            draft_position="D",
            summary="S",
        )
        run.pending_approvals["req1"] = pending
        manager._runs["run1"] = run

        await manager.resolve_approval("run1", "req1", True, "looks good")

        assert pending.future.done()
        assert pending.future.result() == {"approved": True, "notes": "looks good"}

    asyncio.run(_flow())


def test_stream_events_raises_for_unknown_run():
    manager = SessionManager()

    async def _first_event():
        agen = manager.stream_events("nope")
        return await agen.__anext__()

    with pytest.raises(RunNotFoundError):
        asyncio.run(_first_event())


def test_stream_events_replays_history_for_a_terminal_run():
    manager = SessionManager()
    run = RunState(id="run1", question="Q?", status="completed")
    run.history = [
        {"type": "session_started", "session_id": "s1"},
        {"type": "done", "status": "completed"},
    ]
    manager._runs["run1"] = run

    async def _collect():
        return [e async for e in manager.stream_events("run1")]

    events = asyncio.run(_collect())
    assert [e["event"] for e in events] == ["session_started", "done"]


def _fake_client_with_captured_send():
    client = MagicMock()
    client.beta.sessions.events.send = AsyncMock()
    return client


def _sent_result(client) -> dict:
    call = client.beta.sessions.events.send.call_args
    payload = call.kwargs["events"][0]
    return json.loads(payload["content"][0]["text"])


def test_handle_register_approved_position_without_prior_approval_is_rejected():
    manager = SessionManager()
    manager._client = _fake_client_with_captured_send()
    run = RunState(id="run1", question="Q?")
    event = SimpleNamespace(
        id="tool_1",
        input={
            "policy_topic": "Never Approved Topic",
            "policy_question": "Q?",
            "approved_position": "P",
            "approver": "A",
        },
    )

    asyncio.run(manager._handle_register_approved_position(run, "session1", event, "store_x"))

    result = _sent_result(manager._client)
    assert result["error"] == "not_approved"
    assert run.memory_store_path is None


def test_handle_register_approved_position_succeeds_once_topic_is_approved():
    manager = SessionManager()
    manager._client = _fake_client_with_captured_send()
    manager._client.beta.memory_stores.memories.create = AsyncMock(
        return_value=SimpleNamespace(id="mem_123")
    )
    run = RunState(id="run1", question="Q?")
    run.approved_topics["Metro Delays"] = {
        "policy_question": "Q?",
        "draft_position": "Draft.",
        "approver": "Tejasvi Surya",
    }
    event = SimpleNamespace(
        id="tool_1",
        input={
            "policy_topic": "Metro Delays",
            "policy_question": "Q?",
            "approved_position": "Final position.",
            "approver": "Tejasvi Surya",
        },
    )

    asyncio.run(manager._handle_register_approved_position(run, "session1", event, "store_x"))

    result = _sent_result(manager._client)
    assert result["status"] == "registered"
    assert result["memory_id"] == "mem_123"
    assert run.memory_store_path == result["path"]
    assert run.history[-1]["type"] == "position_registered"


def test_handle_request_human_approval_full_cycle_on_approval():
    manager = SessionManager()
    manager._client = _fake_client_with_captured_send()
    run = RunState(id="run1", question="Q?")
    manager._runs["run1"] = run
    event = SimpleNamespace(
        id="tool_1",
        input={
            "policy_topic": "AI Regulation",
            "policy_question": "Central law or sector regulators?",
            "draft_position": "Support a hybrid model.",
            "summary": "Short summary.",
        },
    )

    async def _flow():
        task = asyncio.create_task(manager._handle_request_human_approval(run, "session1", event))
        await asyncio.sleep(0)  # let it register the pending approval and suspend
        assert run.status == "awaiting_approval"
        request_id = next(iter(run.pending_approvals))
        await manager.resolve_approval("run1", request_id, True, "Looks good")
        await task

    asyncio.run(_flow())

    assert run.status == "running"
    assert run.approval_status == "approved"
    assert "AI Regulation" in run.approved_topics
    result = _sent_result(manager._client)
    assert result["approved"] is True


def test_handle_request_human_approval_full_cycle_on_rejection():
    manager = SessionManager()
    manager._client = _fake_client_with_captured_send()
    run = RunState(id="run1", question="Q?")
    manager._runs["run1"] = run
    event = SimpleNamespace(
        id="tool_1",
        input={
            "policy_topic": "AI Regulation",
            "policy_question": "Central law or sector regulators?",
            "draft_position": "Support a hybrid model.",
            "summary": "Short summary.",
        },
    )

    async def _flow():
        task = asyncio.create_task(manager._handle_request_human_approval(run, "session1", event))
        await asyncio.sleep(0)
        request_id = next(iter(run.pending_approvals))
        await manager.resolve_approval("run1", request_id, False, "Needs more evidence")
        await task

    asyncio.run(_flow())

    assert run.approval_status == "rejected"
    assert run.approved_topics == {}
    result = _sent_result(manager._client)
    assert result["approved"] is False
