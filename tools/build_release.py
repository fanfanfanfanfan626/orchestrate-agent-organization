#!/usr/bin/env python3
"""Build the deterministic Persistent AI Studio skill archive."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "orchestrate-agent-organization"
PREFIX = "orchestrate-agent-organization"


def release_bytes(source: Path) -> bytes:
    """Normalize UTF-8 package text so the archive is host-independent."""
    data = source.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checksum-output", type=Path)
    args = parser.parse_args()

    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(path for path in SKILL.rglob("*") if path.is_file()):
            relative = source.relative_to(SKILL).as_posix()
            info = zipfile.ZipInfo(f"{PREFIX}/{relative}", (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, release_bytes(source), compresslevel=9)

    digest = hashlib.sha256(output.read_bytes()).hexdigest().upper()
    if args.checksum_output:
        checksum = args.checksum_output if args.checksum_output.is_absolute() else ROOT / args.checksum_output
        checksum.parent.mkdir(parents=True, exist_ok=True)
        checksum.write_text(f"{digest}  {output.relative_to(ROOT).as_posix()}\n", encoding="utf-8", newline="\n")
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
