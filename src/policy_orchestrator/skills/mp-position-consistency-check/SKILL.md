---
name: mp-position-consistency-check
description: Compares a drafted position against the MP's prior public record (speeches, questions, approved positions) and flags — without silently resolving — any conflict with a past position. Use this during position red-teaming, before a draft reaches human approval.
---

# MP Position Consistency Check

A new position that quietly contradicts something the MP said publicly
last year is a problem the office needs to know about *before* it's
published, not after a journalist finds it.

## Method

1. **Check the MP Policy Profile knowledge base** for prior speeches,
   parliamentary questions, committee interventions, and previously
   approved positions on this or closely related topics.
2. **Check the live MP-office site** (via the `mp_office_updates` MCP tool,
   where attached — `page="parliamentary_work"` or `"blog"`) for anything
   more recent than the knowledge base.
3. **Compare directly.** Does the new draft position agree with, refine, or
   contradict the prior record?
4. **If there is a genuine conflict, flag it explicitly** — state what the
   prior position was, what the new draft says, and how they differ. Do
   **not** silently soften the new draft to avoid the conflict, and do
   **not** silently ignore the prior position. The human reviewer decides
   whether this is an intentional, defensible evolution or a problem to
   fix.
5. **If the new draft is consistent** or is a natural extension of prior
   positions, say so explicitly too — this is useful confirmation, not
   just an absence of a flag.

## Output format

```
Prior related position(s) found: <summary, with source URL and date, or "none found">
Consistency assessment: Consistent / Extends prior position / CONFLICTS with prior position
If conflict: <what changed and why it matters for review>
```

## Common failure modes to avoid

- Treating "I didn't find a prior position" as proof none exists — say
  explicitly that none was found in the sources checked, since absence of
  evidence isn't evidence of absence.
- Resolving an apparent conflict yourself by rewording the draft, instead
  of surfacing it for the human reviewer to decide.
