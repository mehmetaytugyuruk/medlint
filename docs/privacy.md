# Privacy and threat model

medlint is intended to run locally against medical-imaging research data. Local
execution reduces data movement; it does not make an audit or its output
automatically anonymous, compliant, or safe to publish.

## Default protections

- Source files are read-only inputs.
- The core makes no network request, upload, or telemetry call.
- Reports use run-local opaque record aliases.
- Raw PatientID values and raw DICOM UIDs are omitted from default reports.
- Absolute paths are omitted from default reports.
- No image thumbnail or pixel cache is created in `0.1.0`.
- Raw metadata values are not persisted in report artifacts by default.
- Terminal summaries do not echo the chosen report path.
- A report cannot overwrite the input manifest or an audited source file, and
  cannot be created inside an explicit split root.

Aliases are references for interpreting one audit; they are not anonymized
patient identifiers and should not be used to link people across runs.

## Explicit path opt-in

`--include-paths` may add paths for controlled local debugging. A path can
contain patient names, medical record numbers, accession numbers, institutional
layout, or other sensitive context. Treat any opted-in report as sensitive and
review it before sharing.

JSON output is written through a temporary file and atomically moved into place
after the audit. This protects source-file integrity; it does not make the
result non-sensitive or replace appropriate filesystem permissions.

## Out of scope

medlint does not:

- de-identify DICOM metadata;
- detect or remove burned-in pixel PHI;
- certify HIPAA, GDPR, institutional, or data-use compliance;
- determine whether same-subject matching is permitted by a data-use agreement;
  or
- replace institutional governance, ethics review, or qualified privacy review.

## Threats considered

- accidental disclosure of raw identifiers in JSON or terminal output;
- disclosure through absolute paths and filenames;
- accidental inclusion of clinical images in fixtures or CI artifacts;
- unexpected network access or telemetry;
- mutation of source datasets; and
- false confidence caused by silently skipped data.

Privacy regression tests should scan all default renderers for seeded synthetic
identifiers and paths. Coverage tests should prove that unreadable and
unsupported inputs remain visible.

## User responsibilities

- Confirm that local analysis is permitted by the dataset's agreement and your
  institution.
- Use the minimum required permissions and a controlled environment.
- Keep datasets and reports out of version control.
- Do not paste clinical records into public issues.
- Remove audit outputs according to the same retention policy as the source
  data.
- Treat a suspected identifier/path disclosure as a security issue and follow
  [SECURITY.md](../SECURITY.md).
