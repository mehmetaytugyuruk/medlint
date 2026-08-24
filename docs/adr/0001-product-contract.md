# ADR-0001: Product contract and terminology

- **Status:** Accepted
- **Date:** 2026-08-24

## Decision

medlint is a lightweight, offline, pre-training split-integrity smoke test. It
reports evidence of potential contamination risk and the coverage of each
check. It does not prove patient identity, declare leakage from similarity
alone, certify a dataset as clean, or claim to detect every form of leakage.

A no-finding result is stated as: no configured finding was detected within the
checks and coverage reported by this audit.

## Consequences

Every user-facing message, rule, and report must identify the observed fact and
its limitation. Embedding-based similarity and leakage-free certification are
outside the core contract.
