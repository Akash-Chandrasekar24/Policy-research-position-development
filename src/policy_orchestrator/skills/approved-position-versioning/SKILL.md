---
name: approved-position-versioning
description: Formats a human-approved position to match the Policy Position Register's schema so it can be registered verbatim as institutional memory. Use this only after human approval has actually been granted, immediately before calling the register_approved_position tool.
---

# Approved Position Versioning

The Policy Position Register (KB5) is the office's institutional memory of
what's actually been approved. This skill governs the exact record format
so the register stays consistent and usable over time — and it only
applies once approval has genuinely happened.

## Precondition

This skill applies **only** after `request_human_approval` has returned
`approved: true` for this exact topic in this session. If that hasn't
happened, there is nothing to version — go back to
`policy-position-development` / `policy-position-red-teaming` instead.

## Method

Assemble the record with exactly these fields:

1. **Policy topic** — short label, matching the one used in the approval
   request.
2. **Policy question** — the precise question from `policy-question-framing`.
3. **Approved position** — the exact position text that was approved (not
   a paraphrase).
4. **Supporting evidence** — a brief pointer to the key evidence backing
   it, including the literal source URL(s) (not the full brief — a
   pointer, but a clickable one).
5. **Conditions and safeguards** — carried over from the draft, updated if
   the reviewer's approval included changes.
6. **Date approved** — the actual approval date.
7. **Approver** — name/role of the human who approved it, exactly as
   returned by the approval step.
8. **Previous version** — what the prior registered position on this exact
   topic was, if any (check the register, which is read-only to you, before
   assuming there isn't one).
9. **Reason for change** — if this supersedes a prior version, state why
   the position changed; if there's no prior version, state "N/A".
10. **Related speeches and questions** — pointers to related past or
    newly-generated parliamentary material, if any.

## Output

Hand the assembled record to the `register_approved_position` tool exactly
as fields 1-10 above — the tool itself enforces that approval actually
happened and performs the write; this skill's job is only to get the
record format right.

## Common failure modes to avoid

- Calling this skill (or the register tool) before approval was actually
  granted — the tool will reject it, and doing so anyway wastes a turn.
- Paraphrasing the approved position instead of recording it verbatim.
- Failing to check for and reference a genuine previous version when one
  exists.
