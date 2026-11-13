"""P3 SG event keyframes+lossless deltas and 1mm/1degree floor PNG dedup.

Tests are isolated from the live V3 v1/v2 producer.
"""

from __future__ import annotations

import copy
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


def _refresh_manifest(root, doc):
    _write_json(root / "episode_manifest.json", doc)
    marker = json.loads((root / "COMPLETE.json").read_text())
    marker["episode_manifest_sha256"] = hashlib.sha256(
        (root / "episode_manifest.json").read_bytes()
    ).hexdigest()
    _write_json(root / "COMPLETE.json", marker)


def _source_graph(root, index, doc):
    frame = doc["states"][index]["frame"]
    with gzip.open(root / f"state_{index:06d}_frame_{frame:06d}/scene_graph.json.gz", "rt") as fp:
        return json.load(fp)


def _repeat_source_body(root, body_owner, indices, *, reuse_views):
    doc = json.loads((root / "episode_manifest.json").read_text())
    body = _source_graph(root, body_owner, doc)
    for i in indices:
        row = doc["states"][i]
        folder = root / f"state_{i:06d}_frame_{row['frame']:06d}"
        current = _source_graph(root, i, doc)
        graph = copy.deepcopy(body)
        for name in ("frame_id", "timestamp_ns", "original_state_row_sha256"):
            graph[name] = current[name]
        _write_sg(folder / "scene_graph.json.gz", graph)
        row["update_mode"] = "REUSE_ALL" if reuse_views else "ARROW_ONLY"
        if reuse_views:
            for relative in row["view_pngs"]:
                (folder / relative).unlink()
            row["view_pngs"] = []
            row["view_refs"] = {
                relative: {"ref_state": 0, "path": relative}
                for relative in doc["states"][0]["view_pngs"]
            }
    _refresh_manifest(root, doc)


def test_metadata_only_frames_have_no_directory(tmp_path):
    original = tmp_path / "v2"
    mock_v2(original)
    _repeat_source_body(original, 0, range(1, 5), reuse_views=True)
    finished = tmp_path / "v3"
    doc, stats = convert_v2_to_v3(original, finished)
    assert doc["sg_frame_metadata_policy"] == "INLINE_FRAME_METADATA_WITH_DIRECT_SG_BODY_REFS_V1"
    assert stats["sg_keyframes"] == 1
    assert stats["sg_deltas"] == 0
    assert stats["sg_reused"] == 4
    source = json.loads((original / "episode_manifest.json").read_text())
    for i, row in enumerate(doc["states"]):
        assert resolve_scene_graph(finished, i, doc) == _source_graph(original, i, source)
        assert row["scene_graph_frame_metadata"]["frame_id"] == row["frame"]
        if i:
            assert row["scene_graph_ref"] == {"ref_state": 0}
            assert not (finished / f"state_{i:06d}_frame_{row['frame']:06d}").exists()
    assert validate_sg_indexed_episode(finished) == 5


def _delta_reuse_source(root):
    mock_v2(root)
    # State 1 changes geometry. Later states preserve that exact body and
    # retain their own frame/time/GT evidence without new SG files.
    _repeat_source_body(root, 1, range(2, 5), reuse_views=True)


def test_unchanged_delta_body_reuses_physical_delta_without_directory(tmp_path):
    original = tmp_path / "v2"
    _delta_reuse_source(original)
    finished = tmp_path / "v3"
    doc, stats = convert_v2_to_v3(original, finished)
    assert stats["sg_keyframes"] == 1 and stats["sg_deltas"] == 1
    assert stats["sg_reused"] == 3
    assert doc["states"][1]["scene_graph_ref"] == {
        "ref_state": 0, "delta": "scene_graph_delta.json.gz"
    }
    source = json.loads((original / "episode_manifest.json").read_text())
    for i in range(2, 5):
        row = doc["states"][i]
        assert row["scene_graph_ref"] == {"ref_state": 0, "delta_ref_state": 1}
        assert not (finished / f"state_{i:06d}_frame_{row['frame']:06d}").exists()
        assert resolve_scene_graph(finished, i, doc) == _source_graph(original, i, source)
    assert validate_sg_indexed_episode(finished) == 5


def test_png_update_with_reused_sg_creates_only_png_directory(tmp_path):
    original = tmp_path / "v2"
    mock_v2(original)
    _repeat_source_body(original, 0, [1], reuse_views=False)
    floor = original / "state_000001_frame_000010/sixview/floor_top.png"
    Image.new("RGB", (20, 12), (9, 10, 11)).save(floor)
    finished = tmp_path / "v3"
    doc, _ = convert_v2_to_v3(original, finished)
    row = doc["states"][1]
    folder = finished / "state_000001_frame_000010"
    assert row["scene_graph_ref"] == {"ref_state": 0}
    assert row["view_pngs"] == ["sixview/floor_top.png"]
    assert sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()) == [
        "sixview/floor_top.png"
    ]
    assert validate_sg_indexed_episode(finished) == 5


@pytest.mark.parametrize("tamper", [
    "self_delta", "forward_delta", "chained_delta", "delta_path", "metadata",
    "missing_delta", "delta_directory_symlink", "reference_directory_symlink",
])
def test_inline_refs_reject_invalid_targets_and_identity(tmp_path, tamper):
    original = tmp_path / "v2"
    _delta_reuse_source(original)
    finished = tmp_path / "v3"
    doc, _ = convert_v2_to_v3(original, finished)
    rows = doc["states"]
    if tamper == "self_delta":
        rows[2]["scene_graph_ref"]["delta_ref_state"] = 2
    elif tamper == "forward_delta":
        rows[2]["scene_graph_ref"]["delta_ref_state"] = 3
    elif tamper == "chained_delta":
        rows[3]["scene_graph_ref"]["delta_ref_state"] = 2
    elif tamper == "delta_path":
        rows[1]["scene_graph_ref"]["delta"] = "../scene_graph_delta.json.gz"
    elif tamper == "metadata":
        rows[2]["scene_graph_frame_metadata"]["timestamp_ns"] += 1
    elif tamper == "missing_delta":
        (finished / "state_000001_frame_000010/scene_graph_delta.json.gz").unlink()
    elif tamper == "delta_directory_symlink":
        folder = finished / "state_000001_frame_000010"
        folder.rename(finished / "relocated_delta")
        folder.symlink_to(finished / "relocated_delta", target_is_directory=True)
    elif tamper == "reference_directory_symlink":
        (finished / "state_000002_frame_000020").symlink_to(
            finished / "state_000000_frame_000000", target_is_directory=True
        )
    _refresh_manifest(finished, doc)
    with pytest.raises(ValueError):
        validate_sg_indexed_episode(finished)


def test_legacy_v3_metadata_in_delta_stays_readable(tmp_path):
    original = tmp_path / "v2"
    mock_v2(original)
    finished = tmp_path / "legacy_v3"
    doc, _ = convert_v2_to_v3(original, finished)
    # Rebuild the previous v3 wire format without importing a second writer.
    for i, row in enumerate(doc["states"]):
        metadata = row.pop("scene_graph_frame_metadata")
        ref = row["scene_graph_ref"]
        if ref is not None:
            patch_path = finished / f"state_{i:06d}_frame_{row['frame']:06d}/scene_graph_delta.json.gz"
            with gzip.open(patch_path, "rt") as fp:
                patch = json.load(fp)
            patch["changes"].extend([[name], value] for name, value in sorted(metadata.items()))
            _write_sg(patch_path, patch)
    doc["sg_frame_metadata_policy"] = "EXACT_DELTA_TO_PHYSICAL_SG_KEYFRAME"
    for name in ("sg_geometry_policy", "sg_geometry_error_bound_m", "sg_geometry_reference_policy"):
        doc.pop(name, None)
    _refresh_manifest(finished, doc)
    source = json.loads((original / "episode_manifest.json").read_text())
    assert validate_sg_indexed_episode(finished) == 5
    for i in range(5):
        assert resolve_scene_graph(finished, i) == _source_graph(original, i, source)


def _geometry_source(root, offsets):
    mock_v2(root)
    _repeat_source_body(root, 0, range(1, 5), reuse_views=True)
    doc = json.loads((root / "episode_manifest.json").read_text())
    origins = {
        "bbox_min": [0.0, 0.0, 0.0],
        "bbox_max": [0.1, 0.1, 0.5],
        "centroid": [0.05, 0.05, 0.25],
    }
    for i, offset in enumerate(offsets):
        row = doc["states"][i]
        graph = _source_graph(root, i, doc)
        for name, origin in origins.items():
            graph["entities"][0][name] = [a + b for a, b in zip(origin, offset)]
        _write_sg(root / f"state_{i:06d}_frame_{row['frame']:06d}/scene_graph.json.gz", graph)
    return doc


def test_event_numeric_noise_reuses_keyframe_without_frame_directory(tmp_path):
    original = tmp_path / "v2"
    source = _geometry_source(original, [
        (0, 0, 0), (0.00004, 0, 0), (0.00008, 0, 0),
        (0.000085, 0, 0), (0.000085, 0, 0),
    ])
    finished = tmp_path / "event"
    doc, stats = convert_v2_to_v3(original, finished, _event_keyframes=True)
    assert doc["sg_geometry_policy"] == "EVENT_KEYFRAME"
    assert doc["sg_geometry_error_bound_m"] == 0.001
    assert stats["sg_keyframes"] == 1 and stats["sg_deltas"] == 0
    assert stats["sg_reused"] == 4
    keyframe = _source_graph(original, 0, source)
    for i, row in enumerate(doc["states"]):
        raw = _source_graph(original, i, source)
        stored = resolve_scene_graph(finished, i)
        assert row["source_scene_graph_sha256"] == hashlib.sha256(_canonical(raw)).hexdigest()
        assert row["scene_graph_sha256"] == hashlib.sha256(_canonical(stored)).hexdigest()
        assert stored["entities"] == keyframe["entities"]
        for key in ("frame_id", "timestamp_ns", "original_state_row_sha256"):
            assert stored[key] == raw[key]
        if i:
            assert row["source_scene_graph_sha256"] != row["scene_graph_sha256"]
            assert 0 < row["scene_graph_max_geometry_error_m"] < 0.001
            assert not (finished / f"state_{i:06d}_frame_{row['frame']:06d}").exists()
    assert validate_sg_indexed_episode(finished) == 5


def test_event_geometry_drift_accumulates_from_last_physical_keyframe(tmp_path):
    original = tmp_path / "v2"
    _geometry_source(original, [(i * 0.0004, 0, 0) for i in range(5)])
    finished = tmp_path / "event"
    doc, stats = convert_v2_to_v3(original, finished, _event_keyframes=True)
    assert stats["sg_keyframes"] == 2 and stats["sg_deltas"] == 0
    assert [i for i, row in enumerate(doc["states"]) if row["scene_graph"]] == [0, 3]
    assert doc["states"][2]["scene_graph_ref"] == {"ref_state": 0}
    assert doc["states"][2]["scene_graph_max_geometry_error_m"] == pytest.approx(0.0008)
    assert doc["states"][4]["scene_graph_ref"] == {"ref_state": 3}
    assert doc["states"][4]["scene_graph_max_geometry_error_m"] == pytest.approx(0.0004)
    assert doc["states"][3]["source_scene_graph_sha256"] == doc["states"][3]["scene_graph_sha256"]


@pytest.mark.parametrize("offset, new_keyframe", [
    ((0.0006, 0.0006, 0.0), False),
    ((0.0008, 0.0008, 0.0), True),
    ((0.001, 0.0, 0.0), True),
])
def test_event_vector_bound_is_euclidean_and_strict(tmp_path, offset, new_keyframe):
    original = tmp_path / "v2"
    _geometry_source(original, [(0, 0, 0)] + [offset] * 4)
    doc, _ = convert_v2_to_v3(original, tmp_path / "event", _event_keyframes=True)
    assert (doc["states"][1]["scene_graph"] is not None) is new_keyframe


def test_event_connection_distances_use_cumulative_absolute_error(tmp_path):
    original = tmp_path / "v2"
    source = _geometry_source(original, [(0, 0, 0)] * 5)
    for i, row in enumerate(source["states"]):
        graph = _source_graph(original, i, source)
        graph["connections"]["objects"][0]["paths"][0]["distances_m"] = [0.2 + 0.0006 * i]
        _write_sg(original / f"state_{i:06d}_frame_{row['frame']:06d}/scene_graph.json.gz", graph)
    doc, _ = convert_v2_to_v3(original, tmp_path / "event", _event_keyframes=True)
    assert [i for i, row in enumerate(doc["states"]) if row["scene_graph"]] == [0, 2, 4]
    assert doc["states"][1]["scene_graph_max_geometry_error_m"] == pytest.approx(0.0006)
    assert doc["states"][3]["scene_graph_ref"] == {"ref_state": 2}


@pytest.mark.parametrize("change", ["semantic", "unknown_numeric", "geometry_shape"])
def test_event_semantic_or_unrecognized_changes_force_keyframe(tmp_path, change):
    original = tmp_path / "v2"
    source = _geometry_source(original, [(0, 0, 0)] * 5)
    graph = _source_graph(original, 1, source)
    if change == "semantic":
        graph["relations"][0]["type"] = "near"
    elif change == "unknown_numeric":
        graph["entities"][0]["unclassified_metric"] = 1e-7
    else:
        graph["entities"][0]["centroid"] = [0.05, 0.05]
    _write_sg(original / "state_000001_frame_000010/scene_graph.json.gz", graph)
    doc, _ = convert_v2_to_v3(original, tmp_path / "event", _event_keyframes=True)
    assert doc["states"][1]["scene_graph"] == "scene_graph.json.gz"
    assert doc["states"][1]["source_scene_graph_sha256"] == doc["states"][1]["scene_graph_sha256"]


def test_event_nonfinite_geometry_is_rejected_without_publication(tmp_path):
    original = tmp_path / "v2"
    source = _geometry_source(original, [(0, 0, 0)] * 5)
    graph = _source_graph(original, 1, source)
    graph["entities"][0]["centroid"][0] = float("nan")
    with gzip.open(original / "state_000001_frame_000010/scene_graph.json.gz", "wt") as fp:
        json.dump(graph, fp)
    target = tmp_path / "event"
    with pytest.raises(ValueError):
        convert_v2_to_v3(original, target, _event_keyframes=True)
    assert not target.exists()


@pytest.mark.parametrize("tamper", ["negative_error", "bound_error", "raw_hash", "policy_bound"])
def test_event_geometry_evidence_is_validated(tmp_path, tamper):
    original = tmp_path / "v2"
    _geometry_source(original, [(0, 0, 0)] + [(0.00004, 0, 0)] * 4)
    target = tmp_path / "event"
    doc, _ = convert_v2_to_v3(original, target, _event_keyframes=True)
    if tamper == "negative_error":
        doc["states"][1]["scene_graph_max_geometry_error_m"] = -1
    elif tamper == "bound_error":
        doc["states"][1]["scene_graph_max_geometry_error_m"] = 0.001
    elif tamper == "raw_hash":
        doc["states"][1]["source_scene_graph_sha256"] = "bad"
    else:
        doc["sg_geometry_error_bound_m"] = 0.01
    _refresh_manifest(target, doc)
    with pytest.raises(ValueError):
        validate_sg_indexed_episode(target)
