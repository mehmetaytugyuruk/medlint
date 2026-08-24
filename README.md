# medlint

**A lightweight, evidence-first split-integrity auditor for medical imaging
datasets.**

medlint is a pre-training smoke test. It examines declared dataset splits and
reports evidence of relationships that may indicate a contamination risk, such
as an exact file appearing in both train and test, a source/issuer-scoped
PatientID recurring across splits, or the same DICOM UID recurring across
splits.

It does **not** prove patient identity, detect every form of data leakage, or
certify that a dataset is leakage-free.

> **Status:** `0.1.0` is an alpha-stage public API. Its manifest, report, CLI,
> and Python interfaces may change before `1.0.0`.

## Why medlint?

Medical imaging datasets often combine repeated examinations, multiple exports,
derived copies, or inconsistently de-identified DICOM records. Files that still
share a patient, acquisition, or exact-content relationship can accidentally be
assigned to different model-development splits.

medlint gives researchers an explainable checkpoint before expensive model
training. It reports:

- what was inspected;
- what evidence was found;
- why each relationship may matter;
- what could not be evaluated; and
- what should be reviewed manually.

No source file is changed.

## v0.1.0 scope

The first release focuses on a deliberately narrow, deterministic workflow:

- manifest-based or explicit split-root discovery;
- n-way split definitions such as train, validation, test, and folds;
- exact file fingerprints for recognized DICOM and common raster inputs;
- basic DICOM metadata analysis for source/issuer-scoped PatientID and separate
  study, series, and instance UID relationships;
- coverage for unreadable, unsupported, missing, and unusable inputs;
- evidence-based findings with stable rule identifiers;
- a concise terminal summary and deterministic JSON report;
- local, offline, read-only operation; and
- privacy-safe record aliases in default output.

The core depends only on
[`pydicom`](https://github.com/pydicom/pydicom) and the Python standard library.
It has no ML framework, model-weight, database, server, or cloud dependency.

### Not included in v0.1.0

- decoded-pixel fingerprinting;
- perceptual or embedding-based image similarity;
- model-based same-subject matching;
- CT/MRI volume or multi-frame pixel analysis;
- DICOM anonymization or burned-in PHI detection;
- temporal, target, preprocessing, or pretraining-data leakage checks;
- automatic deletion, movement, quarantine, or split repair; and
- HTML reporting.

These limits are part of the product contract. A run with no findings means
only that no configured finding was detected within the reported coverage.

## Installation

Python 3.10 or newer is required; releases are tested on Python 3.10-3.13.

```bash
python -m pip install medlint
```

For development:

```bash
git clone https://github.com/mehmetaytugyuruk/medlint.git
cd medlint
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Quick start

### Runnable PHI-free example

A source checkout includes a deterministic generator for three valid one-pixel
PNG files. One train image is copied byte-for-byte into the test split so the
example has a known `ML001` finding:

```bash
python examples/quickstart/create_example.py
medlint audit \
  --manifest medlint-example-data/splits.csv \
  --output medlint-example-report.json
```

The audit returns exit code `1` and reports a potential contamination risk based
on exact file bytes. The example contains no clinical data or identifiers.

### Option 1: manifest

The canonical input is a UTF-8 CSV manifest. The required columns are `path`
and `split`; `source_namespace` is optional but strongly recommended when data
from more than one export or institution is combined.

```csv
path,split,source_namespace
data/train/image-001.dcm,train,hospital-a-export-1
data/train/image-002.dcm,train,hospital-a-export-1
data/test/image-101.dcm,test,hospital-a-export-1
```

Paths may be relative to the manifest location. Identifiers are treated as
strings. medlint does not infer patient identity from file or directory names.
At least two distinct splits are required for a conclusive cross-split audit.

```bash
medlint audit \
  --manifest splits.csv \
  --output medlint-report.json
```

### Option 2: explicit split roots

For a simple directory layout, repeat `--split NAME=PATH`:

```bash
medlint audit \
  --split train=data/train \
  --split validation=data/validation \
  --split test=data/test \
  --source-namespace local \
  --output medlint-report.json
```

`--source-namespace local` is the default convenience namespace for split-root
input. Choose an explicit, stable namespace when datasets from different
sources are combined. A shared PatientID without an appropriate issuer or
source namespace is not assumed to be globally unique.

Run `medlint audit --help` for the complete command reference.

## Reading a result

The terminal summary is intentionally conservative. An abbreviated example is:

```text
medlint split-integrity audit
Audit state: complete_with_findings
Finding status: potential_risk_detected
Coverage status: complete

Coverage
  Declared splits: 2
  Evaluable splits: 2
  Discovered: 1200
  Exact-file fingerprints: 1200

Findings: 1
  [ML001] 2 records in 2 splits have identical file bytes.

Potential contamination risk detected; review the factual evidence before model training.
```

Each JSON finding records the rule, evidence category, affected splits,
privacy-safe record aliases, observed fact, limitations, and suggested review
action. Evidence and policy outcomes are kept separate: a detector reports an
observation, while policy evaluates the findings and coverage for the audit.
The v0.1 default policy treats every emitted finding as review-blocking and
returns exit code `1`; it does not assign per-finding informational or warning
levels.

Top-level audit states distinguish complete runs with or without findings from
partial, inconclusive, and operational-error runs.

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | Audit completed with required coverage and no configured finding |
| `1` | One or more findings require review under the v0.1 default policy |
| `2` | An operational error prevented a valid audit |
| `3` | Coverage was partial or inconclusive and no finding took precedence |

Exit code `0` is not a leakage-free certificate. CI should archive and inspect
the JSON report, especially its coverage section. The default policy gives a
finding (`1`) precedence over partial coverage (`3`); the JSON still preserves
both states.

## Privacy and offline behavior

medlint is designed for local research environments:

- it does not upload datasets, call a remote API, or send telemetry;
- it opens source data read-only and never changes or repairs it;
- default reports use opaque record aliases;
- default reports omit raw DICOM identifiers and absolute paths;
- `--include-paths` is an explicit opt-in intended only for controlled local
  debugging; and
- v0.1.0 does not create image thumbnails or persist image pixels.

Reports may still be sensitive because relationships, filenames explicitly
included by the user, and local operational details can be identifying. Handle
them under the same institutional rules that govern the source dataset. Do not
commit datasets or reports containing patient information to this repository.

See the
[privacy and threat model](https://github.com/mehmetaytugyuruk/medlint/blob/main/docs/privacy.md)
for details.

## Supported data and interpretation

v0.1.0 recognizes `.dcm` and `.dicom` files, plus common raster suffixes:
`.bmp`, `.jpeg`, `.jpg`, `.png`, `.tif`, and `.tiff`. An extensionless file is
recognized as DICOM only when it has the DICOM Part 10 `DICM` marker after the
128-byte preamble. Other extensions are reported as unsupported and are not
fingerprinted in this release.

Recognized DICOM and raster files receive exact byte-level fingerprints. Raster
pixels are not decoded or interpreted. DICOM analysis is metadata-only, so
v0.1.0 neither requires pixel decoders nor reports transfer-syntax decoding
coverage. CR/DX is the primary tested DICOM profile; multi-frame objects,
out-of-profile modalities, manifest-listed broken paths, malformed files, and
unknown file types remain visible as coverage limitations. An invalid manifest
or explicit split root is an operational error because discovery cannot begin.

See:

- [Quick start](https://github.com/mehmetaytugyuruk/medlint/blob/main/docs/quickstart.md)
- [Manifest contract](https://github.com/mehmetaytugyuruk/medlint/blob/main/docs/manifest-v1.md)
- [Rule catalog](https://github.com/mehmetaytugyuruk/medlint/blob/main/docs/rules.md)
- [Evidence and coverage](https://github.com/mehmetaytugyuruk/medlint/blob/main/docs/concepts/evidence-and-coverage.md)
- [Supported data](https://github.com/mehmetaytugyuruk/medlint/blob/main/docs/supported-data.md)
- [JSON Schema](https://github.com/mehmetaytugyuruk/medlint/blob/main/schemas/audit-result-v1.schema.json)
- [Architecture decisions](https://github.com/mehmetaytugyuruk/medlint/blob/main/docs/adr/README.md)
- [Roadmap](https://github.com/mehmetaytugyuruk/medlint/blob/main/ROADMAP.md)

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy src/medlint
pytest
python -m build
python -m twine check dist/*
```

Contributions are welcome after reading the
[contribution guide](https://github.com/mehmetaytugyuruk/medlint/blob/main/CONTRIBUTING.md)
and
[detector guide](https://github.com/mehmetaytugyuruk/medlint/blob/main/docs/contributing-detectors.md).
Never use real PHI in an issue, pull request, fixture, log, screenshot, or CI
artifact.

## Responsible claims

Please describe medlint as an audit or smoke test, not as proof that leakage is
present or absent. A finding is evidence of a specific observed relationship.
Its scientific meaning depends on the dataset, intended evaluation, split
policy, metadata quality, and audit coverage.

## License

Licensed under the
[Apache License 2.0](https://github.com/mehmetaytugyuruk/medlint/blob/main/LICENSE).

## Citation

If medlint supports your research, use the metadata in
[CITATION.cff](https://github.com/mehmetaytugyuruk/medlint/blob/main/CITATION.cff).
