# Policy Intelligence Orchestrator

A Claude Managed Agents application for an Indian MP's office (Bangalore
South). It turns a policy question into evidence, stakeholder viewpoints,
policy options, trade-offs, and a recommended position — with a mandatory
human-approval step before anything becomes an official position.

The work is split across 1 coordinator ("orchestrator") agent and 8
specialist subagents, each with its own [Agent Skills](src/policy_orchestrator/skills)
and read/write access to shared [knowledge bases](src/policy_orchestrator/core/knowledge_bases.py)
(memory stores). Every subagent is required to cite the literal source URL
for its claims and to connect its findings back to Bangalore South
specifically — see `CITATION_DISCIPLINE` / `RELEVANCE_DISCIPLINE` in
[core/subagents.py](src/policy_orchestrator/core/subagents.py).

## Requirements

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/)
- An Anthropic API key with access to the Managed Agents beta
  (`managed-agents-2026-04-01`)

## Setup

```bash
uv sync
```

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...

# Optional — enables the research-history feature (see below).
# DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### One-time provisioning

Creates the memory stores, uploads the 18 skills, creates the 8 subagents
and the coordinator, and creates the environment. Safe to run once; use
`--force` to tear down and recreate everything.

```bash
uv run policy-setup
```

## Running it

**CLI**, one question per run, with a terminal prompt for the
human-approval step:

```bash
uv run policy-session
```

**Web UI** (FastAPI + server-sent events), with a browser-based approval
modal:

```bash
uv run policy-web
```

Then open `http://127.0.0.1:8000`. Override the bind address/port with the
`HOST` / `PORT` environment variables.

## Research history (optional)

If `DATABASE_URL` points at a Postgres instance with the `pgvector`
extension available (e.g. a free-tier Supabase or Neon project), every
completed run is embedded (locally, via `fastembed` — no extra API calls)
and stored. The next time a similar question comes in, both the CLI and
the web UI offer the cached answer, a cheap "check for updates" refresh,
or a fresh full run instead of always re-running all 8 agents. Leave
`DATABASE_URL` unset and this feature no-ops everywhere it's used — nothing
else in the system depends on it.

## Project layout

```
src/policy_orchestrator/
  settings.py        - centralized paths, model, DB/embedding config
  core/               - knowledge bases, skills registry, subagent + orchestrator prompts
  tools/              - request_human_approval / register_approved_position custom tools
  history/            - optional Postgres+pgvector research-history store
  cli/                - policy-setup / policy-session entry points
  web/                - policy-web (FastAPI) entry point, static assets, templates
  skills/             - the 18 bundled Agent Skills (SKILL.md files)
tests/                - pytest suite (mock-based; no live API calls except test_history_embeddings.py)
```

## Testing

```bash
uv run pytest              # full suite
uv run pytest -m "not slow"  # skip the tests that load the local embedding model
```
