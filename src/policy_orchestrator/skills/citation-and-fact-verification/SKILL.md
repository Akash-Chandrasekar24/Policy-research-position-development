---
name: citation-and-fact-verification
description: Attaches a verifiable citation (source and date/version) to every factual claim, and flags anything that couldn't be verified from a primary or credible source. Use this continuously while assembling evidence, not as a one-time end-of-task check.
---

# Citation and Fact Verification

An unsourced factual claim in a policy brief is a liability — it can be
challenged and, if wrong, discredits the whole document. This skill is the
verification discipline applied to every claim before it's used.

## Method

1. **Every factual claim gets a citation with a literal, clickable URL** —
   not just a source name. At minimum: the URL, and a date or version (bill
   version, report publication date, dataset as-of date). "According to
   [source] (https://...), as of [date], ..." is the target shape, not "It
   is known that..." and not "According to [source]" with no link. If the
   source genuinely has no stable URL (e.g. an in-person briefing), say so
   explicitly instead of citing a source name as if it were a link.
2. **Prefer primary sources.** A ministry's official notification beats a
   news article summarizing it; the bill text beats a think-tank's
   description of the bill.
3. **If you could not verify a claim from a primary or credible source,
   say so explicitly** — label it "unverified" rather than presenting it
   with the same confidence as a sourced claim. Do not drop it silently if
   it seems important; flag it so a human can decide whether to chase it
   down further.
4. **Check for version drift.** A bill, draft rule, or report may have been
   revised since a source was published — note the version/date so later
   readers know whether it's still current.
5. **Distinguish "I found this stated somewhere" from "I confirmed this is
   currently true"** — the latter requires checking the source is still
   current, not just that it once said this.

## Output format

Inline with each claim: `<claim> (https://source-url, date/version)` or
`<claim> [UNVERIFIED — could not confirm from a primary/credible source]`.

## Common failure modes to avoid

- Citing a source that doesn't actually say what the claim states (citation
  padding).
- Treating a claim as verified because it appears in multiple places that
  all trace back to the same original (unverified) source.
- Silently dropping a claim that couldn't be verified instead of flagging
  it as unverified for human review.
- Naming a source ("per a ministry notification") without its URL, or
  inventing a URL when the real one couldn't be found — say "source URL
  unavailable" instead.
