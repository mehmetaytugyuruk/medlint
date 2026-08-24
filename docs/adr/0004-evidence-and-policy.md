# ADR-0004: Detector, evidence, and policy separation

- **Status:** Accepted
- **Date:** 2026-08-24

## Decision

The processing boundary is:

```text
Discovery -> Catalog -> Detectors -> Evidence -> Policy -> Report
```

A detector emits factual findings, coverage, and diagnostics. It does not emit
a top-level pass/fail decision. Policy evaluates immutable evidence and coverage
to produce the audit outcome. Terminal and JSON renderers present the same
canonical audit result and do not reinterpret detector output.

The single `0.1.0` default policy treats every emitted finding as
review-blocking and returns exit code `1`. Per-finding informational or warning
levels and configurable policy profiles are deferred.

Built-in detectors are explicitly registered in `0.1.0`; no public dynamic
plugin framework is introduced.

## Consequences

Scientific evidence remains inspectable independently of a project's chosen
split policy. Future detectors can reuse the catalog and evidence contracts
without coupling to CLI or presentation code.
