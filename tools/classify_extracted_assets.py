"""Classify every extracted reference asset and produce review galleries."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


RULES = [
    ("audio_music", re.compile(r"music|magic_wings|caminho|guardiao|breeze|oath|march|banner|horizon|path|tide", re.I)),
    ("audio_ui", re.compile(r"button|confirm|cancel|accepted|interface|click|menu|notification", re.I)),
    ("audio_creature", re.compile(r"beast|creature|monster|dragon|golem|wolf|bird|animal|idle|hurt|death|charge|growl|roar", re.I)),
    ("audio_combat", re.compile(r"spell|magic|attack|hit|cast|impact|weapon|bow|sword|shield|teleport|thunder", re.I)),
    ("audio_environment", re.compile(r"ambient|nature|wind|water|rain|fire|ice|storm|footstep", re.I)),
    ("map", re.compile(r"map|minimap|caminho|world|region|background", re.I)),
    ("hud", re.compile(r"health|mana|level|input|button|panel|offer|inventory|window|screen", re.I)),
    ("combat", re.compile(r"attack|autoattack|spell|magic|skill|target|hit|damage|shield|sword", re.I)),
    ("character", re.compile(r"player|avatar|character|outfit|wing|mount|portrait", re.I)),
    ("progression", re.compile(r"achievement|rank|badge|guild|clan|founder|medal", re.I)),
    ("effects", re.compile(r"effect|particle|glow|spark|blood|fire|ice|smoke|light", re.I)),
]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def classify(path: Path) -> tuple[str, str]:
    name = path.name
    rules = RULES if path.suffix.lower() == ".wav" else RULES[5:]
    for category, rule in rules:
        if rule.search(name):
            return category, f"filename:{rule.pattern}"
    return "unknown", "no-semantic-name-match"


def gallery(paths: list[Path], output: Path) -> None:
    if not paths:
        return
    paths = paths[:120]
    cell_width, cell_height, columns = 180, 145, 5
    sheet = Image.new("RGBA", (columns * cell_width, ((len(paths) + columns - 1) // columns) * cell_height), (20, 26, 42, 255))
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(paths):
        try:
            image = Image.open(path).convert("RGBA")
            preview = ImageOps.contain(image, (cell_width - 10, cell_height - 30))
            x = index % columns * cell_width
            y = index // columns * cell_height
            sheet.alpha_composite(preview, (x + (cell_width - preview.width) // 2, y + 3))
            draw.text((x + 4, y + cell_height - 23), path.name[:24], fill="white")
        except Exception:
            pass
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(output, quality=90)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    records = []
    grouped: dict[str, list[Path]] = {}
    for path in sorted(args.root.rglob("*")):
        if not path.is_file() or path.name.endswith(".json") or path.name.endswith(".import"):
            continue
        category, reason = classify(path)
        record = {"path": path.relative_to(args.root).as_posix(), "name": path.name,
                  "size": path.stat().st_size, "sha256": digest(path), "category": category,
                  "reason": reason, "extension": path.suffix.lower()}
        if path.suffix.lower() == ".png":
            try:
                with Image.open(path) as image:
                    record["dimensions"] = list(image.size)
            except Exception as error:
                record["decode_error"] = str(error)
            grouped.setdefault(category, []).append(path)
        records.append(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"files": records, "counts": dict(Counter(item["category"] for item in records))}, indent=2), encoding="utf-8")
    gallery_root = args.output.parent / "asset-galleries"
    for category, paths in grouped.items():
        gallery(paths, gallery_root / f"{category}.jpg")
    print(json.dumps({"files": len(records), "counts": dict(Counter(item["category"] for item in records))}))


if __name__ == "__main__":
    main()
