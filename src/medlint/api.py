"""Public, read-only audit API."""

from __future__ import annotations

import platform
from collections.abc import Iterable
from importlib import metadata
from pathlib import Path

from medlint.catalog import CatalogCoverage, DatasetCatalog, build_catalog
from medlint.config import AuditConfig, DatasetSpec, SplitSpec
from medlint.detectors import built_in_detectors
from medlint.evidence import AuditResult, Diagnostic
from medlint.evidence.models import RecordReference
from medlint.io import DiscoveryError, discover
from medlint.policy import AuditPolicy, ConservativeDefaultPolicy

SCHEMA_VERSION = "1.0.0"


def _package_version(distribution: str, fallback: str) -> str:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return fallback


def _provenance() -> tuple[tuple[str, str], ...]:
    return (
        ("medlint", _package_version("medlint", "0+local")),
        ("pydicom", _package_version("pydicom", "unavailable")),
        ("python", platform.python_version()),
    )


def _diagnostics(catalog: DatasetCatalog) -> tuple[Diagnostic, ...]:
    messages = {
        "dicom_dependency_unavailable": (
            "DICOM metadata could not be evaluated because pydicom is unavailable."
        ),
        "dicom_modality_missing": (
            "The DICOM modality is missing, so the v0.1 primary profile could not "
            "be confirmed."
        ),
        "dicom_modality_outside_primary_profile": (
            "The DICOM modality is outside the v0.1 primary CR/DX profile."
        ),
        "dicom_multiframe_inventory": (
            "A multi-frame DICOM object was inventoried outside the v0.1 primary "
            "profile."
        ),
        "dicom_parse_failed": "DICOM metadata could not be parsed.",
        "dicom_structure_missing": (
            "The file did not contain recognizable DICOM structure."
        ),
        "empty_declared_split": (
            "At least one declared split contained no discovered record."
        ),
        "file_hash_failed": "The file could not be read for exact fingerprinting.",
        "file_probe_failed": (
            "The extensionless file could not be inspected for a DICOM preamble."
        ),
        "insufficient_evaluable_splits": (
            "Fewer than two splits contained records evaluable by the active checks."
        ),
        "insufficient_split_count": (
            "A split-integrity audit requires at least two distinct splits."
        ),
        "non_regular_file": "A non-regular filesystem entry was not inspected.",
        "path_missing": "A declared input path does not exist.",
        "patient_id_dummy": (
            "The PatientID was excluded because it is a common dummy value."
        ),
        "patient_id_missing": "No PatientID was available for this DICOM record.",
        "symlink_not_followed": (
            "A symbolic link was inventoried but not followed or inspected."
        ),
        "unsupported_file_type": "The file type is not supported by v0.1 detectors.",
    }
    diagnostics: list[Diagnostic] = []
    for record in catalog.records:
        for issue in record.issues:
            diagnostics.append(
                Diagnostic(
                    code=issue.code,
                    severity="warning",
                    message=messages.get(
                        issue.code,
                        "Evidence was unavailable for this record.",
                    ),
                    record_alias=record.alias,
                )
            )
    dataset_codes = {code for code, _ in catalog.coverage.issue_counts}
    for code in (
        "insufficient_split_count",
        "empty_declared_split",
        "insufficient_evaluable_splits",
    ):
        if code in dataset_codes:
            diagnostics.append(
                Diagnostic(
                    code=code,
                    severity="warning",
                    message=messages[code],
                )
            )
    diagnostics.sort(
        key=lambda item: (item.severity, item.code, item.record_alias or "")
    )
    return tuple(diagnostics)


def _empty_coverage(issue_code: str) -> CatalogCoverage:
    return CatalogCoverage(
        declared_split_count=0,
        populated_split_count=0,
        evaluable_split_count=0,
        discovered=0,
        supported=0,
        hashed=0,
        dicom_candidates=0,
        dicom_parsed=0,
        dicom_identity_incomplete=0,
        outside_primary_profile=0,
        unsupported=0,
        unreadable=0,
        issue_counts=((issue_code, 1),),
    )


def _operational_result(
    spec: DatasetSpec,
    *,
    config: AuditConfig,
    policy: AuditPolicy,
    code: str,
    message: str,
) -> AuditResult:
    coverage = _empty_coverage(code)
    outcome = policy.evaluate((), coverage, (), operational_error=True)
    splits = tuple(sorted({split.name for split in spec.splits}))
    return AuditResult(
        schema_version=SCHEMA_VERSION,
        tool_version=_package_version("medlint", "0+local"),
        config_digest=config.digest(),
        splits=splits,
        findings=(),
        catalog_coverage=coverage,
        detector_coverage=(),
        diagnostics=(Diagnostic(code=code, severity="error", message=message),),
        policy_outcome=outcome,
        provenance=_provenance(),
        _protected_files=(
            () if spec.manifest is None else (spec.manifest.expanduser().absolute(),)
        ),
        _protected_roots=tuple(
            split.root.expanduser().absolute() for split in spec.splits
        ),
    )


def audit(
    dataset: DatasetSpec,
    *,
    config: AuditConfig | None = None,
    policy: AuditPolicy | None = None,
) -> AuditResult:
    """Run the deterministic v0.1 split-integrity audit.

    The function reads source files but never writes to or modifies them.  All
    default serialized output is privacy-safe and path-free.
    """

    resolved_config = config or AuditConfig()
    resolved_policy = policy or ConservativeDefaultPolicy()
    detectors_by_id = {
        detector.detector_id: detector for detector in built_in_detectors()
    }
    unknown = tuple(
        detector_id
        for detector_id in resolved_config.enabled_detector_ids
        if detector_id not in detectors_by_id
    )
    if unknown:
        return _operational_result(
            dataset,
            config=resolved_config,
            policy=resolved_policy,
            code="unknown_detector_configuration",
            message="The audit configuration contains an unknown detector identifier.",
        )

    try:
        artifacts = discover(dataset)
    except DiscoveryError:
        return _operational_result(
            dataset,
            config=resolved_config,
            policy=resolved_policy,
            code="discovery_failed",
            message="Dataset discovery could not be completed.",
        )

    declared_splits = (
        tuple(sorted(split.name for split in dataset.splits))
        if dataset.splits
        else tuple(sorted({artifact.split for artifact in artifacts}))
    )
    catalog = build_catalog(
        artifacts,
        config=resolved_config,
        declared_splits=declared_splits,
    )

    detector_results = tuple(
        detectors_by_id[detector_id].run(catalog)
        for detector_id in resolved_config.enabled_detector_ids
    )
    findings = tuple(
        sorted(
            (
                finding
                for detector_result in detector_results
                for finding in detector_result.findings
            ),
            key=lambda item: (
                item.rule_id,
                item.splits,
                item.record_aliases,
                item.component_id,
            ),
        )
    )
    detector_coverage = tuple(result.coverage for result in detector_results)
    outcome = resolved_policy.evaluate(
        findings,
        catalog.coverage,
        detector_coverage,
    )
    diagnostics = tuple(
        sorted(
            (
                *_diagnostics(catalog),
                *(
                    diagnostic
                    for detector_result in detector_results
                    for diagnostic in detector_result.diagnostics
                ),
            ),
            key=lambda item: (item.severity, item.code, item.record_alias or ""),
        )
    )

    return AuditResult(
        schema_version=SCHEMA_VERSION,
        tool_version=_package_version("medlint", "0+local"),
        config_digest=resolved_config.digest(),
        splits=catalog.splits,
        findings=findings,
        catalog_coverage=catalog.coverage,
        detector_coverage=detector_coverage,
        diagnostics=diagnostics,
        policy_outcome=outcome,
        provenance=_provenance(),
        _record_references=tuple(
            RecordReference(alias=record.alias, path=record.path)
            for record in catalog.records
        ),
        _protected_files=(
            ()
            if dataset.manifest is None
            else (dataset.manifest.expanduser().absolute(),)
        ),
        _protected_roots=tuple(
            split.root.expanduser().absolute() for split in dataset.splits
        ),
    )


def audit_manifest(
    manifest: str | Path,
    *,
    config: AuditConfig | None = None,
    policy: AuditPolicy | None = None,
) -> AuditResult:
    return audit(
        DatasetSpec.from_manifest(manifest),
        config=config,
        policy=policy,
    )


def audit_split_roots(
    splits: Iterable[SplitSpec],
    *,
    config: AuditConfig | None = None,
    policy: AuditPolicy | None = None,
) -> AuditResult:
    return audit(
        DatasetSpec.from_split_roots(splits),
        config=config,
        policy=policy,
    )
