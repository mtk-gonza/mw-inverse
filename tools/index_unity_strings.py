"""Index readable names from Unity containers without decoding payloads."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ASCII = re.compile(rb"[ -~]{4,}")
UTF16 = re.compile(rb"(?:[ -~]\x00){4,}")


def values(path: Path) -> list[str]:
    data = path.read_bytes()
    found = {match.group().decode("ascii", "ignore") for match in ASCII.finditer(data)}
    for match in UTF16.finditer(data):
        found.add(match.group().decode("utf-16-le", "ignore"))
    return sorted(value for value in found if any(character.isalpha() for character in value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = {}
    for path in sorted(args.root.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".assets", ".ress", ".resource", ".ress"}:
            result[path.relative_to(args.root).as_posix()] = values(path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"scope": "readable-string-index", "files": result}, indent=2), encoding="utf-8")
    print(f"Indexed {len(result)} Unity containers -> {args.output}")


if __name__ == "__main__":
    main()
