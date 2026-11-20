#!/usr/bin/env python3
"""news-image-20261120: validate and publish the finished front page.

The finished newspaper front page ships next to this program as
``entry.png`` (JPEG bytes under a ``.png`` name, which the competition
rules allow). Running this program checks that the file is really a
JPEG of a sane size, copies it byte for byte into the output
directory, and then verifies the copy by comparing both its size and
its SHA-256 hash against the original. Nothing is downloaded and no
network is used: only the Python standard library.

Exit codes: 0 means the copy was verified, 1 means a check failed.

Pass ``--check-only`` to validate the image without writing anything:
the program then only reports the size and hash and exits 0 when the
image is a valid JPEG under the size limit.
"""

import hashlib
import os
import sys
from pathlib import Path

ENTRY_FILENAME = "entry.png"
JPEG_PREFIX = b"\xff\xd8\xff"
MAX_ENTRY_BYTES = 1_048_576
OUTPUT_ENV_VAR = "MAKEFUN_OUTPUT_DIR"
DEFAULT_OUTPUT_DIR = "/output"


class EntryProblem(Exception):
    """A single clear reason the entry image cannot be published."""


def locate_entry() -> Path:
    """Return the path of the entry image shipped beside this file."""
    here = Path(__file__).resolve().parent
    entry = here / ENTRY_FILENAME
    if not entry.is_file():
        raise EntryProblem(f"entry image not found: {entry}")
    return entry


def read_and_validate(entry: Path) -> bytes:
    """Read the entry image and check that it is a JPEG of sane size."""
    data = entry.read_bytes()
    if len(data) == 0:
        raise EntryProblem(f"entry image is empty: {entry}")
    if len(data) > MAX_ENTRY_BYTES:
        raise EntryProblem(
            f"entry image is {len(data)} bytes, over the "
            f"{MAX_ENTRY_BYTES} byte limit"
        )
    if not data.startswith(JPEG_PREFIX):
        raise EntryProblem(
            "entry image does not start with JPEG magic bytes "
            "(expected FF D8 FF)"
        )
    return data


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 hex digest of the given bytes."""
    return hashlib.sha256(data).hexdigest()


def choose_output_dir() -> Path:
    """Return the output directory, creating it when it is missing."""
    raw = os.environ.get(OUTPUT_ENV_VAR, DEFAULT_OUTPUT_DIR)
    out_dir = Path(raw)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise EntryProblem(f"cannot create output directory {out_dir}: {exc}")
    if not out_dir.is_dir():
        raise EntryProblem(f"output path is not a directory: {out_dir}")
    return out_dir


def publish(data: bytes, out_dir: Path) -> Path:
    """Write the bytes to the output directory and verify the copy."""
    destination = out_dir / ENTRY_FILENAME
    destination.write_bytes(data)
    written = destination.read_bytes()
    if len(written) != len(data):
        raise EntryProblem(
            f"copy is {len(written)} bytes, expected {len(data)} bytes"
        )
    if sha256_hex(written) != sha256_hex(data):
        raise EntryProblem("copy hash does not match the original")
    return destination


def parse_args(argv):
    """Return True when the caller only wants a validation run."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--check-only"]:
        return True
    if args:
        raise EntryProblem(
            "unknown arguments: " + " ".join(args) + " (try --check-only)"
        )
    return False


def main(argv=None) -> int:
    """Validate the entry image, publish it, and report the result."""
    try:
        check_only = parse_args(argv)
        entry = locate_entry()
        data = read_and_validate(entry)
        if check_only:
            print(
                f"ok: {entry} is a valid JPEG "
                f"({len(data)} bytes, sha256 {sha256_hex(data)[:16]}...)"
            )
            return 0
        out_dir = choose_output_dir()
        destination = publish(data, out_dir)
    except EntryProblem as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(
        f"ok: published {destination} "
        f"({len(data)} bytes, sha256 {sha256_hex(data)[:16]}...)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
