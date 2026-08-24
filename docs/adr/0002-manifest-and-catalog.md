# ADR-0002: Manifest and normalized catalog

- **Status:** Accepted
- **Date:** 2026-08-24

## Decision

The canonical input is a UTF-8 CSV manifest with required `path` and `split`
columns and optional `source_namespace`. Relative paths resolve from the
manifest directory. Repeated `--split NAME=PATH` arguments are a convenience
adapter that produces the same catalog contract and use `local` as their
explicit default namespace.

All identifiers remain strings. The normalized catalog is immutable after
discovery. Patient identity is never inferred from a filename or directory.
Directory discovery does not follow file or directory symlinks; nested links
become diagnostics and coverage gaps, while a symbolic-link split root is an
operational input error. The catalog preserves declared split membership,
including empty explicit roots, without inventing identity from path layout.

## Consequences

Detectors consume one normalized representation regardless of input style.
Merged sources must use deliberate namespaces to avoid treating unrelated local
identifiers as global identifiers.
