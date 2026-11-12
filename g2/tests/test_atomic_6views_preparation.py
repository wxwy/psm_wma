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


def fixture_dataset(tmp_path, *, n=2, task_names=None):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    roots = {"raw": tmp_path / "raw", "flat": tmp_path / "flat",
             "depth": tmp_path / "depth", "plans": tmp_path / "plans",
             "published": tmp_path / "published"}
    for key in ("raw", "flat", "depth"):
        roots[key].mkdir()
    rows = []
    for i in range(n):
        task = task_names[i % len(task_names)] if task_names else "TestTask"
        layout = (i % 10) + 1
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
      <body name="invisible_placeholder"><geom name="invalid_outside_room"
              type="box" pos="0 0 10" size=".2 .2 .02" rgba="0 0 0 0"/></body>
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
    assert nav["geoms"]["invalid_outside_room"]["include"] is False
    assert audit["excluded_invisible_out_of_room_collision_geom_count"] == 1
    assert audit["role_counts"]["visual"] >= 3
    assert audit["not_human_semantic_approved"] is True


@pytest.mark.parametrize("layout", [11, 12, 42, 100001])
def test_dataset_planner_does_not_whitelist_layout_ids(tmp_path, layout):
    roots = fixture_dataset(tmp_path, n=1)
    extra = roots["raw"] / "TestTask/20250820/lerobot/extras/episode_000000"
    (extra / "ep_meta.json").write_text(
        json.dumps({"layout_id": layout, "style_id": 3}))
    depth = roots["depth"] / "tasks/TestTask/episodes/episode_000000"
    entry = json.loads((depth / "manifest.json").read_text())
    for file in entry["identity"]["source_files"]:
        if file["path"].endswith("ep_meta.json"):
            file["sha256"] = _sha(extra / "ep_meta.json")
            file["size"] = (extra / "ep_meta.json").stat().st_size
    (depth / "manifest.json").write_text(json.dumps(entry))
    complete = json.loads((depth / "COMPLETE.json").read_text())
    complete["manifest_sha256"] = _sha(depth / "manifest.json")
    (depth / "COMPLETE.json").write_text(json.dumps(complete))
    found, grouped = planner.discover(roots["flat"] / "flat_v3_mapping.parquet",
                                      roots["raw"], roots["depth"], expected=1)
    assert found[0]["layout_id"] == layout
    assert grouped[layout] == 1


@pytest.mark.parametrize("invalid", [0, -1, True, "10", None])
def test_dataset_planner_rejects_nonpositive_or_noninteger_layouts(tmp_path, invalid):
    roots = fixture_dataset(tmp_path, n=1)
    extra = roots["raw"] / "TestTask/20250820/lerobot/extras/episode_000000"
    (extra / "ep_meta.json").write_text(
        json.dumps({"layout_id": invalid, "style_id": 4}))
    with pytest.raises(planner.PlanError, match="layout_id"):
        planner.discover(roots["flat"] / "flat_v3_mapping.parquet",
                         roots["raw"], roots["depth"], expected=1)


def test_task_filter_and_unlimited_default_per_task(tmp_path):
    roots = fixture_dataset(tmp_path, n=7, task_names=("OpenDrawer", "CloseFridge"))
    rows, _ = planner.discover(
        roots["flat"] / "flat_v3_mapping.parquet", roots["raw"], roots["depth"], expected=7)
    default, counts = planner.select(rows)
    assert [x["episode_id"] for x in default] == list(range(7))
    assert counts == {"CloseFridge": 3, "OpenDrawer": 4}
    a, a_count = planner.select(rows, tasks=["OpenDrawer"], episodes_per_task=None)
    assert [x["episode_id"] for x in a] == [0, 2, 4, 6]
    assert a_count == {"OpenDrawer": 4}
    b, counts_b = planner.select(
        rows, tasks=["CloseFridge,OpenDrawer"], episodes_per_task=2)
    assert [x["episode_id"] for x in b] == [0, 1, 2, 3]
    assert counts_b == {"CloseFridge": 2, "OpenDrawer": 2}
    assert planner.normalize_tasks([]) is None
    assert planner.normalize_tasks(["OpenDrawer"]) == {"OpenDrawer"}
    with pytest.raises(planner.PlanError, match="unknown task"):
        planner.select(rows, tasks=["NotATask"])
    with pytest.raises(planner.PlanError, match="positive integer"):
        planner.select(rows, episodes_per_task=0)
    with pytest.raises(planner.PlanError, match="positive integer"):
        planner.select(rows, episodes_per_task=True)
    with pytest.raises(planner.PlanError, match="duplicate"):
        planner.select(rows, tasks=["OpenDrawer,OpenDrawer"])


def make_committed_receipt(target_root, selection):
    final = target_root / selection["expected_relative_output"]
    final.mkdir(parents=True)
    states = [{"frame": frame} for frame in selection["spatial_frames"]]
    manifest = {
        "schema": "g2_atomic_compact_6views_v1",
        "episode_id": selection["episode_id"],
        "task_class": selection["task_class"],
        "source_renderer": "f27",
        "source_fingerprint": selection["source_fingerprint"],
        "island_four_views_enabled": True,
        "state_count": len(states),
        "states": states,
        "complete": True,
        "training_ready": False,
    }
    (final / "episode_manifest.json").write_text(json.dumps(manifest))
    receipt = {
        "schema": manifest["schema"], "complete": True,
        "renderer": "f27", "episode_id": selection["episode_id"],
        "source_fingerprint": selection["source_fingerprint"],
        "episode_manifest_sha256": _sha(final / "episode_manifest.json"),
        "state_count": len(states), "training_ready": False,
    }
    (final / "COMPLETE.json").write_text(json.dumps(receipt))
    return final


def test_fixed_selection_resume_skips_only_matching_completed_source(tmp_path):
    roots = fixture_dataset(tmp_path, n=6, task_names=("OpenDrawer", "CloseFridge"))
    rows, _ = planner.discover(
        roots["flat"] / "flat_v3_mapping.parquet", roots["raw"], roots["depth"], expected=6)
    chosen, _ = planner.select(rows, episodes_per_task=2)
    assert [row["episode_id"] for row in chosen] == [0, 1, 2, 3]
    complete = make_committed_receipt(roots["published"], chosen[1])
    assert planner.completed_output(chosen[1], roots["published"]) is True
    assert planner.completed_output(chosen[0], roots["published"]) is False
    with pytest.raises(planner.PlanError, match="explicit --resume"):
        planner.build(roots["flat"] / "flat_v3_mapping.parquet", roots["raw"],
                      roots["depth"], roots["plans"], roots["published"],
                      expected=6, episodes_per_task=2)
    assert not roots["plans"].exists()
    summary = planner.build(roots["flat"] / "flat_v3_mapping.parquet", roots["raw"],
                            roots["depth"], roots["plans"], roots["published"],
                            expected=6, episodes_per_task=2, resume=True)
    assert summary["episodes_total"] == 4
    assert summary["dataset_episodes_total"] == 6
    assert summary["episodes_skipped_completed"] == 1
    assert summary["episodes_pending"] == 3
    assert summary["skipped_completed_ids"] == [1]
    assert summary["task_episode_counts"] == {"CloseFridge": 2, "OpenDrawer": 2}
    actual = json.loads((roots["plans"] / "batch_000.json").read_text())
    assert [row["episode_id"] for row in actual["episodes"]] == [0, 2, 3]
    # Repeating --resume with the same plan_root reuses immutable source bytes.
    previous_hash = _sha(roots["plans"] / "batch_000.json")
    reused = planner.build(
        roots["flat"] / "flat_v3_mapping.parquet", roots["raw"],
        roots["depth"], roots["plans"], roots["published"],
        expected=6, episodes_per_task=2, resume=True)
    assert reused["plan_reused"] is True
    assert reused["episodes_pending_now"] == 3
    assert _sha(roots["plans"] / "batch_000.json") == previous_hash
    # Newly completed episodes are skipped, not replaced by later candidates.
    make_committed_receipt(roots["published"], chosen[2])
    reused_again = planner.build(
        roots["flat"] / "flat_v3_mapping.parquet", roots["raw"],
        roots["depth"], roots["plans"], roots["published"],
        expected=6, episodes_per_task=2, resume=True)
    assert reused_again["episodes_pending_now"] == 2
    assert reused_again["episodes_skipped_completed_now"] == 2
    with pytest.raises(planner.PlanError, match="selection or source recipe changed"):
        planner.build(
            roots["flat"] / "flat_v3_mapping.parquet", roots["raw"],
            roots["depth"], roots["plans"], roots["published"],
            expected=6, episodes_per_task=1, resume=True)
    # A different selected episode's marker may never satisfy the frozen source.
    marker = json.loads((complete / "COMPLETE.json").read_text())
    marker["source_fingerprint"] = "0" * 64
    (complete / "COMPLETE.json").write_text(json.dumps(marker))
    with pytest.raises(planner.PlanError, match="identity/recipe differs"):
        planner.completed_output(chosen[1], roots["published"])


def test_resume_rejects_incomplete_output_and_stale_recipe(tmp_path):
    roots = fixture_dataset(tmp_path, n=2)
    rows, _ = planner.discover(roots["flat"] / "flat_v3_mapping.parquet",
                                roots["raw"], roots["depth"], expected=2)
    target = roots["published"] / rows[0]["expected_relative_output"]
    target.mkdir(parents=True)
    with pytest.raises(planner.PlanError, match="incomplete output"):
        planner.completed_output(rows[0], roots["published"])


def test_publisher_fingerprint_binds_output_to_selection(tmp_path):
    selection = {
        "episode_id": 17, "task_class": "TestTask",
        "spatial_frames": [0], "spatial_state_count": 1,
        "source_fingerprint": "c"*64, "expected_relative_output": "published",
    }
    original = fixture_render(tmp_path)
    output = tmp_path / "published"
    compact.package(original, output, episode_id=17, task_class="TestTask",
                    selection=selection)
    assert planner.completed_output(selection, tmp_path)
    manifest = compact.read_json(output / "episode_manifest.json")
    assert manifest["source_fingerprint"] == selection["source_fingerprint"]
    assert compact.read_json(output / "COMPLETE.json")[
        "episode_manifest_sha256"] == _sha(output / "episode_manifest.json")
    with pytest.raises(compact.PackageError, match="pinned selection"):
        compact.package(original, tmp_path / "other", episode_id=17,
                        task_class="TestTask",
                        selection={**selection, "spatial_frames": [10]})


def test_resume_rejects_legacy_upper_view_without_actual_upper_level_sg(tmp_path):
    """A signed COMPLETE marker cannot launder an empty white upper view.

    The existing artifact remains untouched: only explicit, versioned
    regeneration should replace an obsolete content recipe.
    """
    selection = {
        "episode_id": 17, "task_class": "TestTask",
        "spatial_frames": [0], "spatial_state_count": 1,
        "source_fingerprint": "c" * 64, "expected_relative_output": "finished",
    }
    source_root = fixture_render(tmp_path)
    finished = tmp_path / "finished"
    compact.package(source_root, finished, episode_id=17,
                    task_class="TestTask", selection=selection)
    assert planner.completed_output(selection, tmp_path)
    manifest_file = finished / "episode_manifest.json"
    manifest = compact.read_json(manifest_file)
    manifest["states"][0]["view_pngs"].append("sixview/upper_up.png")
    manifest_file.write_text(json.dumps(manifest))
    marker_file = finished / "COMPLETE.json"
    marker = compact.read_json(marker_file)
    marker["episode_manifest_sha256"] = _sha(manifest_file)
    marker_file.write_text(json.dumps(marker))
    with pytest.raises(planner.PlanError, match="upper_up without an SG-certified upper object"):
        planner.completed_output(selection, tmp_path)
    # A real SG-approved upper object suffices for the source-bound gate.
    folder = finished / "state_000000_frame_000000"
    sg_file = folder / "scene_graph.json.gz"
    with gzip.open(sg_file, "rt") as stream:
        graph = json.load(stream)
    graph["entities"] = [{"id": "entity_0", "kind": "object", "upper_member": True}]
    with gzip.open(sg_file, "wt") as stream:
        json.dump(graph, stream)
    assert planner.completed_output(selection, tmp_path)
