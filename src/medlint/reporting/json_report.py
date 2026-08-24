"""JSON rendering that never reinterprets detector evidence."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from medlint.evidence import AuditResult


def canonical_json(
    result: AuditResult,
    *,
    include_paths: bool = False,
    indent: int | None = 2,
) -> str:
    return result.to_json(include_paths=include_paths, indent=indent)


def write_json(
    result: AuditResult,
    destination: str | Path,
    *,
    include_paths: bool = False,
    indent: int | None = 2,
) -> Path:
    path = Path(destination).expanduser()
    resolved_destination = path.resolve(strict=False)
    for protected_file in result._protected_files:
        if resolved_destination == protected_file.resolve(strict=False):
            raise ValueError("the JSON destination overlaps a protected input file")
        try:
            if path.exists() and os.path.samefile(path, protected_file):
                raise ValueError("the JSON destination overlaps a protected input file")
        except OSError:
            pass
    for protected_root in result._protected_roots:
        if resolved_destination.is_relative_to(protected_root.resolve(strict=False)):
            raise ValueError("the JSON destination is inside an audited split root")
    for record in result._record_references:
        resolved_source = record.path.resolve(strict=False)
        same_path = resolved_destination == resolved_source
        same_file = False
        try:
            same_file = path.exists() and os.path.samefile(path, record.path)
        except OSError:
            pass
        if same_path or same_file:
            raise ValueError("the JSON destination overlaps an audited source file")

    payload = canonical_json(result, include_paths=include_paths, indent=indent) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return path
