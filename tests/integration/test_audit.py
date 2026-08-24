from __future__ import annotations

from pathlib import Path

from conftest import TEST_UID_ROOT, write_test_dicom
from medlint import AuditConfig, SplitSpec, audit_manifest, audit_split_roots
from medlint.reporting import terminal_summary


def _rules(result: object) -> set[str]:
    return {finding.rule_id for finding in result.findings}  # type: ignore[attr-defined]


def test_exact_file_duplicate_is_reported_across_splits(tmp_path: Path) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    content = b"synthetic raster fixture"
    (train / "first.png").write_bytes(content)
    (test / "renamed.png").write_bytes(content)

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])

    assert _rules(result) == {"ML001"}
    assert result.finding_status == "potential_risk_detected"
    assert result.coverage_status == "complete"
    assert result.exit_code == 1
    assert result.findings[0].record_aliases == (
        "record-000001",
        "record-000002",
    )


def test_scoped_patient_identifier_match_is_reported(tmp_path: Path) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    write_test_dicom(
        train / "first.dcm",
        patient_id="SYNTHETIC-SHARED-PATIENT",
        study_uid=f"{TEST_UID_ROOT}.10",
        series_uid=f"{TEST_UID_ROOT}.10.1",
        sop_uid=f"{TEST_UID_ROOT}.10.1.1",
    )
    write_test_dicom(
        test / "second.dcm",
        patient_id="SYNTHETIC-SHARED-PATIENT",
        study_uid=f"{TEST_UID_ROOT}.20",
        series_uid=f"{TEST_UID_ROOT}.20.1",
        sop_uid=f"{TEST_UID_ROOT}.20.1.1",
    )

    result = audit_split_roots(
        [
            SplitSpec("train", train, "site-a"),
            SplitSpec("test", test, "site-a"),
        ]
    )

    assert _rules(result) == {"ML101"}
    assert result.exit_code == 1


def test_patient_id_is_not_compared_across_different_source_namespaces(
    tmp_path: Path,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    write_test_dicom(
        train / "first.dcm",
        patient_id="SYNTHETIC-COLLISION",
        issuer=None,
        study_uid=f"{TEST_UID_ROOT}.30",
        series_uid=f"{TEST_UID_ROOT}.30.1",
        sop_uid=f"{TEST_UID_ROOT}.30.1.1",
    )
    write_test_dicom(
        test / "second.dcm",
        patient_id="SYNTHETIC-COLLISION",
        issuer=None,
        study_uid=f"{TEST_UID_ROOT}.40",
        series_uid=f"{TEST_UID_ROOT}.40.1",
        sop_uid=f"{TEST_UID_ROOT}.40.1.1",
    )

    result = audit_split_roots(
        [
            SplitSpec("train", train, "site-a"),
            SplitSpec("test", test, "site-b"),
        ]
    )

    assert _rules(result) == set()
    assert result.exit_code == 0


def test_acquisition_relationships_are_distinct_from_patient_relationship(
    tmp_path: Path,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    write_test_dicom(
        train / "first.dcm",
        patient_id="SYNTHETIC-PATIENT-A",
        study_uid=f"{TEST_UID_ROOT}.50",
        series_uid=f"{TEST_UID_ROOT}.50.1",
        sop_uid=f"{TEST_UID_ROOT}.50.1.1",
    )
    write_test_dicom(
        test / "second.dcm",
        patient_id="SYNTHETIC-PATIENT-B",
        study_uid=f"{TEST_UID_ROOT}.50",
        series_uid=f"{TEST_UID_ROOT}.50.1",
        sop_uid=f"{TEST_UID_ROOT}.50.1.1",
    )

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])

    assert _rules(result) == {"ML102", "ML103", "ML104"}
    assert "ML101" not in _rules(result)


def test_default_json_does_not_expose_patient_ids_or_paths(tmp_path: Path) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    sensitive_patient_id = "SENSITIVE-PATIENT-ID"
    train_path = write_test_dicom(
        train / "patient-name-in-path.dcm",
        patient_id=sensitive_patient_id,
        study_uid=f"{TEST_UID_ROOT}.60",
        series_uid=f"{TEST_UID_ROOT}.60.1",
        sop_uid=f"{TEST_UID_ROOT}.60.1.1",
    )
    write_test_dicom(
        test / "second.dcm",
        patient_id=sensitive_patient_id,
        study_uid=f"{TEST_UID_ROOT}.70",
        series_uid=f"{TEST_UID_ROOT}.70.1",
        sop_uid=f"{TEST_UID_ROOT}.70.1.1",
    )

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])
    safe_json = result.to_json()
    opted_in_json = result.to_json(include_paths=True)

    assert sensitive_patient_id not in safe_json
    assert str(train_path) not in safe_json
    assert str(train_path) in opted_in_json
    assert sensitive_patient_id not in opted_in_json


def test_unsupported_input_makes_no_finding_result_partial(tmp_path: Path) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    (train / "one.png").write_bytes(b"one")
    (test / "two.png").write_bytes(b"two")
    (test / "notes.txt").write_text("unsupported", encoding="utf-8")

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])

    assert _rules(result) == set()
    assert result.coverage_status == "partial"
    assert result.exit_code == 3


def test_semantic_json_is_deterministic_across_runs(tmp_path: Path) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    content = b"deterministic fixture"
    (train / "one.png").write_bytes(content)
    (test / "two.png").write_bytes(content)
    specs = [SplitSpec("train", train), SplitSpec("test", test)]

    first = audit_split_roots(specs).to_json()
    second = audit_split_roots(specs).to_json()

    assert first == second


def test_missing_root_returns_sanitized_operational_result(tmp_path: Path) -> None:
    missing = tmp_path / "sensitive-missing-root"

    result = audit_split_roots([SplitSpec("train", missing)])
    payload = result.to_json()

    assert result.audit_state == "operational_error"
    assert result.exit_code == 2
    assert str(missing) not in payload


def test_one_split_is_inconclusive(tmp_path: Path) -> None:
    train = tmp_path / "train"
    train.mkdir()
    (train / "one.png").write_bytes(b"one")

    result = audit_split_roots([SplitSpec("train", train)])

    assert result.coverage_status == "inconclusive"
    assert result.audit_state == "inconclusive"
    assert result.exit_code == 3
    assert result.splits == ("train",)
    assert "insufficient_split_count" in {
        diagnostic.code for diagnostic in result.diagnostics
    }


def test_empty_counter_split_is_preserved_and_inconclusive(tmp_path: Path) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    (train / "one.png").write_bytes(b"one")

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])

    assert result.splits == ("test", "train")
    assert result.catalog_coverage.declared_split_count == 2
    assert result.catalog_coverage.populated_split_count == 1
    assert result.coverage_status == "inconclusive"
    assert result.exit_code == 3


def test_one_empty_split_in_n_way_audit_makes_coverage_partial(
    tmp_path: Path,
) -> None:
    train = tmp_path / "train"
    validation = tmp_path / "validation"
    test = tmp_path / "test"
    train.mkdir()
    validation.mkdir()
    test.mkdir()
    (train / "one.png").write_bytes(b"one")
    (test / "two.png").write_bytes(b"two")

    result = audit_split_roots(
        [
            SplitSpec("train", train),
            SplitSpec("validation", validation),
            SplitSpec("test", test),
        ]
    )

    assert result.coverage_status == "partial"
    assert result.exit_code == 3


def test_out_of_profile_dicom_modality_makes_coverage_partial(
    tmp_path: Path,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    write_test_dicom(train / "one.dcm", modality="CT")
    write_test_dicom(
        test / "two.dcm",
        modality="DX",
        study_uid=f"{TEST_UID_ROOT}.81",
        series_uid=f"{TEST_UID_ROOT}.81.1",
        sop_uid=f"{TEST_UID_ROOT}.81.1.1",
        patient_id="PATIENT-002",
    )

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])

    assert result.catalog_coverage.outside_primary_profile == 1
    assert result.coverage_status == "partial"
    assert result.exit_code == 3


def test_multiframe_dicom_makes_coverage_partial(tmp_path: Path) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    write_test_dicom(train / "one.dcm", number_of_frames=2)
    write_test_dicom(
        test / "two.dcm",
        study_uid=f"{TEST_UID_ROOT}.82",
        series_uid=f"{TEST_UID_ROOT}.82.1",
        sop_uid=f"{TEST_UID_ROOT}.82.1.1",
        patient_id="PATIENT-002",
    )

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])

    assert result.catalog_coverage.outside_primary_profile == 1
    assert result.coverage_status == "partial"


def test_detector_without_cross_split_evaluable_records_is_inconclusive(
    tmp_path: Path,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    (train / "one.png").write_bytes(b"one")
    (test / "two.png").write_bytes(b"two")

    result = audit_split_roots(
        [SplitSpec("train", train), SplitSpec("test", test)],
        config=AuditConfig(enabled_detector_ids=("ML101",)),
    )

    assert result.detector_coverage[0].evaluated_splits == ()
    assert result.coverage_status == "inconclusive"
    assert result.exit_code == 3


def test_manifest_audit_reports_a_missing_path_as_a_coverage_gap(
    tmp_path: Path,
) -> None:
    train = tmp_path / "train.png"
    test = tmp_path / "test.png"
    train.write_bytes(b"one")
    test.write_bytes(b"two")
    manifest = tmp_path / "splits.csv"
    manifest.write_text(
        "path,split\ntrain.png,train\ntest.png,test\nmissing.png,test\n",
        encoding="utf-8",
    )

    result = audit_manifest(manifest)

    assert result.coverage_status == "partial"
    assert result.exit_code == 3
    assert "path_missing" in {item.code for item in result.diagnostics}


def test_unknown_detector_is_a_sanitized_operational_error(tmp_path: Path) -> None:
    missing = tmp_path / "private-missing-root"

    result = audit_split_roots(
        [SplitSpec("train", missing)],
        config=AuditConfig(enabled_detector_ids=("ML999",)),
    )

    assert result.audit_state == "operational_error"
    assert result.diagnostics[0].code == "unknown_detector_configuration"
    assert str(missing) not in result.to_json()


def test_missing_and_dummy_patient_ids_are_coverage_not_identity_evidence(
    tmp_path: Path,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    write_test_dicom(
        train / "missing.dcm",
        patient_id=None,
        study_uid=f"{TEST_UID_ROOT}.90",
        series_uid=f"{TEST_UID_ROOT}.90.1",
        sop_uid=f"{TEST_UID_ROOT}.90.1.1",
    )
    write_test_dicom(
        test / "dummy.dcm",
        patient_id="ANON",
        study_uid=f"{TEST_UID_ROOT}.91",
        series_uid=f"{TEST_UID_ROOT}.91.1",
        sop_uid=f"{TEST_UID_ROOT}.91.1.1",
    )

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])
    patient_coverage = next(
        item for item in result.detector_coverage if item.detector_id == "ML101"
    )
    terminal = terminal_summary(result)

    assert "ML101" not in _rules(result)
    assert patient_coverage.unavailable_records == 2
    assert dict(patient_coverage.reason_counts) == {
        "patient_id_dummy": 1,
        "patient_id_missing": 1,
    }
    assert result.coverage_status == "partial"
    assert "warning:patient_id_dummy" in terminal
    assert "warning:patient_id_missing" in terminal


def test_malformed_dicom_is_visible_as_partial_coverage(tmp_path: Path) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    (train / "broken.dcm").write_bytes(b"not a dicom object")
    (test / "valid.png").write_bytes(b"valid raster bytes")

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])

    assert result.coverage_status == "partial"
    assert result.catalog_coverage.dicom_parsed == 0
    assert {item.code for item in result.diagnostics} & {
        "dicom_parse_failed",
        "dicom_structure_missing",
    }
