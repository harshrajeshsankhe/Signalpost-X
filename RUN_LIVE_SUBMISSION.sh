#!/usr/bin/env bash
set -euo pipefail

# Signalpost X: one-command live finalization.
# Run from the repository root on a machine with outbound HTTPS access.

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

UV_BIN="$(command -v uv || true)"
PY="python3"
if [[ -n "$UV_BIN" ]]; then
  "$UV_BIN" sync
  RUN=("$UV_BIN" run python)
else
  if [[ ! -d .venv ]]; then "$PY" -m venv .venv; fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  python -m pip install -e .
  RUN=(python)
fi

mkdir -p live-data out/final-1000

if [[ ! -f live-data/signalpost-company-universe-2025.jsonl.gz ]]; then
  curl -fL --retry 3 --retry-delay 2 \
    'https://builderr.ai/signalpost-company-universe-2025.jsonl.gz' \
    -o live-data/signalpost-company-universe-2025.jsonl.gz
fi

if [[ ! -f live-data/brreg-enheter.csv ]]; then
  curl -fL --retry 3 --retry-delay 2 \
    'https://data.brreg.no/enhetsregisteret/api/enheter/lastned/csv' \
    -o live-data/brreg-enheter.csv
fi

# Re-create the exact deterministic 1,000-company manifest from the supplied universe.
"${RUN[@]}" select_entry_batch.py \
  --universe live-data/signalpost-company-universe-2025.jsonl.gz \
  --count 1000 \
  --seed 20260913 \
  --output out/entry-companies.jsonl

# Full submitted profile set.
"${RUN[@]}" run_signalpost_x.py \
  --organisations out/entry-companies.jsonl \
  --bulk live-data/brreg-enheter.csv \
  --out out/final-1000 \
  --run-id signalpost-x-final-1000 \
  --expected-count 1000 \
  --workers 8 \
  --high-recall \
  --site-pages 8

# Structural final gate. This intentionally fails rather than fabricating readiness.
"${RUN[@]}" scripts/finalize_submission.py \
  --profiles out/final-1000/profiles.jsonl \
  --manifest out/entry-companies.jsonl \
  --output out/final-submission-manifest.json

echo
printf '%s\n' 'FINAL 1,000-PROFILE BUILD PASSED STRUCTURAL VALIDATION.'
printf '%s\n' 'Next: run the Builderr frozen 100-company batch and supply its exact envelopes/report.'
