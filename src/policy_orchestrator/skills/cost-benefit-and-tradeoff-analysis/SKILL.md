---
name: cost-benefit-and-tradeoff-analysis
description: Evaluates each policy option's benefits, risks, cost, and stakeholder/constituency impact honestly — including for the option you expect to end up recommending. Use this after policy-option-generation, before feasibility assessment.
---

# Cost-Benefit and Trade-off Analysis

Every option has a real cost. This skill's job is to make that cost
visible for every option, including the one that will likely end up
recommended — an option with no stated downside has not actually been
analyzed.

## Method

For each option produced by `policy-option-generation`, assess:

1. **Benefits** — what does this option actually achieve, and for whom?
   Be specific (whose problem does it solve, how much).
2. **Risks** — what could go wrong, backfire, or be exploited? Include
   risks the option's proponents would rather not emphasize.
3. **Cost** — implementation cost, compliance cost for affected parties,
   and opportunity cost (what doesn't happen if this is chosen).
4. **Stakeholder impact** — pull directly from `stakeholder-position-analysis`:
   who gains, who loses, and by how much.
5. **Karnataka/Bengaluru impact** — pull directly from
   `karnataka-bengaluru-impact-assessment`: is this option better or worse
   for the constituency specifically than the alternatives?

Any cost figure, statistic, or precedent used in this analysis must carry
its literal source URL — an unsourced number is a guess, not evidence.

## Output format

For each option:
```
Option: <name>
Benefits: <list>
Risks: <list>
Cost: <estimate or qualitative if no number exists — state which, with source URL if sourced>
Stakeholder impact: <summary, gains/losses by group>
Karnataka/Bengaluru impact: <summary, with source URL for any cited figure>
```

## Common failure modes to avoid

- Writing a thorough risk list for the option you don't expect to
  recommend, and a thin one for the option you do — apply the same rigor
  to all options.
- Presenting cost estimates without stating whether they're sourced,
  modeled, or a rough qualitative judgment — and without the source URL
  when one exists.
- Confusing "this option has no stated risk" with "this option has no
  risk" — if you can't find a risk, say you looked and found none, rather
  than omitting the field.
