"""Validate the optional runtime reference pack without requiring Godot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    rows = []
    errors = []
    for path in sorted(args.pack.rglob("*")):
        if not path.is_file() or path.name == args.manifest.name or path.name.endswith(".import"):
            continue
        relative = path.relative_to(args.pack).as_posix()
        row = {"path": relative, "size": path.stat().st_size, "sha256": sha256(path)}
        try:
            if path.suffix.lower() == ".png":
                with Image.open(path) as image:
                    row["format"] = image.format
                    row["dimensions"] = list(image.size)
            elif path.suffix.lower() == ".wav":
                if path.read_bytes()[:4] != b"RIFF":
                    raise ValueError("WAV sin cabecera RIFF")
                row["format"] = "WAV"
        except Exception as error:
            errors.append({"path": relative, "error": str(error)})
        rows.append(row)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps({"files": rows, "errors": errors}, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(rows), "errors": len(errors)}))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
