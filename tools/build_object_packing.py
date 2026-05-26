"""Generate the libero_object_packing task suite from libero_object_all_variance.

Each output YAML reuses its source's arena, robot, cameras, objects, and
inits verbatim; only ``id``, ``language``, ``success``, and ``metadata``
change. Re-run after any init-pose refresh upstream to keep the suites in
sync.

Usage:
    python3 tools/build_object_packing.py
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tasks" / "libero_object_all_variance"
DST = REPO / "tasks" / "libero_object_packing"

LANGUAGE = "Pick all the objects and place them in the basket"
CONTAINER = "basket"


def build_one(src_path: Path, dst_path: Path, index: int) -> None:
    raw = yaml.safe_load(src_path.read_text())
    obj_ids = [o["id"] for o in raw["objects"]]
    if CONTAINER not in obj_ids:
        raise ValueError(
            f"{src_path.name}: expected a '{CONTAINER}' object, got {obj_ids}"
        )
    objs = [o for o in obj_ids if o != CONTAINER]

    raw["id"] = f"libero_object_packing.pack_all_objects_v{index:02d}"
    raw["language"] = LANGUAGE
    raw["success"] = {
        "predicate": "pack_all_into",
        "args": {
            "objs": objs,
            "container": CONTAINER,
            "xy_tol": 0.10,
            "z_low": -0.05,
            "z_high": 0.25,
        },
    }
    md = dict(raw.get("metadata") or {})
    md["suite"] = "libero_object_packing"
    md["source"] = f"derived_from_libero_object_all_variance/{src_path.name}"
    md["n_inits"] = len(raw["inits"])
    raw["metadata"] = md

    dst_path.write_text(yaml.safe_dump(raw, sort_keys=False))


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    sources = sorted(SRC.glob("*.yaml"))
    if not sources:
        raise FileNotFoundError(f"no source YAMLs under {SRC}")
    for i, src in enumerate(sources):
        dst = DST / f"pack_all_objects_v{i:02d}.yaml"
        build_one(src, dst, i)
        print(f"{src.name} -> {dst.relative_to(REPO)}")


if __name__ == "__main__":
    main()
