"""Explicitly registered deterministic v0.1 detectors."""

from .base import Detector
from .dicom_identifiers import (
    PatientGroupDetector,
    SeriesInstanceDetector,
    SopInstanceDetector,
    StudyInstanceDetector,
)
from .exact_file import ExactFileDetector


def built_in_detectors() -> tuple[Detector, ...]:
    """Return the fixed v0.1 detector set; this is not a plugin registry."""

    detectors: tuple[Detector, ...] = (
        ExactFileDetector(),
        PatientGroupDetector(),
        StudyInstanceDetector(),
        SeriesInstanceDetector(),
        SopInstanceDetector(),
    )
    return detectors


__all__ = [
    "Detector",
    "ExactFileDetector",
    "PatientGroupDetector",
    "SeriesInstanceDetector",
    "SopInstanceDetector",
    "StudyInstanceDetector",
    "built_in_detectors",
]
