# Final submission checklist

Signalpost X is **not allowed to claim final readiness** until these artifacts exist from a real run:

- [ ] `profiles.jsonl` contains >= 1,000 completed profiles.
- [ ] The profile organisation numbers exactly match the submitted manifest.
- [ ] Every published external claim has evidence and retrieval time.
- [ ] Financial values are sourced from the correct reporting period.
- [ ] Uncertain company matches are quarantined as ambiguous/not available.
- [ ] Daily simulation emits exactly 100 terminal envelopes.
- [ ] Daily simulation stays under 2,000 outbound requests.
- [ ] Daily simulation stays under $10 declared third-party API spend.
- [ ] Refresh is idempotent.
- [ ] No material wrong-company facts are present.
- [ ] Dependencies are pinned.
- [ ] Repository contains no secrets.
- [ ] Final commit SHA is recorded.
- [ ] Submission email contains repository URL, SHA, profile count, manifest URL, run command, models/APIs/licences, expected cost and contact.

## Submission destination
`submit@builderr.ai`
