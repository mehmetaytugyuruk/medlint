# Quick start

This guide demonstrates the intended `0.1.0` workflow. medlint audits declared
splits without modifying their files.

## Install

```bash
python -m pip install medlint
```

Python 3.10 or newer is required; releases are tested on Python 3.10-3.13.

## Run the PHI-free example

From a source checkout, generate three valid one-pixel PNG files and their
manifest:

```bash
python examples/quickstart/create_example.py
medlint audit \
  --manifest medlint-example-data/splits.csv \
  --output medlint-example-report.json
```

The generator deliberately writes identical bytes to one train image and one
test image. The audit therefore reports rule `ML001` and returns exit code `1`.
All files and labels are synthetic; no clinical image or identifier is used.

## Audit a manifest

Create a UTF-8 CSV manifest:

```csv
path,split,source_namespace
data/train/a.dcm,train,site-a-export-1
data/train/b.dcm,train,site-a-export-1
data/test/c.dcm,test,site-a-export-1
```

`path` and `split` are required. `source_namespace` is optional but strongly
recommended for merged exports. Relative paths are resolved from the manifest
location. See the [manifest contract](manifest-v1.md) for exact semantics.

Run:

```bash
medlint audit --manifest splits.csv --output medlint-report.json
```

## Audit split directories

```bash
medlint audit \
  --split train=data/train \
  --split test=data/test \
  --source-namespace local \
  --output medlint-report.json
```

`--split` may be repeated for validation sets or folds. The convenience default
namespace is `local`; use a deliberate stable value when combining sources.
At least two distinct splits must contain records evaluable by an active
detector for a conclusive cross-split audit.

## Interpret the outcome

First inspect the coverage summary. A skipped or unsupported record means that
one or more checks could not evaluate it. Then inspect findings and their rule
explanations.

A result may report:

- an exact file-content relationship across splits;
- a source/issuer-scoped PatientID or DICOM UID relationship across splits;
- missing or unusable metadata; or
- an unreadable or unsupported input.

These are observations to review. Their scientific meaning depends on the
intended split policy. medlint does not declare a dataset leakage-free.

In `0.1.0`, exact-content comparison covers recognized DICOM and common raster
files. Raster images are compared as file bytes only; their pixels are not
decoded. An extensionless input is considered DICOM only when a DICOM Part 10
`DICM` marker is present after the 128-byte preamble.

## CI example

```bash
medlint audit --manifest splits.csv --output medlint-report.json
```

The exit codes are:

- `0`: complete required coverage with no configured finding;
- `1`: one or more findings require review under the v0.1 default policy, even
  if coverage is partial;
- `2`: operational error; and
- `3`: partial or inconclusive coverage.

Archive the JSON report regardless of the exit code. An exit code of `0` is not
a general statement that no leakage exists.

The default policy uses finding-first exit precedence: if a finding and partial
coverage occur together, the process returns `1` while the JSON retains the
`partial` coverage state.

The v0.1 default policy treats every emitted finding as review-blocking. It does
not assign separate informational or warning levels to individual findings.

## Path disclosure

Default reports omit absolute paths and raw identifiers. `--include-paths` is an
explicit opt-in for controlled local debugging. Do not publish an opted-in
report without reviewing it for sensitive information.

medlint refuses to write a report over the input manifest, over an audited
source file, or anywhere inside an explicit split root. Report files are written
atomically after the read-only audit completes.
