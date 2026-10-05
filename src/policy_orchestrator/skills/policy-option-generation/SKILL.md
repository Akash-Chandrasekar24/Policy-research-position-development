---
name: policy-option-generation
description: Generates 2-4 genuinely distinct, defensible policy options instead of one predetermined answer. Use this before trade-off analysis, feasibility, and implementation assessment.
---

# Policy Option Generation

A single "recommended answer" presented without alternatives hides the
real trade-offs from the person who has to defend it. This skill forces at
least two genuinely different options onto the table.

## Method

1. Generate options that differ in **substance**, not just wording — e.g.
   for a regulation question: a centralized-law option, a
   sector-regulator option, and a hybrid option are substantively
   different; three versions of "regulate more" are not.
2. Each option must be **plausible and defensible** — no straw-man options
   included only to make another option look better by comparison.
3. Typical option shapes for regulatory questions:
   - **Option A**: a single centralized framework (consistency, higher
     implementation burden).
   - **Option B**: distributed/sector-specific implementation (flexible,
     risk of inconsistency).
   - **Option C**: a hybrid — common principles nationally, sector-specific
     enforcement (balances the two, needs strong coordination).
4. For non-regulatory questions (spending, a public statement, a
   parliamentary intervention), adapt the same discipline: what are the
   genuinely different postures the MP could take, not just different
   phrasings of the same posture?
5. Hand every option to `cost-benefit-and-tradeoff-analysis`,
   `legal-and-institutional-feasibility`, and
   `implementation-readiness-assessment` for full evaluation — this skill's
   job is only to generate the options, not evaluate them.
6. If an option is modeled on a specific precedent (an existing bill, a
   comparator country's law from `global-policy-benchmarking`), cite its
   source URL when naming it — don't describe a real precedent without
   linking to it.

## Output format

```
Option A: <name>
  Description: <what it actually entails>
Option B: <name>
  Description: <what it actually entails>
Option C (if applicable): <name>
  Description: <what it actually entails>
```

## Common failure modes to avoid

- Generating one real option and two thin variations of it to create the
  appearance of choice.
- Skipping a hybrid/middle option when one plausibly exists.
- Letting the framing of an option smuggle in the evaluation (e.g. naming
  an option "the reckless deregulation option") — keep names neutral.
