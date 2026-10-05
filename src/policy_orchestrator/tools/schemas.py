"""Tool contracts (the JSON schemas Claude sees) for the two custom tools.

No logic here — see handlers.py for execution.
"""

REQUEST_HUMAN_APPROVAL = {
    "type": "custom",
    "name": "request_human_approval",
    "description": (
        "Ask a human reviewer (Tejasvi Surya or the senior team) to approve "
        "or reject a drafted policy position before it can be treated as "
        "official. You MUST call this before treating any position as "
        "approved, and MUST wait for its result rather than assuming "
        "approval. Do not call this more than once per distinct draft "
        "position in a session."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "policy_topic": {
                "type": "string",
                "description": "Short topic label, e.g. 'AI regulation in India'.",
            },
            "policy_question": {
                "type": "string",
                "description": "The precise policy question being decided.",
            },
            "draft_position": {
                "type": "string",
                "description": "The recommended [Draft position] text in full.",
            },
            "summary": {
                "type": "string",
                "description": (
                    "A short (3-5 sentence) summary of the rationale, main "
                    "risk, and confidence level, for a busy reviewer."
                ),
            },
        },
        "required": ["policy_topic", "policy_question", "draft_position", "summary"],
    },
}

REGISTER_APPROVED_POSITION = {
    "type": "custom",
    "name": "register_approved_position",
    "description": (
        "Commit an approved policy position to the Policy Position Register "
        "(the office's institutional policy memory). This will FAIL unless "
        "request_human_approval was already called for this exact topic in "
        "this session and returned approved=true. Only the orchestrator "
        "should call this — never a subagent."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "policy_topic": {
                "type": "string",
                "description": "Must match the topic passed to request_human_approval.",
            },
            "policy_question": {"type": "string"},
            "approved_position": {"type": "string"},
            "supporting_evidence": {
                "type": "string",
                "description": "Brief pointer to the key evidence backing this position.",
            },
            "conditions_and_safeguards": {"type": "string"},
            "approver": {
                "type": "string",
                "description": "Name/role of the human who approved this, e.g. 'Tejasvi Surya'.",
            },
            "previous_version": {
                "type": "string",
                "description": "Optional: what the prior position on this topic was, if any.",
            },
            "reason_for_change": {
                "type": "string",
                "description": "Optional: why the position changed from a prior version, if applicable.",
            },
            "related_speeches_and_questions": {
                "type": "string",
                "description": "Optional: pointers to related past speeches/parliamentary questions.",
            },
        },
        "required": [
            "policy_topic",
            "policy_question",
            "approved_position",
            "approver",
        ],
    },
}

CUSTOM_TOOLS = [REQUEST_HUMAN_APPROVAL, REGISTER_APPROVED_POSITION]
