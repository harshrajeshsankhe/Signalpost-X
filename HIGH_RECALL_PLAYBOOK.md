# Signalpost X — High-Recall Competition Playbook

## Objective

Maximize external company-information recall while preserving the challenge's exact-company precision gate.

## Pipeline

1. **Identity anchor** — organisation number is the immutable key.
2. **Official base** — registry, accounting, roles, group and locations are populated from the supplied official snapshot/connectors.
3. **Website enrichment** — crawl the registry website with bounded same-domain traversal.
4. **Identity firewall** — a site is publishable only after an exact-entity assessment. Structured data alone never proves identity.
5. **Discovery** — optional Brave search is used only for missing websites; search results are transient and the selected site is independently fetched before promotion.
6. **External signals** — company-site job/activity/people navigation is retained as evidence hints; it is not silently converted into unsupported facts.
7. **Refresh** — content hashes and prior evidence are preserved so changes can be detected without duplication.
8. **Audit** — every daily run must emit exactly the evaluator-requested number of terminal envelopes, including unavailable/ambiguous states.

## Run

Base competition run:

```bash
uv run python run_signalpost_x.py \
  --organisations out/entry-companies.jsonl \
  --bulk brreg-enheter.csv \
  --out out/competition \
  --expected-count 1000 \
  --workers 8
```

High-recall website enrichment:

```bash
uv run python run_signalpost_x.py \
  --organisations out/entry-companies.jsonl \
  --bulk brreg-enheter.csv \
  --out out/competition \
  --expected-count 1000 \
  --workers 8 \
  --high-recall \
  --site-pages 12
```

Missing-website discovery is optional and requires a permitted provider/API key:

```bash
BRAVE_SEARCH_API_KEY='...' uv run python run_signalpost_x.py \
  --organisations out/entry-companies.jsonl \
  --bulk brreg-enheter.csv \
  --out out/competition \
  --expected-count 1000 \
  --workers 8 \
  --with-brave \
  --brave-limit 1000 \
  --high-recall
```

## Budget policy

For the evaluator's 100-company daily run, keep a hard request budget below 2,000 and declared external API spend below $10. Prefer official/registry sources, cache immutable responses, avoid repeated URLs, and stop enrichment when the marginal request cannot materially improve recall.

## Precision policy

Never infer:

- employees = 0 when unknown;
- revenue/profit from snippets;
- a person belongs to a company because of a same-name match;
- a job belongs to a company without exact company evidence;
- a website belongs to a company from domain similarity alone.

If identity cannot be proven, emit `ambiguous` or `not_available` rather than publishing the candidate.

## Submission gate

Before sending the email to Builderr, freeze the exact repository commit and verify:

- 1,000 completed profiles;
- organisation-number manifest exactly matches the profiles;
- source URL + retrieval date + reporting period for claims;
- exactly 100 terminal envelopes in each daily-test simulation;
- no duplicate organisation numbers;
- no material wrong-company matches;
- request/cost budget compliance;
- refresh replay demonstrates true-change detection and idempotence;
- README contains one-command execution instructions;
- APIs/models/licences and expected cost per 100 companies are documented.
