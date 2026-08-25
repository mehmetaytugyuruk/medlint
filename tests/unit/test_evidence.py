from __future__ import annotations

import pytest

from medlint.evidence import DetectorCoverage, DetectorResult


def test_detector_result_requires_matching_coverage_identifier() -> None:
    coverage = DetectorCoverage(
        detector_id="ML001",
        eligible_records=0,
        evaluated_records=0,
        unavailable_records=0,
        eligible_splits=(),
        evaluated_splits=(),
    )

    with pytest.raises(ValueError, match="coverage identifiers must match"):
        DetectorResult(detector_id="ML999", findings=(), coverage=coverage)
