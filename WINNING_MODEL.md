# Signalpost X — 80+ Winning Model

## Core strategy

**Evidence-First Hybrid Ensemble**:

1. **BRREG / official filings are the canonical identity and financial layer.**
2. **Company-owned pages are the primary external layer.**
3. **Structured data + sitemap discovery comes before broad crawling.**
4. **Jobs, people and activity are targeted separately rather than crawling blindly.**
5. **Licensed/search discovery is used only when the official website is missing.**
6. **No LLM is allowed to decide company identity or invent a claim.**
7. Any optional LLM is a *ranking/summarisation layer over already captured evidence*.

## Why this should outperform a simple crawler

Builderr awards 35 points for coverage and 30 for accuracy, with a 60% weighted external-company-recall gate and 95% external precision gate. The correct optimisation is therefore **marginal evidence gained per request while preserving identity precision**, not maximum page count.

## Publication firewall

A fact may be published only when one of these holds:

- exact organisation number appears in the evidence; or
- full legal-name match + municipality match; or
- very strong legal-name match + at least two independent identity signals.

Otherwise the evidence is quarantined as `ambiguous` / `not_available`.

## Route order

`company_home → structured_data → sitemap_targeted → about/contact → people → jobs → news/activity → licensed_search_discovery`

The route planner is deterministic and budget-aware.

## 100-company budget

Hard constraints:

- 45 minutes
- 2,000 outbound requests
- $10 declared external API spend
- exactly 100 terminal envelopes

Use concurrency for independent companies, but keep per-company page budgets bounded. Cache by URL/content hash and never spend repeated requests on unchanged sources.

## 80+ target profile

The target is not a guaranteed score. It is an engineering target based on the published rubric:

- Coverage: maximise unique verified external companies and claims.
- Accuracy: preserve ≥95% precision through the identity firewall.
- Refresh: immutable prior snapshots + deterministic diffs + idempotent reruns.
- Synthesis: explain what changed, what is known, and what remains unknown.
- UX: search → profile → evidence → change history in one flow.

A real 80+ result must be demonstrated by Builderr's frozen daily test; it cannot be claimed from local fixture tests.
