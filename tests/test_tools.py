"""Custom-tool contract and handler checks — no real API calls."""
import json
from unittest.mock import MagicMock

from policy_orchestrator.tools import (
    CUSTOM_TOOLS,
    PolicyToolHandler,
    REGISTER_APPROVED_POSITION,
    REQUEST_HUMAN_APPROVAL,
    build_position_record,
)


def test_custom_tools_contains_both_tool_names():
    names = {t["name"] for t in CUSTOM_TOOLS}
    assert names == {"request_human_approval", "register_approved_position"}


def test_request_human_approval_requires_four_fields():
    assert set(REQUEST_HUMAN_APPROVAL["input_schema"]["required"]) == {
        "policy_topic",
        "policy_question",
        "draft_position",
        "summary",
    }


def test_register_approved_position_requires_four_fields():
    assert set(REGISTER_APPROVED_POSITION["input_schema"]["required"]) == {
        "policy_topic",
        "policy_question",
        "approved_position",
        "approver",
    }


def test_build_position_record_includes_all_fields_and_slugified_path():
    tool_input = {
        "policy_topic": "AI Regulation In India!",
        "policy_question": "Central law or sector regulators?",
        "approved_position": "Support a hybrid model.",
        "supporting_evidence": "See evidence brief.",
        "conditions_and_safeguards": "Independent testing regime.",
        "approver": "Tejasvi Surya",
    }
    path, content = build_position_record(tool_input, fallback_approver="fallback")

    assert path.startswith("/ai-regulation-in-india/")
    assert path.endswith(".md")
    assert "# AI Regulation In India!" in content
    assert "Support a hybrid model." in content
    assert "Tejasvi Surya" in content


def test_build_position_record_falls_back_to_default_approver():
    path, content = build_position_record({"policy_topic": "X"}, fallback_approver="Fallback Approver")
    assert "Fallback Approver" in content


def test_register_approved_position_rejected_without_prior_approval():
    handler = PolicyToolHandler(client=MagicMock(), position_register_store_id="memstore_x")
    result = json.loads(
        handler.handle(
            "register_approved_position",
            {
                "policy_topic": "Never Approved Topic",
                "policy_question": "Q?",
                "approved_position": "Position.",
                "approver": "Someone",
            },
        )
    )
    assert result["error"] == "not_approved"


def test_register_approved_position_succeeds_once_topic_is_marked_approved():
    fake_client = MagicMock()
    fake_memory = MagicMock(id="mem_123")
    fake_client.beta.memory_stores.memories.create.return_value = fake_memory

    handler = PolicyToolHandler(client=fake_client, position_register_store_id="memstore_x")
    # Simulate what _request_human_approval does on an actual approval,
    # without going through its interactive input() prompt.
    handler.approved_topics["Metro Delays"] = {
        "policy_question": "Q?",
        "draft_position": "Draft.",
        "approver": "Tejasvi Surya",
    }

    result = json.loads(
        handler.handle(
            "register_approved_position",
            {
                "policy_topic": "Metro Delays",
                "policy_question": "Q?",
                "approved_position": "Final position.",
                "approver": "Tejasvi Surya",
            },
        )
    )
    assert result["status"] == "registered"
    assert result["memory_id"] == "mem_123"
    fake_client.beta.memory_stores.memories.create.assert_called_once()


def test_unknown_tool_name_returns_error():
    handler = PolicyToolHandler(client=MagicMock(), position_register_store_id="memstore_x")
    result = json.loads(handler.handle("some_other_tool", {}))
    assert result["error"] == "unknown_tool"
