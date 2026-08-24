"""Input and audit configuration for :mod:`medlint`.

The objects in this module deliberately describe *declared* inputs only.  They
do not inspect the filesystem and can therefore be created safely by callers
before an audit begins.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SplitSpec:
    """A named dataset split rooted at a local directory.

    ``source_namespace`` scopes identifiers that are not globally unique, most
    importantly DICOM ``PatientID``.  The default is suitable for a dataset
    originating from one logical source.  Merged exports should declare a
    separate namespace for each source.
    """

    name: str
    root: Path
    source_namespace: str = "local"

    def __post_init__(self) -> None:
        name = self.name.strip()
        namespace = self.source_namespace.strip()
        if not name:
            raise ValueError("split name must not be empty")
        if not namespace:
            raise ValueError("source_namespace must not be empty")
        if not name.isprintable():
            raise ValueError("split name must not contain control characters")
        if not namespace.isprintable():
            raise ValueError("source_namespace must not contain control characters")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "root", Path(self.root).expanduser())
        object.__setattr__(self, "source_namespace", namespace)


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    """Immutable declaration of one manifest or one or more split roots."""

    manifest: Path | None = None
    splits: tuple[SplitSpec, ...] = ()

    def __post_init__(self) -> None:
        manifest = None if self.manifest is None else Path(self.manifest).expanduser()
        object.__setattr__(self, "manifest", manifest)
        object.__setattr__(self, "splits", tuple(self.splits))
        if (manifest is None) == (not self.splits):
            raise ValueError("declare exactly one of manifest or split roots")
        split_names = tuple(split.name for split in self.splits)
        if len(split_names) != len(set(split_names)):
            raise ValueError("split root names must be unique")

    @classmethod
    def from_manifest(cls, path: str | Path) -> DatasetSpec:
        return cls(manifest=Path(path))

    @classmethod
    def from_split_roots(cls, splits: Iterable[SplitSpec]) -> DatasetSpec:
        return cls(splits=tuple(splits))


@dataclass(frozen=True, slots=True)
class AuditConfig:
    """Configuration that affects audit semantics.

    Dataset paths are intentionally absent from :meth:`digest`; the digest
    describes detector behavior rather than disclosing where data is stored.
    """

    file_hash_algorithm: str = "sha256"
    file_hash_chunk_bytes: int = 1024 * 1024
    enabled_detector_ids: tuple[str, ...] = field(
        default_factory=lambda: (
            "ML001",
            "ML101",
            "ML102",
            "ML103",
            "ML104",
        )
    )

    def __post_init__(self) -> None:
        if self.file_hash_algorithm != "sha256":
            raise ValueError("v0.1 supports only sha256 file fingerprints")
        if self.file_hash_chunk_bytes <= 0:
            raise ValueError("file_hash_chunk_bytes must be positive")
        detector_ids = tuple(self.enabled_detector_ids)
        if not detector_ids:
            raise ValueError("at least one detector must be enabled")
        if any(not detector_id.strip() for detector_id in detector_ids):
            raise ValueError("detector identifiers must not be empty")
        if len(detector_ids) != len(set(detector_ids)):
            raise ValueError("detector identifiers must be unique")
        object.__setattr__(self, "enabled_detector_ids", detector_ids)

    def digest(self) -> str:
        payload = {
            "enabled_detector_ids": list(self.enabled_detector_ids),
            "file_hash_algorithm": self.file_hash_algorithm,
            "file_hash_chunk_bytes": self.file_hash_chunk_bytes,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
