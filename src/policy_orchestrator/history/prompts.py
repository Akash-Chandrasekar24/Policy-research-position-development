"""Task-text builders shared by cli.session and web.manager, so the two
runtimes phrase a fresh run and a "check for updates" refresh run
identically.
"""
import textwrap

from policy_orchestrator.history.models import RunRecord


def build_task_text(question: str) -> str:
    return (
        "Produce a full policy analysis and, if a draft position is "
        "approved through the human-approval step, the full set of office "
        "outputs, for the following policy question.\n\n"
        f"POLICY QUESTION: {question}"
    )


def build_refresh_task_text(question: str, match: RunRecord) -> str:
    asked_on = f"{match.created_at:%Y-%m-%d}" if match.created_at else "an earlier date"
    return textwrap.dedent(
        f"""
        The office previously researched a closely related question on {asked_on}
        (topic: "{match.topic or 'unrecorded'}"):

        PRIOR QUESTION: {match.question}
        PRIOR POSITION ({match.approval_status}): {match.draft_position or '(none recorded)'}

        Do not repeat research that has not changed. Focus on what is new or
        different since {asked_on}: check for developments in the evidence,
        any changed stakeholder positions, and whether the prior position
        still holds. 
        
        CRITICAL: In your final [Draft position] and summary, you MUST explicitly compare the new findings to the prior position. Use phrases like "This was the policy before...", "Now it has progressed to..." or "This is the update...".

        Either confirm the prior position still stands (with a note on what you checked) or produce an updated [Draft position].
        Still route any position through the request_human_approval step as
        normal before it can be treated as approved.

        POLICY QUESTION: {question}
        """
    ).strip()
