# Manifest contract v1

This document defines the CSV manifest accepted by medlint `0.1.x`. The
manifest is the canonical way to declare dataset membership when files do not
already live under separate split roots.

## File format

- Encoding: UTF-8, with or without a UTF-8 byte-order mark.
- Format: CSV with a header row.
- Required headers: exactly `path` and `split`.
- Optional header: `source_namespace`.
- Additional columns are accepted but ignored by `0.1.x`.

Header names are case-sensitive. Required values are trimmed at their outer
whitespace and must not be empty. Split and namespace labels must contain only
printable characters so they cannot inject terminal control sequences.

## Columns

### `path`

A local file or directory. A relative value is resolved from the directory
containing the manifest. A directory is discovered recursively.

medlint does not infer a patient or group identifier from a path. Missing,
non-regular, unreadable file, and symbolic-link rows remain visible as coverage
limitations. Symbolic links are inventoried but never followed. A directory
that cannot be traversed prevents valid discovery and is an operational error.
A split root passed through `--split` must itself not be a symbolic link.

### `split`

The exact, case-sensitive split name, such as `train`, `validation`, `test`, or
`fold-0`. A conclusive cross-split audit requires at least two distinct splits
with records evaluable by at least one active detector.

### `source_namespace`

The scope in which local administrative identifiers are interpreted. It
defaults to `local` when omitted or empty. Use deliberate stable values when a
manifest combines exports or institutions. The namespace participates in the
PatientID equality scope but is not written to the default report.

## Repeated declarations

Rows are preserved rather than silently deduplicated. Declaring the same path
in different splits lets the exact-file detector expose that cross-split
relationship. Repeating a row within one split can inflate record counts and
should be removed by the dataset maintainer.

## Example

```csv
path,split,source_namespace
data/train/image-001.dcm,train,site-a-export-1
data/validation/image-101.dcm,validation,site-a-export-1
data/test/image-201.dcm,test,site-a-export-1
```

The manifest and its paths may be sensitive. Default reports omit them, while
`--include-paths` explicitly opts into path-bearing JSON.
