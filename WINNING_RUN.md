# Signalpost X — final winning-run protocol

## Goal
Maximise external recall while keeping exact-company precision above the 95% hard gate.

## 1. Install
```bash
uv sync
```

## 2. Prepare the supplied frozen BRREG snapshot
Use the Builderr-supplied snapshot exactly as provided. Do not substitute a different universe.

## 3. Generate the 1,000 submitted profiles
```bash
python run_signalpost_x.py \
  --organisations out/entry-companies.jsonl \
  --bulk /PATH/TO/BRREG_SNAPSHOT.csv \
  --out out/final-1000 \
  --run-id signalpost-x-final-1000 \
  --expected-count 1000 \
  --workers 8 \
  --high-recall \
  --site-pages 8
```

The resulting `profiles.jsonl` is the submitted profile set. Do not label a profile complete unless it has the required evidence structure; missing information remains explicit.

## 4. Run the daily-test simulation
```bash
python run_signalpost_x.py \
  --organisations /PATH/TO/DAILY_100.jsonl \
  --bulk /PATH/TO/BRREG_SNAPSHOT.csv \
  --out out/daily-test \
  --run-id signalpost-x-daily-test \
  --expected-count 100 \
  --workers 8 \
  --high-recall \
  --site-pages 8
```

For discovery, set `BRAVE_SEARCH_API_KEY` only if a permitted Builderr-approved configuration is being used and cost is recorded.

## 5. Final gate
```bash
python scripts/finalize_submission.py \
  --profiles out/final-1000/profiles.jsonl \
  --manifest out/entry-companies.jsonl \
  --envelopes out/daily-test/envelopes.jsonl
```

A non-zero exit means the package is **not** submission-ready.

## 6. Freeze
After all validation passes, create one immutable Git commit and record its exact SHA. Do not change code after freezing.

## Competition constraints
- 100 terminal envelopes exactly for each daily batch.
- 45-minute wall-clock limit.
- 2,000 outbound-request maximum.
- $10 maximum declared external API spend per daily batch.
- 95%+ external precision and no material wrong-company publication.
- 60%+ weighted external company recall.
- Preserve source, retrieval time and reporting period.
- Idempotent refresh and preserved previous evidence.
