"""Command-line interface for the deterministic medlint audit."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from medlint import __version__
from medlint.api import audit
from medlint.config import DatasetSpec, SplitSpec
from medlint.reporting import write_json
from medlint.reporting.terminal import terminal_summary


def _split_argument(value: str) -> tuple[str, Path]:
    name, separator, raw_path = value.partition("=")
    name = name.strip()
    raw_path = raw_path.strip()
    if not separator or not name or not raw_path:
        raise argparse.ArgumentTypeError("expected NAME=PATH")
    if not name.isprintable():
        raise argparse.ArgumentTypeError(
            "split name must not contain control characters"
        )
    return name, Path(raw_path)


def _non_empty_string(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise argparse.ArgumentTypeError("value must not be empty")
    if not normalized.isprintable():
        raise argparse.ArgumentTypeError("value must not contain control characters")
    return normalized


def _paths_overlap(first: Path, second: Path) -> bool:
    if first.expanduser().resolve(strict=False) == second.expanduser().resolve(
        strict=False
    ):
        return True
    try:
        return first.exists() and second.exists() and os.path.samefile(first, second)
    except OSError:
        return False


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="medlint",
        description=("Evidence-first medical-imaging dataset split-integrity audits."),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    audit_parser = commands.add_parser(
        "audit",
        help="audit declared dataset splits without modifying source files",
    )
    inputs = audit_parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument(
        "--manifest",
        type=Path,
        help="CSV manifest with path, split, and optional source_namespace columns",
    )
    inputs.add_argument(
        "--split",
        action="append",
        type=_split_argument,
        metavar="NAME=PATH",
        help="split root; repeat for train, validation, test, or folds",
    )
    audit_parser.add_argument(
        "--source-namespace",
        default="local",
        type=_non_empty_string,
        help="identifier namespace used by --split roots (default: local)",
    )
    audit_parser.add_argument(
        "--output",
        type=Path,
        help="write the canonical JSON report to this local path",
    )
    audit_parser.add_argument(
        "--include-paths",
        action="store_true",
        help="explicitly include local paths in JSON output (privacy-sensitive)",
    )
    return parser


def _dataset_spec(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> DatasetSpec:
    if args.manifest is not None:
        return DatasetSpec.from_manifest(args.manifest)

    split_arguments = args.split or []
    names = [name for name, _ in split_arguments]
    if len(set(names)) != len(names):
        parser.error("each --split name must be unique")
    return DatasetSpec.from_split_roots(
        SplitSpec(name, path, args.source_namespace) for name, path in split_arguments
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.command != "audit":  # pragma: no cover - guarded by argparse
        parser.error("an audit command is required")

    try:
        dataset = _dataset_spec(args, parser)
    except ValueError:
        print("medlint: invalid dataset specification", file=sys.stderr)
        return 2
    if (
        args.output is not None
        and dataset.manifest is not None
        and _paths_overlap(args.output, dataset.manifest)
    ):
        print(
            "medlint: the JSON destination overlaps the input manifest",
            file=sys.stderr,
        )
        return 2

    result = audit(dataset)
    print(terminal_summary(result))

    if args.output is not None:
        try:
            write_json(
                result,
                args.output,
                include_paths=args.include_paths,
            )
        except (OSError, ValueError):
            print("medlint: the JSON report could not be written", file=sys.stderr)
            return 2
        print("JSON report written.")
    elif args.include_paths:
        print(
            "medlint: --include-paths has no effect without --output",
            file=sys.stderr,
        )

    return result.exit_code
