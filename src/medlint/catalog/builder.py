"""Build the normalized catalog without modifying source data."""

from __future__ import annotations

from collections import Counter

from medlint.config import AuditConfig
from medlint.fingerprints import sha256_file
from medlint.io import DiscoveredArtifact
from medlint.io.dicom import (
    ParsedDicomMetadata,
    classify_path,
    parse_dicom_metadata,
)
from medlint.privacy import IdentifierTokenizer, assign_record_aliases

from .models import (
    CatalogCoverage,
    CatalogRecord,
    DatasetCatalog,
    DicomSignals,
    RecordIssue,
)


def _tokenize_dicom(
    metadata: ParsedDicomMetadata,
    *,
    source_namespace: str,
    tokenizer: IdentifierTokenizer,
) -> DicomSignals:
    patient_id = metadata.patient_id
    patient_status = metadata.patient_id_status
    issuer = metadata.issuer_of_patient_id

    patient_token = None
    if patient_status == "usable" and patient_id is not None:
        patient_token = tokenizer.token(
            "patient-group-v1",
            (source_namespace, issuer or "", patient_id),
        )

    def uid_token(domain: str, value: str | None) -> str | None:
        return None if value is None else tokenizer.token(domain, (value,))

    return DicomSignals(
        patient_id_status=patient_status,
        patient_group_token=patient_token,
        study_uid_token=uid_token("study-instance-uid-v1", metadata.study_instance_uid),
        series_uid_token=uid_token(
            "series-instance-uid-v1", metadata.series_instance_uid
        ),
        sop_uid_token=uid_token("sop-instance-uid-v1", metadata.sop_instance_uid),
        modality=metadata.modality,
        number_of_frames=metadata.number_of_frames,
    )


def _build_record(
    artifact: DiscoveredArtifact,
    alias: str,
    *,
    config: AuditConfig,
    tokenizer: IdentifierTokenizer,
) -> CatalogRecord:
    if artifact.discovery_issue is not None:
        return CatalogRecord(
            alias=alias,
            split=artifact.split,
            source_namespace=artifact.source_namespace,
            path=artifact.path,
            media_type="unavailable",
            supported=False,
            file_sha256=None,
            dicom=None,
            issues=(RecordIssue(artifact.discovery_issue, "unreadable"),),
        )

    media_type, classification_issue = classify_path(artifact.path)
    issues: list[RecordIssue] = []
    supported = media_type in {"dicom", "raster"}
    if classification_issue is not None:
        category = "unreadable" if media_type == "unreadable" else "unsupported"
        issues.append(RecordIssue(classification_issue, category))

    file_hash: str | None = None
    if supported:
        try:
            file_hash = sha256_file(
                artifact.path,
                chunk_bytes=config.file_hash_chunk_bytes,
            )
        except (OSError, ValueError):
            issues.append(RecordIssue("file_hash_failed", "unreadable"))

    dicom_signals = None
    if media_type == "dicom":
        parse_result = parse_dicom_metadata(artifact.path)
        if parse_result.metadata is None:
            issues.append(
                RecordIssue(
                    parse_result.error_code or "dicom_parse_failed",
                    "unreadable",
                )
            )
        else:
            dicom_signals = _tokenize_dicom(
                parse_result.metadata,
                source_namespace=artifact.source_namespace,
                tokenizer=tokenizer,
            )
            if dicom_signals.patient_id_status == "missing":
                issues.append(RecordIssue("patient_id_missing", "metadata_unavailable"))
            elif dicom_signals.patient_id_status == "dummy":
                issues.append(RecordIssue("patient_id_dummy", "metadata_unavailable"))
            if (
                dicom_signals.number_of_frames is not None
                and dicom_signals.number_of_frames > 1
            ):
                issues.append(
                    RecordIssue(
                        "dicom_multiframe_inventory",
                        "outside_primary_profile",
                    )
                )
            if dicom_signals.modality is None:
                issues.append(
                    RecordIssue(
                        "dicom_modality_missing",
                        "outside_primary_profile",
                    )
                )
            elif dicom_signals.modality not in {"CR", "DX"}:
                issues.append(
                    RecordIssue(
                        "dicom_modality_outside_primary_profile",
                        "outside_primary_profile",
                    )
                )

    return CatalogRecord(
        alias=alias,
        split=artifact.split,
        source_namespace=artifact.source_namespace,
        path=artifact.path,
        media_type=media_type,
        supported=supported,
        file_sha256=file_hash,
        dicom=dicom_signals,
        issues=tuple(sorted(issues, key=lambda issue: (issue.category, issue.code))),
    )


def build_catalog(
    artifacts: tuple[DiscoveredArtifact, ...],
    *,
    config: AuditConfig,
    declared_splits: tuple[str, ...] | None = None,
) -> DatasetCatalog:
    """Normalize discovered artifacts into an immutable catalog."""

    aliases = assign_record_aliases(len(artifacts))
    tokenizer = IdentifierTokenizer()
    records = tuple(
        _build_record(
            artifact,
            alias,
            config=config,
            tokenizer=tokenizer,
        )
        for artifact, alias in zip(artifacts, aliases, strict=True)
    )

    normalized_declared_splits = tuple(
        sorted(
            set(declared_splits)
            if declared_splits is not None
            else {artifact.split for artifact in artifacts}
        )
    )
    populated_splits = {record.split for record in records}
    evaluable_splits = {
        record.split
        for record in records
        if record.file_sha256 is not None or record.dicom is not None
    }

    issue_counts = Counter(issue.code for record in records for issue in record.issues)
    if len(normalized_declared_splits) < 2:
        issue_counts["insufficient_split_count"] += 1
    empty_split_count = len(set(normalized_declared_splits) - populated_splits)
    if empty_split_count:
        issue_counts["empty_declared_split"] += empty_split_count
    if len(evaluable_splits) < 2:
        issue_counts["insufficient_evaluable_splits"] += 1

    coverage = CatalogCoverage(
        declared_split_count=len(normalized_declared_splits),
        populated_split_count=len(populated_splits),
        evaluable_split_count=len(evaluable_splits),
        discovered=len(records),
        supported=sum(record.supported for record in records),
        hashed=sum(record.file_sha256 is not None for record in records),
        dicom_candidates=sum(record.media_type == "dicom" for record in records),
        dicom_parsed=sum(record.dicom is not None for record in records),
        dicom_identity_incomplete=sum(
            record.dicom is not None
            and (
                record.dicom.patient_group_token is None
                or record.dicom.study_uid_token is None
                or record.dicom.series_uid_token is None
                or record.dicom.sop_uid_token is None
            )
            for record in records
        ),
        outside_primary_profile=sum(
            any(issue.category == "outside_primary_profile" for issue in record.issues)
            for record in records
        ),
        unsupported=sum(record.media_type == "unsupported" for record in records),
        unreadable=sum(
            any(issue.category == "unreadable" for issue in record.issues)
            for record in records
        ),
        issue_counts=tuple(sorted(issue_counts.items())),
    )
    return DatasetCatalog(
        records=records,
        coverage=coverage,
        declared_splits=normalized_declared_splits,
    )
