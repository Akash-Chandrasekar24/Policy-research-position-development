---
name: sensitivity-and-confidentiality-review
description: Screens content for anything that shouldn't be made public yet — unconfirmed claims, internal deliberation, unapproved positions — before it's written to any public-facing output. Use this as the last check before producing the Public Communication Pack, and before writing any output file.
---

# Sensitivity and Confidentiality Review

Internal deliberation (weaknesses surfaced by red-teaming, rejected
alternative positions, unconfirmed evidence) must never leak into
public-facing material. This skill is that gate.

## Method

Before any content is written to `/mnt/session/outputs/`, check it against
this list:

1. **Approval status** — is this content about a position that is still
   [Draft position], or has it actually been marked [Approved position]?
   The **Public Communication Pack** may only be produced for an
   [Approved position]. Everything else (Policy Snapshot, Detailed Brief,
   Decision Matrix, Position Note, Parliamentary Action Pack) is for
   internal office use regardless of approval status, and should say so.
2. **Internal deliberation** — remove or exclude red-teaming weaknesses,
   rejected alternative options, and internal confidence caveats from
   anything public-facing. These are valuable for the office's internal
   Detailed Policy Brief; they are not for a citizen explainer or press
   Q&A.
3. **Unverified claims** — anything flagged `[UNVERIFIED]` by
   `citation-and-fact-verification` must not appear in public-facing
   material stated as fact.
4. **Attribution discipline** — never state or imply "this is Tejasvi
   Surya's position" for anything short of an actual [Approved position].
   Internal documents use [Draft position] / [AI recommendation] /
   [Policy option] / [Research finding] labels; public documents, once
   approved, may state the position as the office's own.
5. **Constituent/personal data** — if any input evidence included
   constituency representations naming private individuals, ensure no
   personal information ends up in public-facing output without a clear
   need and, ideally, without the office's separate sign-off.

## Output format

A short pass/fail note per output file:
```
File: <name>
Contains only approved-position content where required: yes/no
Internal deliberation excluded: yes/no
Unverified claims excluded or flagged: yes/no
Cleared for its intended audience (internal / public): yes/no — <notes if no>
```

## Common failure modes to avoid

- Generating the Public Communication Pack for a position that is still
  only [Draft position].
- Copy-pasting language from the Detailed Policy Brief (which may include
  internal caveats) directly into a citizen explainer without this review.
