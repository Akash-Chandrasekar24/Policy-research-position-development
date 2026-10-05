#!/usr/bin/env python3
"""
Custom tools with Claude Managed Agents — worked example.

Demonstrates the full custom-tool loop:
  1. Declare a custom tool on the agent (a *contract*, not code).
  2. Stream the session.
  3. When the agent calls the tool, the session pauses with
     stop_reason: requires_action.
  4. YOUR code executes the tool and sends back user.custom_tool_result.
  5. The agent resumes with the result and continues the task.

The custom tool here is `ticket_system`: a single consolidated tool with an
`action` parameter (lookup | create | list_open), following the docs' advice
to group related operations rather than making one tool per action.

In this demo the "backend" is an in-memory dict. In production, swap the body
of run_ticket_system() for real calls to Jira / Zendesk / your own DB.

Docs:
  https://platform.claude.com/docs/en/managed-agents/tools#custom-tools
  https://platform.claude.com/docs/en/managed-agents/events-and-streaming#handling-custom-tool-calls

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."
Run:
    python custom_tool_agent.py
"""

import json
import os
import sys
import uuid

from anthropic import Anthropic

BETA_HEADER = "managed-agents-2026-04-01"


# ---------------------------------------------------------------------------
# 1. The custom tool DEFINITION (the contract Claude sees).
#
#    Note the detailed description and per-parameter descriptions — this is
#    the single biggest factor in whether the agent calls the tool correctly.
#    One tool with an `action` enum instead of three separate tools.
# ---------------------------------------------------------------------------
TICKET_TOOL = {
    "type": "custom",
    "name": "ticket_system",
    "description": (
        "Access the internal customer support ticketing system. Use this to "
        "look up an existing ticket by its ID, create a new support ticket, "
        "or list currently open tickets. Call this whenever the user asks "
        "about ticket status, wants to file an issue, or needs an overview of "
        "outstanding work. Do NOT use it for general questions unrelated to "
        "support tickets. The system is the source of truth for ticket state, "
        "so always call it rather than guessing ticket details."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["lookup", "create", "list_open"],
                "description": (
                    "Which operation to perform. 'lookup' fetches one ticket "
                    "by id. 'create' opens a new ticket (requires title and "
                    "description). 'list_open' returns all unresolved tickets."
                ),
            },
            "ticket_id": {
                "type": "string",
                "description": "The ticket id, required only for the 'lookup' action (e.g. 'TKT-1042').",
            },
            "title": {
                "type": "string",
                "description": "Short summary of the issue, required for 'create'.",
            },
            "description": {
                "type": "string",
                "description": "Full details of the issue, required for 'create'.",
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "urgent"],
                "description": "Priority for a new ticket. Defaults to 'medium' if omitted.",
            },
        },
        "required": ["action"],
    },
}


# ---------------------------------------------------------------------------
# The fake backend. Replace with real Jira/Zendesk/DB calls in production.
# ---------------------------------------------------------------------------
_TICKETS = {
    "TKT-1042": {
        "id": "TKT-1042",
        "title": "Login page returns 500 after password reset",
        "status": "open",
        "priority": "high",
        "assignee": "Priya N.",
    },
    "TKT-1039": {
        "id": "TKT-1039",
        "title": "Export to CSV missing the last row",
        "status": "resolved",
        "priority": "low",
        "assignee": "Marcus T.",
    },
}


def run_ticket_system(tool_input: dict) -> str:
    """Execute the tool on YOUR infrastructure and return a string result.

    Returns high-signal JSON only — exactly what the agent needs to reason
    about its next step, nothing more (per the docs' response-design advice).
    """
    action = tool_input.get("action")

    if action == "lookup":
        ticket = _TICKETS.get(tool_input.get("ticket_id", ""))
        if not ticket:
            return json.dumps({"error": "not_found", "ticket_id": tool_input.get("ticket_id")})
        return json.dumps(ticket)

    if action == "create":
        new_id = f"TKT-{1043 + len(_TICKETS)}"
        ticket = {
            "id": new_id,
            "title": tool_input.get("title", "Untitled"),
            "status": "open",
            "priority": tool_input.get("priority", "medium"),
            "assignee": "unassigned",
        }
        _TICKETS[new_id] = ticket
        return json.dumps(ticket)

    if action == "list_open":
        open_tickets = [t for t in _TICKETS.values() if t["status"] == "open"]
        return json.dumps({"open_tickets": open_tickets, "count": len(open_tickets)})

    return json.dumps({"error": "unknown_action", "action": action})


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set.")

    client = Anthropic()

    # -- Create the agent with built-in toolset PLUS our custom tool ---------
    agent = client.beta.agents.create(
        name="Support Agent",
        model={"id": "claude-sonnet-5"},
        system=(
            "You are a customer support assistant. Use the ticket_system tool "
            "to look up, create, and list support tickets. Always confirm "
            "ticket details from the system rather than assuming them."
        ),
        tools=[
            {"type": "agent_toolset_20260401"},  # built-ins (bash, read, etc.)
            TICKET_TOOL,                          # our custom contract
        ],
    )

    environment = client.beta.environments.create(
        name="support-env",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )

    session = client.beta.sessions.create(
        agent=agent.id,
        environment_id=environment.id,
        title="Support custom-tool demo",
    )

    # Keep a map of event_id -> custom_tool_use event so we can look up the
    # tool name + input when the session pauses asking us to act.
    custom_tool_calls: dict[str, object] = {}

    user_request = (
        "Check the status of ticket TKT-1042, and if it's still open, "
        "create a new high-priority ticket titled 'Escalation: login 500s' "
        "describing that customers cannot log in after a password reset. "
        "Then give me a short summary."
    )

    print("USER:", user_request, "\n")
    print("─" * 70)

    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[{
                "type": "user.message",
                "content": [{"type": "text", "text": user_request}],
            }],
        )

        for event in stream:
            etype = event.type

            if etype == "agent.message":
                for block in event.content:
                    text = getattr(block, "text", "")
                    if text:
                        print(text, end="", flush=True)

            elif etype == "agent.custom_tool_use":
                # The agent wants OUR tool. Remember it by id so we can run it
                # when the session pauses with requires_action.
                custom_tool_calls[event.id] = event
                print(f"\n  [agent requests custom tool: {event.name} {event.input}]")

            elif etype == "agent.tool_use":
                print(f"\n  [built-in tool: {event.name}]")

            elif etype == "session.status_idle":
                stop = getattr(event, "stop_reason", None)
                if stop and stop.type == "requires_action":
                    # Run each blocked custom tool and send results back.
                    results = []
                    for event_id in stop.event_ids:
                        call = custom_tool_calls.get(event_id)
                        if call is None:
                            continue
                        output = run_ticket_system(call.input)
                        print(f"\n  [executed {call.name} -> {output}]")
                        results.append({
                            "type": "user.custom_tool_result",
                            "custom_tool_use_id": event_id,
                            "content": [{"type": "text", "text": output}],
                        })
                    if results:
                        client.beta.sessions.events.send(session.id, events=results)
                    # Session transitions back to running; keep streaming.
                    continue
                else:
                    # No pending action — the agent is genuinely done.
                    print("\n\n  [agent finished]")
                    break

            elif etype == "session.error":
                print(f"\n  [error] {getattr(event, 'message', event)}")
                break

    print("\n" + "─" * 70)
    print("Final ticket store:", json.dumps(_TICKETS, indent=2))


if __name__ == "__main__":
    main()