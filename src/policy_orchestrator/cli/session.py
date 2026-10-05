#!/usr/bin/env python3
"""
Runtime entry point for the Policy Intelligence Orchestrator (CLI).

Loads the IDs written by `uv run policy-setup`, starts a session against
the coordinator agent with all 5 knowledge bases mounted, sends the policy
question, and drives the event loop — including the two custom tools
(request_human_approval, register_approved_position) and narration of
subagent thread activity.

If DATABASE_URL is configured (see policy_orchestrator.history), a
question is first checked against every previously *completed* run via
semantic similarity. A close-enough match is shown immediately, with the
choice to use it as-is, run a cheaper "check for updates" pass instead of
full research, or ignore it and run fresh. With no DATABASE_URL set, this
step is skipped entirely and behavior is identical to before the history
feature existed.

Usage:
    uv run policy-session "What position should the MP take on regulating
    high-risk AI systems in India?"
"""
import json
import os
import sys
import textwrap

from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic

from policy_orchestrator.core import MEMORY_STORES
from policy_orchestrator.history import RunRecord, build_refresh_task_text, build_task_text, embed
from policy_orchestrator.history import db as history_db
from policy_orchestrator.settings import BETA_HEADER, OUTPUT_DIR, SIMILARITY_THRESHOLD, STATE_FILE
from policy_orchestrator.tools import PolicyToolHandler

DEFAULT_QUESTION = (
    "What position should the MP take on regulating high-risk AI systems in "
    "India?"
)


def load_state() -> dict:
    if not STATE_FILE.exists():
        sys.exit(
            f"{STATE_FILE} not found. Run `uv run policy-setup` first to "
            f"provision the agents, memory stores, and environment."
        )
    return json.loads(STATE_FILE.read_text())


def build_resources(state: dict) -> list[dict]:
    """Session `resources` payload for the 5 knowledge bases.

    Shared with policy_orchestrator.web.manager so the CLI and web runtimes
    mount memory stores identically.
    """
    resources = []
    for kb in MEMORY_STORES:
        store = state["memory_stores"][kb["key"]]
        resources.append(
            {
                "type": "memory_store",
                "memory_store_id": store["id"],
                "access": store["access"],
                "instructions": kb["description"][:4096],
            }
        )
    return resources


def print_console_url(session_id: str) -> None:
    print(
        f"  Trace: https://platform.claude.com/workspaces/default/sessions/{session_id}"
        f"  (swap 'default' for your workspace slug if not in the Default workspace)"
    )


# -- research history -------------------------------------------------------

def check_history(question_embedding: list[float]) -> RunRecord | None:
    """Returns the closest past completed run above SIMILARITY_THRESHOLD, or
    None if the history feature is disabled or nothing matched closely enough."""
    if not history_db.is_enabled():
        return None
    conn = history_db.connect()
    try:
        return history_db.find_similar(conn, question_embedding, SIMILARITY_THRESHOLD)
    finally:
        conn.close()


def prompt_history_choice(match: RunRecord) -> str:
    print("\n" + "=" * 70)
    print(f"FOUND A SIMILAR PAST QUESTION  (similarity: {match.similarity:.2f})")
    print("=" * 70)
    print(f"Asked:  {match.created_at:%Y-%m-%d}" if match.created_at else "Asked:  (unknown date)")
    print(f"Topic:  {match.topic or '(none recorded)'}")
    print(f"Status: {match.approval_status}")
    print("\nPrior question:")
    print(textwrap.fill(match.question, width=70))
    print("\nPrior position:")
    print(textwrap.fill(match.draft_position or "(none recorded)", width=70))
    print("=" * 70)

    choice = ""
    while choice not in ("1", "2", "3"):
        choice = input(
            "\n[1] Use this answer as-is (free, no new research)\n"
            "[2] Check for updates (cheaper than a full run)\n"
            "[3] Run a full fresh analysis anyway\n"
            "Choice: "
        ).strip()
    return {"1": "cached", "2": "refresh", "3": "fresh"}[choice]


# -- session runtime ---------------------------------------------------------

def run_session(client: Anthropic, state: dict, task_text: str) -> tuple[str, PolicyToolHandler]:
    orchestrator = state["orchestrator"]
    session = client.beta.sessions.create(
        agent={"type": "agent", "id": orchestrator["id"], "version": orchestrator["version"]},
        environment_id=state["environment_id"],
        title="Policy Intelligence session",
        resources=build_resources(state),
    )
    print(f"  session.id = {session.id}")
    print_console_url(session.id)

    tool_handler = PolicyToolHandler(
        client=client,
        position_register_store_id=state["memory_stores"]["position_register"]["id"],
    )

    print("\n" + "-" * 70)
    print("SESSION ACTIVITY")
    print("-" * 70)

    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": task_text}]}],
        )

        for event in stream:
            etype = event.type

            if etype == "agent.message":
                for block in event.content:
                    text = getattr(block, "text", "")
                    if text:
                        print(text, end="", flush=True)

            elif etype == "agent.tool_use":
                print(f"\n  [orchestrator tool] {event.name}")

            elif etype == "agent.custom_tool_use":
                print(f"\n  [custom tool call] {event.name}  input={event.input}")
                result = tool_handler.handle(event.name, event.input)
                print(f"  [custom tool result] {result}")
                client.beta.sessions.events.send(
                    session.id,
                    events=[
                        {
                            "type": "user.custom_tool_result",
                            "custom_tool_use_id": event.id,
                            "content": [{"type": "text", "text": result}],
                        }
                    ],
                )

            elif etype == "session.thread_created":
                print(f"\n  [subagent started] {event.agent_name}")

            elif etype == "session.thread_status_idle":
                print(f"\n  [subagent idle] {event.agent_name}")

            elif etype in ("agent.thread_message_sent", "agent.thread_message_received"):
                direction = "-> " if etype.endswith("_sent") else "<- "
                other = getattr(event, "to_agent_name", None) or getattr(
                    event, "from_agent_name", ""
                )
                print(f"\n  [thread message {direction}{other}]")

            elif etype == "session.error":
                print(f"\n  [error] {getattr(event, 'message', event)}")

            elif etype == "session.status_terminated":
                print("\n\n  [session terminated]")
                break

            elif etype == "session.status_idle":
                stop = getattr(event, "stop_reason", None)
                if stop is not None and getattr(stop, "type", None) == "requires_action":
                    # Custom tool results are already sent above inline;
                    # nothing else to do — keep draining.
                    continue
                print("\n\n  [orchestrator finished]")
                break

    print("-" * 70)
    return session.id, tool_handler


def download_outputs(client: Anthropic, session_id: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = client.beta.files.list(scope_id=session_id, betas=[BETA_HEADER])

    downloaded = []
    for f in files:
        content = client.beta.files.download(f.id)
        dest = OUTPUT_DIR / f.filename
        content.write_to_file(str(dest))
        downloaded.append(dest)

    if downloaded:
        print("\nDownloaded outputs:")
        for d in downloaded:
            print(f"  -> {d.resolve()}")
    else:
        print(
            "\nNo output files found yet (agent may not have written any, or "
            "indexing is still catching up — check the Console trace)."
        )


def report_usage(client: Anthropic, session_id: str) -> None:
    session = client.beta.sessions.retrieve(session_id, betas=[BETA_HEADER])
    usage = getattr(session, "usage", None)
    if usage:
        print("\nToken usage:")
        print(f"  input          = {getattr(usage, 'input_tokens', 0):,}")
        print(f"  output         = {getattr(usage, 'output_tokens', 0):,}")
        print(f"  cache_creation = {getattr(usage, 'cache_creation_input_tokens', 0):,}")
        print(f"  cache_read     = {getattr(usage, 'cache_read_input_tokens', 0):,}")


def save_to_history(session_id: str, question: str, question_embedding: list[float], tool_handler: PolicyToolHandler) -> None:
    if not history_db.is_enabled():
        return
    record = RunRecord(
        id=session_id,
        question=question,
        topic=tool_handler.last_topic,
        status="completed",
        approval_status=tool_handler.last_approval_status,
        draft_position=tool_handler.last_draft_position,
        confidence=None,  # not captured as a distinct structured field today
        memory_store_path=tool_handler.last_memory_store_path,
        output_dir=str(OUTPUT_DIR),
    )
    conn = history_db.connect()
    try:
        history_db.insert_run(conn, record, question_embedding)
        print(f"\nSaved to research history (id={session_id}).")
    finally:
        conn.close()


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Export it and try again.")

    question = " ".join(sys.argv[1:]).strip() or DEFAULT_QUESTION

    print("\nPolicy Intelligence Orchestrator")
    print("=" * 70)
    print("Policy question:")
    print(textwrap.fill(question, width=70, initial_indent="  ", subsequent_indent="  "))
    print()

    question_embedding = embed(question) if history_db.is_enabled() else None

    match = check_history(question_embedding) if question_embedding else None
    if match is not None:
        choice = prompt_history_choice(match)
        if choice == "cached":
            print("\nUsing the cached answer — no new research run.")
            print(f"\n[{match.approval_status}] {match.draft_position}")
            return
        task_text = build_refresh_task_text(question, match) if choice == "refresh" else build_task_text(question)
    else:
        task_text = build_task_text(question)

    state = load_state()
    client = Anthropic()

    session_id, tool_handler = run_session(client, state, task_text)
    download_outputs(client, session_id)
    report_usage(client, session_id)

    if question_embedding is not None:
        save_to_history(session_id, question, question_embedding, tool_handler)

    print(
        f"\nDone. Open {OUTPUT_DIR}/ for the generated outputs, or re-check "
        f"the Policy Position Register memory store for anything approved "
        f"this session."
    )


if __name__ == "__main__":
    main()
