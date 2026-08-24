# Contributing a detector

The `0.1.0` detector boundary is intentionally small. Built-in detectors are
registered explicitly; medlint does not expose a dynamic third-party plugin
framework yet.

## Detector responsibility

A detector:

1. consumes the normalized, immutable catalog;
2. evaluates one clearly bounded evidence source;
3. emits factual findings, coverage, and diagnostics; and
4. remains deterministic, read-only, and independent of CLI/report rendering.

A detector must not decide the top-level pass/fail outcome. That belongs to the
policy layer.

## Proposal checklist

Before implementing a detector, document:

- the observable fact it measures;
- what the evidence proves and does not prove;
- eligible records and required fields;
- missing, unsupported, and error behavior;
- false-positive and false-negative mechanisms;
- algorithm and parameter versioning;
- performance and memory expectations; and
- privacy and dependency impact.

## Finding requirements

Each finding needs:

- a stable, namespaced rule ID and rule version;
- an evidence category and strength separate from policy outcome;
- affected splits and opaque record aliases;
- the observed fact or measurement;
- the method and rule version, with run configuration represented by the
  report-level configuration digest;
- an explanation and limitation;
- a suggested review action; and
- a component identifier when multiple records form one relationship group.

Do not emit raw PatientID, DICOM UIDs, or absolute paths into the canonical
finding model.

## Coverage requirements

Report the number of eligible and evaluated records, categorized skip/error
reasons, and the eligible/evaluated split scope. A detector that did not
evaluate records in at least two splits cannot support a conclusive cross-split
outcome. Unsupported input must not be treated as a negative finding.

## Tests

A detector contribution should include:

- positive and negative synthetic oracle cases;
- missing and malformed input cases;
- input-order determinism tests;
- privacy regression tests;
- evidence/policy separation tests; and
- a performance check if candidate comparison can grow faster than linearly.

Model-based detectors and heavy ML dependencies are outside the core `0.1.0`
contract. A future experimental module requires its own scientific, privacy,
license, and external-validation review.
