"""Export Unity Mesh objects to OBJ text without modifying source containers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import UnityPy


SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def clean(value: object, fallback: str) -> str:
    result = SAFE.sub("_", str(value)).strip("._")[:120]
    return result or fallback


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    destination = args.output / "Mesh"
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for source in sorted(args.root.glob("*.assets")):
        environment = UnityPy.load(str(source))
        for info in environment.objects:
            if info.type.name != "Mesh":
                continue
            try:
                mesh = info.read()
                obj = mesh.export("obj")
                path = destination / f"{source.stem}_{clean(mesh.m_Name, 'mesh')}_{info.path_id}.obj"
                path.write_text(obj, encoding="utf-8")
                records.append({"source": source.name, "path_id": info.path_id, "name": mesh.m_Name,
                                "vertices": int(mesh.m_VertexData.m_VertexCount),
                                "path": str(path.relative_to(args.output))})
            except Exception as error:
                records.append({"source": source.name, "path_id": info.path_id, "error": str(error)})
    report = args.output / "mesh-extraction-report.json"
    report.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps({"meshes": len(records), "exported": sum("error" not in item for item in records), "report": str(report)}))


if __name__ == "__main__":
    main()
