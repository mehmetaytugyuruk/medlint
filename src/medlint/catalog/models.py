"""Normalized immutable records used by all built-in detectors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RecordIssue:
    code: str
    category: str


@dataclass(frozen=True, slots=True)
class DicomSignals:
    """Privacy-preserving DICOM evidence signals.

    Tokens are run-local equality keys.  They must never be serialized or
    treated as public stable identifiers.
    """

    patient_id_status: str
    patient_group_token: str | None
    study_uid_token: str | None
    series_uid_token: str | None
    sop_uid_token: str | None
    modality: str | None
    number_of_frames: int | None


@dataclass(frozen=True, slots=True)
class CatalogRecord:
    alias: str
    split: str
    source_namespace: str
    path: Path
    media_type: str
    supported: bool
    file_sha256: str | None
    dicom: DicomSignals | None
    issues: tuple[RecordIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class CatalogCoverage:
    declared_split_count: int
    populated_split_count: int
    evaluable_split_count: int
    discovered: int
    supported: int
    hashed: int
    dicom_candidates: int
    dicom_parsed: int
    dicom_identity_incomplete: int
    outside_primary_profile: int
    unsupported: int
    unreadable: int
    issue_counts: tuple[tuple[str, int], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "declared_split_count": self.declared_split_count,
            "populated_split_count": self.populated_split_count,
            "evaluable_split_count": self.evaluable_split_count,
            "discovered": self.discovered,
            "supported": self.supported,
            "hashed": self.hashed,
            "dicom_candidates": self.dicom_candidates,
            "dicom_parsed": self.dicom_parsed,
            "dicom_identity_incomplete": self.dicom_identity_incomplete,
            "outside_primary_profile": self.outside_primary_profile,
            "unsupported": self.unsupported,
            "unreadable": self.unreadable,
            "issue_counts": [
                {"code": code, "count": count} for code, count in self.issue_counts
            ],
        }


@dataclass(frozen=True, slots=True)
class DatasetCatalog:
    records: tuple[CatalogRecord, ...]
    coverage: CatalogCoverage
    declared_splits: tuple[str, ...]

    @property
    def splits(self) -> tuple[str, ...]:
        return self.declared_splits
