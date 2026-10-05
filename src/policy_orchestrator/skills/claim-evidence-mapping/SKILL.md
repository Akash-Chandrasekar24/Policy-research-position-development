---
name: claim-evidence-mapping
description: Separates verified facts from opinion/commentary and flags contradictions between sources. Use this while assembling evidence, before it's handed to option generation or position drafting.
---

# Claim-Evidence Mapping

Raw search results mix facts, official claims, advocacy framing, and
speculation. This skill is the discipline of keeping those separate so
downstream agents don't accidentally treat opinion as fact.

## Method

1. For every claim you plan to use, classify it as one of:
   - **Fact** — independently verifiable (a statute's text, a published
     statistic, a dated government notification).
   - **Official claim** — stated by a government/ministry/company but not
     independently verified (e.g. a ministry's own estimate of a scheme's
     impact).
   - **Opinion/advocacy** — a stakeholder's or commentator's interpretation
     or recommendation.
2. For each **fact**, note the source and, where possible, a second source
   that corroborates it. If you cannot find a second source, say so rather
   than presenting single-sourced facts with unwarranted confidence.
3. Actively look for **contradicting evidence** — a source that disagrees
   with the claim you're about to record. Don't just search until you find
   support for the expected answer; search enough to know if the picture is
   contested.
4. When two credible sources disagree, record both positions and the
   disagreement itself as a finding — do not silently pick the one that
   fits the narrative.
5. Timestamp every claim with the source's publication date so staleness
   is visible later.

## Output format

```
Claim: <statement>
Type: Fact | Official claim | Opinion/advocacy
Source(s): <citation(s)>
Corroborated: yes/no
Contradicted by: <source, if any> — <what it says instead>
```

## Common failure modes to avoid

- Laundering an advocacy group's framing into the evidence base as if it
  were a neutral fact.
- Reporting only the evidence that supports the position you suspect is
  right (motivated search).
- Merging "the ministry claims X" and "X is independently verified" into
  one undifferentiated bullet point.
