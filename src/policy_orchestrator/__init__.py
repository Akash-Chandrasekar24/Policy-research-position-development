"""Policy Intelligence Orchestrator — a Claude Managed Agents application.

Subpackages:
    settings    Centralized runtime constants (paths, model, beta header).
    core        Domain config: knowledge bases, skills registry, subagents,
                coordinator system prompt (data + prompt-building only).
    tools       Custom tool contracts (schemas) and the sync CLI handler
                (handlers) for request_human_approval / register_approved_position.
    cli         Command-line entry points: one-time provisioning (setup)
                and the terminal runtime (session).
    web         FastAPI front end: async session orchestration (manager),
                routes (app), and the browser UI (static/templates).
    skills      Bundled Agent Skills (SKILL.md per skill) uploaded by
                cli.setup via the Skills API.
"""
