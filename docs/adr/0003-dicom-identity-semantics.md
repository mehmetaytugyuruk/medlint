# ADR-0003: DICOM identity semantics

- **Status:** Accepted
- **Date:** 2026-08-24

## Decision

PatientID is usable as group evidence only within IssuerOfPatientID and/or an
explicit source namespace. Empty and common dummy values are reported as
unusable, not compared as identities.

StudyInstanceUID, SeriesInstanceUID, and SOPInstanceUID remain study-, series-,
and instance-level evidence. They are never promoted to proof of a real-world
patient identity.

## Consequences

Rules must name the DICOM level they evaluate. Reports redact the raw values and
explain what each relationship proves and does not prove.

Rules that combine identifier evidence with contradictory pixel or content
evidence are deferred until the necessary content representation is implemented
and validated; they are not part of `0.1.0`.
