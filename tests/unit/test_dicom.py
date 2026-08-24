from __future__ import annotations

import logging
import warnings
from pathlib import Path

from conftest import write_test_dicom
from medlint.io.dicom import classify_path, parse_dicom_metadata, patient_id_status


def test_parse_dicom_reads_only_supported_identity_signals(tmp_path: Path) -> None:
    path = write_test_dicom(tmp_path / "image.dcm")

    result = parse_dicom_metadata(path)

    assert result.error_code is None
    assert result.metadata is not None
    assert result.metadata.patient_id == "PATIENT-001"
    assert result.metadata.patient_id_status == "usable"
    assert result.metadata.issuer_of_patient_id == "TEST-HOSPITAL"
    assert result.metadata.modality == "DX"


def test_common_dummy_patient_ids_are_not_usable() -> None:
    for value in (None, "", "ANON", "unknown", "0000", "XXXX"):
        assert patient_id_status(value or None) != "usable"


def test_extensionless_part10_dicom_is_recognized(tmp_path: Path) -> None:
    path = write_test_dicom(tmp_path / "image_without_extension")

    media_type, issue = classify_path(path)

    assert media_type == "dicom"
    assert issue is None


def test_unknown_file_type_is_reported_as_unsupported(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("not medical image data", encoding="utf-8")

    media_type, issue = classify_path(path)

    assert media_type == "unsupported"
    assert issue == "unsupported_file_type"


def test_invalid_uid_value_does_not_leak_through_warnings_or_logging(
    tmp_path: Path,
    capsys: object,
    caplog: object,
) -> None:
    sensitive_uid = "PHI-LIKE-UID-JANE-DOE"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        path = write_test_dicom(tmp_path / "invalid-uid.dcm", study_uid=sensitive_uid)

    capsys.readouterr()  # type: ignore[attr-defined]
    caplog.clear()  # type: ignore[attr-defined]
    caplog.set_level(logging.WARNING, logger="pydicom")  # type: ignore[attr-defined]

    result = parse_dicom_metadata(path)
    captured = capsys.readouterr()  # type: ignore[attr-defined]

    assert result.error_code is None
    assert result.metadata is not None
    assert result.metadata.study_instance_uid is None
    assert sensitive_uid not in captured.out
    assert sensitive_uid not in captured.err
    assert sensitive_uid not in caplog.text  # type: ignore[attr-defined]
