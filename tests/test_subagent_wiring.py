"""Verifies cli.setup wires skills -> subagents -> coordinator correctly,
entirely against a mocked Anthropic client. No real API calls are made —
this only checks that the *shapes* we send to client.beta.agents.create()
and client.beta.skills.create() are correct.
"""
from unittest.mock import MagicMock

from policy_orchestrator.cli import setup as cli_setup
from policy_orchestrator.core import SKILLS, SUBAGENTS, skills_for


def _fake_client():
    client = MagicMock()

    def fake_skill_create(files):
        _fname, content, _ctype = files[0]
        text = content.decode("utf-8")
        key = next(
            line.split(":", 1)[1].strip()
            for line in text.splitlines()
            if line.startswith("name:")
        )
        fake = MagicMock()
        fake.id = f"skill_{key}"
        fake.latest_version = "1"
        return fake

    client.beta.skills.create.side_effect = fake_skill_create

    created_agents = []

    def fake_agent_create(**kwargs):
        created_agents.append(kwargs)
        fake = MagicMock()
        fake.id = f"agent_{kwargs['name'].lower().replace(' ', '_')}"
        fake.version = 1
        return fake

    client.beta.agents.create.side_effect = fake_agent_create
    client._created_agents = created_agents  # stash for assertions
    return client


def test_create_skills_uploads_all_eighteen():
    client = _fake_client()
    skills = cli_setup.create_skills(client)
    assert len(skills) == 18
    assert client.beta.skills.create.call_count == 18


def test_each_subagent_gets_exactly_its_owned_skills():
    client = _fake_client()
    skills = cli_setup.create_skills(client)
    cli_setup.create_subagents(client, skills)

    by_name = {a["name"]: a for a in client._created_agents}
    for spec in SUBAGENTS:
        agent_kwargs = by_name[spec["name"]]
        got_ids = sorted(sk["skill_id"] for sk in agent_kwargs["skills"])
        expected_ids = sorted(f"skill_{k}" for k in skills_for(spec["key"]))
        assert got_ids == expected_ids, spec["key"]


def test_total_skill_attachments_across_all_agents_equals_eighteen():
    client = _fake_client()
    skills = cli_setup.create_skills(client)
    cli_setup.create_subagents(client, skills)

    total_attached = sum(len(a["skills"]) for a in client._created_agents)
    assert total_attached == len(SKILLS)


def test_orchestrator_roster_references_all_eight_subagent_ids():
    client = _fake_client()
    skills = cli_setup.create_skills(client)
    subagents = cli_setup.create_subagents(client, skills)
    orchestrator = cli_setup.create_orchestrator(client, subagents)

    assert orchestrator["id"] is not None
    coordinator_kwargs = next(
        a for a in client._created_agents if a["name"] == "Policy Intelligence Orchestrator"
    )
    roster = coordinator_kwargs["multiagent"]["agents"]
    assert sorted(roster) == sorted(info["id"] for info in subagents.values())
    assert len(roster) == 8
