"""CPU-only regression for 9,126-row plan, compact Room+Island exports and safe rebinding."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from g2.offline import atomic_6views_plan as planner
from g2.offline import atomic_6views_compact as compact
from g2.offline import atomic_6views_source as source


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture_dataset(tmp_path, *, n=2):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    roots = {"raw": tmp_path / "raw", "flat": tmp_path / "flat",
             "depth": tmp_path / "depth", "plans": tmp_path / "plans",
             "published": tmp_path / "published"}
    for key in ("raw", "flat", "depth"):
        roots[key].mkdir()
    rows = []
    for i in range(n):
        task, layout = "TestTask", (i % 10) + 1
        local = i
        extra = roots["raw"] / task / "20250820" / "lerobot" / "extras" / f"episode_{local:06d}"
        extra.mkdir(parents=True)
        originals = {}
        for name, contents in {
                "model.xml.gz": b"test-original-mjcf",
                "states.npz": b"test-original-states",
                "ep_meta.json": json.dumps({"layout_id": layout, "style_id": layout}).encode(),
        }.items():
            p = extra / name
            p.write_bytes(contents)
            originals[name] = p
        length = 21 + i
        row = {"task_class": task, "local_episode_index": local,
               "global_episode_index": i, "length": length}
        rows.append(row)
        d = roots["depth"] / "tasks" / task / "episodes" / f"episode_{i:06d}"
        d.mkdir(parents=True)
        m = {"schema": "psm_wma_robocasa_rgbd_pose_v2",
             "status": "COMPLETE", "export_digest": "digest" + str(i),
             "frame_count": length,
             "identity": {"episode": row, "cameras": ["robot0_agentview_left"],
                 "source_files": [{"path": str(p), "size": p.stat().st_size,
                                   "sha256": _sha(p)} for p in originals.values()]}}
        (d / "manifest.json").write_text(json.dumps(m))
        (d / "COMPLETE.json").write_text(json.dumps({
            "schema": m["schema"], "export_digest": m["export_digest"],
            "manifest_sha256": _sha(d / "manifest.json")}))
    pq.write_table(pa.Table.from_pylist(rows), roots["flat"] / "flat_v3_mapping.parquet")
    return roots


def test_frames_and_last_state_included_exactly_once():
    assert planner.frame_ids(21) == [0, 10, 20]
    assert planner.frame_ids(22) == [0, 10, 20, 21]
    assert planner.frame_ids(2) == [0, 1]
    with pytest.raises(planner.PlanError):
        planner.frame_ids(1)


def test_planner_builds_immutable_batches_and_island_fourviews(tmp_path):
    roots = fixture_dataset(tmp_path, n=3)
    summary = planner.build(
        roots["flat"] / "flat_v3_mapping.parquet",
        roots["raw"], roots["depth"], roots["plans"], roots["published"],
        expected=3, batch_size=2)
    assert summary["episodes_total"] == 3
    assert summary["batches_total"] == 2
    assert summary["spatial_state_total"] == 3 + 4 + 4
    assert summary["renderer"] == "f27"
    assert summary["island_four_views"] is True
    a = compact.read_json(roots["plans"] / "batch_000.json")
    assert len(a["episodes"]) == 2
    assert a["island_four_views"] is True
    assert a["renderer"] == "f27"
    assert a["episodes"][0]["spatial_frames"] == [0, 10, 20]
    assert a["episodes"][1]["expected_relative_output"].startswith("tasks/TestTask/episodes")
    assert not roots["published"].exists()
    with pytest.raises(planner.PlanError, match="already exists"):
        planner.build(roots["flat"] / "flat_v3_mapping.parquet",
                      roots["raw"], roots["depth"], roots["plans"], roots["published"],
                      expected=3, batch_size=2)


def test_planner_rejects_wrong_depth_episode_mapping(tmp_path):
    roots = fixture_dataset(tmp_path)
    d = roots["depth"] / "tasks/TestTask/episodes/episode_000001"
    m = compact.read_json(d / "manifest.json")
    m["identity"]["episode"]["global_episode_index"] = 99
    (d / "manifest.json").write_text(json.dumps(m))
    c = compact.read_json(d / "COMPLETE.json")
    c["manifest_sha256"] = _sha(d / "manifest.json")
    (d / "COMPLETE.json").write_text(json.dumps(c))
    with pytest.raises(planner.PlanError, match="episode mapping"):
        planner.discover(roots["flat"] / "flat_v3_mapping.parquet",
                         roots["raw"], roots["depth"], expected=2)


def fixture_render(tmp_path, *, island=True, graph=True):
    source_root = tmp_path / "source"
    state = source_root / "state_000000_frame_000000"
    images = ["sixview/floor_top.png"]
    if island:
        images.append("islands/island_1/plus_X.png")
    for name in images:
        path = state / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"PNG-DIAGNOSTIC-SAMPLE")
    (state / "direct_color_views.json").write_text(json.dumps({
        "frame_id": 0, "view_count": len(images),
        "visual_geometry_source": "SURFACE_REGISTRY_VISUAL_GEOMETRY",
        "surface_material_identity_per_pixel": True, "training_ready": False,
        "views": [{"rgb_file": p} for p in images]}))
    if graph:
        (state / "scene_graph.json").write_text(json.dumps({
            "frame_id": 0, "scene_id": "s", "source_sha256": "frozen_source",
            "entities": [{"id": "item"}]}))
    (source_root / "episode_receipt.json").write_text(json.dumps({
        "schema": "g2_repository_native_view_episode_v1",
        "complete": True, "training_ready": False, "source_material_identity_per_pixel": True,
        "view_opaque_geometry_source": "SURFACE_REGISTRY_VISUAL_GEOMETRY",
        "spatial_state_count": 1, "source_inputs_sha256": "a"*64,
        "states": [{"state_id": 0, "frame": 0, "view_count": len(images)}]}))
    return source_root


def test_compact_preserves_room_and_independent_island_and_graph(tmp_path):
    s = fixture_render(tmp_path)
    report = compact.package(s, tmp_path / "finished", episode_id=17, task_class="TestTask")
    assert report["state_count"] == 1
    assert report["states"][0]["islands"] == ["island_1"]
    state = tmp_path / "finished/state_000000_frame_000000"
    assert (state / "sixview/floor_top.png").is_file()
    assert (state / "islands/island_1/plus_X.png").is_file()
    with gzip.open(state / "scene_graph.json.gz", "rb") as f:
        assert json.loads(f.read())["entities"][0]["id"] == "item"
    assert not (tmp_path / "finished/g2_original_gpu").exists()
    assert (tmp_path / "finished/COMPLETE.json").is_file()
    assert compact.read_json(tmp_path / "finished/COMPLETE.json")["training_ready"] is False
    assert (s / "episode_receipt.json").is_file()
    with pytest.raises(compact.PackageError, match="already exists"):
        compact.package(s, tmp_path / "finished", episode_id=17, task_class="TestTask")


def test_compact_fails_closed_if_graph_missing(tmp_path):
    s = fixture_render(tmp_path, graph=False)
    with pytest.raises(compact.PackageError, match="scene graph"):
        compact.inspect_episode(s)


def test_untrusted_island_paths_are_rejected():
    for value in ("../outside.png", "/tmp/file.png", "islands/foo.png",
                  "sixview/outside.json", "islands/../trick.png"):
        with pytest.raises(compact.PackageError):
            compact._relative(value)


def test_path_rebinding_only_changes_asset_references(tmp_path):
    asset = tmp_path / "assets"
    asset.mkdir()
    (asset / "mesh.obj").write_bytes(b"not parsed in this test")
    scene = tmp_path / "scene.xml.gz"
    with gzip.open(scene, "wb") as stream:
        stream.write(b'<mujoco><asset><mesh file="/historical/assets/mesh.obj" '
                     b' scale="1 1 1"/></asset></mujoco>')
    content, references, changes = source.rebind_xml(scene, rules=[
        ("/historical/assets", str(asset))])
    assert changes == 1
    assert str(asset / "mesh.obj").encode() in content
    assert b'scale="1 1 1"' in content
    assert references[0][0] == "/historical/assets/mesh.obj"


def test_official_metadata_uses_compiled_roles_and_true_source_categories():
    mujoco = pytest.importorskip("mujoco")
    from g2.offline import atomic_6views_metadata as metadata
    xml = """<mujoco><worldbody>
      <body name="floor_room"><geom name="floor_room_g0" type="box" size=".5 .5 .1"/>
        <geom name="floor_room_g0_vis" type="box" size=".5 .5 .1"
              group="1" contype="0" conaffinity="0"/></body>
      <body name="wall_room"><geom name="wall_room_g0" type="box" size=".1 1 1"/>
        <geom name="wall_room_g0_vis" type="box" size=".1 1 1"
              group="1" contype="0" conaffinity="0"/></body>
      <body name="window_group_room"><geom name="window_group_room_g0" type="box" size=".2 .2 .02"/>
        <geom name="window_group_room_g0_vis" type="box" size=".2 .2 .02"
              rgba=".5 .6 .9 .15" group="1" contype="0" conaffinity="0"/></body>
      <body name="robot0_base"><geom name="robot0_g0_vis" type="box" size=".1 .1 .1"
              group="1" contype="0" conaffinity="0"/></body>
    </worldbody></mujoco>"""
    model = mujoco.MjModel.from_xml_string(xml)
    ep_meta = {"fixtures": {
        "floor_room": {"cls": "Floor"}, "wall_room": {"cls": "Wall"},
        "window_group_room": {"cls": "Window"}},
        "object_cfgs": []}
    role, nav, audit = metadata.derive(
        model, ep_meta, scene_id="test_scene",
        state_sha256="b"*64, model_source_sha256="a"*64)
    assert nav["geoms"]["floor_room_g0"]["kind"] == "floor"
    assert nav["geoms"]["wall_room_g0"]["kind"] == "wall"
    assert nav["geoms"]["window_group_room_g0"]["category_id"] == "window"
    assert role["geoms"]["window_group_room_g0_vis"]["role"] == "visual"
    assert role["geoms"]["window_group_room_g0_vis"]["source_kind"] == "ep_meta"
    assert nav["geoms"]["robot0_g0_vis"]["include"] is False
    assert audit["role_counts"]["visual"] >= 3
    assert audit["not_human_semantic_approved"] is True
