"""Create a tiny PHI-free dataset for the medlint quickstart."""

from __future__ import annotations

import argparse
import csv
import struct
import zlib
from pathlib import Path


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)
    )


def _grayscale_png(value: int) -> bytes:
    """Return a valid one-pixel, eight-bit grayscale PNG."""

    header = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
    scanline = bytes((0, value))
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", header),
            _png_chunk(b"IDAT", zlib.compress(scanline, level=9)),
            _png_chunk(b"IEND", b""),
        )
    )


def create_example(destination: Path) -> Path:
    if destination.exists():
        raise FileExistsError("refusing to overwrite an existing example destination")

    train = destination / "train"
    validation = destination / "validation"
    test = destination / "test"
    for directory in (train, validation, test):
        directory.mkdir(parents=True, exist_ok=True)

    duplicate = _grayscale_png(48)
    (train / "image-a.png").write_bytes(duplicate)
    (validation / "image-b.png").write_bytes(_grayscale_png(208))
    (test / "image-a-copy.png").write_bytes(duplicate)

    manifest = destination / "splits.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("path", "split", "source_namespace"))
        writer.writerow(("train/image-a.png", "train", "synthetic-example"))
        writer.writerow(("validation/image-b.png", "validation", "synthetic-example"))
        writer.writerow(("test/image-a-copy.png", "test", "synthetic-example"))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("medlint-example-data"),
        help="directory to create (default: medlint-example-data)",
    )
    args = parser.parse_args()
    try:
        manifest = create_example(args.destination)
    except FileExistsError as error:
        parser.error(str(error))
    print(f"Created synthetic example manifest: {manifest}")


if __name__ == "__main__":
    main()
