"""Derive a finite source-bound G2 navigation grid from official MuJoCo geometry.

No hardcoded Layout ID or prerecorded Layout1/10 scene. The TEST_ONLY known
volume is an approximation around the original finite floor slabs; it is not
silently promoted to certified real-camera free space.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from g2.io import ContractError
from g2.sim.robocasa_geometry import GRID_SCHEMA as SCHEMA
from g2.sim.robocasa_geometry import grid_from_source
from g2.sim.source_geometry import apply_state, load_model

__all__ = ["SCHEMA", "build", "grid_from_source", "main"]


def build(model_xml, original_states, native_metadata, output, *,
          asset_roots=("/mnt/data1/data_v2_0617/robocasa_repo",
                       "/mnt/data1/data_v2_0617/robosuite_repo")):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ContractError("grid plan output already exists")
    model, _ = load_model(model_xml, asset_roots)
    data, state = apply_state(model, original_states, 0, "mujoco_fullphysics")
    source = json.loads(Path(native_metadata).read_text(encoding="utf-8"))
    report = grid_from_source(model, data, source)
    report["scene_id"] = source["scene_id"]
    report["frame_zero_source_row_sha256"] = state["row_sha256"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    for name, value in (("grid_plan.json", report),
                        ("known_region.json", report["known_region"])):
        with (output / name).open("x",encoding="utf-8") as f:
            json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
            f.write("\n")
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-xml",required=True)
    p.add_argument("--states",required=True)
    p.add_argument("--metadata",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args(argv)
    report=build(args.model_xml,args.states,args.metadata,args.output)
    print(json.dumps({"scene_id":report["scene_id"],"grid":report["grid"],
                      "known_free_space_is_test_only":True},sort_keys=True),flush=True)


if __name__=="__main__":
    main()
