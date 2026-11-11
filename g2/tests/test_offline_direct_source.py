"""Source binding regressions; no GPU, native raster library or real assets."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from g2.io import ContractError, canonical
from g2.offline.direct_source import load_source, verify_input_config
from g2.sim import source_geometry


def _write_json(path, data):
    path.write_text(json.dumps(data, sort_keys=True, allow_nan=False) + "\n")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _make_inputs(tmp_path, rows=None):
    model = tmp_path / "model.xml"
    model.write_text("<mujoco/>")
    records = [{
        "logical_id": "root.xml", "path": str(model),
        "sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
        "bytes": model.stat().st_size,
    }]
    rows = np.zeros((3, 4), np.float64) if rows is None else rows
    states = tmp_path / "states.npz"
    np.savez(states, states=rows)
    identity = {
        "schema": "nav_sg_mujoco_oracle_v1",
        "mujoco_version": "fixture-version",
        "model_source_sha256": source_geometry.model_source_hash(records),
    }
    source_hash = hashlib.sha256(canonical(identity)).hexdigest()
    gt = {
        "source_identity": identity, "source_sha256": source_hash,
        "scene_id": "TEST_ONLY_direct_source", "sources": records,
        "state": {
            "path": str(states), "format": "mujoco_fullphysics", "frame_id": 0,
            "file_sha256": hashlib.sha256(states.read_bytes()).hexdigest(),
            "row_sha256": hashlib.sha256(np.asarray(rows[0], dtype="<f8").tobytes()).hexdigest(),
        },
    }
    dense = {
        "source_sha256": source_hash,
        "model_source_sha256": identity["model_source_sha256"],
        "frame_id": 200,
        "sampled_geoms": [{"geom_id": 0}],
    }
    role = {"geoms": {"visual_geom": {"role": "visual"}}}
    config = {
        "schema": "g2_direct_color_episode_inputs_v1",
        "source_manifest": _write_json(tmp_path / "source.json", gt),
        "visual_inventory": _write_json(tmp_path / "visual.json", dense),
        "role_map": _write_json(tmp_path / "roles.json", role),
        "states": [],
    }
    for frame in (0, 2):
        snapshot = {
            "frame_id": frame, "scene_id": gt["scene_id"], "source_sha256": source_hash,
            "world_frame": "map", "rooms": [{"uid": 0}],
            "entities": [{"id": "object_0", "source_instance_id": "fixture:object_0"}],
        }
        config["states"].append({
            "frame": frame,
            "snapshot": _write_json(tmp_path / ("snapshot_%d.json" % frame), snapshot),
        })
    return config, gt


def _fake_compiler(monkeypatch, gt, expected_width=4, version="fixture-version"):
    model = SimpleNamespace(ngeom=1)
    fake = SimpleNamespace(
        __version__=version,
        mj_stateSize=lambda model, state_kind: expected_width,
        mjtState=SimpleNamespace(mjSTATE_FULLPHYSICS=1),
    )
    monkeypatch.setitem(sys.modules, "mujoco", fake)
    monkeypatch.setattr(source_geometry, "load_model", lambda *args: (model, gt["sources"]))
    return model


def test_explicit_refs_preserve_frame_order_and_frame_independent_inventory(tmp_path):
    config, _ = _make_inputs(tmp_path)
    gt, dense, role, snapshots = verify_input_config(config)
    assert [snapshot["frame_id"] for snapshot in snapshots] == [0, 2]
    assert dense["frame_id"] == 200
    assert role["geoms"]["visual_geom"]["role"] == "visual"
    assert gt["scene_id"] == snapshots[0]["scene_id"]


def test_modified_reference_bytes_are_rejected(tmp_path):
    config, _ = _make_inputs(tmp_path)
    path = Path(config["role_map"]["path"])
    path.write_text(path.read_text() + " ")
    with pytest.raises(ContractError, match="SHA256 mismatch"):
        verify_input_config(config)


@pytest.mark.parametrize("frames", [(1, 2), (0, 0), (0, True), (0, -1)])
def test_invalid_frame_order_rejected_before_snapshot_access(tmp_path, frames):
    config, _ = _make_inputs(tmp_path)
    for item, frame in zip(config["states"], frames):
        item["frame"] = frame
    with pytest.raises(ContractError, match="frame"):
        verify_input_config(config)


@pytest.mark.parametrize("field,value", [
    ("scene_id", "another_scene"), ("source_sha256", "a" * 64), ("frame_id", 1),
])
def test_resigned_snapshot_cannot_change_scene_source_or_frame(tmp_path, field, value):
    config, _ = _make_inputs(tmp_path)
    reference = config["states"][1]["snapshot"]
    path = Path(reference["path"])
    snapshot = json.loads(path.read_text())
    snapshot[field] = value
    config["states"][1]["snapshot"] = _write_json(path, snapshot)
    with pytest.raises(ContractError, match="snapshot scene/source/frame"):
        verify_input_config(config)


def test_load_source_retains_original_frame_indexed_rows(tmp_path, monkeypatch):
    rows = np.arange(12, dtype=np.float64).reshape(3, 4)
    config, gt = _make_inputs(tmp_path, rows)
    model = _fake_compiler(monkeypatch, gt)
    actual_model, initial, _, _, actual_rows = load_source(config)
    assert actual_model is model
    assert initial["frame_id"] == 0
    np.testing.assert_array_equal(actual_rows, rows)


def test_fullphysics_row_width_is_checked_against_compiled_model(tmp_path, monkeypatch):
    config, gt = _make_inputs(tmp_path)
    _fake_compiler(monkeypatch, gt, expected_width=5)
    with pytest.raises(ContractError, match="fullphysics state shape"):
        load_source(config)


def test_runtime_mujoco_version_is_exact(tmp_path, monkeypatch):
    config, gt = _make_inputs(tmp_path)
    _fake_compiler(monkeypatch, gt, version="different-version")
    with pytest.raises(ContractError, match="compiler version"):
        load_source(config)


def test_resigned_manifest_cannot_replace_initial_state_row_hash(tmp_path, monkeypatch):
    config, gt = _make_inputs(tmp_path)
    gt["state"]["row_sha256"] = "a" * 64
    config["source_manifest"] = _write_json(Path(config["source_manifest"]["path"]), gt)
    _fake_compiler(monkeypatch, gt)
    with pytest.raises(ContractError, match="initial fullphysics row"):
        load_source(config)


def test_model_file_change_is_rejected_before_compilation(tmp_path, monkeypatch):
    config, gt = _make_inputs(tmp_path)
    _fake_compiler(monkeypatch, gt)
    Path(gt["sources"][0]["path"]).write_text("<mujoco><worldbody/></mujoco>")
    with pytest.raises(ContractError, match="model source file hash/size"):
        load_source(config)
