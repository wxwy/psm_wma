"""Peer findings: PNG contract and sub-mm connection/Island lifetime."""

import copy
import shutil

import numpy as np
import pytest
from PIL import Image

from g2.io import ContractError, digest, read_json, write_json
from g2.latent_cache.streaming import decode_final_png
from g2.nav_bridge.connections import verify_connection_evidence
from g2.offline.atomic_6views_connections import compute
from g2.offline.output_profile import OutputProfile
from g2.offline.scene_view_event_index import SceneViewCursor
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.tests.test_stage_a_package import stage_case
from g2.views.robot_pose_marker import overlay_final_top_views


def test_bad_final_png_is_not_complete_even_with_matching_renderer_sha(tmp_path):
    kwargs, _ = stage_case(
        tmp_path, OutputProfile(selection_top_variant="clean", marker_variants=False)
    )
    image = kwargs["rendered"] / "state_000000_frame_000000/sixview/floor_top.png"
    Image.new("RGB", (1, 1), (230, 220, 210)).save(image)
    for path in kwargs["rendered"].glob("state_*/direct_color_views.json"):
        report = read_json(path)
        for view in report["views"]:
            if view["rgb_file"] == "sixview/floor_top.png":
                view["sha256"] = digest(image)
        write_json(path, report)
    target = tmp_path / "published"
    with pytest.raises(ContractError, match="dimensions"):
        package_stage_a(destination=target, **kwargs)
    assert not target.exists()
    assert not list(tmp_path.glob("._stage_a_*/COMPLETE.json"))
    with pytest.raises(ContractError, match="PNG"):
        decode_final_png(b"\x89PNG\r\n\x1a\nnot-an-image", expected_size=(64, 64))


@pytest.mark.parametrize("reappears", [False, True])
def test_sub_mm_island_retirement_keeps_history_but_no_current_payload(
    tmp_path, reappears
):
    kwargs, snapshots = stage_case(
        tmp_path, OutputProfile(selection_top_variant="clean")
    )
    config = read_json(kwargs["inputs"])
    cursor = SceneViewCursor([11])
    modes = []
    for i, (row, snapshot) in enumerate(zip(config["states"], snapshots)):
        snapshot = copy.deepcopy(snapshot)
        lift = 0.2998 if i == 0 or (i == 2 and reappears) else 0.3002
        for entity in snapshot["entities"]:
            if entity["id"] in ("entity_2", "entity_3"):
                for key in ("bbox_min", "bbox_max"):
                    entity[key][2] += lift
                for vertex in entity["vertices"]:
                    vertex[2] += lift
        (
            snapshot["connections"],
            snapshot["entities"],
            snapshot["affiliations_complete"],
        ) = compute(snapshot["entities"], [0], connection_distance=0.3, known=True)
        verify_connection_evidence(snapshot)
        for key in ("snapshot", "scene_graph"):
            write_json(row[key]["path"], snapshot)
            row[key]["sha256"] = digest(row[key]["path"])
        event = cursor.observe(
            i,
            row["frame"],
            np.array([[0.0, 0.0, lift]]),
            np.eye(3)[None],
            [0.3 if i else 0.0, 0.0, 0.0],
        )
        modes.append(event.mode)
        assert event.object_translation_max_m < 0.001
    assert modes == ["FULL", "ARROW_ONLY", "REUSE_ALL"]
    write_json(kwargs["inputs"], config)
    receipt_path = kwargs["rendered"] / "episode_receipt.json"
    receipt = read_json(receipt_path)
    receipt["source_inputs_sha256"] = digest(kwargs["inputs"])
    write_json(receipt_path, receipt)
    target = tmp_path / "published"
    result = package_stage_a(destination=target, **kwargs)
    validate_profile_episode(target)
    vid = "islands/island_0_entity_2/plus_X"
    source = read_json(target / "spatial_source.json")
    assert source["views"][vid]["state_records"] == [0, None, 0 if reappears else None]
    absent = read_json(target / result["states"][1]["spatial_metadata"])
    assert absent["views"][vid]["availability"] == "absent"
    assert absent["views"][vid]["image_owner"]["state_id"] == 0
    assert absent["views"][vid]["membership"]["native_entity_ids"] == []
    assert (
        absent["view_catalog"][vid]["reason"]
        == "NATIVE_ISLAND_RETIRED_IN_CURRENT_MEMBER_PLAN"
    )
    assert vid not in result["states"][1]["selection"]["selected_view_ids"]
    assert "island_0_entity_2" not in result["states"][1]["islands"]


def test_marked_variant_matches_existing_overlay_reference(tmp_path):
    kwargs, _ = stage_case(
        tmp_path / "fixture", OutputProfile(selection_top_variant="clean")
    )
    first = kwargs["rendered"] / "state_000000_frame_000000"
    legacy = tmp_path / "legacy_overlay"
    shutil.copytree(first, legacy)
    report = read_json(legacy / "direct_color_views.json")
    report["views"] = [
        v for v in report["views"] if not v["rgb_file"].endswith("_w_rbs.png")
    ]
    write_json(legacy / "direct_color_views.json", report)
    overlay_final_top_views(legacy, report["raw_robot_pose"])
    assert digest(legacy / "sixview/floor_top.png") == digest(
        first / "sixview/floor_top_w_rbs.png"
    )
