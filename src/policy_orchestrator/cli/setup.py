#!/usr/bin/env python3
"""
ONE-TIME SETUP for the Policy Intelligence Orchestrator.

Creates (in order):
  1. The 5 Memory Stores (knowledge bases).
  2. The 18 Agent Skills (real Skills-API resources, uploaded from the
     SKILL.md files bundled under policy_orchestrator/skills/).
  3. The 8 specialist subagents, each with its owning skills attached.
  4. The coordinator agent, with a `multiagent` roster referencing the 8
     subagent IDs.
  5. One shared cloud Environment.

Persists every returned ID to policy_state.json (in the current working
directory — see settings.py). Re-running this script refuses to run if
that file already exists (pass --force to recreate everything from
scratch) — agents/environments/memory stores are persistent resources, not
per-run parameters; see the Managed Agents anti-pattern this guards
against in shared/managed-agents-core.md.

Usage:
    uv run policy-setup [--force]
"""
import json
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic

from policy_orchestrator.core import (
    MEMORY_STORES,
    ORCHESTRATOR_SYSTEM,
    SKILLS,
    SUBAGENTS,
    skill_path,
    skills_for,
)
from policy_orchestrator.settings import ENVIRONMENT_NAME, MODEL, STATE_FILE
from policy_orchestrator.tools import CUSTOM_TOOLS

MAX_RETRIES = 4
INITIAL_RETRY_DELAY_SECONDS = 2.0


def run_with_retry(label: str, func):
    delay = INITIAL_RETRY_DELAY_SECONDS
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            text = str(exc).lower()
            if "rate limited" not in text and "429" not in text or attempt == MAX_RETRIES:
                raise
            print(f"  [warn] {label} rate limited; retrying in {delay:.1f}s "
                  f"(attempt {attempt}/{MAX_RETRIES})")
            time.sleep(delay)
            delay *= 2
    raise last_exc


def create_memory_stores(client: Anthropic) -> dict:
    print("Creating memory stores (knowledge bases)...")
    stores = {}
    for kb in MEMORY_STORES:
        store = run_with_retry(
            f"memory store '{kb['name']}'",
            lambda kb=kb: client.beta.memory_stores.create(
                name=kb["name"], description=kb["description"]
            ),
        )
        stores[kb["key"]] = {"id": store.id, "access": kb["access"], "name": kb["name"]}
        print(f"  {kb['name']:<32} -> {store.id}")
    return stores


def create_skills(client: Anthropic) -> dict:
    print("\nCreating 18 Agent Skills from policy_orchestrator/skills/...")
    skills = {}
    for spec in SKILLS:
        path = skill_path(spec["key"])
        if not path.exists():
            raise FileNotFoundError(
                f"Missing skill file: {path} — expected one SKILL.md per "
                f"entry in policy_orchestrator.core.skills_registry.SKILLS."
            )
        # The Skills API requires every uploaded file to sit inside one
        # top-level directory, with SKILL.md at that directory's root — a
        # bare "SKILL.md" filename (no directory prefix) is rejected with
        # 400 "SKILL.md file must be exactly in the top-level folder."
        skill = run_with_retry(
            f"skill '{spec['key']}'",
            lambda spec=spec, path=path: client.beta.skills.create(
                files=[(f"{spec['key']}/SKILL.md", path.read_bytes(), "text/markdown")],
            ),
        )
        skills[spec["key"]] = {"id": skill.id, "version": skill.latest_version}
        print(f"  {spec['key']:<38} -> {skill.id} (v{skill.latest_version})")
    return skills


def create_subagents(client: Anthropic, skills: dict) -> dict:
    print("\nCreating 8 specialist subagents...")
    agents = {}
    for spec in SUBAGENTS:
        tools = [{"type": "agent_toolset_20260401"}]

        agent_skills = [
            {"type": "custom", "skill_id": skills[key]["id"], "version": skills[key]["version"]}
            for key in skills_for(spec["key"])
        ]

        kwargs = {
            "name": spec["name"],
            "model": MODEL,
            "system": spec["system"],
            "tools": tools,
            "skills": agent_skills,
        }

        agent = run_with_retry(
            f"subagent '{spec['name']}'",
            lambda kwargs=kwargs: client.beta.agents.create(**kwargs),
        )
        agents[spec["key"]] = {"id": agent.id, "version": agent.version, "name": spec["name"]}
        print(
            f"  {spec['name']:<38} -> {agent.id} (v{agent.version})"
            f" [{len(agent_skills)} skill(s)]"
        )
    return agents


def create_orchestrator(client: Anthropic, subagents: dict):
    print("\nCreating coordinator (Policy Intelligence Orchestrator)...")
    roster = [info["id"] for info in subagents.values()]
    orchestrator = run_with_retry(
        "orchestrator agent",
        lambda: client.beta.agents.create(
            name="Policy Intelligence Orchestrator",
            model=MODEL,
            system=ORCHESTRATOR_SYSTEM,
            tools=[{"type": "agent_toolset_20260401"}, *CUSTOM_TOOLS],
            multiagent={"type": "coordinator", "agents": roster},
        ),
    )
    print(f"  Policy Intelligence Orchestrator     -> {orchestrator.id} (v{orchestrator.version})")
    return {"id": orchestrator.id, "version": orchestrator.version}


def create_environment(client: Anthropic):
    print("\nCreating shared environment...")
    environment = run_with_retry(
        "environment",
        lambda: client.beta.environments.create(
            name=ENVIRONMENT_NAME,
            config={"type": "cloud", "networking": {"type": "unrestricted"}},
        ),
    )
    print(f"  {ENVIRONMENT_NAME:<32} -> {environment.id}")
    return environment.id


def main() -> None:
    force = "--force" in sys.argv
    if STATE_FILE.exists() and not force:
        sys.exit(
            f"{STATE_FILE} already exists — the agents/environment/memory "
            f"stores are already provisioned. Re-run with --force only if "
            f"you intend to create a brand-new set of resources (the old "
            f"ones will be orphaned, not deleted)."
        )

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Export it and try again.")

    print("Policy Intelligence Orchestrator — one-time setup")
    print("=" * 70)

    client = Anthropic()

    memory_stores = create_memory_stores(client)
    skills = create_skills(client)
    subagents = create_subagents(client, skills)
    orchestrator = create_orchestrator(client, subagents)
    environment_id = create_environment(client)

    state = {
        "environment_id": environment_id,
        "orchestrator": orchestrator,
        "subagents": subagents,
        "memory_stores": memory_stores,
        "skills": skills,
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))

    print("\n" + "=" * 70)
    print(f"Done. Saved all IDs to {STATE_FILE.resolve()}")
    print("Run `uv run policy-session \"<policy question>\"` to start a session.")


if __name__ == "__main__":
    main()
