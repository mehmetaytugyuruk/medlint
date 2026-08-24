# ADR-0006: Privacy defaults and record aliases

- **Status:** Accepted
- **Date:** 2026-08-24

## Decision

Default terminal and JSON reports omit raw PatientID, raw DICOM UIDs, absolute
paths, thumbnails, and cached raw metadata. Records use deterministic,
run-local opaque aliases assigned from canonical catalog ordering. These aliases
are report references, not reusable anonymized patient identifiers.

Path output requires explicit `--include-paths` opt-in. The core performs no
upload, telemetry, remote API call, or source-data mutation.

## Consequences

Equivalent catalogs can produce deterministically ordered reports without
persisting raw identity values. Opted-in diagnostic reports remain sensitive
and must not be published without review.
