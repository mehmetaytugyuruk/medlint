# Evidence, policy, and coverage

medlint separates three questions that are often incorrectly collapsed into
one score.

## 1. What was observed?

A detector records a factual relationship, such as two records having the same
file fingerprint, a source/issuer-scoped PatientID appearing across splits, or
the same valid StudyInstanceUID appearing across splits.
Each finding includes a stable rule ID, affected privacy-safe aliases, evidence
category, explanation, limitations, and suggested review action.

An exact file match proves that file content is identical. It does not by
itself prove a real-world patient identity. A matching study, series, or
instance UID is acquisition-level evidence, not a universal patient key.

## 2. How should the observation affect this audit?

A separate policy evaluates findings and coverage without changing the factual
evidence. In `0.1.0`, the single conservative default policy treats every
emitted finding as review-blocking and returns exit code `1`. Per-finding
informational and warning levels are not part of the v0.1 contract.

The separation still matters because later policies may need to represent
different evaluation designs without changing detector observations.

Detectors do not emit pass/fail decisions, and report renderers do not
reinterpret evidence.

## 3. What could be evaluated?

Catalog coverage inventories discovered, supported, unsupported, unreadable,
and out-of-profile records. Separately, each detector reports its eligible,
evaluated, and unavailable record counts, categorized unavailability reasons,
and eligible/evaluated split scope. Together these show whether metadata or
content required by an active rule was present and usable.

The top-level audit states are:

- `complete_no_findings`;
- `complete_with_findings`;
- `partial`;
- `inconclusive`; and
- `operational_error`.

Insufficient coverage cannot be represented as `complete_no_findings`.

The default policy uses these practical boundaries:

- `complete`: at least one active detector evaluated records in two or more
  splits, and no required input or detector evidence was unavailable;
- `partial`: a cross-split comparison was possible, but at least one declared
  split, record, metadata value, or primary-profile condition was unavailable;
- `inconclusive`: fewer than two distinct/evaluable splits were available to
  every active detector; and
- `operational_error`: discovery or configuration prevented a valid audit.

Coverage is split-aware. An empty test directory does not disappear from a
split-root audit, and a detector that evaluated only one split cannot produce a
complete no-finding outcome.

## Conservative interpretation

The safe summary for a no-finding audit is:

> No configured finding was detected within the checks and coverage reported by
> this audit.

Do not shorten this to “no leakage” or “dataset clean.” medlint does not inspect
target leakage, test-set tuning, preprocessing fit, all temporal relationships,
or pretraining-data overlap.
