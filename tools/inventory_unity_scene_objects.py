"""Inventory Unity scene objects and component relationships for reconstruction."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import UnityPy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    records = []
    counts = Counter()
    for source in sorted(args.root.glob("*.assets")):
        environment = UnityPy.load(str(source))
        for info in environment.objects:
            counts[info.type.name] += 1
            if info.type.name not in {"GameObject", "Material", "MeshRenderer", "MeshFilter", "AnimationClip", "Animator", "PrefabInstance"}:
                continue
            try:
                data = info.read()
                record = {"source": source.name, "path_id": info.path_id, "type": info.type.name}
                if info.type.name == "GameObject":
                    record.update({"name": data.m_Name, "components": [str(component) for component in data.m_Components]})
                elif info.type.name == "Material":
                    record.update({"name": data.m_Name, "shader": str(getattr(data, "m_Shader", ""))})
                elif info.type.name == "MeshFilter":
                    record["mesh"] = str(getattr(data, "m_Mesh", ""))
                elif info.type.name == "MeshRenderer":
                    record["materials"] = [str(material) for material in getattr(data, "m_Materials", [])]
                elif info.type.name == "AnimationClip":
                    record.update({"name": data.m_Name, "length": float(getattr(data, "m_MuscleClip", {}).get("m_StopTime", 0.0)) if isinstance(getattr(data, "m_MuscleClip", {}), dict) else None})
                else:
                    record["name"] = str(getattr(data, "m_Name", ""))
                records.append(record)
            except Exception as error:
                records.append({"source": source.name, "path_id": info.path_id, "type": info.type.name, "error": str(error)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"counts": counts, "objects": records}, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"objects": len(records), "types": len(counts), "counts": counts}))


if __name__ == "__main__":
    main()
