from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from medlint import audit_manifest


def test_documented_quickstart_generator_produces_the_expected_finding(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    generator = project_root / "examples" / "quickstart" / "create_example.py"
    destination = tmp_path / "medlint-example-data"

    completed = subprocess.run(
        [sys.executable, str(generator), "--destination", str(destination)],
        check=True,
        capture_output=True,
        text=True,
    )
    result = audit_manifest(destination / "splits.csv")

    assert "Created synthetic example manifest" in completed.stdout
    assert result.audit_state == "complete_with_findings"
    assert result.exit_code == 1
    assert {finding.rule_id for finding in result.findings} == {"ML001"}
    assert result.catalog_coverage.discovered == 3
