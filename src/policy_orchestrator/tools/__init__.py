"""Custom tools for the Policy Intelligence Orchestrator.

Two tools, both executed host-side (never inside the sandbox):

  - request_human_approval: pauses the session and asks a human operator
    (Tejasvi Surya / senior team) to allow/deny a draft position. This is
    the ONLY path by which a draft can become "approved".
  - register_approved_position: writes an approved position to the Policy
    Position Register memory store. Hard-gated on approval having actually
    been granted THIS SESSION — an agent cannot call this successfully
    without a prior `request_human_approval` call returning approved=true,
    regardless of what its prompt claims.

Split by concern:
    schemas    the tool contracts (name, description, input_schema) Claude sees
    handlers   the sync CLI implementation (PolicyToolHandler) that executes them

See examples/custom_tool.py in this repo for the base pattern (tool
definition + requires_action handling) this extends. The async web backend
(policy_orchestrator.web.manager) implements the same two tools independently
— see that module — but shares build_position_record() from handlers.py so
the two never drift on record format.
"""
from policy_orchestrator.tools.handlers import PolicyToolHandler, build_position_record
from policy_orchestrator.tools.schemas import (
    CUSTOM_TOOLS,
    REGISTER_APPROVED_POSITION,
    REQUEST_HUMAN_APPROVAL,
)

__all__ = [
    "PolicyToolHandler",
    "build_position_record",
    "CUSTOM_TOOLS",
    "REGISTER_APPROVED_POSITION",
    "REQUEST_HUMAN_APPROVAL",
]
