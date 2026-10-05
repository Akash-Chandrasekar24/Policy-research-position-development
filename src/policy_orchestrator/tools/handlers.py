"""Execution for the two custom tools (see schemas.py for their contracts).

PolicyToolHandler is the synchronous, terminal-`input()`-based
implementation used by the CLI (policy_orchestrator.cli.session). The web
backend (policy_orchestrator.web.manager) implements the same two tools
independently around asyncio, but both share build_position_record() below
so the Policy Position Register's record format never drifts between them.
"""
import json
import textwrap
from datetime import datetime, timezone


def _slugify(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text.strip()]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "untitled"


def build_position_record(tool_input: dict, fallback_approver: str) -> tuple[str, str]:
    """Build the (memory path, markdown content) for an approved position.

    Pure — no I/O — so both the sync CLI handler (PolicyToolHandler below)
    and the async web backend can share the exact same record format without
    duplicating it.
    """
    topic = tool_input.get("policy_topic", "")
    date_approved = datetime.now(timezone.utc).date().isoformat()
    content = textwrap.dedent(
        f"""
        # {topic}

        - **Policy question**: {tool_input.get('policy_question', '')}
        - **Approved position**: {tool_input.get('approved_position', '')}
        - **Supporting evidence**: {tool_input.get('supporting_evidence', '')}
        - **Conditions and safeguards**: {tool_input.get('conditions_and_safeguards', '')}
        - **Date approved**: {date_approved}
        - **Approver**: {tool_input.get('approver', fallback_approver)}
        - **Previous version**: {tool_input.get('previous_version', 'None')}
        - **Reason for change**: {tool_input.get('reason_for_change', 'N/A')}
        - **Related speeches and questions**: {tool_input.get('related_speeches_and_questions', 'None')}
        """
    ).strip()
    path = f"/{_slugify(topic)}/{date_approved}.md"
    return path, content


class PolicyToolHandler:
    """Stateful dispatcher for the two custom tools, scoped to one session.

    `approved_topics` tracks which topics have received a human `allow` this
    session — this is the actual security boundary for
    register_approved_position, not anything the agent's prompt says.

    `last_topic` / `last_draft_position` / `last_approval_status` /
    `last_memory_store_path` record the most recent request_human_approval
    and register_approved_position calls regardless of outcome — purely for
    cli.session to populate a history.RunRecord after the run finishes; they
    have no bearing on the approval gate itself.
    """

    def __init__(self, client, position_register_store_id: str):
        self._client = client
        self._store_id = position_register_store_id
        self.approved_topics: dict[str, dict] = {}
        self.last_topic: str | None = None
        self.last_draft_position: str | None = None
        self.last_approval_status: str = "draft"
        self.last_memory_store_path: str | None = None

    def handle(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "request_human_approval":
            return self._request_human_approval(tool_input)
        if tool_name == "register_approved_position":
            return self._register_approved_position(tool_input)
        return json.dumps({"error": "unknown_tool", "name": tool_name})

    # -- request_human_approval ------------------------------------------------

    def _request_human_approval(self, tool_input: dict) -> str:
        topic = tool_input.get("policy_topic", "")
        print("\n" + "=" * 70)
        print("HUMAN APPROVAL REQUIRED")
        print("=" * 70)
        print(f"Topic:    {topic}")
        print(f"Question: {tool_input.get('policy_question', '')}")
        print("\nSummary:")
        print(textwrap.fill(tool_input.get("summary", ""), width=70))
        print("\nDraft position:")
        print(textwrap.fill(tool_input.get("draft_position", ""), width=70))
        print("=" * 70)

        decision = ""
        while decision not in ("y", "n"):
            decision = input(
                "Approve this draft position for Tejasvi Surya / senior team? [y/n]: "
            ).strip().lower()

        approved = decision == "y"
        notes = ""
        if not approved:
            notes = input("Notes for revision (optional): ").strip()
        approver = "Tejasvi Surya / senior team (console approval)"

        self.last_topic = topic
        self.last_draft_position = tool_input.get("draft_position", "")
        self.last_approval_status = "approved" if approved else "rejected"

        if approved:
            self.approved_topics[topic] = {
                "policy_question": tool_input.get("policy_question", ""),
                "draft_position": tool_input.get("draft_position", ""),
                "approver": approver,
                "approved_at": datetime.now(timezone.utc).isoformat(),
            }

        return json.dumps(
            {
                "approved": approved,
                "approver": approver if approved else None,
                "notes": notes or None,
            }
        )

    # -- register_approved_position --------------------------------------------

    def _register_approved_position(self, tool_input: dict) -> str:
        topic = tool_input.get("policy_topic", "")
        record = self.approved_topics.get(topic)
        if record is None:
            return json.dumps(
                {
                    "error": "not_approved",
                    "message": (
                        f"No approved request_human_approval result found for "
                        f"topic '{topic}' in this session. Call "
                        f"request_human_approval first and wait for "
                        f"approved=true before registering."
                    ),
                }
            )

        path, content = build_position_record(tool_input, record["approver"])
        try:
            memory = self._client.beta.memory_stores.memories.create(
                self._store_id,
                path=path,
                content=content,
            )
        except Exception as exc:  # noqa: BLE001 - surface any API error to the agent
            return json.dumps({"error": "write_failed", "message": str(exc)})

        self.last_memory_store_path = path

        return json.dumps(
            {
                "status": "registered",
                "memory_id": memory.id,
                "path": path,
            }
        )
