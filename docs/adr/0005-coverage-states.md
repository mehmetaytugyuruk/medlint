# ADR-0005: Coverage and inconclusive behavior

- **Status:** Accepted
- **Date:** 2026-08-24

## Decision

Catalog coverage inventories discovered, supported, unsupported, unreadable,
and out-of-profile records. Each detector separately reports eligible,
evaluated, and unavailable record counts, categorized reasons, and its
eligible/evaluated split scope. The canonical top-level states are:

- `complete_no_findings`;
- `complete_with_findings`;
- `partial`;
- `inconclusive`; and
- `operational_error`.

Missing required evidence or coverage below policy requirements cannot produce
`complete_no_findings`. At least one active detector must evaluate records in
two distinct splits. Declared, populated, eligible, and evaluated split scope is
preserved in coverage.

CLI exit codes are `0` for a complete audit with no configured finding, `1` when
one or more findings require review under the v0.1 default policy, `2` for an
operational error, and `3` for partial or inconclusive coverage without a
finding. Findings take exit-code precedence over coverage gaps; both remain
explicit in canonical JSON.

## Consequences

Unsupported input never disappears and never becomes an implicit negative
result. CI users can distinguish dataset evidence from a tool failure.
