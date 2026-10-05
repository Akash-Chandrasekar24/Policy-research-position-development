---
name: official-policy-source-research
description: Retrieves and organizes official government and research sources for a policy question — bills, ministry documents, committee reports, budgets, datasets, peer-reviewed research, think-tank reports. Use whenever you need to establish the current factual and policy baseline before forming an opinion.
---

# Official Policy Source Research

Evidence for a policy position must come from identifiable sources, not
from general knowledge or plausible-sounding assertion. This skill governs
how to find and organize that evidence.

## Source priority order

1. **Primary government sources** — bills and draft legislation, ministry
   policy documents, parliamentary committee reports, questions and
   ministerial answers (Lok Sabha / Rajya Sabha), CAG and NITI Aayog
   reports, Union and Karnataka budgets, government consultation papers,
   official datasets and dashboards (data.gov.in, PRS Legislative Research
   summaries of bills).
2. **Research sources** — peer-reviewed research, university and research
   institution publications, think-tank reports (ORF, CPR, Takshashila,
   etc.), international organisation reports (OECD, World Bank, UN
   agencies), official policies from comparison countries.
3. Only fall back to general web search / commentary when neither of the
   above is available, and label it explicitly as secondary/unverified.

## Method

1. Use `web_search` / `web_fetch` (and the tender/MP-office MCP tools where
   attached) to retrieve primary documents first — search for the bill
   name, ministry name + "notification"/"report", or the specific dataset.
2. Extract the **current Indian policy position**: what law/regulation
   exists today, who administers it, what it actually says (not what
   commentary says it says).
3. Extract **existing sectoral regulations** that already touch this area
   — don't assume there's a regulatory vacuum without checking.
4. Extract **market and adoption data** — the concrete numbers (funding,
   users, incidents, spend) that make the policy question tangible.
5. Extract **research findings** — what independent research says about
   the effects of similar policies, here or elsewhere.
6. Extract **known implementation gaps** — where the current framework is
   acknowledged (by government or independent audits) to be failing.
7. Hand off every extracted claim to the `claim-evidence-mapping` skill's
   discipline (source + contradiction check) and `citation-and-fact-verification`
   before finalizing.

Every finding below must be cited with the literal source URL, not just a
source name — the office needs to be able to open the exact page.

## Output format

```
Current Indian policy position: <finding> (source URL)
Existing sectoral regulations: <finding> (source URL)
Market/adoption data: <finding> (source URL)
Research findings: <finding> (source URL)
Known implementation gaps: <finding> (source URL)
```

## Common failure modes to avoid

- Treating a news article's summary of a bill as equivalent to the bill
  text — go to the primary document when the decision is consequential.
- Presenting a single research paper's finding as consensus.
- Omitting the publication date — policy facts (draft vs. passed, in force
  vs. proposed) go stale fast.
