# ADR-0008: v0.1.0 support matrix

- **Status:** Accepted
- **Date:** 2026-08-24

## Decision

`0.1.0` supports Python 3.10-3.13, local filesystems, n-way CSV manifests,
explicit split roots, exact byte-level fingerprints for recognized DICOM and
common raster files, and readable single-frame two-dimensional DICOM metadata.
CR and DX are the primary tested DICOM profile.

Recognized suffixes are `.dcm`, `.dicom`, `.bmp`, `.jpeg`, `.jpg`, `.png`,
`.tif`, and `.tiff`. Extensionless DICOM detection requires the DICOM Part 10
`DICM` marker after the 128-byte preamble. Other extensions are unsupported and
are not fingerprinted.

Raster files receive exact stored-byte fingerprints only. DICOM handling is
metadata-only and does not decode pixels, so transfer-syntax decoder coverage is
not evaluated. Multi-frame objects, volumes, untested modalities, malformed
files, and manifest-listed broken paths are inventoried and reduce coverage.
They are not silently claimed as fully analyzed. An invalid manifest or
explicit split root is an operational input error because discovery cannot
begin.
The core runtime dependency is limited to pydicom plus the Python standard
library.

## Consequences

Support may expand only with documented semantics and PHI-free tests. Pixel
codec availability is neither required nor evaluated by this metadata-only
release.
