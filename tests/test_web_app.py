"""FastAPI route checks for the web front end — no real Anthropic API calls.

STATE_FILE is unset in this dev checkout (no `policy-setup` run), so
`configured` is False by default; the "not provisioned" paths are exercised
directly. Where a run needs to exist, it's inserted straight into
app.state.manager._runs rather than going through start_run(), which would
schedule a real background API call.
"""
import pytest
from fastapi.testclient import TestClient

from policy_orchestrator.web.app import app
from policy_orchestrator.web.manager import RunState


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_get_config_reports_not_provisioned(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is False
    assert body["history_configured"] is False
    assert len(body["subagents"]) == 8
    assert "policy-setup" in body["message"]


def test_similar_returns_no_match_when_history_disabled(client):
    resp = client.get("/api/similar", params={"question": "What about metro delays?"})
    assert resp.status_code == 200
    assert resp.json() == {"match": None}


def test_start_run_without_provisioning_returns_409(client):
    resp = client.post("/api/runs", json={"question": "Should we back this bill?"})
    assert resp.status_code == 409


def test_get_unknown_run_returns_404(client):
    resp = client.get("/api/runs/does-not-exist")
    assert resp.status_code == 404


def test_stream_unknown_run_returns_404(client):
    resp = client.get("/api/runs/does-not-exist/stream")
    assert resp.status_code == 404


def test_reject_approval_without_notes_returns_422(client):
    resp = client.post("/api/runs/run1/approvals/req1", json={"approved": False})
    assert resp.status_code == 422


def test_submit_approval_for_unknown_run_returns_404(client):
    resp = client.post("/api/runs/does-not-exist/approvals/req1", json={"approved": True})
    assert resp.status_code == 404


def test_submit_approval_for_unknown_request_id_returns_409(client):
    app.state.manager._runs["run_known"] = RunState(id="run_known", question="Q?")
    resp = client.post(
        "/api/runs/run_known/approvals/no-such-request", json={"approved": True}
    )
    assert resp.status_code == 409


def test_download_output_for_unknown_run_returns_404(client):
    resp = client.get("/api/runs/does-not-exist/outputs/brief.md")
    assert resp.status_code == 404


def test_download_output_for_missing_file_returns_404(client):
    app.state.manager._runs["run_no_files"] = RunState(id="run_no_files", question="Q?")
    resp = client.get("/api/runs/run_no_files/outputs/brief.md")
    assert resp.status_code == 404


def test_download_output_returns_file_contents(client, tmp_path, monkeypatch):
    monkeypatch.setattr("policy_orchestrator.web.app.OUTPUT_ROOT", tmp_path)
    run_dir = tmp_path / "run_with_file"
    run_dir.mkdir()
    (run_dir / "brief.md").write_text("# Policy Snapshot", encoding="utf-8")

    app.state.manager._runs["run_with_file"] = RunState(id="run_with_file", question="Q?")

    resp = client.get("/api/runs/run_with_file/outputs/brief.md")
    assert resp.status_code == 200
    assert resp.text == "# Policy Snapshot"
