"""CPU fixtures for the existing image/reference index, not scene acceptance."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from g2.latent_cache.source import scan_episode, verify_source

FLOOR = "sixview/floor_top.png"
SIDE = "sixview/plus_X.png"
ISLAND0 = "islands/island_0_entity_18/plus_Y.png"
ISLAND1 = "islands/island_1_entity_27/minus_Y.png"


def _seal(root, doc):
    raw = (json.dumps(doc, sort_keys=True) + "\n").encode()
    (root / "episode_manifest.json").write_bytes(raw)
    marker = {
        "schema": doc["schema"],
        "complete": True,
        "episode_id": doc["episode_id"],
        "state_count": len(doc["states"]),
        "renderer": "f27",
        "training_ready": False,
        "source_fingerprint": doc["source_fingerprint"],
        "episode_manifest_sha256": hashlib.sha256(raw).hexdigest(),
    }
    (root / "COMPLETE.json").write_text(json.dumps(marker) + "\n")


def _fixture(root, *, version=3):
    root.mkdir()
    rows = [
        {"state_id": 10, "frame": 5, "view_pngs": [FLOOR, ISLAND0], "view_refs": {}},
        {
            "state_id": 30,
            "frame": 17,
            "view_pngs": [SIDE],
            "view_refs": {
                FLOOR: {"ref_state": 0, "path": FLOOR},
                ISLAND0: {"ref_state": 0, "path": ISLAND0},
            },
        },
        {
            "state_id": 80,
            "frame": 29,
            "view_pngs": [FLOOR, ISLAND1],
            "view_refs": {ISLAND0: {"ref_state": 0, "path": ISLAND0}},
        },
        {
            "state_id": 110,
            "frame": 90,
            "view_pngs": [],
            "view_refs": {
                FLOOR: {"ref_state": 2, "path": FLOOR},
                SIDE: {"ref_state": 1, "path": SIDE},
                ISLAND1: {"ref_state": 2, "path": ISLAND1},
            },
        },
    ]
    if version == 1:
        for row in rows:
            row["view_refs"] = {}
    for ordinal, row in enumerate(rows):
        for path in row["view_pngs"]:
            p = root / f"state_{ordinal:06d}_frame_{row['frame']:06d}" / path
            p.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (13 + ordinal, 7), (ordinal * 20, 80, 180)).save(p)
    doc = {
        "schema": f"g2_atomic_compact_6views_v{version}",
        "complete": True,
        "episode_id": 42,
        "task_class": "NavigateKitchen",
        "source_renderer": "f27",
        "training_ready": False,
        "source_fingerprint": "a" * 64,
        "state_count": len(rows),
        "states": rows,
    }
    _seal(root, doc)
    return doc


def test_union_all_states_sparse_logical_ids_and_multiple_islands(
    tmp_path, monkeypatch
):
    from g2.latent_cache import source

    root = tmp_path / "episode"
    _fixture(root)
    calls = []
    original = source._png

    def count(root, path):
        calls.append(path)
        return original(root, path)

    monkeypatch.setattr(source, "_png", count)
    plan = scan_episode(root)
    assert plan["episode_key"] == "NavigateKitchen/episode_000042"
    assert [s["logical_state_id"] for s in plan["states"]] == [10, 30, 80, 110]
    assert [s["frame"] for s in plan["states"]] == [5, 17, 29, 90]
    assert set(plan["views"]) == {FLOOR[:-4], SIDE[:-4], ISLAND0[:-4], ISLAND1[:-4]}
    assert len(calls) == len(set(calls)) == 5
    floor, side = plan["views"][FLOOR[:-4]], plan["views"][SIDE[:-4]]
    assert floor["state_records"] == [0, 0, 1, 1]
    assert side["state_records"] == [None, 0, None, 0]
    assert plan["views"][ISLAND0[:-4]]["state_records"] == [0, 0, 0, None]
    assert plan["views"][ISLAND1[:-4]]["state_records"] == [None, None, 0, 0]
    record = floor["records"][1]
    assert (
        record["owner_state_ordinal"],
        record["owner_state_id"],
        record["owner_frame"],
    ) == (2, 80, 29)
    assert record["png_path"] == "state_000002_frame_000029/" + FLOOR
    assert record["original_hw"] == [7, 15]
    assert floor["path"] == "sixview/floor_top.pt"
    assert plan["views"][ISLAND1[:-4]]["path"] == ISLAND1[:-4] + ".pt"
    assert not (root / "state_000003_frame_000090").exists()
    assert verify_source(plan)


@pytest.mark.parametrize("version", [1, 2, 3])
def test_all_source_schemas_and_no_source_writes(tmp_path, version):
    root = tmp_path / "episode"
    _fixture(root, version=version)
    before = {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }
    plan = scan_episode(root)
    assert plan["source"]["schema"].endswith(str(version))
    assert verify_source(plan)
    assert {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    } == before


def test_zero_islands_and_multiple_room_path_identity(tmp_path):
    root = tmp_path / "episode"
    doc = _fixture(root, version=1)
    for i, row in enumerate(doc["states"]):
        row["view_pngs"] = [p for p in row["view_pngs"] if p.startswith("sixview/")]
        row.pop("state_id")
        if i == 0:
            for room in (0, 1):
                path = f"sixview/room_{room}/floor_top.png"
                p = root / "state_000000_frame_000005" / path
                p.parent.mkdir(parents=True)
                Image.new("RGB", (4, 6), (250, 250, 250)).save(p)
                row["view_pngs"].append(path)
    _seal(root, doc)
    plan = scan_episode(root)
    assert not any(k.startswith("islands/") for k in plan["views"])
    assert "sixview/room_0/floor_top" in plan["views"]
    assert "sixview/room_1/floor_top" in plan["views"]
    assert [r["logical_state_id"] for r in plan["states"]] == [0, 1, 2, 3]


@pytest.mark.parametrize(
    "change",
    [
        "future",
        "self",
        "chain",
        "different_path",
        "traversal",
        "control",
        "duplicate",
        "overlap",
    ],
)
def test_bad_refs_and_inventory_fail_closed(tmp_path, change):
    root = tmp_path / "episode"
    doc = _fixture(root)
    if change == "future":
        doc["states"][1]["view_refs"][FLOOR]["ref_state"] = 2
    elif change == "self":
        doc["states"][1]["view_refs"][FLOOR]["ref_state"] = 1
    elif change == "chain":
        doc["states"][3]["view_refs"][FLOOR]["ref_state"] = 1
    elif change == "different_path":
        doc["states"][1]["view_refs"][FLOOR]["path"] = SIDE
    elif change == "traversal":
        doc["states"][0]["view_pngs"].append("sixview/../outside.png")
    elif change == "control":
        doc["states"][0]["view_pngs"].append("sixview/new\nline.png")
    elif change == "duplicate":
        doc["states"][0]["view_pngs"].append(FLOOR)
    else:
        doc["states"][0]["view_refs"][FLOOR] = {"path": FLOOR, "ref_state": 0}
    _seal(root, doc)
    with pytest.raises(ValueError):
        scan_episode(root)


@pytest.mark.parametrize(
    "change", ["duplicate_logical", "bool_logical", "nonmonotonic_frame", "bool_frame"]
)
def test_bad_state_identity(tmp_path, change):
    root = tmp_path / "episode"
    doc = _fixture(root)
    row = doc["states"][1]
    if change == "duplicate_logical":
        row["state_id"] = 10
    elif change == "bool_logical":
        row["state_id"] = True
    elif change == "nonmonotonic_frame":
        row["frame"] = 5
    else:
        row["frame"] = True
    _seal(root, doc)
    with pytest.raises(ValueError):
        scan_episode(root)


@pytest.mark.parametrize("change", ["missing", "corrupt", "not_png", "not_rgb"])
def test_declared_images_must_exist_and_decode(tmp_path, change):
    root = tmp_path / "episode"
    _fixture(root)
    p = root / "state_000000_frame_000005" / FLOOR
    if change == "missing":
        p.unlink()
    elif change == "corrupt":
        p.write_bytes(b"not-an-image")
    elif change == "not_png":
        Image.new("RGB", (4, 4)).save(p, format="JPEG")
    else:
        Image.new("L", (4, 4)).save(p)
    with pytest.raises(ValueError):
        scan_episode(root)


@pytest.mark.parametrize(
    "change", ["root", "physical_file", "physical_parent", "reference_only_state"]
)
def test_symlinks_including_unmaterialized_state_are_rejected(tmp_path, change):
    root = tmp_path / "episode"
    _fixture(root)
    if change == "root":
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        root = alias
    elif change == "physical_file":
        path = root / "state_000000_frame_000005" / FLOOR
        old = root / "saved.png"
        path.rename(old)
        path.symlink_to(old)
    elif change == "physical_parent":
        path = root / "state_000000_frame_000005/sixview"
        old = root / "saved_images"
        path.rename(old)
        path.symlink_to(old, target_is_directory=True)
    else:
        (root / "state_000003_frame_000090").symlink_to(
            root / "state_000000_frame_000005", target_is_directory=True
        )
    with pytest.raises(ValueError):
        scan_episode(root)


@pytest.mark.parametrize("change", ["png", "manifest", "complete", "missing"])
def test_source_verification_catches_build_time_changes(tmp_path, change):
    root = tmp_path / "episode"
    doc = _fixture(root)
    plan = scan_episode(root)
    if change == "png":
        Image.new("RGB", (13, 7), (1, 2, 3)).save(
            root / "state_000000_frame_000005" / FLOOR
        )
    elif change == "manifest":
        doc["instruction"] = (
            "different task text cannot silently reuse an old source identity"
        )
        _seal(root, doc)
    elif change == "complete":
        p = root / "COMPLETE.json"
        p.write_text(p.read_text() + "\n")
    else:
        (root / "state_000000_frame_000005" / FLOOR).unlink()
    with pytest.raises(ValueError):
        verify_source(plan)


def test_original_v2_and_v3_validators_accept_cache_namespace(tmp_path):
    from g2.offline.scene_graph_compact_v3 import (
        convert_v2_to_v3,
        validate_sg_indexed_episode,
    )
    from g2.offline.scene_view_index_package import (
        repackage_indexed,
        validate_indexed_episode,
    )
    from g2.tests.test_scene_graph_compact_v3 import mock_v2
    from g2.tests.test_scene_view_index_package import create_legacy, events

    legacy = tmp_path / "legacy"
    legacy.mkdir()
    create_legacy(legacy)
    v2 = tmp_path / "v2"
    repackage_indexed(legacy, v2, events())
    original = tmp_path / "v3_source"
    mock_v2(original)
    v3 = tmp_path / "v3"
    convert_v2_to_v3(original, v3)
    for root, validator, count in [
        (v2, validate_indexed_episode, 3),
        (v3, validate_sg_indexed_episode, 5),
    ]:
        before = {
            p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*")
            if p.is_file()
        }
        cache = root / "vae_cache/sixview"
        cache.mkdir(parents=True)
        (cache / "floor_top.pt").write_bytes(
            b"cache-namespace-fixture-not-a-numerical-payload"
        )
        (root / "vae_cache/manifest.json").write_text("{}\n")
        (root / "vae_cache/COMPLETE.json").write_text("{}\n")
        assert validator(root) == count
        assert verify_source(scan_episode(root))
        assert all((root / rel).read_bytes() == raw for rel, raw in before.items())


def test_source_scan_does_not_import_model_or_simulator(tmp_path):
    root = tmp_path / "episode"
    _fixture(root)
    code = """import sys
from g2.latent_cache.source import scan_episode
scan_episode(sys.argv[1])
assert not any(k in sys.modules for k in ('torch', 'mujoco', 'rospy', 'OpenGL', 'cosmos_framework'))
"""
    subprocess.run(
        [sys.executable, "-c", code, str(root)],
        check=True,
        cwd=Path(__file__).resolve().parents[2],
    )
