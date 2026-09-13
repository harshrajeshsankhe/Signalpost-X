# Signalpost X — competition agent

A precision-first extension of Builderr's Signalpost starter kit. It keeps the starter's official Brønnøysund pipeline and adds:

- deterministic, stratified 1,000+ company selection;
- a company-identity firewall before external publication;
- bounded company-site deep crawl using robots and same-registered-domain checks;
- structured-data extraction without trusting it as identity proof;
- source/evidence normalization with content hashes;
- optional transient Brave discovery for missing websites (only when `BRAVE_SEARCH_API_KEY` is supplied);
- refresh replay and deterministic change detection;
- request/time/cost budgets;
- local audit reports for precision-risk cases.

## Quick start

```bash
uv sync
python3 agent/select_stratified.py --universe signalpost-company-universe-2025.jsonl.gz --count 1000 --output out/entry-companies.jsonl
```

For the official live pipeline, follow the Builderr starter's BRREG snapshot instructions, then:

```bash
uv run python scripts/run_competition_batch.py \
  --organisations out/entry-companies.jsonl \
  --bulk brreg-enheter.csv \
  --profiles-output out/profiles.jsonl \
  --output out/envelopes.jsonl \
  --report out/run-report.json \
  --run-id signalpost-x-001 \
  --expected-count 1000 \
  --workers 8
```

Optional missing-website discovery:

```bash
export BRAVE_SEARCH_API_KEY='...'
uv run python scripts/run_brave_discovery.py \
  --input out/profiles.jsonl \
  --output out/profiles-discovered.jsonl \
  --report out/discovery-report.json \
  --limit 100 \
  --promote-verified
```

Do not enable a connector unless its provider terms, robots policy, rate limits and evidence-retention rights permit the intended use. Search-provider output is treated as transient by the included Brave adapter.

## Competition design

The agent optimizes qualification before raw recall:

1. exact organisation number is the immutable company key;
2. official registry/financial/role/location evidence is the base layer;
3. websites and external candidates are quarantined until independently verified;
4. unsupported facts are omitted rather than guessed;
5. every published claim has source URL, retrieval time and reporting/effective period where applicable;
6. refreshes compare content/value and preserve previous snapshots.

No system can guarantee a win against a hidden daily test. This repository is designed to maximize the probability of qualifying while leaving an auditable path for iterative score improvement.
