"""Own explicit counter-shaped input and the inspected public code catalog.

Does not execute upstream generators and does not read private scenes. A valid
evidence binding deliberately leaves every real role unknown pending review.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from g2.io import digest, new_output, read_json, verified_file, write_json
from g2.sim.asset_inventory import inventory
from g2.sim.prescan import adapter_source_sha256
from g2.sim.role_review import analyze
from g2.sim.source_geometry import load_model, model_source_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-source-root", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--expected-adapter-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    public = Path(args.public_source_root).resolve(strict=True)
    out = new_output(args.output, [public, args.catalog]); out.mkdir(parents=True)
    reference = read_json(args.catalog); matched = []
    for key, record in reference["sources"].items():
        path = verified_file(public, record); payload = path.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
        assert blob == record["git_blob_sha"]
        matched.append({"source_id": key, "git_blob_sha": blob, "sha256": digest(path)})
    assert adapter_source_sha256() == args.expected_adapter_sha256
    own = out / "TEST_ONLY_own_source"; own.mkdir()
    xml = own / "model.xml"
    xml.write_text('''<mujoco><asset><material name="own_counter_counter_top" rgba=".3 .6 .9 1"/></asset>
      <worldbody><body name="own_counter"><joint type="slide" axis="1 0 0"/>
        <geom name="own_counter_top_visual" type="box" size=".5 .3 .015" pos="0 0 .485"
              group="1" material="own_counter_counter_top" mass="1e-8" contype="0" conaffinity="0"/>
        <geom name="own_counter_top_0" type="box" size=".25 .3 .015" pos="-.25 0 .485" group="0"/>
        <geom name="own_counter_top_1" type="box" size=".25 .3 .015" pos=".25 0 .485" group="0"/>
        <geom name="own_counter_reg_main" type="box" size=".5 .3 .5" rgba="1 0 0 0" contype="0" conaffinity="0"/>
      </body></worldbody></mujoco>''')
    model, sources = load_model(xml)
    qpos = np.zeros((201, model.nq)); qpos[200] = .12
    states = own / "states.npz"; np.savez(states, qpos=qpos, time=np.arange(201) * .02)
    metadata = own / "metadata.json"
    write_json(metadata, {"schema": "g2_sim_prescan_v1", "scene_id": "TEST_ONLY_PUBLIC_CATALOG_ROLE_ANALYSIS",
        "geoms": {}, "state_source": {"model_source_sha256": model_source_hash(sources), "states_sha256": digest(states)}})
    paths = []
    for frame in (0, 200):
        target = out / ("inventory" + str(frame))
        inventory(xml, target, metadata=metadata, states=states, frame=frame)
        paths.append(target / "inventory.json")
    empty = analyze(paths, args.catalog, out / "unresolved")
    template = read_json(out / "unresolved/hypotheses_template.json")
    entry = template["entries"][0]
    entry.update(role="visual", rule_id="counter_contiguous_visual",
        classification_reason="TEST_ONLY own emitted full box and material; a source hypothesis, not private role truth",
        emission_trace="Own fixture reproduces the inspected Counter contiguous-top emission structure",
        condition_evidence={"counter_parameters": "Own width1/depth.6/height1/thickness.03 yield size.5/.3/.015 posz.485",
            "material_binding": "Own XML material own_counter_counter_top binds the full box",
            "original_emission_branch": "Own known contiguous-top structure matches inspected code; no server instance claim"})
    hypotheses = out / "own_hypothesis.json"
    write_json(hypotheses, {"schema": "g2_role_hypotheses_v1", "entries": [entry]})
    candidate = analyze(paths, args.catalog, out / "candidate", decisions=hypotheses,
                        generator_roots={"robocasa": public, "robosuite": public})
    assert empty["remaining_unclassified_count"] == candidate["remaining_unclassified_count"] == 4
    assert candidate["candidate_role_counts"] == {"visual": 1}
    assert candidate["geom_analysis"][0]["role"] == "UNCLASSIFIED"
    assert candidate["training_ready"] is candidate["full_scene_source_certified"] is False
    assert adapter_source_sha256() == args.expected_adapter_sha256
    result = {"status": "PASS", "scope": "OWN_INPUT_PUBLIC_REFERENCE_ONLY_NOT_LAYOUT_CLASSIFICATION",
        "catalog_sha256": digest(args.catalog), "public_source_matches": matched,
        "frames": [0, 200], "compiled_geoms": 4, "unresolved_before": 4, "unresolved_after": 4,
        "evidence_bound_candidates": 1, "actual_role_assignments": 0,
        "original_590_components_accessed_or_classified": False, "generator_code_executed": False,
        "adapter_source_sha256_unchanged": args.expected_adapter_sha256, "training_ready": False}
    write_json(out / "summary.json", result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
