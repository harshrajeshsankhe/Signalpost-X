# Signalpost X

**Evidence-first company intelligence for Norwegian businesses.**

Signalpost X is a research pipeline built for the Signalpost company-intelligence challenge. It combines official Norwegian registry data with carefully verified company websites and external evidence to produce structured, auditable company profiles.

The system is designed around a simple rule:

> **If the evidence does not clearly belong to the company, it does not get published.**

---

## Overview

The Signalpost universe contains more than **411,000 eligible Norwegian companies**.

Signalpost X can process batches of organisation numbers and produce a complete JSONL result for every input company. The pipeline is built for repeatable runs, controlled web enrichment and incremental refreshes.

### What it provides

* Registry-backed company identity
* Financial information from official sources
* Roles and registered workplaces
* Group and company relationships
* First-party website research
* Structured external evidence
* Evidence timestamps and content hashes
* Request and runtime accounting
* Checkpoint and resume support
* Deterministic refresh and change detection
* One terminal result for every input company

The implementation deliberately favours **precision over unsupported coverage**.

---

## Architecture

The pipeline follows an evidence-first flow:

```text
Organisation Number
        │
        ▼
Brønnøysund Registry
        │
        ├── Company identity
        ├── Financial data
        ├── Roles
        ├── Workplaces
        └── Group relationships
        │
        ▼
Official Company Website
        │
        ├── Structured data
        ├── About / Contact
        ├── People
        ├── Jobs
        ├── News / Activity
        └── Site navigation
        │
        ▼
Identity Verification
        │
        ├── Verified → Publish
        └── Uncertain → Quarantine
        │
        ▼
Evidence-backed Company Profile
```

The organisation number is the primary identity key throughout the pipeline.

External information is treated as a candidate until it passes the identity checks. Similar names, parent companies, brands, franchises and unrelated businesses are not promoted as company evidence.

---

## Why the pipeline is structured this way

Company intelligence is not just a data collection problem. The difficult part is determining whether a piece of information actually belongs to the company being researched.

Signalpost X therefore separates:

1. **Discovery** — finding potentially useful information
2. **Verification** — determining whether it belongs to the target company
3. **Publication** — adding only sufficiently supported information to the final profile

This separation makes the system easier to audit and safer to extend with additional data sources.

---

## Data sources

The primary data foundation is the **Brønnøysund Register Centre**.

Website research uses the official website associated with the company record whenever available. The crawler prioritises structured and static content before considering more expensive retrieval strategies.

Additional discovery connectors can be enabled where the source permits automated access.

The project does **not** assume that an open-source library or publicly visible website automatically grants permission to scrape a platform. Source terms, robots policies, rate limits, licences and API requirements are treated as part of the connector configuration.

See:

* `docs/external-connectors.md`
* `docs/competition-control-loop.md`

---

## Repository structure

```text
Signalpost-X/
├── agent/
│   ├── site_intelligence.py
│   ├── high_recall.py
│   ├── winning_model.py
│   └── ...
│
├── scripts/
│   ├── run_competition_batch.py
│   ├── run_high_recall.py
│   ├── run_refresh_replay.py
│   ├── select_entry_batch.py
│   └── finalize_submission.py
│
├── tests/
│   └── fixtures/
│
├── docs/
│   ├── competition-control-loop.md
│   └── external-connectors.md
│
├── out/
├── run_signalpost_x.py
├── pyproject.toml
└── README.md
```

---

## Requirements

* Python **3.12+**
* `uv` recommended for environment management
* Internet access for live company research

Install the project with:

```bash
uv sync
```

---

## Quick start

The repository includes a deterministic refresh example that uses saved responses and does not require network access.

```bash
python3 scripts/run_refresh_replay.py \
  --manifest tests/fixtures/refresh-snapshots.json \
  --output out/refresh-demo.json
```

The generated report demonstrates material-change detection between two snapshots of the same company.

The example is intended as a reproducibility check. It is not a measure of live competition performance.

---

## Running a live batch

Download the required company data:

```bash
curl -L \
  'https://data.brreg.no/enhetsregisteret/api/enheter/lastned/csv' \
  -o brreg-enheter.csv

curl -L \
  'https://builderr.ai/signalpost-company-universe-2025.jsonl.gz' \
  -o signalpost-universe.jsonl.gz
```

Select the submission batch:

```bash
uv run python select_entry_batch.py \
  --universe signalpost-universe.jsonl.gz \
  --count 1000 \
  --output entry-companies.jsonl
```

For a small smoke test:

```bash
head -n 10 entry-companies.jsonl > smoke-companies.jsonl

uv run python scripts/run_competition_batch.py \
  --organisations smoke-companies.jsonl \
  --bulk brreg-enheter.csv \
  --profiles-output out/smoke-profiles.jsonl \
  --output out/smoke-envelopes.jsonl \
  --report out/smoke-report.json \
  --run-id smoke-001 \
  --expected-count 10
```

Once the smoke test is satisfactory, run the full batch:

```bash
uv run python scripts/run_competition_batch.py \
  --organisations entry-companies.jsonl \
  --bulk brreg-enheter.csv \
  --profiles-output out/profiles.jsonl \
  --output out/envelopes.jsonl \
  --report out/run-report.json \
  --run-id local-001 \
  --expected-count 1000
```

Run the test suite:

```bash
uv run --with pytest pytest -q
```

---

## Live submission runner

For a complete 1,000-company run, the repository also includes:

```bash
./RUN_LIVE_SUBMISSION.sh
```

The script handles the environment setup, data acquisition, batch selection, company processing and final validation.

The exact run configuration and generated reports are retained with the submission artifacts.

---

## Identity verification

Identity matching is deliberately conservative.

The strongest signals include:

* Exact organisation number
* Exact registered legal name
* Municipality consistency
* Registry-linked website
* Evidence from company-controlled pages

A candidate that cannot be confidently associated with the target organisation remains unverified rather than being published.

This is particularly important for:

* Companies with similar names
* Parent/subsidiary relationships
* Brands operating under another legal entity
* Franchises
* Former company names
* People with multiple business affiliations

---

## Web research strategy

Website retrieval follows a deterministic route plan.

Typical routes include:

```text
Company homepage
      ↓
Structured data
      ↓
Sitemap
      ↓
About / Contact
      ↓
People
      ↓
Jobs
      ↓
News / Activity
      ↓
Permitted external discovery
```

Static HTML is preferred because it is faster, cheaper and easier to reproduce.

Browser-based retrieval is reserved for cases where deterministic checks indicate that it is necessary.

---

## Evidence model

Each published claim is intended to remain traceable to its source.

Evidence records include information such as:

* Source URL
* Retrieval timestamp
* Reporting period where applicable
* Content hash
* Source type
* Verification status

The system distinguishes between information that is:

* available
* missing
* ambiguous
* blocked
* not applicable
* affected by a source error

These states are kept separate so that an unavailable data point is never silently converted into a guessed value.

---

## Refresh and change detection

Signalpost X supports comparison against previous company snapshots.

The refresh pipeline identifies material changes while avoiding noise from repeated or unchanged data.

The repository includes a saved replay fixture covering:

* expected material changes
* false-change prevention
* repeated execution
* evidence preservation

This provides a deterministic way to test the refresh logic without relying on live websites.

---

## Request and cost controls

The pipeline tracks operational metrics including:

* outbound requests
* request latency
* runtime
* external API usage
* third-party cost

The architecture is designed around the challenge limits and uses deterministic routing to avoid unnecessary requests.

---

## Testing

Run the complete test suite with:

```bash
uv run --with pytest pytest -q
```

The tests cover core identity handling, evidence processing, refresh behaviour, URL safety, output contracts and supporting pipeline components.

---

## Reproducibility

The project aims to make every important decision reproducible.

Strategies and thresholds are kept deterministic wherever possible. AI is not used as the authority for company identity or publication decisions.

Where AI-assisted ranking or synthesis is used, it operates on already collected and verified evidence rather than inventing or independently asserting company facts.

---

## Submission contract

A valid submission requires:

* At least 1,000 completed company profiles
* The exact organisation-number manifest used
* One documented batch command
* Exactly one terminal envelope per input
* Reproducible dependency setup
* Refresh input and material-change output
* Machine-readable run reporting
* Declared models and APIs
* Source and licence assumptions

The submitted repository contains the corresponding implementation and artifacts.

---

## Project status

**Submission batch:** 1,000 companies

**Submission commit:**

```text
826fe8b2c142eb7e7642f6cac74d45fde69e3c22
```

**Manifest SHA-256:**

```text
b7f3c4aff09bcceeac7178310a4b23db3687968026e4e0bd4e8e368c2eb57dd9
```

**Profiles SHA-256:**

```text
34214345e84298630653304c6a639551018cff669030b2117dd9cc21f9e00e03
```

---

## Design principles

The project follows a few principles throughout the implementation:

**Identity before enrichment.**

**Evidence before publication.**

**Precision before volume.**

**Deterministic decisions before probabilistic ones.**

**Missing information is better than incorrect information.**

**Every important claim should be explainable.**

---

## License

See the repository's source files and documentation for the applicable licences and third-party source terms.

This project is intended for the Signalpost challenge and should be operated within the terms and usage policies of every external source it accesses.
