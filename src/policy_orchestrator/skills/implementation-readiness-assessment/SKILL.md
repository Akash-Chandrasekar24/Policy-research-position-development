---
name: implementation-readiness-assessment
description: Produces a realistic implementation timeline for each policy option, accounting for the legislative/regulatory process and institutional build-up required. Use this last in the options-evaluation sequence, after feasibility.
---

# Implementation Readiness Assessment

A recommendation without a realistic timeline invites the office to
over-promise. This skill forces a grounded estimate.

## Method

For each option, estimate the realistic path and duration:

1. **Process required** — which of these does the option require: cabinet
   approval, a bill through both houses, a rule/notification, a court
   ruling, or purely administrative action? Each has a different typical
   duration in the Indian legislative calendar.
2. **Sequencing dependencies** — does this option depend on something else
   happening first (a companion bill, a budget allocation, an institution
   being set up)?
3. **Realistic timeline** — give a range (not a false-precision single
   date), anchored to comparable past processes where possible (e.g. "the
   [comparable] Act took roughly N years from introduction to being in
   force").
4. **Near-term vs. long-term milestones** — what could realistically happen
   in the current session/year vs. what is a multi-year horizon.

## Output format

```
Option: <name>
Process required: <steps>
Dependencies: <list, or "none identified">
Realistic timeline: <range, with the comparable precedent it's anchored to (source URL)>
Near-term milestone: <what's achievable soon>
```

## Common failure modes to avoid

- Giving a specific date ("by March 2027") without basis — use ranges
  anchored to precedent instead.
- Naming a comparable precedent without linking to the source that
  establishes its actual timeline.
- Ignoring dependencies that would actually block the timeline (e.g.
  assuming a regulator will be adequately staffed without evidence).
- Treating "administrative action only" as automatically fast — some
  administrative processes (inter-ministerial consultation) take longer
  than expected.
