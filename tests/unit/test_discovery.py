from __future__ import annotations

from pathlib import Path

import pytest

from medlint.config import DatasetSpec, SplitSpec
from medlint.io.discovery import DiscoveryError, discover


def test_split_root_discovery_is_deterministic(tmp_path: Path) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    train.mkdir()
    test.mkdir()
    (train / "z.png").write_bytes(b"z")
    (train / "a.png").write_bytes(b"a")
    (test / "b.png").write_bytes(b"b")

    spec = DatasetSpec.from_split_roots(
        [SplitSpec("train", train), SplitSpec("test", test)]
    )

    first = discover(spec)
    second = discover(spec)

    assert first == second
    assert [(item.split, item.path.name) for item in first] == [
        ("test", "b.png"),
        ("train", "a.png"),
        ("train", "z.png"),
    ]


def test_manifest_retains_same_path_in_different_splits(tmp_path: Path) -> None:
    image = tmp_path / "image.png"
    image.write_bytes(b"synthetic image bytes")
    manifest = tmp_path / "splits.csv"
    manifest.write_text(
        "path,split,source_namespace\nimage.png,train,site-a\nimage.png,test,site-a\n",
        encoding="utf-8",
    )

    artifacts = discover(DatasetSpec.from_manifest(manifest))

    assert len(artifacts) == 2
    assert {artifact.split for artifact in artifacts} == {"train", "test"}
    assert artifacts[0].path == artifacts[1].path == image


def test_manifest_requires_path_and_split_columns(tmp_path: Path) -> None:
    manifest = tmp_path / "invalid.csv"
    manifest.write_text("file,group\na.png,train\n", encoding="utf-8")

    with pytest.raises(DiscoveryError, match="path and split"):
        discover(DatasetSpec.from_manifest(manifest))


def test_manifest_rejects_non_printable_split_labels(tmp_path: Path) -> None:
    image = tmp_path / "image.png"
    image.write_bytes(b"synthetic image bytes")
    manifest = tmp_path / "invalid-label.csv"
    manifest.write_text(
        'path,split\nimage.png,"train\x1b[2J"\n',
        encoding="utf-8",
    )

    with pytest.raises(DiscoveryError, match="non-printable label"):
        discover(DatasetSpec.from_manifest(manifest))


def test_missing_split_root_is_an_operational_error(tmp_path: Path) -> None:
    spec = DatasetSpec.from_split_roots([SplitSpec("train", tmp_path / "missing")])

    with pytest.raises(DiscoveryError, match="does not exist"):
        discover(spec)


def test_file_symlink_is_inventoried_but_not_followed(tmp_path: Path) -> None:
    root = tmp_path / "train"
    root.mkdir()
    target = tmp_path / "outside.png"
    target.write_bytes(b"outside")
    link = root / "linked.png"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symbolic links are unavailable on this platform")

    artifacts = discover(DatasetSpec.from_split_roots([SplitSpec("train", root)]))

    assert len(artifacts) == 1
    assert artifacts[0].path == link.absolute()
    assert artifacts[0].discovery_issue == "symlink_not_followed"


def test_symlink_split_root_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "linked-root"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symbolic links are unavailable on this platform")

    spec = DatasetSpec.from_split_roots([SplitSpec("train", link)])

    with pytest.raises(DiscoveryError, match="symbolic link"):
        discover(spec)


def test_walk_error_is_not_silently_ignored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "train"
    root.mkdir()

    def failing_walk(
        _root: Path,
        *,
        followlinks: bool,
        onerror: object,
    ) -> list[object]:
        del followlinks
        assert callable(onerror)
        onerror(PermissionError("synthetic denial"))
        return []

    monkeypatch.setattr("medlint.io.discovery.os.walk", failing_walk)
    spec = DatasetSpec.from_split_roots([SplitSpec("train", root)])

    with pytest.raises(DiscoveryError, match="could not be traversed"):
        discover(spec)
