"""Immutable final pixels and clean/marker variants; no VAE or renderer load."""

from dataclasses import FrozenInstanceError

import pytest
from PIL import Image

from g2.io import ContractError, digest, read_json, write_json
from g2.latent_cache.streaming import ConsumerLimits, final_pixel_event
from g2.offline.output_profile import OutputProfile
from g2.offline.spatial_metadata import canonical_direction_count
from g2.offline.stage_a import package_stage_a
from g2.tests.test_stage_a_package import stage_case
from g2.views.robot_pose_marker import overlay_final_top_views


def test_two_rooms_clean_base_preserved_and_outside_marker_not_absence(tmp_path):
    views = []
    for uid, origin in ((0, [0, 0, 0]), (1, [10, 0, 0])):
        native = f"rooms/{uid}/floor_top"
        rel = f"sixview/rooms/{uid}/floor_top.png"
        path = tmp_path / rel
        path.parent.mkdir(parents=True)
        Image.new("RGB", (64, 64), (250, 230, 210)).save(path)
        (tmp_path / "g2_original_gpu" / native).mkdir(parents=True)
        write_json(
            tmp_path / "g2_original_gpu" / native / "view.json",
            dict(
                axis="floor_top",
                coordinate_frame="NATIVE_ROOM_REFERENCE",
                reference_frame={"origin_world": origin},
                right_world=[1, 0, 0],
                up_world=[0, 1, 0],
                uv_min_room=[-2, -2],
                meters_per_pixel=0.0625,
                width=64,
                height=64,
            ),
        )
        views.append(dict(native_view=native, rgb_file=rel, sha256=digest(path)))
    write_json(tmp_path / "direct_color_views.json", dict(views=views, view_count=2))
    before = {v["rgb_file"]: digest(tmp_path / v["rgb_file"]) for v in views}
    pose = dict(position_world=[0, 0, 0], forward_world=[1, 0, 0])
    overlay_final_top_views(tmp_path, pose, preserve_clean=True)
    result = read_json(tmp_path / "direct_color_views.json")
    assert before == {p: digest(tmp_path / p) for p in before}
    assert result["view_count"] == 4 and result["canonical_view_count"] == 2
    marked = {v["native_view"]: v for v in result["views"] if v["variant"] == "w_rbs"}
    assert marked["rooms/0/floor_top"]["marker_drawn"] is True
    assert marked["rooms/1/floor_top"]["marker_drawn"] is False
    assert (
        marked["rooms/1/floor_top"]["sha256"] == before["sixview/rooms/1/floor_top.png"]
    )
    hashes = {v["rgb_file"]: v["sha256"] for v in result["views"]}
    overlay_final_top_views(tmp_path, pose, preserve_clean=True)
    repeated = read_json(tmp_path / "direct_color_views.json")
    assert hashes == {v["rgb_file"]: v["sha256"] for v in repeated["views"]}
    assert canonical_direction_count(hashes) == 2
    with pytest.raises(ContractError, match="outside every"):
        overlay_final_top_views(
            tmp_path,
            dict(position_world=[100, 100, 0], forward_world=[1, 0, 0]),
            preserve_clean=True,
        )


def test_immutable_events_use_exact_final_png_and_bounded_contract(tmp_path):
    path = tmp_path / "floor_top.png"
    Image.new("RGB", (32, 32), (10, 20, 30)).save(path)
    before = path.read_bytes()
    common = dict(
        episode_key="NavigateKitchen/episode_000000",
        view_id="sixview/floor_top",
        canonical_view_id="sixview/floor_top",
        variant="clean",
        source_fingerprint="a" * 64,
        profile_id="b" * 64,
    )
    event = final_pixel_event(path, **common)
    other = final_pixel_event(path, **dict(common, profile_id="c" * 64))
    assert event.event_id != other.event_id  # publication scope
    assert event.pixel_record_key == other.pixel_record_key  # same numeric work
    path.write_bytes(b"changed after handoff")
    assert event.png_bytes == before and event.rgb_sha256 != digest(path)
    assert event.final_pixel_phase == "FINAL_CLEAN_PIXELS"
    with pytest.raises(FrozenInstanceError):
        event.png_bytes = b"replace"
    with pytest.raises(ValueError):
        ConsumerLimits(max_events=0)
    with pytest.raises(ValueError):
        ConsumerLimits(max_spool_bytes=-1)
    assert "png_bytes" not in event.descriptor()


def test_marker_disabled_is_explicit_and_selection_variant_is_not_a_training_default(
    tmp_path,
):
    profile = OutputProfile(selection_top_variant="clean", marker_variants=False)
    kwargs, _ = stage_case(tmp_path, profile)
    target = tmp_path / "published"
    result = package_stage_a(destination=target, **kwargs)
    for state in result["states"]:
        metadata = read_json(target / state["spatial_metadata"])
        assert (
            metadata["view_catalog"]["sixview/floor_top_w_rbs"]["availability"]
            == "disabled"
        )
        assert (
            metadata["view_catalog"]["sixview/floor_top_w_rbs"]["reason"]
            == "MARKER_VARIANT_DISABLED"
        )
        assert not state["selection"]["selection_is_training_default"]
        assert "sixview/floor_top_w_rbs" not in state["selection"]["selected_view_ids"]
