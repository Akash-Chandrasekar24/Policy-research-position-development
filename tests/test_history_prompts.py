"""Task-text builder checks — pure string functions, no database, no API calls."""
from datetime import datetime, timezone

from policy_orchestrator.history import RunRecord, build_refresh_task_text, build_task_text


def test_build_task_text_includes_the_question():
    text = build_task_text("Should the MP support metro phase 3 funding?")
    assert "Should the MP support metro phase 3 funding?" in text
    assert "POLICY QUESTION:" in text


def _sample_match(**overrides) -> RunRecord:
    defaults = dict(
        id="run_123",
        question="What should our stance be on high-risk AI regulation?",
        topic="AI regulation in India",
        status="completed",
        approval_status="approved",
        draft_position="Support a hybrid governance model.",
        confidence=None,
        memory_store_path="/ai-regulation-in-india/2026-06-01.md",
        output_dir=None,
        created_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return RunRecord(**defaults)


def test_build_refresh_task_text_includes_prior_position_and_new_question():
    match = _sample_match()
    text = build_refresh_task_text("What position should the MP take on AI regulation now?", match)

    assert "2026-06-01" in text
    assert "AI regulation in India" in text
    assert match.question in text
    assert match.draft_position in text
    assert "What position should the MP take on AI regulation now?" in text
    assert "request_human_approval" in text  # still routes through approval


def test_build_refresh_task_text_handles_missing_fields_gracefully():
    match = _sample_match(topic=None, draft_position=None, created_at=None)
    text = build_refresh_task_text("New question", match)
    assert "unrecorded" in text
    assert "none recorded" in text
    assert "an earlier date" in text
