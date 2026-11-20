"""Derive factual geom visibility and GT instance metadata from RoboCasa source.

No scene-specific names, material colors, or learned semantics are invented.
Official ep_meta fixture/object identities are used for category provenance.
Unmatched geometry stays explicit UNKNOWN, never deleted. Robot exclusion
follows the recorded PandaOmron root prefixes, with review status retained.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from g2.io import ContractError
from g2.offline.atomic_6views_source import DEFAULT_ASSET_ROOTS, _hash
from g2.sim.robocasa_geometry import METADATA_SCHEMA as SCHEMA
from g2.sim.robocasa_geometry import ROBOT_PREFIXES as ROBOT_PREFIXES
from g2.sim.robocasa_geometry import derive_scene_metadata as derive
from g2.sim.source_geometry import load_model, model_source_hash

__all__ = ["ROBOT_PREFIXES", "SCHEMA", "build", "derive", "main"]


def build(rebased_xml, ep_meta, states, output, *, scene_id, asset_roots=DEFAULT_ASSET_ROOTS):
    source = Path(rebased_xml).resolve(strict=True)
    ep_meta = Path(ep_meta).resolve(strict=True)
    states = Path(states).resolve(strict=True)
    dest = Path(output).absolute()
    if dest.exists() or dest.is_symlink():
        raise ContractError("metadata output already exists")
    meta = json.loads(ep_meta.read_text())
    model, sources = load_model(source, asset_roots)
    from g2.sim.source_geometry import apply_state
    data,_=apply_state(model,states,0,"mujoco_fullphysics")
    role, native, audit = derive(
        model, meta, scene_id=scene_id, state_sha256=_hash(states),
        model_source_sha256=model_source_hash(sources),state_data=data)
    dest.mkdir(parents=True)
    for filename, body in (("role_map.json", role), ("native_metadata.json", native),
                           ("source_classification_audit.json", audit)):
        with (dest / filename).open("x", encoding="utf-8") as f:
            json.dump(body, f, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            f.write("\n")
    return audit


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rebased-xml", required=True)
    p.add_argument("--ep-meta", required=True)
    p.add_argument("--states", required=True)
    p.add_argument("--scene-id", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args(argv)
    print(json.dumps(build(args.rebased_xml, args.ep_meta, args.states,
                           args.output, scene_id=args.scene_id), ensure_ascii=False))


if __name__ == "__main__":
    main()
