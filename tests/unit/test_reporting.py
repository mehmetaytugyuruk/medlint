from __future__ import annotations

from pathlib import Path

import pytest

import medlint.evidence as evidence
from medlint import AuditResult, audit_manifest
from medlint.reporting import write_json


def _manifest_result(tmp_path: Path) -> tuple[AuditResult, Path, Path]:
    train = tmp_path / "train.png"
    test = tmp_path / "test.png"
    train.write_bytes(b"train")
    test.write_bytes(b"test")
    manifest = tmp_path / "splits.csv"
    manifest.write_text(
        "path,split\ntrain.png,train\ntest.png,test\n",
        encoding="utf-8",
    )
    return audit_manifest(manifest), manifest, train


def test_private_record_reference_is_not_exported() -> None:
    assert not hasattr(evidence, "RecordReference")


def test_writer_protects_manifest_and_audited_record_paths(tmp_path: Path) -> None:
    result, manifest, train = _manifest_result(tmp_path)

    with pytest.raises(ValueError, match="protected input file"):
        write_json(result, manifest)

    with pytest.raises(ValueError, match="audited source file"):
        write_json(result, train)

    assert manifest.read_text(encoding="utf-8").startswith("path,split")
    assert train.read_bytes() == b"train"


def test_atomic_writer_removes_temporary_file_after_replace_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _, _ = _manifest_result(tmp_path)
    output = tmp_path / "report.json"

    def fail_replace(_source: Path, _destination: Path) -> None:
        raise OSError("synthetic replace failure")

    monkeypatch.setattr("medlint.reporting.json_report.os.replace", fail_replace)

    with pytest.raises(OSError, match="synthetic replace failure"):
        write_json(result, output)

    assert not output.exists()
    assert not tuple(tmp_path.glob(".report.json.*.tmp"))
