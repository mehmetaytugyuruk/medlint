"""Minimal, metadata-only DICOM parsing for the v0.1 evidence engine."""

from __future__ import annotations

import logging
import re
import unicodedata
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

DICOM_SUFFIXES = frozenset({".dcm", ".dicom"})
RASTER_SUFFIXES = frozenset({".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff"})


@dataclass(frozen=True, slots=True)
class ParsedDicomMetadata:
    patient_id: str | None
    patient_id_status: str
    issuer_of_patient_id: str | None
    study_instance_uid: str | None
    series_instance_uid: str | None
    sop_instance_uid: str | None
    modality: str | None
    number_of_frames: int | None


@dataclass(frozen=True, slots=True)
class DicomParseResult:
    metadata: ParsedDicomMetadata | None
    error_code: str | None = None


_DUMMY_PATIENT_IDS = frozenset(
    {
        "0",
        "anon",
        "anonymous",
        "anonymized",
        "deidentified",
        "dummy",
        "na",
        "none",
        "null",
        "patient",
        "removed",
        "test",
        "unknown",
        "unk",
        "withheld",
    }
)


class _DiscardPydicomValidationLogs(logging.Filter):
    """Prevent pydicom validation messages from bypassing the privacy boundary."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.funcName != "warn_and_log"


@contextmanager
def _suppress_pydicom_messages() -> Iterator[None]:
    """Keep raw DICOM values out of warnings and logging output.

    pydicom's value validation reports through both :mod:`warnings` and its
    ``pydicom`` logger, and those messages may embed the rejected value.  The
    caller converts failures and unavailable evidence into medlint's stable,
    path-free diagnostic categories instead.
    """

    logger = logging.getLogger("pydicom")
    log_filter = _DiscardPydicomValidationLogs()
    logger.addFilter(log_filter)
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=UserWarning,
                module=r"^pydicom(?:\.|$)",
            )
            yield
    finally:
        logger.removeFilter(log_filter)


def _clean_text(value: object | None) -> str | None:
    if value is None:
        return None
    cleaned = unicodedata.normalize("NFKC", str(value)).replace("\x00", "").strip()
    return cleaned or None


def patient_id_status(value: str | None) -> str:
    if value is None:
        return "missing"
    compact = re.sub(r"[\s_./-]+", "", value).casefold()
    if compact in _DUMMY_PATIENT_IDS:
        return "dummy"
    if compact and (set(compact) <= {"0"} or set(compact) <= {"x"}):
        return "dummy"
    return "usable"


def has_dicom_preamble(path: Path) -> tuple[bool, str | None]:
    """Check the Part 10 ``DICM`` preamble without parsing the file."""

    try:
        with path.open("rb") as stream:
            header = stream.read(132)
    except OSError:
        return False, "file_probe_failed"
    return len(header) >= 132 and header[128:132] == b"DICM", None


def classify_path(path: Path) -> tuple[str, str | None]:
    """Return ``dicom``, ``raster``, ``unsupported``, or ``unreadable``."""

    suffix = path.suffix.casefold()
    if suffix in DICOM_SUFFIXES:
        return "dicom", None
    if suffix in RASTER_SUFFIXES:
        return "raster", None
    if not suffix:
        is_dicom, error = has_dicom_preamble(path)
        if error is not None:
            return "unreadable", error
        if is_dicom:
            return "dicom", None
    return "unsupported", "unsupported_file_type"


def _dataset_has_dicom_structure(dataset: object) -> bool:
    return any(
        getattr(dataset, name, None) is not None
        for name in (
            "SOPClassUID",
            "SOPInstanceUID",
            "StudyInstanceUID",
            "SeriesInstanceUID",
            "PatientID",
            "Modality",
            "Rows",
            "Columns",
        )
    )


def _valid_uid(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        from pydicom.uid import UID

        return value if UID(value).is_valid else None
    except Exception:
        return None


def parse_dicom_metadata(path: Path) -> DicomParseResult:
    """Read only the metadata needed by v0.1 detectors.

    Raw identifiers are returned only to the catalog builder, which immediately
    converts them to run-local equality tokens and then discards them.
    """

    try:
        import pydicom
    except ImportError:
        return DicomParseResult(None, "dicom_dependency_unavailable")

    tags = [
        "PatientID",
        "IssuerOfPatientID",
        "StudyInstanceUID",
        "SeriesInstanceUID",
        "SOPInstanceUID",
        "SOPClassUID",
        "Modality",
        "NumberOfFrames",
        "Rows",
        "Columns",
    ]
    with _suppress_pydicom_messages():
        try:
            dataset = pydicom.dcmread(
                path,
                stop_before_pixels=True,
                specific_tags=tags,
                force=True,
            )
        except (OSError, ValueError, EOFError):
            return DicomParseResult(None, "dicom_parse_failed")
        except Exception:
            # Decoder/library failures must be visible but error text may contain a
            # sensitive path, so only a stable category crosses this boundary.
            return DicomParseResult(None, "dicom_parse_failed")

        if not _dataset_has_dicom_structure(dataset):
            return DicomParseResult(None, "dicom_structure_missing")

        patient_id = _clean_text(getattr(dataset, "PatientID", None))
        frames_text = _clean_text(getattr(dataset, "NumberOfFrames", None))
        try:
            number_of_frames = None if frames_text is None else int(frames_text)
        except (TypeError, ValueError):
            number_of_frames = None

        metadata = ParsedDicomMetadata(
            patient_id=patient_id,
            patient_id_status=patient_id_status(patient_id),
            issuer_of_patient_id=_clean_text(
                getattr(dataset, "IssuerOfPatientID", None)
            ),
            study_instance_uid=_valid_uid(
                _clean_text(getattr(dataset, "StudyInstanceUID", None))
            ),
            series_instance_uid=_valid_uid(
                _clean_text(getattr(dataset, "SeriesInstanceUID", None))
            ),
            sop_instance_uid=_valid_uid(
                _clean_text(getattr(dataset, "SOPInstanceUID", None))
            ),
            modality=_clean_text(getattr(dataset, "Modality", None)),
            number_of_frames=number_of_frames,
        )
        return DicomParseResult(metadata)
