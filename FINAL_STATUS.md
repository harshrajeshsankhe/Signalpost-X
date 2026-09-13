# Final status — Signalpost X

## What is verified locally

- 1,000-company deterministic manifest is present.
- Manifest contains 1,000 unique organisation numbers.
- Selection audit: `risk_count = 0`.
- Python source compilation passes.
- Refresh replay fixture: 2 expected changes, 2 true positives, 0 false positives, 0 false negatives, precision 1.0, recall 1.0, idempotent rerun true.
- A local Git commit exists for the current codebase.

## What cannot be honestly marked complete in this environment

The supplied 1,000-row `out/entry-companies.jsonl` is a **selection manifest**, not 1,000 completed evidence-backed profiles. The Builderr qualification rules require at least 1,000 completed profiles and a frozen 100-company daily test. This environment has no outbound network access, so the live Brønnøysund bulk snapshot and company websites cannot be fetched here.

Therefore this repository deliberately does **not** fabricate a passing score or pretend that the 1,000 profiles are complete.

## One-command completion on an internet-enabled machine

```bash
./RUN_LIVE_SUBMISSION.sh
```

That command downloads the Builderr universe and BRREG bulk data, rebuilds the exact deterministic 1,000-company manifest, runs the full evidence pipeline, and invokes the structural submission gate. It fails closed if required evidence is missing.

## Competition rule reminder

Builderr currently requires at least 1,000 completed profiles, exactly 100 terminal envelopes for each daily batch, <=2,000 outbound requests, <=$10 external API spend, >=95% external precision, >=60% weighted external company recall, and no material wrong-company publication. The official challenge page is the source of truth.
