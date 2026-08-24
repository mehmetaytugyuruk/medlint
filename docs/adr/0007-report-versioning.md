# ADR-0007: Canonical report and versioning

- **Status:** Accepted
- **Date:** 2026-08-24

## Decision

Canonical JSON is the durable audit record. It carries an explicit report
schema version, tool version, rule IDs and rule versions, configuration digest,
finding methods, dependency provenance, findings, coverage, diagnostics, and
policy outcome.

Schema versions and package versions evolve independently. Breaking report
changes require a schema-major change; compatible additions require a schema
minor change. Rule meaning cannot change under an existing rule ID/version.
Serialization and semantic ordering must be deterministic.

## Consequences

Human-readable renderers consume canonical results rather than detector state.
The first concrete schema version is frozen together with its JSON Schema and
golden fixtures before the `0.1.0` tag.
