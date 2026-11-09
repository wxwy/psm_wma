"""CPU-only own source parity; never reads external/private scene inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", required=True)
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    baseline = Path(args.baseline_root).resolve()
    candidate = Path(args.candidate_root).resolve()
    sys.path.insert(0, str(candidate))
    import mujoco
    import numpy as np
    from g2.io import digest, write_json
    from g2.sim.source_geometry import load_model, model_source_hash, primitive_mesh
    from g2.sim.color_evidence import verify_color_evidence

    output = Path(args.output).resolve(); output.mkdir(parents=True, exist_ok=False)
    source = output / "own_source"; source.mkdir()
    vertices, faces = primitive_mesh("box", np.asarray([.2, .3, .4]))
    (source / "mesh.obj").write_text("".join("v %.17g %.17g %.17g\n" % tuple(v) for v in vertices)
        + "vt .25 .25\nvt .75 .25\nvt .25 .75\n"
        + "".join("f %d/1 %d/2 %d/3\n" % tuple(f + 1) for f in faces))
    model = source / "model.xml"
    model.write_text('''<mujoco><asset><mesh name="m" file="mesh.obj"/>
      <texture name="t" type="2d" builtin="checker" rgb1="1 0 0" rgb2="0 1 0" width="2" height="2"/>
      <material name="mat" texture="t" rgba="1 1 1 1"/></asset><worldbody>
      <body name="moving"><joint type="slide" axis="1 0 0"/>
        <geom name="mesh" type="mesh" mesh="m" material="mat"/></body>
      <geom name="box" type="box" size=".1 .2 .3" pos="1 0 0"/>
      <geom name="sphere" type="sphere" size=".2" pos="2 0 0"/>
      <geom name="ellipsoid" type="ellipsoid" size=".1 .2 .3" pos="3 0 0"/>
      <geom name="capsule" type="capsule" size=".1 .2" pos="4 0 0"/>
      <geom name="cylinder" type="cylinder" size=".1 .2" pos="5 0 0"/>
      </worldbody></mujoco>''')
    metadata = source / "roles.json"
    qpos = np.zeros((201, 1)); qpos[200] = .12
    states = source / "states.npz"; np.savez(states, qpos=qpos, time=np.arange(201) * .02)
    compiled, sources = load_model(model)
    names = [mujoco.mj_id2name(compiled, mujoco.mjtObj.mjOBJ_GEOM, g) for g in range(compiled.ngeom)]
    write_json(metadata, {"schema": "g2_sim_prescan_v1", "scene_id": "TEST_ONLY_POSITIVE_PARITY",
        "state_source": {"model_source_sha256": model_source_hash(sources), "states_sha256": digest(states)},
        "geoms": {name: {"role": "visual", "source_kind": "mjcf", "geom_name": name,
                          "classification_reason": "Own positive surface parity fixture"} for name in names}})
    results = []
    for frame in (0, 200):
        paths = []
        for label, root in (("old", baseline), ("new", candidate)):
            target = output / (label + "_f" + str(frame))
            env = dict(os.environ, PYTHONPATH=str(root))
            command = [sys.executable, "-m", "g2.sim.prescan", "--mjcf", str(model), "--metadata", str(metadata),
                       "--states", str(states), "--frame", str(frame), "--spacing", ".2", "--output", str(target)]
            run = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            (output / (label + "_f" + str(frame) + ".log")).write_text(run.stdout + run.stderr)
            assert run.returncode == 0, run.stderr
            paths.append(target)
        old, new = [b"".join((path / "precolored.txt").read_bytes().splitlines(keepends=True)[7:]) for path in paths]
        assert old == new, "XYZ/RGB/valid data rows differ"
        manifests = [json.loads((path / "manifest.json").read_bytes()) for path in paths]
        assert manifests[0]["source_identity"]["color_evidence_protocol"] == "g2_sample_color_audit_v1"
        assert manifests[1]["source_identity"]["color_evidence_protocol"] == "g2_sample_color_audit_v2"
        assert manifests[0]["source_identity"]["adapter_source_sha256"] != manifests[1]["source_identity"]["adapter_source_sha256"]
        assert manifests[0]["visual_source_sha256"] != manifests[1]["visual_source_sha256"]
        for path, manifest in zip(paths, manifests):
            assert verify_color_evidence(path, manifest, path / "precolored.txt")
        assert manifests[0]["point_count"] == manifests[1]["point_count"]
        assert manifests[0]["state"] == manifests[1]["state"]
        assert manifests[0]["bounds_min"] == manifests[1]["bounds_min"]
        assert manifests[0]["bounds_max"] == manifests[1]["bounds_max"]
        assert [row["local_geometry_sha256"] for row in manifests[0]["visual_geoms"]] == [
            row["local_geometry_sha256"] for row in manifests[1]["visual_geoms"]]
        results.append({"frame_id": frame, "geometry_types": names, "data_rows_byte_identical": True,
            "point_count": manifests[1]["point_count"], "data_rows_sha256": hashlib.sha256(new).hexdigest(),
            "state_bounds_and_original_geometry_hashes_identical": True,
            "old_v1_and_new_v2_disk_evidence_verified":True,
            "adapter_and_visual_source_epoch_changed":True})
    report = {"status": "PASS", "scope": "OWN_POSITIVE_FIXTURES_ONLY_NOT_REAL_LAYOUT_ACCEPTANCE",
        "baseline_runtime": "3b6c6055e36824be33ed947745aa3e5b839da832", "frames": results,
        "header_comparison": "SOURCE_CODE_IDENTITY_EXPECTED_TO_CHANGE_DATA_ROWS_ONLY_COMPARED",
        "python": sys.version, "mujoco": mujoco.__version__, "numpy": np.__version__, "training_ready": False}
    write_json(output / "parity.json", report)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
