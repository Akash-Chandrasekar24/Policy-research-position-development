"""CLI session runtime checks — no real Anthropic API calls.

Covers the pieces of policy_orchestrator.cli.session that don't require a
live session stream: state loading, resource building, and the history
lookup/save helpers (all mocked at the policy_orchestrator.history.db
boundary). run_session()'s event loop is exercised with a fully mocked
sync Anthropic client so the custom-tool dispatch and stop-condition logic
run for real, without any network access.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from policy_orchestrator.core import MEMORY_STORES
from policy_orchestrator.history import RunRecord
from policy_orchestrator.tools import PolicyToolHandler

from policy_orchestrator.cli import session as cli_session


def _sample_state() -> dict:
    memory_stores = {
        kb["key"]: {"id": f"memstore_{kb['key']}", "access": kb["access"]}
        for kb in MEMORY_STORES
    }
    return {
        "orchestrator": {"id": "agent_orch", "version": "1"},
        "environment_id": "env_1",
        "memory_stores": memory_stores,
    }


def test_load_state_exits_when_state_file_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(cli_session, "STATE_FILE", tmp_path / "policy_state.json")
    with pytest.raises(SystemExit):
        cli_session.load_state()


def test_load_state_returns_parsed_json(monkeypatch, tmp_path):
    state_file = tmp_path / "policy_state.json"
    state_file.write_text(json.dumps({"hello": "world"}))
    monkeypatch.setattr(cli_session, "STATE_FILE", state_file)

    assert cli_session.load_state() == {"hello": "world"}


def test_build_resources_covers_every_knowledge_base():
    state = _sample_state()
    resources = cli_session.build_resources(state)

    assert len(resources) == len(MEMORY_STORES)
    for resource, kb in zip(resources, MEMORY_STORES):
        assert resource["type"] == "memory_store"
        assert resource["memory_store_id"] == f"memstore_{kb['key']}"
        assert resource["access"] == kb["access"]
        assert resource["instructions"] == kb["description"][:4096]


def test_check_history_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr(cli_session.history_db, "is_enabled", lambda: False)
    connect = MagicMock(side_effect=AssertionError("should not connect when disabled"))
    monkeypatch.setattr(cli_session.history_db, "connect", connect)

    assert cli_session.check_history([0.1, 0.2]) is None


def test_check_history_delegates_to_db_when_enabled(monkeypatch):
    fake_conn = MagicMock()
    sentinel = RunRecord(
        id="run_1",
        question="Q?",
        topic="T",
        status="completed",
        approval_status="approved",
        draft_position="D",
        confidence=None,
        memory_store_path=None,
        output_dir=None,
        similarity=0.9,
    )
    monkeypatch.setattr(cli_session.history_db, "is_enabled", lambda: True)
    monkeypatch.setattr(cli_session.history_db, "connect", lambda: fake_conn)
    monkeypatch.setattr(
        cli_session.history_db, "find_similar", lambda conn, emb, threshold: sentinel
    )

    result = cli_session.check_history([0.1, 0.2])

    assert result is sentinel
    fake_conn.close.assert_called_once()


def _sample_match(**overrides) -> RunRecord:
    defaults = dict(
        id="run_1",
        question="What should our stance be on metro delays?",
        topic="Metro Phase-3 delays",
        status="completed",
        approval_status="approved",
        draft_position="Support accelerated funding.",
        confidence=None,
        memory_store_path=None,
        output_dir=None,
        similarity=0.9,
    )
    defaults.update(overrides)
    return RunRecord(**defaults)


def test_prompt_history_choice_maps_input_to_choice(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "2")
    choice = cli_session.prompt_history_choice(_sample_match())
    assert choice == "refresh"


def test_prompt_history_choice_reprompts_on_invalid_input(monkeypatch):
    answers = iter(["x", "9", "3"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    choice = cli_session.prompt_history_choice(_sample_match())
    assert choice == "fresh"


def test_save_to_history_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(cli_session.history_db, "is_enabled", lambda: False)
    connect = MagicMock(side_effect=AssertionError("should not connect when disabled"))
    monkeypatch.setattr(cli_session.history_db, "connect", connect)

    tool_handler = PolicyToolHandler(client=MagicMock(), position_register_store_id="store_x")
    cli_session.save_to_history("session_1", "Q?", [0.1, 0.2], tool_handler)  # must not raise


def test_save_to_history_builds_record_from_tool_handler(monkeypatch):
    fake_conn = MagicMock()
    monkeypatch.setattr(cli_session.history_db, "is_enabled", lambda: True)
    monkeypatch.setattr(cli_session.history_db, "connect", lambda: fake_conn)
    captured = {}
    monkeypatch.setattr(
        cli_session.history_db,
        "insert_run",
        lambda conn, record, embedding: captured.update(record=record, embedding=embedding),
    )

    tool_handler = PolicyToolHandler(client=MagicMock(), position_register_store_id="store_x")
    tool_handler.last_topic = "AI Regulation"
    tool_handler.last_approval_status = "approved"
    tool_handler.last_draft_position = "Support a hybrid model."
    tool_handler.last_memory_store_path = "/ai-regulation/2026-01-01.md"

    cli_session.save_to_history("session_1", "Should we regulate AI?", [0.1, 0.2], tool_handler)

    record = captured["record"]
    assert record.id == "session_1"
    assert record.question == "Should we regulate AI?"
    assert record.topic == "AI Regulation"
    assert record.approval_status == "approved"
    assert record.draft_position == "Support a hybrid model."
    assert record.memory_store_path == "/ai-regulation/2026-01-01.md"
    assert captured["embedding"] == [0.1, 0.2]
    fake_conn.close.assert_called_once()


class _FakeEventStream:
    """Stands in for `client.beta.sessions.events.stream(...)` — a sync
    context manager that iterates over a fixed, pre-built event list."""

    def __init__(self, events):
        self._events = events

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def __iter__(self):
        return iter(self._events)


def test_run_session_dispatches_custom_tools_and_stops_on_idle(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")  # auto-approve

    events = [
        SimpleNamespace(type="agent.message", content=[SimpleNamespace(text="Researching...")]),
        SimpleNamespace(type="agent.tool_use", name="web_search"),
        SimpleNamespace(
            type="agent.custom_tool_use",
            id="tu_approve",
            name="request_human_approval",
            input={
                "policy_topic": "AI Regulation",
                "policy_question": "Central law or sector regulators?",
                "draft_position": "Support a hybrid model.",
                "summary": "Short summary.",
            },
        ),
        SimpleNamespace(
            type="session.status_idle",
            stop_reason=SimpleNamespace(type="requires_action"),
        ),
        SimpleNamespace(
            type="agent.custom_tool_use",
            id="tu_register",
            name="register_approved_position",
            input={
                "policy_topic": "AI Regulation",
                "policy_question": "Central law or sector regulators?",
                "approved_position": "Support a hybrid model.",
                "approver": "Tejasvi Surya",
            },
        ),
        SimpleNamespace(type="session.status_idle", stop_reason=None),
    ]

    sent_events = []
    fake_client = MagicMock()
    fake_client.beta.sessions.create.return_value = SimpleNamespace(id="session_1")
    fake_client.beta.sessions.events.stream.return_value = _FakeEventStream(events)
    fake_client.beta.sessions.events.send.side_effect = (
        lambda session_id, events: sent_events.append(events[0])
    )
    fake_client.beta.memory_stores.memories.create.return_value = SimpleNamespace(id="mem_1")

    session_id, tool_handler = cli_session.run_session(fake_client, _sample_state(), "Do the research.")

    assert session_id == "session_1"
    # First send() is the user.message kicking off the task; the next two
    # are the tool results for the approval and the registration.
    assert sent_events[0]["type"] == "user.message"
    approval_result = json.loads(sent_events[1]["content"][0]["text"])
    assert approval_result["approved"] is True
    register_result = json.loads(sent_events[2]["content"][0]["text"])
    assert register_result["status"] == "registered"
    assert tool_handler.last_approval_status == "approved"
    assert tool_handler.last_memory_store_path == register_result["path"]
