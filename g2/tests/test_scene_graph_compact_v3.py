"""P3 SG event keyframes+lossless deltas and 1mm/1degree floor PNG dedup.

Tests are isolated from the live V3 v1/v2 producer.
"""

from __future__ import annotations

import gzip
import hashlib
import json

import pytest
from PIL import Image

from g2.offline.atomic_6views_plan import PlanError, completed_output
from g2.offline.scene_graph_compact_v3 import (
    SCHEMA,
    convert_v2_to_v3,
    resolve_scene_graph,
    validate_sg_indexed_episode,
)


def _canonical(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def _write_json(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(_canonical(value))


def _write_sg(p, graph):
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, "wb", compresslevel=3) as fp:
        fp.write(_canonical(graph))


def _sg(frame, i, *, topology=None):
    base = 1.0 if i < 3 else 1.2
    return {
        "schema": "g2_robocasa_original_source_spatial_scene_graph_v1",
        "frame_id": frame,
        "timestamp_ns": (frame + 1) * 50000000,
        "original_state_row_sha256": f"{i:064x}",
        "scene_id": "scene_test_A",
        "source_sha256": "a" * 64,
        "training_ready": False,
        "rooms": [{"uid": 0, "label": "Kitchen", "center": [0.0, 0.0, 0.0]}],
        "relations": [
            {"source": "room_0", "target": "entity_0", "type": "contains"}
            if topology is None
            else {"source": "room_0", "target": "entity_0", "type": "near"}
        ],
        "entities": [
            {
                "id": "entity_0",
                "source_instance_id": "fixture:kettle",
                "kind": "object",
                "label": "kettle",
                "bbox_min": [base + i * 1e-7, 0.0, 0.0],
                "bbox_max": [base + 0.1 + i * 1e-7, 0.1, 0.5],
                "centroid": [base + 0.05 + i * 1e-7, 0.05, 0.25],
                "floor_member": True,
                "upper_member": False,
                "room_uid": 0,
            }
        ],
        "connections": {
            "threshold_m": 0.3,
            "objects": [
                {
                    "entity_id": "entity_0",
                    "paths": [
                        {
                            "nodes": ["entity_0", "room_0"],
                            "distances_m": [0.2 + i * 1e-7],
                            "direct_bbox_gap_m": 0.15 + i * 1e-7,
                        }
                    ],
                }
            ],
        },
    }


def mock_v2(root):
    root.mkdir(parents=True)
    frames = [0, 10, 20, 30, 40]
    modes = ["FULL", "ARROW_ONLY", "REUSE_ALL", "FULL", "ARROW_ONLY"]
    floors = "sixview/floor_top.png"
    side = "sixview/plus_Y.png"
    rows = []
    for i, frame in enumerate(frames):
        folder = root / f"state_{i:06d}_frame_{frame:06d}"
        folder.mkdir()
        sg = _sg(frame, i, topology="semantic_change" if i == 4 else None)
        _write_sg(folder / "scene_graph.json.gz", sg)
        physical = []
        refs = {}
        if i == 0:
            physical = [floors, side]
        elif i == 1:
            physical = [floors]
            refs[side] = {"path": side, "ref_state": 0}
        elif i == 2:
            refs[floors] = {"path": floors, "ref_state": 1}
            refs[side] = {"path": side, "ref_state": 0}
        elif i == 3:
            physical = [floors, side]
        else:
            physical = [floors]
            refs[side] = {"path": side, "ref_state": 3}
        for rel in physical:
            target = folder / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            # Frame 1's floor PNG is bitwise equal to frame 0. Frame 2
            # references frame 1, which will get deduplicated to frame 0.
            pixel = (80, 50, 20) if i < 3 else (120, 90, 10)
            Image.new("RGB", (20, 12), pixel).save(target)
        rows.append(
            dict(
                frame=frame,
                view_pngs=physical,
                view_refs=refs,
                update_mode=modes[i],
                scene_graph="scene_graph.json.gz",
                islands=[],
            )
        )
    summary = dict(
        schema="g2_atomic_compact_6views_v2",
        states=rows,
        state_count=len(rows),
        episode_id=11,
        task_class="FixtureTest",
        source_renderer="f27",
        source_fingerprint="f" * 64,
        complete=True,
        training_ready=False,
        indexed_views_enabled=True,
        image_reuse_basis="NONROBOT_GT_VISUAL_POSE_AND_ROBOT_BASE_XY_YAW",
        scene_motion_translation_tol_m=0.001,
        scene_motion_rotation_tol_deg=1.0,
        source_20hz=True,
        spatial_frequency_hz=2,
    )
    _write_json(root / "episode_manifest.json", summary)
    marker = dict(
        schema=summary["schema"],
        complete=True,
        episode_id=11,
        state_count=len(rows),
        renderer="f27",
        source_fingerprint=summary["source_fingerprint"],
        episode_manifest_sha256=hashlib.sha256(
            (root / "episode_manifest.json").read_bytes()
        ).hexdigest(),
    )
    _write_json(root / "COMPLETE.json", marker)
    return frames


def test_lossless_sg_deltas_and_direct_png_refs(tmp_path):
    original = tmp_path / "v2"
    frames = mock_v2(original)
    finished = tmp_path / "v3"
    doc, stats = convert_v2_to_v3(original, finished)
    assert doc["schema"] == SCHEMA
    assert doc["robot_motion_reference_policy"] == "PREVIOUS_SAMPLED_STATE_LEGACY"
    assert doc["robot_motion_xy_tol_m"] == 1e-10
    assert validate_sg_indexed_episode(finished) == len(frames)
    assert [s["scene_graph"] for s in doc["states"]] == [
        "scene_graph.json.gz",
        None,
        None,
        "scene_graph.json.gz",
        "scene_graph.json.gz",
    ]
    assert [
        s["scene_graph_ref"]["ref_state"] if s["scene_graph_ref"] else None
        for s in doc["states"]
    ] == [None, 0, 0, None, None]
    assert stats["sg_keyframes"] == 3 and stats["sg_deltas"] == 2
    assert stats["physical_pngs"] < 7
    rows = doc["states"]
    assert rows[1]["view_refs"]["sixview/floor_top.png"]["ref_state"] == 0
    assert rows[2]["view_refs"]["sixview/floor_top.png"]["ref_state"] == 0
    for i, frame in enumerate(frames):
        with gzip.open(
            original / f"state_{i:06d}_frame_{frame:06d}/scene_graph.json.gz", "rt"
        ) as stream:
            expected = json.load(stream)
        assert resolve_scene_graph(finished, i, doc) == expected
        assert (
            resolve_scene_graph(finished, i)["original_state_row_sha256"] == f"{i:064x}"
        )
    assert (original / "COMPLETE.json").is_file()
    assert not (finished / "state_000001_frame_000010/scene_graph.json.gz").exists()


def test_forged_forward_sg_ref_is_rejected(tmp_path):
    original = tmp_path / "v2"
    mock_v2(original)
    finished = tmp_path / "v3"
    convert_v2_to_v3(original, finished)
    manifest_file = finished / "episode_manifest.json"
    doc = json.loads(manifest_file.read_text())
    doc["states"][2]["scene_graph_ref"]["ref_state"] = 2
    _write_json(manifest_file, doc)
    receipt_file = finished / "COMPLETE.json"
    receipt = json.loads(receipt_file.read_text())
    receipt["episode_manifest_sha256"] = hashlib.sha256(
        manifest_file.read_bytes()
    ).hexdigest()
    _write_json(receipt_file, receipt)
    with pytest.raises(ValueError, match="prior keyframe"):
        validate_sg_indexed_episode(finished)


def test_forged_patch_with_untrusted_matching_receipt_is_rejected(tmp_path):
    original = tmp_path / "v2"
    mock_v2(original)
    finished = tmp_path / "v3"
    convert_v2_to_v3(original, finished)
    patch = finished / "state_000001_frame_000010/scene_graph_delta.json.gz"
    with gzip.open(patch, "rt") as fp:
        data = json.load(fp)
    data["changes"][0][1] = "CORRUPTED"
    _write_sg(patch, data)
    with pytest.raises(ValueError, match="hash mismatch|provenance"):
        validate_sg_indexed_episode(finished)


def test_v2_v3_mixed_resume_requires_explicit_opt_in(tmp_path):
    original = tmp_path / "source_v2"
    frames = mock_v2(original)
    root = tmp_path / "new_output"
    relative = "tasks/FixtureTest/episodes/episode_000011"
    target = root / relative
    convert_v2_to_v3(original, target)
    row = {
        "episode_id": 11,
        "task_class": "FixtureTest",
        "spatial_frames": frames,
        "source_fingerprint": "f" * 64,
        "expected_relative_output": relative,
    }
    with pytest.raises(PlanError, match="explicit v3-capable"):
        completed_output(row, root, allow_index_v2=True)
    assert completed_output(row, root, allow_index_v2=True, allow_index_v3=True)
    forged = dict(row, source_fingerprint="0" * 64)
    with pytest.raises(PlanError, match="invalid indexed v3"):
        completed_output(forged, root, allow_index_v2=True, allow_index_v3=True)


def test_conversion_refuses_source_overlap_and_existing_outputs(tmp_path):
    source = tmp_path / "v2"
    mock_v2(source)
    with pytest.raises(ValueError, match="overlaps|exists"):
        convert_v2_to_v3(source, source)
    target = tmp_path / "v3"
    convert_v2_to_v3(source, target)
    with pytest.raises(ValueError, match="overlaps|exists"):
        convert_v2_to_v3(source, target)
