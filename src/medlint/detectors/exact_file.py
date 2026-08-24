"""Cross-split byte-identical file evidence."""

from __future__ import annotations

from collections import Counter

from medlint.catalog import DatasetCatalog
from medlint.evidence import (
    DetectorCoverage,
    DetectorResult,
    EvidenceCategory,
)

from ._grouping import cross_split_findings


class ExactFileDetector:
    detector_id = "ML001"
    rule_version = "1"

    def run(self, catalog: DatasetCatalog) -> DetectorResult:
        eligible = tuple(record for record in catalog.records if record.supported)
        evaluated = tuple(
            record for record in eligible if record.file_sha256 is not None
        )
        unavailable = len(eligible) - len(evaluated)
        reasons = Counter(
            issue.code
            for record in eligible
            if record.file_sha256 is None
            for issue in record.issues
            if issue.category == "unreadable"
        )
        findings = cross_split_findings(
            evaluated,
            key=lambda record: record.file_sha256,
            rule_id=self.detector_id,
            rule_version=self.rule_version,
            category=EvidenceCategory.EXACT_FILE_CONTENT_RELATIONSHIP,
            strength="exact_content_match",
            observed_fact=(
                "{record_count} records in {split_count} splits have identical "
                "file bytes."
            ),
            method="SHA-256 over the complete stored file bytes",
            explanation=(
                "The same byte content was observed in more than one declared split, "
                "which is a potential split-contamination risk."
            ),
            limitation=(
                "This proves an exact content relationship, not patient identity; it "
                "does not detect files rewritten with different metadata or encoding."
            ),
            recommendation=(
                "Review the source records and split assignment before model training."
            ),
        )
        return DetectorResult(
            detector_id=self.detector_id,
            findings=findings,
            coverage=DetectorCoverage(
                detector_id=self.detector_id,
                eligible_records=len(eligible),
                evaluated_records=len(evaluated),
                unavailable_records=unavailable,
                eligible_splits=tuple(sorted({record.split for record in eligible})),
                evaluated_splits=tuple(sorted({record.split for record in evaluated})),
                reason_counts=tuple(sorted(reasons.items())),
            ),
        )
