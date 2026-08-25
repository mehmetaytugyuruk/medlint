# Changelog

All notable changes to medlint will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows Semantic Versioning while its public API matures through
the `0.x` series.

## [Unreleased]

## [0.1.1] - 2026-08-25

### Added

- Added the repository visual identity and README header without adding brand
  assets to the wheel or source distribution.

### Fixed

- Prevented the default `AuditResult` representation used by notebooks and logs
  from exposing internal record references or local filesystem paths. Canonical
  JSON and the explicit `include_paths` opt-in are unchanged.
- Reject inconsistent detector results whose detector and coverage identifiers
  do not match, before they can reach policy evaluation or reporting.

### Changed

- Removed an unused internal DICOM signal and stopped re-exporting the private
  `RecordReference` implementation detail. The supported root API, CLI, rule
  behavior, and report schema are unchanged.
- Expanded PHI-free regression coverage for partial audits with findings,
  missing DICOM Modality, invalid UTF-8 manifests, and the
  `python -m medlint --version` entry point.
- Updated GitHub Actions to current Node 24-based releases and moved tag-based
  PyPI releases to Trusted Publishing after removing the one-time v0.1.0
  bootstrap secret.

## [0.1.0] - 2026-08-24

The first public alpha release provides a deterministic,
medical-imaging-specific split-integrity smoke test with:

- manifest and explicit split-root discovery;
- exact file-content duplicate evidence across splits;
- source/issuer-scoped DICOM PatientID evidence plus separate study, series, and
  instance UID evidence;
- coverage and uncertainty reporting;
- conservative policy evaluation;
- privacy-safe terminal and canonical JSON reports; and
- a lightweight, offline, read-only core.

It also includes a versioned JSON Schema, PHI-free synthetic tests, architecture
decision records, a runnable PHI-free quickstart generator, contributor and
security guidance, and pinned automated CI and release workflows. It does not
certify that a dataset is leakage-free.

[Unreleased]: https://github.com/mehmetaytugyuruk/medlint/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/mehmetaytugyuruk/medlint/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/mehmetaytugyuruk/medlint/releases/tag/v0.1.0
