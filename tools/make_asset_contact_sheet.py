"""Create a local visual index of extracted reference images."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()
    candidates = []
    for path in args.root.rglob("*.png"):
        try:
            image = Image.open(path)
            width, height = image.size
            score = width * height
            candidates.append((score, path, image.copy().convert("RGBA")))
        except Exception:
            pass
    candidates.sort(key=lambda item: item[0], reverse=True)
    candidates = candidates[: args.limit]
    cell_width, cell_height = 180, 150
    columns = 5
    sheet = Image.new("RGBA", (columns * cell_width, ((len(candidates) + columns - 1) // columns) * cell_height), (24, 30, 48, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (_, path, image) in enumerate(candidates):
        x = (index % columns) * cell_width
        y = (index // columns) * cell_height
        preview = ImageOps.contain(image, (cell_width - 12, cell_height - 34))
        sheet.alpha_composite(preview, (x + (cell_width - preview.width) // 2, y + 4))
        draw.text((x + 5, y + cell_height - 26), path.name[:25], fill=(230, 240, 255, 255))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(args.output, quality=92)
    print(f"Created {args.output} from {len(candidates)} images")


if __name__ == "__main__":
    main()
