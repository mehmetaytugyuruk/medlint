# Supported data and coverage

This document defines the initial `0.1.0` support boundary. The implementation
and tests are the final authority for the exact supported set at release time.

## Supported input declarations

- UTF-8 CSV manifests with `path` and `split` columns
- Optional `source_namespace` manifest column
- Repeated explicit split roots through `--split NAME=PATH`
- Local filesystem paths
- N-way train, validation, test, and fold membership

Identity-like values are treated as strings. medlint does not infer patient
identity from filenames or directories.

Directory discovery is recursive and does not follow symbolic links. Nested
links are inventoried as coverage gaps; a split root that is itself a symbolic
link is rejected as an operational input error. Non-regular filesystem entries
are not opened.

## v0.1.0 DICOM profile

Files ending in `.dcm` or `.dicom` are treated as DICOM candidates. An
extensionless file is treated as DICOM only when its first 132 bytes contain the
DICOM Part 10 `DICM` marker after the 128-byte preamble. A DICOM file stored with
another nonstandard extension is unsupported in `0.1.0`.

The primary tested profile is local, single-frame, two-dimensional DICOM, with
CR and DX as the initial medical-image modalities. DICOM processing is
metadata-only; pixel data is not decoded.

Within readable DICOM metadata, the first release evaluates:

- PatientID together with IssuerOfPatientID and/or source namespace;
- StudyInstanceUID;
- SeriesInstanceUID; and
- SOPInstanceUID.

Those fields represent different identity or acquisition levels. A shared UID
must not be promoted to patient-identity proof.

## Exact file-content checks

Byte-level cryptographic fingerprinting is limited to recognized DICOM files
and common raster suffixes: `.bmp`, `.jpeg`, `.jpg`, `.png`, `.tif`, and
`.tiff`. Exact file equality is reported separately from DICOM metadata
evidence.

Raster files are not decoded, validated as images, or compared by pixel content
in `0.1.0`; only their exact stored bytes are fingerprinted. Unknown extensions
are reported as unsupported and are not fingerprinted.

## Inventoried but not pixel-analyzed in v0.1.0

- multi-frame DICOM objects;
- 3D CT or MRI volumes;
- unsupported or unknown modalities;
- malformed DICOM objects;
- manifest-listed broken, inaccessible, or unreadable file paths; and
- non-DICOM raster image pixels.

These inputs must remain visible in coverage rather than disappear from a run.
Some may still be eligible for exact byte-level fingerprinting.

An invalid manifest or explicit split root is an operational input error rather
than a record-level coverage limitation because dataset discovery cannot begin.

## Deferred capabilities

- exact decoded-pixel fingerprints;
- resize/recompression-aware perceptual similarity;
- embedding or model-based similarity;
- thumbnails and visual review galleries; and
- modality-specific pixel normalization.

Support claims will expand only when their semantics and synthetic fixtures are
documented and tested. Because `0.1.0` does not decode pixel data, it does not
evaluate or report pixel-decoder or transfer-syntax decoding coverage.
