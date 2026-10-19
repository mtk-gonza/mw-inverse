"""Recover Unity AudioClip sample streams with UnityPy."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import UnityPy


SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def clean(value: object) -> str:
    return SAFE.sub("_", str(value)).strip("._")[:140] or "audio"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    destination = args.output / "AudioClip"
    destination.mkdir(parents=True, exist_ok=True)
    exported = []
    errors = []
    for source in sorted(args.root.glob("*.assets")):
        environment = UnityPy.load(str(source))
        for info in environment.objects:
            if info.type.name != "AudioClip":
                continue
            try:
                clip = info.read()
                samples = clip.samples
                for sample_name, sample_bytes in samples.items():
                    path = destination / f"{source.stem}_{clean(sample_name)}"
                    path.write_bytes(sample_bytes)
                    exported.append({"source": source.name, "path_id": info.path_id, "name": str(clip.m_Name), "path": str(path.relative_to(args.output))})
            except Exception as error:
                errors.append({"source": source.name, "path_id": info.path_id, "error": str(error)})
    (args.output / "audio-extraction-report.json").write_text(json.dumps({"exported": exported, "errors": errors}, indent=2), encoding="utf-8")
    print(json.dumps({"exported": len(exported), "errors": len(errors)}))


if __name__ == "__main__":
    main()
