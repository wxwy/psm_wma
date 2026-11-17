"""Synthetic native/F27 boundary tests, not real RoboCasa acceptance."""

import copy
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from g2.io import ContractError, digest, read_json, write_json
from g2.latent_cache.contract import CacheError
from g2.latent_cache.source import scan_episode
from g2.latent_cache.storage import build_lock
from g2.latent_cache.streaming import ConsumerLimits
from g2.offline.episode import _reuse_scene_view_keyframe
from g2.offline.output_profile import OutputProfile
from g2.offline.scene_view_event_index import SceneViewCursor
from g2.offline.stage_a import RAW_SCHEMA, package_stage_a, validate_profile_episode
from g2.tests.test_connections import connection_case
from g2.views.render_connections import renderer_member_sets
from g2.views.robot_pose_marker import MarkerAppearance, overlay_final_top_views


def stage_case(root, profile):
    """Actual marker/reuse functions; synthetic certified native geometry."""
    root = Path(root)
    source, raw = root / "source", root / "raw"
    source.mkdir(parents=True)
    raw.mkdir()
    original = connection_case()
    for i, entity in enumerate(original["entities"]):
        entity.update(
            source_instance_id="fixture:target" if i in (2, 3) else "fixture:source",
            source_part_id="part_" + str(i),
        )
    plan = renderer_member_sets(original)
    first = raw / "state_000000_frame_000000"
    assets = []
    catalog = {}
    for native, members in plan.items():
        meta = dict(
            axis=members["axis"],
            coordinate_frame="NATIVE_ROOM_REFERENCE",
            reference_frame=original["rooms"][0]["reference_frame"],
            right_world=[1, 0, 0],
            up_world=[0, 1, 0],
            forward_world=[0, 0, -1],
            uv_min_room=[-2, -2],
            width=64,
            height=64,
            meters_per_pixel=0.0625,
            native_entity_ids=members["native_entity_ids"],
            image_generated=False,
            reason="NO_OBJECT_WITH_PROJECTABLE_SURFACE_IN_NATIVE_DIRECTION",
        )
        name = native.split("/")[-1]
        if (
            name == "floor_top"
            or (name == "minus_Y" and not members["island_id"])
            or (name == "plus_X" and members["island_id"] == "island_0_entity_2")
        ):
            rel = (
                (
                    "islands/" + members["island_id"] + "/"
                    if members["island_id"]
                    else "sixview/"
                )
                + name
                + ".png"
            )
            path = first / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (64, 64), (230, 220, 210)).save(path)
            assets.append(dict(native_view=native, rgb_file=rel, sha256=digest(path)))
            meta.update(image_generated=True, reason="TEST_ONLY_SYNTHETIC_SURFACE")
        (first / "g2_original_gpu" / native).mkdir(parents=True, exist_ok=True)
        write_json(first / "g2_original_gpu" / native / "view.json", meta)
        catalog[native] = meta
    write_json(
        first / "direct_color_views.json",
        dict(
            views=assets,
            view_count=len(assets),
            frame_id=0,
            scene_source_state=0,
            renderer_view_catalog=catalog,
        ),
    )
    pose = dict(
        position_world=[0.0, 0.0, 0.0],
        forward_world=[1.0, 0.0, 0.0],
        source_body="TEST_ONLY_CHASSIS",
        forward_axis="body_local_positive_X",
    )
    if profile.marker_variants and profile.render_rgb:
        overlay_final_top_views(first, pose, preserve_clean=True)
    full_report = read_json(first / "direct_color_views.json")
    full_report["raw_robot_pose"] = dict(
        pose, source_frame=0, frame=0, coordinate_frame="world"
    )
    write_json(first / "direct_color_views.json", full_report)
    cursor = SceneViewCursor([11])
    cursor.observe(0, 0, np.zeros((1, 3)), np.eye(3)[None], [0.0, 0.0, 0.0])
    rows, snapshots = [], []
    for state_id, frame in enumerate((0, 10, 20)):
        snapshot = copy.deepcopy(original)
        snapshot["frame_id"] = frame
        snapshots.append(snapshot)
        path = source / f"snapshot_{frame}.json"
        graph_path = source / f"sg_{frame}.json"
        write_json(path, snapshot)
        write_json(graph_path, snapshot)
        current_pose = dict(
            pose, position_world=[0.3, 0.0, 0.0] if state_id else [0.0, 0.0, 0.0]
        )
        raw_pose = dict(
            current_pose, source_frame=frame, frame=frame, coordinate_frame="world"
        )
        rows.append(
            dict(
                frame=frame,
                snapshot=dict(path=str(path), sha256=digest(path)),
                scene_graph=dict(path=str(graph_path), sha256=digest(graph_path)),
                raw_robot_pose=raw_pose,
            )
        )
        if state_id:
            directory = raw / f"state_{state_id:06d}_frame_{frame:06d}"
            directory.mkdir()
            event = cursor.observe(
                state_id, frame, np.zeros((1, 3)), np.eye(3)[None], [0.3, 0.0, 0.0]
            )
            report = _reuse_scene_view_keyframe(
                directory,
                first,
                full_report,
                event,
                snapshot,
                current_pose,
                MarkerAppearance(),
                "game_arrow",
                profile,
            )
            report["raw_robot_pose"] = raw_pose
            write_json(directory / "direct_color_views.json", report)
    inputs = source / "episode_inputs.json"
    write_json(inputs, dict(states=rows))
    write_json(
        raw / "episode_receipt.json",
        dict(
            schema=RAW_SCHEMA,
            complete=True,
            output_profile_id=profile.to_dict()["profile_id"],
            source_inputs_sha256=digest(inputs),
            states=[dict(state_id=i, frame=r["frame"]) for i, r in enumerate(rows)],
        ),
    )
    metadata = dict(
        fixtures=dict(target=dict(cls="Counter"), source=dict(cls="Counter")),
        fixture_refs=dict(target_fixture="target", src_fixture="source"),
        object_cfgs=[],
        lang="Navigate to the target counter.",
    )
    captions = {
        f: dict(
            original_text=metadata["lang"],
            task_index=4,
            frame_index=f,
            episode_index=0,
            authority="TEST_ONLY_CAPTION_ROWS",
        )
        for f in (0, 10, 20)
    }
    return dict(
        inputs=inputs,
        rendered=raw if profile.render_rgb else None,
        profile=profile,
        episode_id=0,
        task_class="NavigateKitchen",
        ep_meta=metadata,
        source_fingerprint="a" * 64,
        captions=captions,
    ), snapshots


def test_final_pixels_membership_owner_and_bidirectional_union(tmp_path):
    kwargs, _ = stage_case(tmp_path, OutputProfile(selection_top_variant="clean"))
    target = tmp_path / "published"
    result = package_stage_a(destination=target, **kwargs)
    assert result["profile_complete"] and not result["training_ready"]
    assert (target / "COMPLETE.json").is_file()
    assert validate_profile_episode(target) == result
    source = read_json(target / "spatial_source.json")
    assert source["views"]["sixview/floor_top"]["state_records"] == [0, 0, 0]
    assert source["views"]["sixview/floor_top_w_rbs"]["state_records"] == [0, 1, 1]
    marked = source["views"]["sixview/floor_top_w_rbs"]["owners"][1]
    assert marked["state_id"] == 1 and marked["scene_geometry_source_state"] == 0
    spatial = read_json(target / result["states"][2]["spatial_metadata"])
    assert spatial["views"]["sixview/floor_top_w_rbs"]["image_owner"]["state_id"] == 1
    assert spatial["views"]["sixview/floor_top"]["image_owner"]["state_id"] == 0
    assert spatial["view_catalog"]["sixview/plus_Y"]["availability"] == "absent"
    assert set(result["states"][2]["selection"]["selected_view_ids"]) == {
        "sixview/floor_top",
        "islands/island_0_entity_2/plus_X",
    }
    assert len(read_json(target / "language.json")["texts"]) == 1
    with pytest.raises((CacheError, ContractError)):
        scan_episode(target)  # No weakening of the legacy completed scanner.
    with pytest.raises(ContractError, match="exists"):
        package_stage_a(destination=target, **kwargs)


@pytest.mark.parametrize(
    "png,vae", [(True, False), (True, True), (False, True), (False, False)]
)
def test_four_profile_combinations_and_separate_source_readiness(tmp_path, png, vae):
    profile = OutputProfile(
        sixview_png=png,
        island_png=png,
        view_vae=vae,
        selection=png or vae,
        selection_top_variant="clean" if png or vae else None,
        spatial_metadata=png or vae,
        marker_variants=png or vae,
    )
    kwargs, _ = stage_case(tmp_path, profile)
    observed = []
    target = tmp_path / "published"
    result = package_stage_a(destination=target, event_sink=observed.append, **kwargs)
    assert result["profile_complete"] is not vae
    assert (target / "COMPLETE.json").exists() is not vae
    assert result["products"]["view_vae"] == ("pending" if vae else "disabled")
    assert bool(observed) is vae
    assert (target / "_spatial_inputs").exists() is (vae and not png)
    assert (target / "state_000000_frame_000000/sixview").exists() is png
    validate_profile_episode(target, require_complete=not vae)
    if vae:
        with pytest.raises(ContractError, match="incomplete"):
            validate_profile_episode(target)
    else:
        assert result["products"]["robot_pose"] == "ready"


def test_consumer_failure_budget_and_source_mutation_never_publish_complete(tmp_path):
    kwargs, _ = stage_case(
        tmp_path,
        OutputProfile(
            selection_top_variant="clean",
            sixview_png=False,
            island_png=False,
            view_vae=True,
        ),
    )
    target = tmp_path / "failed"
    with pytest.raises(ContractError, match="budget"):
        package_stage_a(
            destination=target, limits=ConsumerLimits(max_spool_bytes=1), **kwargs
        )
    assert not target.exists()
    assert list(tmp_path.glob("._stage_a_*/FAILED.json"))
    assert not list(tmp_path.glob("._stage_a_*/COMPLETE.json"))

    def failed(_):
        raise RuntimeError("consumer unavailable")

    with pytest.raises(RuntimeError, match="consumer unavailable"):
        package_stage_a(destination=target, event_sink=failed, **kwargs)
    assert not target.exists()
    with build_lock(target.parent / (".stage-a-lock-" + target.name)):
        with pytest.raises(CacheError, match="another builder"):
            package_stage_a(destination=target, **kwargs)

    def mutation(_):
        kwargs["inputs"].write_text("{}")

    with pytest.raises(ContractError, match="changed during"):
        package_stage_a(destination=target, event_sink=mutation, **kwargs)
    assert not target.exists()


def test_corruption_and_fake_complete_rejected_without_touching_source(tmp_path):
    kwargs, _ = stage_case(
        tmp_path, OutputProfile(selection_top_variant="clean", view_vae=True)
    )
    target = tmp_path / "published"
    package_stage_a(destination=target, **kwargs)
    write_json(
        target / "COMPLETE.json",
        dict(schema="g2_spatial_profile_episode_v1", complete=True),
    )
    with pytest.raises(ContractError, match="completion"):
        validate_profile_episode(target)
    (target / "COMPLETE.json").unlink()
    source = read_json(target / "spatial_source.json")
    path = target / source["views"]["sixview/floor_top"]["owners"][0]["path"]
    path.write_bytes(b"corrupt")
    with pytest.raises(ContractError, match="damaged"):
        validate_profile_episode(target, require_complete=False)


def test_missing_complete_is_corrupt_even_when_allowing_source_readiness(tmp_path):
    kwargs, _ = stage_case(tmp_path, OutputProfile(selection_top_variant="clean"))
    target = tmp_path / "published"
    package_stage_a(destination=target, **kwargs)
    (target / "COMPLETE.json").unlink()
    with pytest.raises(ContractError, match="incomplete"):
        validate_profile_episode(target, require_complete=False)
