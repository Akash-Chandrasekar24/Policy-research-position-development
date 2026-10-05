---
name: policy-question-framing
description: Converts a broad, ambiguous policy topic into one precise, decidable policy question with explicit scope, time horizon, and boundaries. Use this first, before any research begins, whenever the input is a topic ("AI regulation", "metro delays") rather than an already-specific question.
---

# Policy Question Framing

A broad topic cannot be researched — it has to be reduced to a specific
decision before evidence-gathering, stakeholder mapping, or option
generation can start. This skill is the first step of every policy
workflow in this office.

## Method

1. **Identify the real decision.** Ask: what choice is actually in front of
   the MP's office? A topic like "AI regulation" hides several different
   decisions (support/oppose a bill, push an amendment, raise a question in
   Parliament, take a public position). Name the decision explicitly.
2. **Narrow to one sharp question.** Convert the topic into a single
   sentence that could be answered "yes/no" or "option A vs B vs C" — not
   an open-ended essay prompt.
   - Broad: "AI regulation"
   - Framed: "Should India adopt a central AI law, or regulate high-risk AI
     through existing sector regulators?"
3. **Set the scope.** State what's in and explicitly what's out. A question
   about AI regulation is not automatically a question about data
   protection, platform liability, or chip export controls — say so if
   those are excluded.
4. **Set the time horizon.** Is this about the current Lok Sabha session, a
   bill expected within the year, or a multi-year policy direction? This
   changes which evidence and which options are relevant.
5. **Name the ministries/regulators involved.** e.g. MeitY, TRAI, RBI —
   whichever bodies actually have jurisdiction over the decision.
6. **List the concrete decisions required.** What does the office actually
   need to produce at the end — a position for a debate, an answer to a
   constituent, a vote recommendation, a press statement?
7. **State research boundaries.** What should the Evidence Research Agent
   NOT spend time on, because it's out of scope for this question?
8. **State the Bangalore South angle**, if one is already apparent at this
   framing stage (a local project, a past commitment, a constituent-facing
   effect) — this seeds the Karnataka/Bengaluru Impact Agent's work, even if
   later research refines or overturns it.

If this framing step relies on a specific fact (a bill number, a scheme
name, a deadline), cite the source URL for that fact — don't state it as
settled without one.

## Output format

```
Policy question: <one sentence, decidable>
Scope: <what's included>
Out of scope: <what's explicitly excluded>
Time horizon: <session / year / multi-year>
Ministries / regulators involved: <list>
Decisions required: <list>
Research boundaries: <list>
Bangalore South angle (if apparent): <finding, with source URL, or "none yet identified">
```

## Common failure modes to avoid

- Restating the topic as a question without narrowing it ("What should be
  done about AI regulation?" is not framed — it's the topic with a question
  mark).
- Silently assuming scope instead of stating it — a downstream agent should
  never have to guess what's in or out.
- Skipping the time horizon — a question about a bill currently in
  Parliament needs different evidence than a five-year policy direction.
