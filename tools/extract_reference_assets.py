"""Extract readable Unity Texture2D/Sprite assets to a private local folder.

This tool never writes to the installed game and refuses to use an output path
outside the repository's private reference directory unless explicitly passed.
The output is ignored by Git; it is for local experimental comparison only.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import UnityPy


DEFAULT_INPUT = Path(r"C:\Users\gonzalo.gonzalez\AppData\Local\MagicWingsBOTeado\current\Magic Wings_Data")
DEFAULT_OUTPUT = Path("client/assets/reference-private")


def safe_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("._")
    return value[:160] or "unnamed"


def object_name(obj: Any) -> str:
    try:
        return str(obj.read().m_Name)
    except Exception:
        return f"asset_{obj.path_id}"


def save_image(data: Any, destination: Path) -> bool:
    image = getattr(data, "image", None)
    if image is None:
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)
    return True


def extract(input_path: Path, output_path: Path) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    output_path.mkdir(parents=True, exist_ok=True)
    environment = UnityPy.load(str(input_path))
    manifest: list[dict[str, Any]] = []
    used_names: set[str] = set()
    counts: dict[str, int] = {}

    for obj in environment.objects:
        type_name = obj.type.name
        if type_name not in {"Texture2D", "Sprite"}:
            continue
        try:
            data = obj.read()
            name = safe_name(str(getattr(data, "m_Name", "")))
            if not name:
                name = f"asset_{obj.path_id}"
            base_name = name
            suffix = 2
            while name.lower() in used_names:
                name = f"{base_name}_{suffix}"
                suffix += 1
            used_names.add(name.lower())
            destination = output_path / "sprites" / f"{name}.png"
            if not save_image(data, destination):
                continue
            counts[type_name] = counts.get(type_name, 0) + 1
            manifest.append({
                "type": type_name,
                "name": name,
                "source_path_id": int(obj.path_id),
                "file": str(destination.relative_to(output_path)).replace("\\", "/"),
            })
        except Exception as error:
            manifest.append({"type": type_name, "source_path_id": int(obj.path_id), "error": str(error)})

    report = {
        "input": str(input_path),
        "output": str(output_path),
        "unitypy_version": getattr(UnityPy, "__version__", "unknown"),
        "counts": counts,
        "assets": manifest,
    }
    (output_path / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = extract(args.input, args.output)
    print(json.dumps({"counts": report["counts"], "assets": len(report["assets"]), "output": report["output"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
