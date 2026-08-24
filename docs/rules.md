# Built-in rule catalog

This catalog defines the built-in `0.1.0` evidence rules. Every rule groups all
records sharing its exact equality key into one component and emits a finding
only when that component spans at least two declared splits.

All current rules have rule version `1`. A rule ID and version describe an
observation, not a conclusion that leakage or patient identity has been proven.

| Rule | Observed relationship | Eligible input | Evidence strength |
|---|---|---|---|
| `ML001` | Complete stored file bytes have the same SHA-256 digest | Recognized DICOM and common raster files | Exact content match |
| `ML101` | The same usable PatientID occurs in the same source and issuer scope | Readable DICOM metadata with usable PatientID | Scoped identifier match |
| `ML102` | The same valid StudyInstanceUID occurs across splits | Readable DICOM metadata with a valid study UID | Acquisition identifier match |
| `ML103` | The same valid SeriesInstanceUID occurs across splits | Readable DICOM metadata with a valid series UID | Acquisition identifier match |
| `ML104` | The same valid SOPInstanceUID occurs across splits | Readable DICOM metadata with a valid instance UID | Acquisition identifier match |

## `ML001`: exact stored-file content

The detector streams the complete file bytes through SHA-256. Equality proves
that the stored content is byte-identical. It does not prove patient identity
and does not detect files changed by metadata rewriting, transcoding, resizing,
or recompression.

## `ML101`: scoped PatientID

PatientID text is Unicode-normalized, stripped, screened for missing and common
dummy values, and compared exactly within a tuple of source namespace,
IssuerOfPatientID, and PatientID. Raw values and their internal run-local
equality tokens are never serialized.

This is administrative group evidence. PatientID may be reused, regenerated,
or incorrectly assigned, so it is not proof of a real-world person's identity.

## `ML102`-`ML104`: acquisition identifiers

StudyInstanceUID, SeriesInstanceUID, and SOPInstanceUID are validated and
compared separately at their own DICOM levels. A match indicates a shared
study-, series-, or object-level identifier. None is promoted to patient-level
proof, and incorrect or regenerated UIDs remain possible.

## Policy and coverage

The conservative default policy treats every emitted finding as a blocking
request for review and returns exit code `1`. Missing values, unsupported
records, out-of-profile DICOM, and unreadable data are reported through coverage
instead of being converted into negative findings.

No-finding output means only that these configured rules found no cross-split
relationship within their recorded coverage.
