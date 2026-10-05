---
name: speech-and-question-conversion
description: Converts an approved or draft policy position into the office's Parliamentary Action Pack — questions for Parliament, committee intervention points, ministry meeting questions, amendments, speech points, and follow-ups. Use this in the final output-production step.
---

# Speech and Question Conversion

An analysis is only useful to a parliamentarian if it's converted into
things they can actually say or ask. This skill produces that conversion.

## Method

For the given position and its supporting evidence, produce:

1. **Questions for Parliament** — 2-4 draft questions (starred/unstarred
   style) that would extract useful information or put the position on
   record, addressed to the correct ministry.
2. **Committee intervention points** — if the topic falls under a standing
   committee's remit, 2-3 talking points suited to a committee discussion
   rather than the floor of the House.
3. **Ministry meeting questions** — pointed questions for a direct meeting
   with the relevant ministry/regulator, distinct in tone from public
   parliamentary questions (more technical, less rhetorical).
4. **Suggested amendments** — if a bill is actually in play, concrete
   amendment language reflecting the position's conditions/safeguards, not
   just a restatement of the position.
5. **Speech points** — 3-5 short, quotable points suitable for a floor
   speech, grounded in the cited evidence (never invent a statistic for
   rhetorical effect).
6. **Follow-up actions** — concrete next steps for the office (a written
   question to file, a stakeholder meeting to request, a follow-up date).

## Output format

```
Parliamentary questions:
  1. <question>
  ...
Committee intervention points: <bulleted>
Ministry meeting questions: <bulleted>
Suggested amendments: <text, or "not applicable — no active bill">
Speech points: <bulleted, each traceable to a cited fact>
Follow-up actions: <bulleted, with an owner/timeframe where possible>
```

## Common failure modes to avoid

- Writing generic questions that could apply to any topic rather than
  ones grounded in this specific evidence base.
- Producing speech points with numbers or claims that don't trace back to
  a citation from earlier in the pipeline.
