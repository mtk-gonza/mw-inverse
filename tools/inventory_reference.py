"""Create a metadata-only inventory of the local Unity reference copy."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    files = []
    for path in sorted(args.root.rglob("*")):
        if path.is_file():
            files.append({
                "path": path.relative_to(args.root).as_posix(),
                "size": path.stat().st_size,
                "sha256": digest(path),
                "extension": path.suffix.lower(),
            })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"root": str(args.root), "files": files}, indent=2), encoding="utf-8")
    print(f"Inventoried {len(files)} files -> {args.output}")


if __name__ == "__main__":
    main()
