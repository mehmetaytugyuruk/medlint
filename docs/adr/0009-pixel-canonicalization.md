# ADR-0009: Pixel canonicalization

- **Status:** Deferred
- **Date:** 2026-08-24

## Context

Exact decoded-pixel fingerprints require explicit decisions about frame
selection, dtype, endianness, bit depth, photometric interpretation, and
modality, VOI, or presentation transforms. Combining these choices under a
generic “image hash” would make evidence ambiguous.

## Decision

Decoded-pixel fingerprints and perceptual representations are excluded from
`0.1.0`. The first release performs exact byte-level fingerprinting only for
recognized DICOM and common raster inputs. Raster pixels are not decoded. No
placeholder pixel abstraction is added to the core.

Before a later release implements pixel analysis, a replacing ADR must define
and golden-test separate exact stored-pixel and normalized perceptual
representations.

## Consequences

The normalized catalog and evidence contracts allow future evidence sources,
but `0.1.0` reports no pixel-equality or visual-similarity claim.
