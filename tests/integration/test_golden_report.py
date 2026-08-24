from __future__ import annotations

import json
from pathlib import Path

from medlint import SplitSpec, audit_split_roots

GOLDEN_PATH = Path(__file__).resolve().parents[1] / "golden" / "audit-result-v1.json"


def test_exact_duplicate_report_matches_the_versioned_golden_file(
    tmp_path: Path,
) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    (train / "one.png").write_bytes(b"golden")
    (test / "two.png").write_bytes(b"golden")

    payload = audit_split_roots(
        [SplitSpec("train", train), SplitSpec("test", test)]
    ).to_dict()
    payload["tool_version"] = "<tool-version>"
    payload["provenance"] = {
        "medlint": "<tool-version>",
        "pydicom": "<pydicom-version>",
        "python": "<python-version>",
    }

    expected = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert payload == expected
