"""Extract supported Unity object classes to the ignored reference directory."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import UnityPy


SAFE = re.compile(r"[^A-Za-z0-9._-]+")
SUPPORTED = {"Texture2D", "Sprite", "AudioClip", "Mesh"}


def safe_name(value: str, fallback: str) -> str:
    value = SAFE.sub("_", value).strip("._")
    return value[:120] or fallback


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = []
    sources = sorted(args.root.glob("*.assets"))
    for source in sources:
        environment = UnityPy.load(str(source))
        source_report = {"source": source.name, "objects": len(environment.objects), "exported": [], "errors": []}
        for object_info in environment.objects:
            kind = object_info.type.name
            if kind not in SUPPORTED:
                continue
            try:
                data = object_info.read()
                name = safe_name(getattr(data, "m_Name", ""), f"path_{object_info.path_id}")
                destination = args.output / kind
                destination.mkdir(parents=True, exist_ok=True)
                if kind in {"Texture2D", "Sprite"} and getattr(data, "image", None) is not None:
                    path = destination / f"{source.stem}_{name}_{object_info.path_id}.png"
                    data.image.save(path)
                elif kind == "AudioClip":
                    samples = getattr(data, "samples", {})
                    if not samples:
                        continue
                    first_path = None
                    for sample_name, sample_bytes in samples.items():
                        sample_path = destination / f"{source.stem}_{safe_name(str(sample_name), name)}"
                        sample_path.write_bytes(sample_bytes)
                        first_path = sample_path
                    path = first_path
                elif kind == "Mesh":
                    exported = data.export(str(destination))
                    path = Path(exported) if exported else destination / f"{source.stem}_{name}_{object_info.path_id}.obj"
                else:
                    continue
                source_report["exported"].append({"type": kind, "name": name, "path": str(path.relative_to(args.output))})
            except Exception as error:  # individual Unity objects may use unsupported compression
                source_report["errors"].append({"type": kind, "path_id": object_info.path_id, "error": str(error)})
        report.append(source_report)
    (args.output / "extraction-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"sources": len(report), "exported": sum(len(item["exported"]) for item in report),
                      "errors": sum(len(item["errors"]) for item in report)}))


if __name__ == "__main__":
    main()
