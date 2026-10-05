---
name: policy-position-development
description: Drafts a recommended policy position from evaluated options, with rationale, safeguards, and a stated confidence level. This is pass 1 of position drafting — always follow it with policy-position-red-teaming before finalizing.
---

# Policy Position Development (Pass 1)

This skill turns evaluated options into one recommended [Draft position] —
never an [Approved position]; only the human-approval workflow can create
that label.

## Method

1. **Select the recommended option** from those evaluated by
   `cost-benefit-and-tradeoff-analysis`, `legal-and-institutional-feasibility`,
   and `implementation-readiness-assessment` — usually the one with the best
   balance, not necessarily the one with zero downsides (none will have
   zero downsides).
2. **Write the position as a clear, quotable statement** the MP could
   actually say — not a hedge-everything paragraph. e.g.: "Support a hybrid
   AI governance model with common national principles, mandatory
   safeguards for high-risk systems, and sector-specific implementation."
3. **State the rationale** — the 2-4 strongest reasons this option was
   chosen over the alternatives, referencing the evidence and trade-off
   analysis. Carry forward the literal source URLs those upstream agents
   cited — do not restate a finding without its citation.
4. **State explicit conditions/safeguards** — what has to be true or in
   place for this position to hold (e.g. "contingent on an independent
   testing regime" or "provided compliance thresholds scale with company
   size").
5. **State a confidence level** — High / Medium / Low, based on how
   contested the evidence and stakeholder landscape were.
6. Label the output clearly: **[Draft position]** — never claim it is the
   MP's or office's actual position.

## Output format

```
[Draft position]: <the quotable statement>
Rationale: <2-4 reasons, each with the source URL it's based on>
Conditions and safeguards: <list>
Confidence level: High/Medium/Low — <why>
```

## Next step

Always pass this draft to `policy-position-red-teaming` before it goes
anywhere near the human-approval step — a draft that hasn't been
challenged is not ready for review.
