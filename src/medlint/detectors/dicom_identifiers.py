"""Conservative cross-split DICOM identifier evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from medlint.catalog import CatalogRecord, DatasetCatalog, DicomSignals
from medlint.evidence import (
    DetectorCoverage,
    DetectorResult,
    EvidenceCategory,
)

from ._grouping import cross_split_findings

TokenGetter = Callable[[DicomSignals], str | None]


@dataclass(frozen=True, slots=True)
class _IdentifierRule:
    detector_id: str
    token_getter: TokenGetter
    category: EvidenceCategory
    strength: str
    field_label: str
    explanation: str
    limitation: str


class _DicomIdentifierDetector:
    rule_version = "1"
    rule: _IdentifierRule

    @property
    def detector_id(self) -> str:
        return self.rule.detector_id

    def run(self, catalog: DatasetCatalog) -> DetectorResult:
        eligible = tuple(
            record for record in catalog.records if record.media_type == "dicom"
        )

        def token(record: CatalogRecord) -> str | None:
            if record.dicom is None:
                return None
            return self.rule.token_getter(record.dicom)

        evaluated = tuple(record for record in eligible if token(record) is not None)
        missing_reasons: Counter[str] = Counter()
        for record in eligible:
            if token(record) is not None:
                continue
            if record.dicom is None:
                missing_reasons["dicom_metadata_unavailable"] += 1
            elif self.detector_id == "ML101":
                missing_reasons[f"patient_id_{record.dicom.patient_id_status}"] += 1
            else:
                missing_reasons["identifier_missing_or_invalid"] += 1

        findings = cross_split_findings(
            evaluated,
            key=token,
            rule_id=self.detector_id,
            rule_version=self.rule_version,
            category=self.rule.category,
            strength=self.rule.strength,
            observed_fact=(
                "{record_count} DICOM records in {split_count} splits share "
                f"the same usable {self.rule.field_label}."
            ),
            method=f"Exact normalized {self.rule.field_label} equality",
            explanation=self.rule.explanation,
            limitation=self.rule.limitation,
            recommendation=(
                "Review the related source records and intended split policy before "
                "model training."
            ),
        )
        return DetectorResult(
            detector_id=self.detector_id,
            findings=findings,
            coverage=DetectorCoverage(
                detector_id=self.detector_id,
                eligible_records=len(eligible),
                evaluated_records=len(evaluated),
                unavailable_records=len(eligible) - len(evaluated),
                eligible_splits=tuple(sorted({record.split for record in eligible})),
                evaluated_splits=tuple(sorted({record.split for record in evaluated})),
                reason_counts=tuple(sorted(missing_reasons.items())),
            ),
        )


class PatientGroupDetector(_DicomIdentifierDetector):
    rule = _IdentifierRule(
        detector_id="ML101",
        token_getter=lambda value: value.patient_group_token,
        category=EvidenceCategory.AUTHORITATIVE_GROUP_RELATIONSHIP,
        strength="scoped_identifier_match",
        field_label="source/issuer-scoped PatientID",
        explanation=(
            "A usable PatientID within the same declared source and issuer scope "
            "appears in more than one split, which may conflict with a new-patient "
            "evaluation design."
        ),
        limitation=(
            "PatientID is an administrative identifier, may be reused or regenerated, "
            "and does not prove a person's real-world identity."
        ),
    )


class StudyInstanceDetector(_DicomIdentifierDetector):
    rule = _IdentifierRule(
        detector_id="ML102",
        token_getter=lambda value: value.study_uid_token,
        category=EvidenceCategory.ACQUISITION_IDENTIFIER_RELATIONSHIP,
        strength="acquisition_identifier_match",
        field_label="StudyInstanceUID",
        explanation=(
            "The same DICOM study identifier appears in more than one split, which "
            "indicates a shared acquisition-level relationship."
        ),
        limitation=(
            "A StudyInstanceUID identifies a study, not a real-world patient, and "
            "incorrect or regenerated UIDs remain possible."
        ),
    )


class SeriesInstanceDetector(_DicomIdentifierDetector):
    rule = _IdentifierRule(
        detector_id="ML103",
        token_getter=lambda value: value.series_uid_token,
        category=EvidenceCategory.ACQUISITION_IDENTIFIER_RELATIONSHIP,
        strength="acquisition_identifier_match",
        field_label="SeriesInstanceUID",
        explanation=(
            "The same DICOM series identifier appears in more than one split, which "
            "indicates a shared series-level relationship."
        ),
        limitation=(
            "A SeriesInstanceUID identifies a series, not a real-world patient, and "
            "incorrect or regenerated UIDs remain possible."
        ),
    )


class SopInstanceDetector(_DicomIdentifierDetector):
    rule = _IdentifierRule(
        detector_id="ML104",
        token_getter=lambda value: value.sop_uid_token,
        category=EvidenceCategory.ACQUISITION_IDENTIFIER_RELATIONSHIP,
        strength="acquisition_identifier_match",
        field_label="SOPInstanceUID",
        explanation=(
            "The same DICOM object identifier appears in more than one split, which "
            "indicates a shared instance-level relationship."
        ),
        limitation=(
            "A SOPInstanceUID identifies a DICOM object, not a real-world patient, "
            "and incorrect or regenerated UIDs remain possible."
        ),
    )
