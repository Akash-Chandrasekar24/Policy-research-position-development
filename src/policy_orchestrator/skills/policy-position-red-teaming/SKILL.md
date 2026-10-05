---
name: policy-position-red-teaming
description: Challenges a drafted policy position by actively looking for contradicting evidence, likely opposition, unintended effects, and feasibility gaps. This is pass 2 of position drafting — always run it immediately after policy-position-development, on the same draft, before it reaches the human-approval step.
---

# Policy Position Red-Teaming (Pass 2)

A position that has only been argued for, never argued against, is not
ready to be shown to a human reviewer. This skill is an adversarial pass
against the office's own draft.

## Method

Ask each question explicitly and answer it honestly — do not skip a
question because the answer is inconvenient:

1. **What evidence contradicts this position?** Go back through the
   evidence base specifically looking for what was under-weighted. Cite
   the literal source URL for any counter-evidence you surface.
2. **Who is likely to oppose this, and why?** Not just "some stakeholders"
   — name which ones from the stakeholder map, and their strongest
   argument.
3. **What unintended effects could this position produce?** Second-order
   consequences the rationale didn't consider.
4. **Is this legally and administratively feasible?** Re-check against
   `legal-and-institutional-feasibility` — does the draft's confidence
   match what that analysis actually found?
5. **Can the MP defend this under hostile questioning?** Simulate the
   toughest likely question in Parliament or from the press, and check
   whether the draft survives it.

## Method — revising the draft

- If red-teaming surfaces a serious weakness, **revise the draft position
  or add explicit caveats** — don't just note the weakness and leave the
  original draft unchanged.
- If red-teaming shows the primary draft is genuinely weak, **produce an
  alternative position** rather than forcing the original through.
- Update the confidence level from `policy-position-development` if the
  red-team pass changes how solid the position looks.

## Output format

```
Weaknesses found: <list, with the specific counter-evidence/opposition/effect and its source URL>
Feasibility re-check: <consistent with pass 1? if not, what changed>
Revised [Draft position] (if changed): <statement>
Alternative position (if pass 1's draft doesn't hold up): <statement>
Updated confidence level: High/Medium/Low
```

## Common failure modes to avoid

- Treating red-teaming as a formality — writing one weak counterargument
  and immediately dismissing it.
- Not actually updating the draft or confidence level even when red-teaming
  found something substantial.
