"""Deterministic manifest and split-root discovery."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path

from medlint.config import DatasetSpec


class DiscoveryError(RuntimeError):
    """Raised for an input-level failure that prevents dataset discovery."""


@dataclass(frozen=True, slots=True)
class DiscoveredArtifact:
    path: Path
    split: str
    source_namespace: str
    discovery_issue: str | None = None


def _stable_path(path: Path) -> str:
    return os.path.normcase(str(path.absolute()))


def _unavailable_artifact(
    path: Path,
    split: str,
    source_namespace: str,
    issue: str,
) -> DiscoveredArtifact:
    return DiscoveredArtifact(
        path=path.absolute(),
        split=split,
        source_namespace=source_namespace,
        discovery_issue=issue,
    )


def _walk_root(
    root: Path,
    split: str,
    source_namespace: str,
) -> list[DiscoveredArtifact]:
    root = root.expanduser().absolute()
    if root.is_symlink():
        raise DiscoveryError("a configured split root is a symbolic link")
    if not root.exists():
        raise DiscoveryError("a configured split root does not exist")
    if not root.is_dir():
        raise DiscoveryError("a configured split root is not a directory")

    artifacts: list[DiscoveredArtifact] = []

    def traversal_error(error: OSError) -> None:
        raise DiscoveryError(
            "a configured split root could not be traversed"
        ) from error

    try:
        for directory, directory_names, file_names in os.walk(
            root,
            followlinks=False,
            onerror=traversal_error,
        ):
            directory_names.sort()
            file_names.sort()
            base = Path(directory)

            linked_directories = [
                name for name in directory_names if (base / name).is_symlink()
            ]
            directory_names[:] = [
                name for name in directory_names if name not in linked_directories
            ]
            artifacts.extend(
                _unavailable_artifact(
                    base / name,
                    split,
                    source_namespace,
                    "symlink_not_followed",
                )
                for name in linked_directories
            )

            for file_name in file_names:
                candidate = base / file_name
                if candidate.is_symlink():
                    artifacts.append(
                        _unavailable_artifact(
                            candidate,
                            split,
                            source_namespace,
                            "symlink_not_followed",
                        )
                    )
                    continue
                if not candidate.is_file():
                    artifacts.append(
                        _unavailable_artifact(
                            candidate,
                            split,
                            source_namespace,
                            "non_regular_file",
                        )
                    )
                    continue
                artifacts.append(
                    DiscoveredArtifact(
                        path=candidate.absolute(),
                        split=split,
                        source_namespace=source_namespace,
                    )
                )
    except OSError as exc:
        raise DiscoveryError("a configured split root could not be traversed") from exc
    return artifacts


def _discover_manifest(manifest: Path) -> list[DiscoveredArtifact]:
    manifest = manifest.expanduser().absolute()
    if not manifest.exists() or not manifest.is_file():
        raise DiscoveryError("the configured manifest is not a readable file")

    artifacts: list[DiscoveredArtifact] = []
    try:
        with manifest.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None:
                raise DiscoveryError("the manifest has no header")
            fieldnames = tuple(name.strip() for name in reader.fieldnames if name)
            if "path" not in fieldnames or "split" not in fieldnames:
                raise DiscoveryError("the manifest requires path and split columns")

            for row_number, row in enumerate(reader, start=2):
                raw_path = (row.get("path") or "").strip()
                split = (row.get("split") or "").strip()
                namespace = (row.get("source_namespace") or "local").strip()
                if not raw_path or not split or not namespace:
                    raise DiscoveryError(
                        f"manifest row {row_number} has an empty required value"
                    )
                if not split.isprintable() or not namespace.isprintable():
                    raise DiscoveryError(
                        f"manifest row {row_number} has a non-printable label"
                    )
                path = Path(raw_path).expanduser()
                if not path.is_absolute():
                    path = manifest.parent / path
                path = path.absolute()
                if path.is_symlink():
                    artifacts.append(
                        _unavailable_artifact(
                            path,
                            split,
                            namespace,
                            "symlink_not_followed",
                        )
                    )
                    continue
                if not path.exists():
                    artifacts.append(
                        _unavailable_artifact(
                            path,
                            split,
                            namespace,
                            "path_missing",
                        )
                    )
                    continue
                if path.is_dir():
                    artifacts.extend(_walk_root(path, split, namespace))
                elif not path.is_file():
                    artifacts.append(
                        _unavailable_artifact(
                            path,
                            split,
                            namespace,
                            "non_regular_file",
                        )
                    )
                else:
                    artifacts.append(
                        DiscoveredArtifact(
                            path=path,
                            split=split,
                            source_namespace=namespace,
                        )
                    )
    except UnicodeError as exc:
        raise DiscoveryError("the manifest is not valid UTF-8 text") from exc
    except csv.Error as exc:
        raise DiscoveryError("the manifest is not valid CSV") from exc
    except OSError as exc:
        raise DiscoveryError("the manifest could not be read") from exc
    return artifacts


def discover(spec: DatasetSpec) -> tuple[DiscoveredArtifact, ...]:
    """Discover declared artifacts and return them in deterministic order.

    Duplicate declarations are retained: declaring the same physical path in
    two different splits is itself relevant evidence for an audit.
    """

    if spec.manifest is not None:
        artifacts = _discover_manifest(spec.manifest)
    else:
        artifacts = []
        for split in spec.splits:
            artifacts.extend(_walk_root(split.root, split.name, split.source_namespace))

    artifacts.sort(
        key=lambda artifact: (
            artifact.split.casefold(),
            artifact.split,
            artifact.source_namespace.casefold(),
            artifact.source_namespace,
            _stable_path(artifact.path),
        )
    )
    return tuple(artifacts)
