# medlint Project Roadmap

## Document Status

This document is the source of truth for medlint's product scope, architecture,
and development sequence. It describes the work that must be completed before
the project can be considered a trustworthy pre-training audit tool.

The roadmap deliberately keeps the first release deterministic, explainable,
offline, and independent of model-based image similarity. Any future
embedding-based capability must be optional and must earn its place through a
separate scientific validation process.

## Contents

- [Project Vision](#project-vision)
- [Product Positioning](#product-positioning)
- [Core Problem](#core-problem)
- [Non-Goals](#non-goals)
- [Design Principles](#design-principles)
- [Evidence and Decision Model](#evidence-and-decision-model)
- [v0.1 Support Boundary](#v01-support-boundary)
- [v0.1.0 Definition](#v010-definition)
- [Architecture](#architecture)
- [Development Phases](#development-phases)
- [Technical Risks and Mitigations](#technical-risks-and-mitigations)
- [Phase 0 Architecture Decisions](#phase-0-architecture-decisions)
- [Future Extension Possibilities](#future-extension-possibilities)

## Project Vision

medlint helps medical-imaging researchers detect potential dataset split
integrity problems before training a model.

Its purpose is to make a careful pre-training audit easy to run, easy to
understand, and easy to reproduce. It should replace fragile one-off scripts
with a small, well-tested, open-source core that reports both the evidence it
found and the evidence it could not evaluate.

## Product Positioning

> A lightweight medical imaging dataset split-integrity auditor that acts as a
> pre-training smoke test for detecting potential contamination risks.

medlint is an evidence-producing audit tool. It is not a patient-identification
system and it does not certify that a dataset is leakage-free.

The primary workflow is:

1. A researcher defines train, validation, test, or fold membership through a
   manifest or explicit split roots.
2. medlint discovers and normalizes the dataset without modifying source data.
3. Deterministic detectors examine identifiers and file content in v0.1, with
   separately validated pixel/content modules added only in later phases.
4. Each detector emits factual evidence and coverage information.
5. A separate policy layer evaluates that evidence for the intended split
   policy.
6. medlint produces machine-readable and human-readable reports.

Primary users are academic research teams, dataset maintainers, benchmark and
challenge organizers, and teams combining de-identified exports from multiple
sources.

## Core Problem

Medical-imaging datasets are frequently assembled from repeated examinations,
derived image copies, multiple exports, or inconsistent metadata. These records
can be assigned to different model-development splits without the researcher
realizing that they remain related.

Common failure modes include:

- the same patient group appearing in more than one split;
- the same study, series, or DICOM instance appearing in more than one split;
- byte-identical or pixel-identical files with different names or metadata;
- resized, recompressed, or otherwise derived image copies crossing splits;
- conflicting identifiers caused by data merging or de-identification;
- incomplete metadata or unsupported files creating false confidence in an
  apparently clean audit.

Whether a relationship is inappropriate depends on the intended evaluation.
For example, a new-patient generalization study and a longitudinal known-patient
study require different split policies. medlint therefore reports evidence
first and evaluates it through an explicit policy rather than declaring every
cross-split relationship to be leakage.

## Product Language and Interpretation

User-facing language must be conservative and specific.

Preferred wording includes:

- "potential contamination risk detected";
- "cross-split patient-group identifier match";
- "exact decoded-pixel match";
- "possible derived-image copy; review recommended";
- "audit incomplete" or "evidence unavailable."

The project must avoid unsupported claims such as:

- "patient identity proven";
- "leakage exists" based on visual similarity alone;
- "dataset is clean" or "leakage-free";
- a similarity value presented as a calibrated probability or confidence;
- "no contamination" when coverage is partial or indeterminate.

A no-finding result must be phrased as: no configured finding was detected
within the checks and coverage reported by this audit.

## Non-Goals

The following are outside the v0.1 product contract:

- proving or discovering a person's real-world identity;
- embedding-based or model-based patient similarity;
- detecting every form of data leakage, including target leakage, test-set
  tuning, preprocessing leakage, temporal leakage, or pretraining-data overlap;
- DICOM anonymization or burned-in PHI detection;
- changing, deleting, moving, quarantining, or automatically re-splitting
  source data;
- clinical validation or assessment of image quality;
- 3D CT/MRI volumes, multi-frame studies, or universal modality support;
- PACS integration, cloud execution, telemetry, a database, a server, or a
  dashboard;
- a generic data-quality framework;
- a public dynamic plugin framework in the first release;
- a single aggregate risk or confidence score.

## Design Principles

### 1. Evidence before conclusions

Detectors report observable relationships. Policy evaluates those findings and
their coverage without changing the evidence. The v0.1 default treats every
emitted finding as review-blocking; configurable and per-finding dispositions
are later capabilities.

### 2. Deterministic and explainable by default

Every v0.1 finding must identify the rule, records, splits, observed fact,
method, limitations, and recommended review action that produced it.

### 3. Coverage is a first-class result

Unreadable files, missing metadata, unsupported inputs, and unavailable
detector evidence must be visible in the result. Dependencies such as pixel
codecs become coverage dimensions only when an enabled detector requires them;
v0.1 does not decode pixels. Lack of usable evidence must never be silently
converted into a passing audit.

### 4. Read-only and privacy-safe

Source datasets are immutable inputs. Reports exclude raw PatientID values,
raw DICOM identifiers, absolute paths, and thumbnails by default. Network
access, telemetry, and automatic uploads are prohibited in the core workflow.

### 5. DICOM-aware identity semantics

Identifiers must be interpreted according to what they identify. PatientID is
source- and issuer-scoped; Study, Series, and SOP Instance UIDs represent
different acquisition levels and do not independently prove patient identity.

### 6. Separate discovery, detection, policy, and presentation

The core flow is:

```text
Discovery
  -> Normalized Dataset Catalog
  -> Detection Modules
  -> Evidence Model
  -> Policy Evaluation
  -> Canonical Report
  -> Human-Readable Renderers
```

No detector should contain report-rendering or CLI logic. Reporters must not
reinterpret evidence or create policy decisions.

### 7. Small stable abstractions, not a framework

The first release needs a clear detector contract and versioned evidence model,
not dynamic plugin discovery or a generalized workflow engine. Built-in
detectors should be registered explicitly. External extensibility can be added
only after real contributor demand exists.

### 8. Lightweight core

The base package must not depend on PyTorch, TensorFlow, FAISS, model weights,
or other heavy ML components. Optional future modules must use the same catalog
and evidence contracts without changing core semantics.

### 9. Reproducibility

Reports record tool, schema, rule, algorithm, configuration, and relevant
dependency versions. Equivalent inputs and configuration should produce
deterministically ordered semantic results.

## Evidence and Decision Model

### v0.1 evidence categories

v0.1 implements three factual categories instead of collapsing them into a
single contamination score:

1. **Authoritative group relationship**: a usable, source/issuer-scoped
   PatientID appears across splits. The category name describes administrative
   group evidence; it does not prove real-world identity.
2. **Acquisition identifier relationship**: the same valid StudyInstanceUID,
   SeriesInstanceUID, or SOPInstanceUID appears across splits.
3. **Exact file-content relationship**: byte-identical recognized files are
   identified by a SHA-256 fingerprint over their complete stored bytes.

Coverage gaps are represented separately through catalog coverage, detector
coverage, and diagnostics; they are not findings. Exact decoded-pixel evidence,
perceptual derived-copy evidence, metadata/content conflicts, manifest group
mappings, and AccessionNumber rules are possible later additions, not v0.1
categories.

An exact content match proves a content relationship, not necessarily a patient
relationship. Likewise, a DICOM instance or study match identifies an
acquisition relationship, not a person's real-world identity.

### Finding contract

Every finding should contain at least:

- a stable `rule_id` and rule version;
- evidence category and evidence strength;
- affected splits and privacy-safe record aliases;
- the observed fact or measurement;
- algorithm, parameters, and threshold version where applicable;
- a concise explanation and limitation statement;
- a recommended manual review or remediation action;
- a component identifier when multiple records form one connected group.

The surrounding canonical report carries configuration, provenance, and
detector/catalog coverage shared by its findings.

Evidence strength and policy outcome are separate fields. A detector does not
decide whether the audit passes or fails.

### Coverage contract

Catalog coverage inventories discovered, supported, unsupported, unreadable,
and out-of-profile records. Each v0.1 detector separately reports:

- records eligible for evaluation;
- records successfully evaluated;
- unavailable eligible records and categorized reasons; and
- eligible and evaluated split scope.

Metadata usability is represented through detector unavailability reasons and
catalog diagnostics. Pixel-codec and candidate-generation coverage are added
only with future detectors that require them.

Top-level audit states should distinguish:

- `complete_no_findings`;
- `complete_with_findings`;
- `partial`;
- `inconclusive`;
- `operational_error`.

The v0.1 default policy uses the documented fixed exit-code precedence. A future
schema version may support additional policy dispositions, but canonical
detector evidence must remain unchanged.

## v0.1 Support Boundary

The first release targets:

- n-way train, validation, test, and fold definitions;
- manifest-based input as the canonical workflow;
- explicit split directories as a convenience workflow;
- single-frame, two-dimensional DICOM images with CR/DX as the primary profile;
- common raster formats such as PNG, JPEG, and TIFF for content-based checks;
- local filesystems and offline execution.

The scanner must inventory multi-frame objects, volumes, unknown modalities,
malformed files, symbolic links, and manifest-listed broken paths, but it does
not analyze their pixels in v0.1. These records must reduce reported coverage
rather than disappear from the audit. An invalid manifest or explicit split
root is instead an operational error because discovery cannot begin. Pixel
decoders and transfer-syntax decoding coverage are not evaluated until pixel
analysis is introduced.

No patient identifier may be inferred from a filename or directory layout.
v0.1 exposes no path-based identity extraction rule.

## v0.1.0 Definition

v0.1.0 is the first public, installable release. It must be small but genuinely
useful and medical-imaging specific. It is complete only when it provides an
end-to-end, deterministic audit with all of the following capabilities:

### Inputs and discovery

- a documented, versioned manifest schema;
- n-way split support;
- recursive discovery under explicit roots;
- duplicate-path and symlink handling with documented semantics;
- stable treatment of identifiers as strings;
- source namespaces for merged datasets;
- a normalized, immutable dataset catalog.

### DICOM and metadata analysis

- PatientID interpreted with IssuerOfPatientID and/or an explicit source
  namespace;
- StudyInstanceUID, SeriesInstanceUID, and SOPInstanceUID checked according to
  their acquisition level;
- empty and common dummy patient identifiers excluded from identity evidence;
- metadata availability and usability coverage.

### Content analysis

- cryptographic file fingerprints;
- connected-component grouping to avoid unmanageable pair lists;
- transparent fingerprint versioning.

### Evidence, policy, and reports

- stable rule identifiers;
- the versioned finding and coverage contracts;
- one conservative default policy;
- canonical JSON and JSON Schema;
- concise terminal output;
- documented CI exit-code semantics;
- reproducibility metadata and a configuration digest;
- explanations for every finding and every unsupported condition.

### Quality and maintenance

- PHI-free synthetic DICOM and raster fixtures;
- unit, integration, golden, privacy, and end-to-end tests;
- supported-data and limitation documentation;
- project, security, release, and citation documentation;
- installable wheels and source distribution.

v0.1.0 does not include decoded-pixel fingerprints, perceptual similarity,
HTML reporting, or embedding-based similarity. Those are later capabilities,
not hidden requirements for the first public release.

## Architecture

### Core components

1. **Discovery and input adapters** enumerate explicit sources and parse
   manifests without changing the dataset.
2. **Normalized catalog** represents every discovered artifact, its split,
   source namespace, parse state, normalized metadata, and fingerprint
   references.
3. **Detectors** consume the catalog and emit findings, coverage, and
   diagnostics. They are deterministic, stateless where practical, and
   read-only.
4. **Evidence model** provides the versioned canonical representation shared by
   all detectors.
5. **Policy evaluator** maps evidence and coverage to audit outcomes without
   modifying the underlying evidence. v0.1 ships one conservative policy;
   supported user-selectable profiles are future work.
6. **Report model** stores the complete audit result as canonical JSON.
7. **Renderers** create human-readable views exclusively from the canonical
   report. v0.1 includes terminal output; a static HTML renderer is deferred.

### Minimal interfaces

The architecture should stabilize only the interfaces necessary to keep these
responsibilities separate:

- `DatasetSpec` / `SplitSpec`: declared inputs and split policy context;
- `CatalogRecord`: normalized, immutable artifact metadata;
- `Detector`: catalog-to-detector-result contract;
- `DetectorResult`: findings, coverage, and diagnostics;
- `Finding`: versioned factual evidence;
- `AuditPolicy`: evidence-to-outcome rules;
- `AuditResult`: canonical, versioned report.

These interfaces form the alpha-stage v0.1 foundation. They may evolve before
v1.0, but their responsibility boundaries are enforced by the implementation
and tests. A public third-party plugin API is not required for v0.1.

### Proposed project structure

```text
medlint/
|-- pyproject.toml
|-- README.md
|-- ROADMAP.md
|-- LICENSE
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- SECURITY.md
|-- CITATION.cff
|-- src/
|   `-- medlint/
|       |-- api.py
|       |-- cli.py
|       |-- config.py
|       |-- catalog/
|       |-- io/
|       |   |-- manifest.py
|       |   |-- filesystem.py
|       |   |-- dicom.py
|       |   `-- raster.py
|       |-- fingerprints/
|       |-- detectors/
|       |-- evidence/
|       |-- policy/
|       |-- privacy/
|       `-- reporting/
|-- tests/
|   |-- unit/
|   |-- integration/
|   |-- golden/
|   |-- privacy/
|   |-- property/
|   |-- performance/
|   `-- fixtures/
|-- docs/
|   |-- concepts/
|   |-- rules/
|   |-- supported-data.md
|   |-- privacy.md
|   `-- contributing-detectors.md
|-- examples/
|   `-- quickstart/
|-- schemas/
|-- benchmarks/
`-- .github/workflows/
```

This is a target structure, not a requirement to create every file at project
initialization. Directories should be added only when their first real module or
document is needed.

## Development Phases

Phase 0 produces the first public v0.1.0 release. Later phases expand the
deterministic evidence engine and mature the user experience. Each phase must
end with reviewable evidence that its success criteria have been met. Later
phases should not compensate for an unresolved contract or correctness problem
in an earlier phase.

| Phase | Focus | Exit condition |
|---|---|---|
| 0 | First medical-specific vertical slice and v0.1.0 | Exact-file and basic DICOM cross-split findings with coverage and privacy-safe JSON |
| 1 | Deeper deterministic content detectors | Pixel and derived-copy oracle cases produce correct, explainable evidence |
| 2 | Policy configuration and report UX | Supported policy profiles and new renderers preserve evidence and privacy semantics |
| 3 | Hardening and API stabilization | Reproducible package, documented support boundary, successful pilots |

### Phase 0 - First public v0.1.0

**Estimated duration:** 2-3 weeks for one maintainer

**Status:** Release candidate; local gates passed and public v0.1.0 publication
is the remaining exit condition.

**Objective**

Finalize the small set of architectural contracts and publish a narrow,
medical-specific, end-to-end deterministic audit tool.

**Why this phase exists**

The first public release must be more than a package-name placeholder. It must
provide real value while keeping its claims narrow. The main early risk is
semantic ambiguity: what identifiers mean, what an exact-file fingerprint
proves, how incomplete coverage is represented, and where policy begins.

**Deliverables**

- approved architecture decision records for the decisions listed below;
- initial manifest, catalog, finding, coverage, and audit-result schemas;
- manifest and explicit split-root discovery;
- normalized catalog with privacy-safe internal record aliases;
- one exact file-fingerprint detector;
- a source/issuer-scoped PatientID cross-split detector plus separate
  StudyInstanceUID, SeriesInstanceUID, and SOPInstanceUID detectors;
- DICOM metadata parse and field-availability coverage;
- minimal evidence and policy evaluation path;
- concise terminal output;
- deterministic canonical JSON output;
- PHI-free synthetic fixtures and end-to-end tests;
- initial rule naming and schema versioning conventions;
- README, license, security guidance, and limitations;
- buildable wheel and source distribution;
- public GitHub repository and PyPI v0.1.0 release after all release checks pass.

**Success criteria**

- an n-way synthetic dataset can be discovered and normalized;
- an injected cross-split exact file duplicate is reported with an explanation;
- injected cross-split patient, study, series, and instance identifiers produce
  the correct evidence category;
- identifiers from different source namespaces are not silently combined;
- skipped or unreadable inputs appear in coverage;
- equivalent inputs produce deterministically ordered semantic JSON;
- default output contains no raw PatientID, DICOM identifier, or absolute path;
- source files remain unchanged;
- evidence and policy outcomes can be inspected independently;
- wheel and source distribution install successfully in a clean environment;
- the documented quickstart works against the PHI-free example data;
- GitHub and PyPI release metadata identify v0.1.0 as an alpha-stage API.

**Risks**

- prematurely exposing unstable classes as public API;
- privacy-safe aliases conflicting with determinism;
- an input schema too narrow for merged datasets;
- publishing before package, privacy, and installation checks pass.

**Entry dependencies (satisfied 2026-08-24)**

- approval of the Phase 0 architecture decisions;
- agreement on the v0.1 support boundary and terminology.

### Phase 1 - Deeper deterministic content evidence

**Estimated duration:** 4-6 weeks

**Objective**

Extend the explainable content evidence engine beyond byte-identical files.

**Deliverables**

- exact decoded-pixel fingerprinting with documented canonicalization;
- perceptual derived-copy candidate detection and secondary verification;
- richer dummy, missing, and low-information identifier analysis;
- properly scoped accession evidence;
- UID/pixel and identifier/content contradiction rules;
- scalable candidate grouping and richer component review for non-exact
  relationships;
- detector-specific codec and candidate-generation coverage;
- representative performance and memory benchmark harnesses.

**Success criteria**

- every new synthetic oracle case produces the expected evidence class;
- byte-identical and pixel-identical relationships remain distinguishable;
- DICOM identifiers are never treated as stronger evidence than their defined
  semantic level;
- pHash findings are labeled as possible derived copies, not patient matches;
- unsupported codecs, modalities, and multi-frame objects reduce coverage;
- same UID with changed pixels produces a conflict finding;
- detector results are stable under input-order changes;
- representative scans complete within documented time and memory budgets.

**Risks**

- DICOM decoder and transfer-syntax variability;
- incorrect pixel canonicalization;
- pHash false positives in homogeneous radiographs;
- quadratic comparison growth and oversized finding sets;
- de-identification removing or regenerating identifiers.

**Dependencies**

- Phase 0 schemas and rule conventions;
- explicit optional-codec support policy;
- PHI-free test cases covering difficult DICOM variants.

### Phase 2 - Policy configuration and reporting UX

**Estimated duration:** 3-4 weeks

**Objective**

Extend the already usable v0.1 workflow with deliberately supported policy
configuration and additional report views without weakening its uncertainty or
privacy semantics.

**Deliverables**

- a documented policy-profile selection mechanism;
- configurable fail/warn behavior with explicit, versioned semantics and no
  change to detector evidence;
- richer CLI filtering and terminal summaries for large audits;
- compatible schema evolution for any new policy-disposition fields;
- offline static HTML renderer driven only by canonical JSON;
- renderer privacy controls and path-sensitive report warnings;
- pilot audit procedure for representative research datasets.

**Success criteria**

- a researcher can select a supported policy profile and understand how it
  changes outcomes;
- terminal, JSON, and HTML views agree on the underlying evidence;
- new policy behavior is covered by compatibility and privacy tests;
- HTML output cannot expose paths or identifiers without explicit opt-in;
- pilot users can trace every policy outcome back to specific evidence.

**Risks**

- users interpreting a no-finding result as a leakage-free guarantee;
- policy configuration becoming a hidden scoring system;
- HTML accidentally exposing identifiers, paths, or burned-in PHI;
- report scale reducing usability.

**Dependencies**

- stable Phase 1 evidence and coverage output;
- approved default policy and privacy behavior.

### Phase 3 - Hardening and API stabilization

**Estimated duration:** 3-5 weeks

**Objective**

Mature the package toward a stable public API and a broader real-world support
contract without forcing a premature v1.0.0 release.

**Deliverables**

- property and performance suites beyond the v0.1 unit, integration, golden,
  and privacy baseline;
- Python and operating-system CI expansion beyond the initial Linux matrix;
- optional-codec CI strategy for detectors introduced after v0.1;
- cross-version schema, rule, wheel, and source-distribution compatibility
  tests;
- reviewed API stability and deprecation policy;
- usability revisions informed by external contributors and pilot users;
- at least three documented pilot audits using data that may be safely tested.

**Success criteria**

- package artifacts remain compatible across the documented support matrix;
- all supported synthetic, privacy, property, and performance cases pass across
  the expanded CI matrix;
- no real PHI or restricted dataset enters the repository or CI artifacts;
- results are reproducible within documented platform and codec constraints;
- unsupported data is documented and represented correctly in coverage;
- external researchers can use the public API and contribute a detector without
  relying on undocumented internals;
- the release documentation does not claim leakage certification or patient
  identification.

**Risks**

- dependency and codec drift;
- cross-platform pixel-decoding differences;
- premature API stability promises;
- maintainer burden from broad format expectations.

**Dependencies**

- successful representative pilots;
- stable v0.1 schemas, terminology, and support matrix.

## Release-Level Success Criteria

v0.1.0 succeeds if it can demonstrate all of the following:

- it finds known, injected file and basic DICOM identifier relationships in the
  supported scope;
- it does not overstate what any relationship proves;
- it exposes incomplete evidence rather than silently passing it;
- every finding is explainable and reproducible;
- default reports are safe for local research use and avoid raw PHI;
- the core installs without heavy ML dependencies or network access;
- its architecture accepts another deterministic detector without changes to
  catalog, evidence, policy, or report semantics;
- its wheel and source distribution install and run in a clean environment;
- its quickstart demonstrates an actionable pre-training check.

Downloads, stars, or detector count are not primary v0.1.0 success metrics.

## Versioning and Release Policy

medlint uses Python-compatible semantic versioning:

- v0.1.0 is the first functional public release produced by Phase 0;
- backward-compatible fixes to that release use v0.1.1, v0.1.2, and so on;
- meaningful new capability may advance the minor version to v0.2.0, v0.3.0,
  and later 0.x releases;
- internal phase numbers do not mechanically determine public version numbers;
- alpha, beta, or release-candidate suffixes are used only when a real external
  pre-release testing need exists;
- v1.0.0 is reserved for a documented and intentionally stable public API,
  report schema, CLI contract, and rule-ID compatibility policy.

Every production PyPI release must be created from a matching protected Git
tag after CI, package-build, clean-install, privacy, and smoke-test gates pass.
Publishing should use PyPI Trusted Publishing with a dedicated GitHub Actions
workflow and approval-protected release environment.

## Technical Risks and Mitigations

| Risk | Consequence | Initial mitigation |
|---|---|---|
| PatientID collisions across institutions | False patient-group relationships | Require source namespace and use IssuerOfPatientID when available |
| Removed, dummy, or regenerated identifiers | Missed relationships or false confidence | Measure usability, detect common dummy patterns, and report inconclusive coverage |
| Incorrect DICOM UID interpretation | Overstated patient evidence | Encode Study/Series/SOP semantics in stable rule definitions and tests |
| Pixel canonicalization errors | Missed or false exact-pixel matches | Separate stored-pixel and perceptual representations; specify and golden-test transformations |
| Codec and transfer-syntax variation | Platform-dependent coverage | Make codec support explicit and include decoder provenance in reports |
| Perceptual-hash ambiguity | False duplicate alerts | Use candidate plus secondary verification; conservative labeling and review workflow |
| Pairwise comparison growth | Excessive runtime and report volume | Index fingerprints, bucket candidates, group connected components, and benchmark early |
| Reported PHI or identifying paths | Privacy incident | Opaque aliases, default redaction, no thumbnails, privacy golden tests |
| No-finding result interpreted as certification | Scientific misuse | Prominent scope and coverage language in every output format |
| Detector and schema churn | Broken integrations and contributor confusion | Version schemas and rules; delay broad public API guarantees |
| Dependency creep | Loss of lightweight installation | Keep core dependencies narrow and isolate optional capabilities |
| Cross-platform nondeterminism | Irreproducible audits | Canonical ordering, normalized serialization, and platform/codec test matrices |

## Phase 0 Architecture Decisions

The Phase 0 decisions are recorded under [`docs/adr/`](docs/adr/). Any
replacement must state its compatibility and migration impact rather than
silently changing the contract in code.

| Record | Status | Decision |
|---|---|---|
| [ADR-0001](docs/adr/0001-product-contract.md) | Accepted | Evidence-first product contract and conservative terminology |
| [ADR-0002](docs/adr/0002-manifest-and-catalog.md) | Accepted | Manifest, split-root discovery, and normalized catalog semantics |
| [ADR-0003](docs/adr/0003-dicom-identity-semantics.md) | Accepted | Source/issuer-scoped PatientID and acquisition-level UID semantics |
| [ADR-0004](docs/adr/0004-evidence-and-policy.md) | Accepted | Detector, evidence, policy, and renderer separation |
| [ADR-0005](docs/adr/0005-coverage-states.md) | Accepted | Split-aware coverage, audit states, and exit-code precedence |
| [ADR-0006](docs/adr/0006-privacy-aliases.md) | Accepted | Default redaction, run-local aliases, and explicit path opt-in |
| [ADR-0007](docs/adr/0007-report-versioning.md) | Accepted | Canonical JSON, schema, rule, and serialization versioning |
| [ADR-0008](docs/adr/0008-v010-support-matrix.md) | Accepted | Exact v0.1.0 data and dependency support boundary |
| [ADR-0009](docs/adr/0009-pixel-canonicalization.md) | Deferred | Pixel canonicalization and perceptual representations are excluded from v0.1.0 |

## Future Extension Possibilities

Future work should be driven by validated user needs and representative data,
not by a goal of maximizing feature count.

### Additional deterministic evidence

- stronger manifest/group mapping support;
- dataset provenance and export-batch evidence;
- temporal and visit-level policy profiles;
- additional DICOM metadata consistency rules;
- integrations that export canonical findings to DVC, FiftyOne, CI annotation,
  or other research workflows;
- richer scalable candidate indexes and component visualization.

### Additional modalities

- mammography, OCT, ultrasound, and digital pathology adapters;
- multi-frame and 3D CT/MRI support with modality-specific catalog and
  fingerprint semantics;
- modality-specific perceptual similarity only after separate validation.

Each modality must define what constitutes an artifact, acquisition, series,
and meaningful pixel representation. Universal image normalization should not
be assumed.

### Optional experimental model-based module

Embedding-based same-subject similarity may be explored in a later v0.2 or
v1.x experimental extension. It is not a committed roadmap phase.

Before such a module is accepted, it requires:

- a separate privacy and dual-use review;
- license and pretraining-data provenance review;
- patient-disjoint development, calibration, and test identities;
- exact and perceptual duplicates removed from its primary evaluation;
- hard negatives and realistic contamination prevalence;
- at least two untouched external sites;
- review-budget, false-alert, incremental-yield, and worst-group metrics;
- an externally fixed go/no-go threshold;
- conservative "suspected same-subject visual relationship" terminology;
- optional dependencies isolated from the core package;
- no ability to produce a blocking result by itself in its first release.

If the scientific gate fails, medlint remains a complete deterministic
split-integrity auditor. The core architecture must not depend on the future
module succeeding.

### Contributor extensibility

If external detector contributions become frequent, the project may later
stabilize a public detector API or Python entry-point mechanism. That decision
should follow demonstrated need, compatibility tests, and a clear maintenance
policy; it should not be pre-built into v0.1.

## Definition of Done for the Roadmap

The project owner approved entry into Phase 0 on 2026-08-24, including:

- the product wording and non-goals;
- the v0.1.0 support boundary and first-release definition;
- the phase sequence and v0.1.0-first release policy;
- the eight accepted Phase 0 architecture decisions and the explicit deferral
  of pixel canonicalization;
- the rule that embedding-based similarity remains outside the core roadmap.

The Phase 0 implementation is now at release-candidate status. Public v0.1.0
publication and post-publication installation verification close the phase.
