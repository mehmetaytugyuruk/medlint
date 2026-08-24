from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from medlint import SplitSpec, audit_split_roots

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "schemas" / "audit-result-v1.schema.json"
)


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _complete_payload(
    root: Path,
    *,
    duplicate: bool = False,
    include_paths: bool = False,
) -> dict[str, object]:
    train = root / "train"
    test = root / "test"
    train.mkdir(parents=True)
    test.mkdir()
    (train / "one.png").write_bytes(b"train")
    (test / "two.png").write_bytes(b"train" if duplicate else b"test")

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])
    return result.to_dict(include_paths=include_paths)


def _partial_payload(root: Path) -> dict[str, object]:
    train = root / "train"
    test = root / "test"
    train.mkdir(parents=True)
    test.mkdir()
    (train / "one.png").write_bytes(b"train")
    (test / "two.png").write_bytes(b"test")
    (test / "notes.txt").write_text("unsupported", encoding="utf-8")

    result = audit_split_roots([SplitSpec("train", train), SplitSpec("test", test)])
    return result.to_dict()


def test_real_audit_outputs_validate_against_draft_2020_12(tmp_path: Path) -> None:
    validator = _validator()
    safe_payload = _complete_payload(tmp_path / "safe")
    path_payload = _complete_payload(
        tmp_path / "paths",
        duplicate=True,
        include_paths=True,
    )
    partial_payload = _partial_payload(tmp_path / "partial")
    operational_payload = audit_split_roots(
        [SplitSpec("train", tmp_path / "missing")]
    ).to_dict()

    assert safe_payload["audit_state"] == "complete_no_findings"
    assert "record_paths" not in safe_payload
    assert path_payload["audit_state"] == "complete_with_findings"
    assert path_payload["record_paths"]
    assert partial_payload["audit_state"] == "partial"
    assert operational_payload["audit_state"] == "operational_error"

    for payload in (
        safe_payload,
        path_payload,
        partial_payload,
        operational_payload,
    ):
        validator.validate(payload)


def test_schema_rejects_inconsistent_status_and_exit_code_combinations(
    tmp_path: Path,
) -> None:
    validator = _validator()
    valid_payload = _complete_payload(tmp_path / "complete")

    policy_mismatch = copy.deepcopy(valid_payload)
    policy_mismatch["policy"]["coverage_status"] = "partial"  # type: ignore[index]

    wrong_exit_code = copy.deepcopy(valid_payload)
    wrong_exit_code["policy"]["exit_code"] = 2  # type: ignore[index]

    impossible_complete_state = copy.deepcopy(valid_payload)
    impossible_complete_state["audit_state"] = "complete_with_findings"
    impossible_complete_state["policy"]["audit_state"] = (  # type: ignore[index]
        "complete_with_findings"
    )

    empty_findings_with_positive_status = copy.deepcopy(valid_payload)
    empty_findings_with_positive_status["finding_status"] = "potential_risk_detected"
    empty_findings_with_positive_status["policy"]["finding_status"] = (  # type: ignore[index]
        "potential_risk_detected"
    )

    for index, payload in enumerate(
        (
            policy_mismatch,
            wrong_exit_code,
            impossible_complete_state,
            empty_findings_with_positive_status,
        )
    ):
        assert list(validator.iter_errors(payload)), f"invalid case {index} passed"


def test_schema_requires_split_aware_coverage_fields(tmp_path: Path) -> None:
    validator = _validator()
    valid_payload = _complete_payload(tmp_path / "complete")

    missing_catalog_field = copy.deepcopy(valid_payload)
    missing_catalog_field["coverage"]["catalog"].pop(  # type: ignore[index, union-attr]
        "declared_split_count"
    )

    missing_detector_field = copy.deepcopy(valid_payload)
    missing_detector_field["coverage"]["detectors"][0].pop(  # type: ignore[index, union-attr]
        "evaluated_splits"
    )

    assert not validator.is_valid(missing_catalog_field)
    assert not validator.is_valid(missing_detector_field)
