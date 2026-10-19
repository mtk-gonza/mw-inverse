"""Build a compact catalog for the locally extracted reference library."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def category(path: Path) -> str:
    if path.suffix.lower() == ".wav":
        return "audio"
    if "Sprite" in path.parts:
        return "sprites"
    if "Texture2D" in path.parts:
        return "textures"
    return "other"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    files = []
    for path in sorted(args.root.rglob("*")):
        if path.is_file() and path.name not in {"extraction-report.json", "audio-extraction-report.json"}:
            files.append({"path": path.relative_to(args.root).as_posix(), "size": path.stat().st_size,
                          "sha256": digest(path), "category": category(path)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"scope": "local-reference-library", "files": files}, indent=2), encoding="utf-8")
    print(f"Catalogued {len(files)} extracted files -> {args.output}")


if __name__ == "__main__":
    main()
