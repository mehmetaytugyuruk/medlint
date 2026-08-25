from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from medlint.cli import main


def test_python_module_entry_point_reports_the_installed_version() -> None:
    project_root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [sys.executable, "-m", "medlint", "--version"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout.startswith("medlint ")
    assert completed.stderr == ""


def test_cli_writes_privacy_safe_json_and_returns_finding_code(
    tmp_path: Path,
    capsys: object,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    shared = b"cross-split exact duplicate"
    (train / "one.png").write_bytes(shared)
    (test / "two.png").write_bytes(shared)
    output = tmp_path / "audit.json"

    exit_code = main(
        [
            "audit",
            "--split",
            f"train={train}",
            "--split",
            f"test={test}",
            "--output",
            str(output),
        ]
    )
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert "Potential contamination risk detected" in captured.out
    assert payload["finding_status"] == "potential_risk_detected"
    assert "record_paths" not in payload
    assert str(train) not in output.read_text(encoding="utf-8")
    assert str(output) not in captured.out


def test_cli_include_paths_requires_explicit_opt_in(
    tmp_path: Path,
    capsys: object,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    (train / "one.png").write_bytes(b"one")
    (test / "two.png").write_bytes(b"two")
    output = tmp_path / "audit-with-paths.json"

    exit_code = main(
        [
            "audit",
            "--split",
            f"train={train}",
            "--split",
            f"test={test}",
            "--output",
            str(output),
            "--include-paths",
        ]
    )
    capsys.readouterr()  # type: ignore[attr-defined]
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["record_paths"]
    assert str(train) in output.read_text(encoding="utf-8")


def test_cli_refuses_to_overwrite_an_audited_source(
    tmp_path: Path,
    capsys: object,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    source = train / "source.png"
    original = b"do not overwrite"
    source.write_bytes(original)
    (test / "other.png").write_bytes(b"other")

    exit_code = main(
        [
            "audit",
            "--split",
            f"train={train}",
            "--split",
            f"test={test}",
            "--output",
            str(source),
        ]
    )
    captured = capsys.readouterr()  # type: ignore[attr-defined]

    assert exit_code == 2
    assert source.read_bytes() == original
    assert str(source) not in captured.out
    assert str(source) not in captured.err


def test_cli_refuses_to_overwrite_the_manifest(
    tmp_path: Path,
    capsys: object,
) -> None:
    train = tmp_path / "train.png"
    test = tmp_path / "test.png"
    train.write_bytes(b"one")
    test.write_bytes(b"two")
    manifest = tmp_path / "splits.csv"
    original = "path,split\ntrain.png,train\ntest.png,test\n"
    manifest.write_text(original, encoding="utf-8")

    exit_code = main(
        [
            "audit",
            "--manifest",
            str(manifest),
            "--output",
            str(manifest),
        ]
    )
    captured = capsys.readouterr()  # type: ignore[attr-defined]

    assert exit_code == 2
    assert manifest.read_text(encoding="utf-8") == original
    assert str(manifest) not in captured.out
    assert str(manifest) not in captured.err


def test_cli_refuses_to_create_a_report_inside_a_split_root(
    tmp_path: Path,
    capsys: object,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    (train / "one.png").write_bytes(b"one")
    (test / "two.png").write_bytes(b"two")
    output = train / "new-report.json"

    exit_code = main(
        [
            "audit",
            "--split",
            f"train={train}",
            "--split",
            f"test={test}",
            "--output",
            str(output),
        ]
    )
    capsys.readouterr()  # type: ignore[attr-defined]

    assert exit_code == 2
    assert not output.exists()


def test_cli_rejects_an_empty_namespace_without_a_traceback(
    tmp_path: Path,
    capsys: object,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()

    with pytest.raises(SystemExit) as error:
        main(
            [
                "audit",
                "--split",
                f"train={train}",
                "--split",
                f"test={test}",
                "--source-namespace",
                " ",
            ]
        )
    captured = capsys.readouterr()  # type: ignore[attr-defined]

    assert error.value.code == 2
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("--split", "train\nforged=/private/sensitive"),
        ("--source-namespace", "site\x1b[2J"),
    ],
)
def test_cli_rejects_control_characters_without_a_traceback_or_path_disclosure(
    tmp_path: Path,
    capsys: object,
    argument: str,
    value: str,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    args = [
        "audit",
        "--split",
        f"train={train}",
        "--split",
        f"test={test}",
    ]
    if argument == "--split":
        args.extend([argument, f"{value}={tmp_path / 'sensitive'}"])
    else:
        args.extend([argument, value])

    with pytest.raises(SystemExit) as error:
        main(args)
    captured = capsys.readouterr()  # type: ignore[attr-defined]

    assert error.value.code == 2
    assert "Traceback" not in captured.err
    assert str(tmp_path) not in captured.err
    assert "forged" not in captured.err
