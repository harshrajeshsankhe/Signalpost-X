# Signalpost X architecture

## Core rule

The organisation number is the immutable identity key. External evidence is never published merely because a search result, brand name, social handle, or similar domain looks plausible.

## Publication firewall

Candidate → exact-domain/identity checks → evidence capture → publish/quarantine.

The default threshold is deliberately conservative. When evidence is insufficient, the agent abstains.

## Research order

1. Registry identity
2. Annual accounts / financial history
3. Roles
4. Group structure
5. Registered locations
6. Registry-linked company website
7. Same-domain priority pages
8. Optional permitted external connectors

## Budget

The competition runner retains Builderr's request/runtime accounting. External connectors should be budgeted before invocation; no connector should be allowed to consume the whole 2,000-request envelope.

## Refresh

Snapshots are keyed by organisation number and content hash. Changes are value changes, not mere crawl timestamps. Earlier evidence remains available in prior snapshots.
