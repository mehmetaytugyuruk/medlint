from __future__ import annotations

from pathlib import Path

import pytest

from medlint.config import AuditConfig, DatasetSpec, SplitSpec


def test_dataset_spec_requires_exactly_one_input_mode(tmp_path: Path) -> None:
    train = SplitSpec("train", tmp_path / "train")

    with pytest.raises(ValueError, match="exactly one"):
        DatasetSpec()

    with pytest.raises(ValueError, match="exactly one"):
        DatasetSpec(manifest=tmp_path / "splits.csv", splits=(train,))


def test_split_spec_rejects_empty_names_and_namespaces(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="split name"):
        SplitSpec(" ", tmp_path)

    with pytest.raises(ValueError, match="source_namespace"):
        SplitSpec("train", tmp_path, " ")

    with pytest.raises(ValueError, match="control characters"):
        SplitSpec("train\x1b[2J", tmp_path)


def test_config_digest_is_stable() -> None:
    first = AuditConfig().digest()
    second = AuditConfig().digest()

    assert first == second
    assert len(first) == 64


def test_split_root_names_must_be_unique(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="split root names must be unique"):
        DatasetSpec.from_split_roots(
            [
                SplitSpec("train", tmp_path / "first"),
                SplitSpec("train", tmp_path / "second"),
            ]
        )


def test_detector_configuration_must_be_nonempty_and_unique() -> None:
    with pytest.raises(ValueError, match="at least one detector"):
        AuditConfig(enabled_detector_ids=())

    with pytest.raises(ValueError, match="must be unique"):
        AuditConfig(enabled_detector_ids=("ML001", "ML001"))

    with pytest.raises(ValueError, match="must not be empty"):
        AuditConfig(enabled_detector_ids=(" ",))


def test_hash_configuration_rejects_unsupported_values() -> None:
    with pytest.raises(ValueError, match="only sha256"):
        AuditConfig(file_hash_algorithm="md5")

    with pytest.raises(ValueError, match="must be positive"):
        AuditConfig(file_hash_chunk_bytes=0)
