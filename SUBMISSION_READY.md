# Signalpost X — Submission Readiness

**Current state:** competition-ready architecture; final entry requires a real run against the Builderr-supplied Brreg snapshot and permitted external providers.

## Artifacts to submit

- `out/entry-companies.jsonl` — 1,000 organisation numbers with stratified selection metadata.
- `profiles.jsonl` — final completed profiles from the real competition run.
- `envelopes.jsonl` — terminal envelopes for the tested batch.
- public Git repository URL.
- exact immutable commit hash.
- one-command run instruction.
- model/API/licence declaration.
- expected cost per 100-company run.
- contact details.

## What is already prepared

- deterministic 1,000-company selection;
- selection audit;
- exact-company website identity gate;
- bounded high-recall company-site enrichment;
- optional Brave discovery;
- refresh replay fixture;
- dashboard preview;
- audit scripts;
- competition playbook.

## What cannot be truthfully claimed until the live run

The local refresh fixture is not a Builderr score. External recall, external precision and final ranking must be measured by the challenge harness. No implementation can guarantee a win before those tests.
