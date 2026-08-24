from __future__ import annotations

from pathlib import Path

from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian

TEST_UID_ROOT = "1.2.826.0.1.3680043.10.5432"


def write_test_dicom(
    path: Path,
    *,
    patient_id: str | None = "PATIENT-001",
    issuer: str | None = "TEST-HOSPITAL",
    study_uid: str = f"{TEST_UID_ROOT}.1",
    series_uid: str = f"{TEST_UID_ROOT}.1.1",
    sop_uid: str = f"{TEST_UID_ROOT}.1.1.1",
    modality: str = "DX",
    number_of_frames: int | None = None,
) -> Path:
    """Write a small, metadata-only, synthetic DICOM fixture with no real PHI."""

    path.parent.mkdir(parents=True, exist_ok=True)
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.1.1"
    file_meta.MediaStorageSOPInstanceUID = sop_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = f"{TEST_UID_ROOT}.99"

    dataset = FileDataset(
        str(path),
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )
    dataset.SOPClassUID = file_meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = sop_uid
    dataset.StudyInstanceUID = study_uid
    dataset.SeriesInstanceUID = series_uid
    dataset.Modality = modality
    if number_of_frames is not None:
        dataset.NumberOfFrames = number_of_frames
    dataset.Rows = 1
    dataset.Columns = 1
    if patient_id is not None:
        dataset.PatientID = patient_id
    if issuer is not None:
        dataset.IssuerOfPatientID = issuer
    dataset.save_as(path, enforce_file_format=True)
    return path
