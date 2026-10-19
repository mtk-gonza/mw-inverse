"""Audit Unity serialized containers without extracting proprietary payloads."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify(path: Path) -> str:
    with path.open("rb") as source:
        header = source.read(32)
    if header.startswith(b"UnityFS"):
        return "UnityFS"
    if header.startswith(b"UnityRaw"):
        return "UnityRaw"
    if header.startswith(b"UnityWeb"):
        return "UnityWeb"
    return "serialized-or-opaque"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = []
    for path in sorted(args.root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".assets", ".ress", ".resource", ".resS".lower()}:
            continue
        rows.append({
            "path": path.relative_to(args.root).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256(path),
            "container": classify(path),
            "paired_stream": path.with_suffix(path.suffix + ".resS").exists(),
            "extracted": False,
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"files": rows, "scope": "metadata-only"}, indent=2), encoding="utf-8")
    print(f"Audited {len(rows)} Unity containers -> {args.output}")


if __name__ == "__main__":
    main()
