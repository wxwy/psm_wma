"""CPU storage/reader fixtures; these never load or validate a real VAE."""

import json
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import torch

from g2.io import digest
from g2.latent_cache.contract import (
    COMPLETE_SCHEMA,
    INDEX_SCHEMA,
    PAYLOAD_SCHEMA,
    CacheError,
    fingerprint,
    make_recipe,
    preprocessing_recipe,
)
from g2.latent_cache.storage import (
    ViewReader,
    atomic_json,
    build_lock,
    inspect_view_payload,
    open_episode_index,
    validate_payload_binding,
    write_view_payload,
)


def _metadata(view, source, recipe, *, mapping=None):
    records = [
        {
            "record_index": 0,
            "owner_state_ordinal": 0,
            "owner_state_id": 2,
            "owner_frame": 0,
            "png_path": "state_000000_frame_000000/" + view + ".png",
            "png_sha256": "a" * 64,
            "original_hw": [16, 24],
        },
        {
            "record_index": 1,
            "owner_state_ordinal": 2,
            "owner_state_id": 29,
            "owner_frame": 48,
            "png_path": "state_000002_frame_000048/" + view + ".png",
            "png_sha256": "b" * 64,
            "original_hw": [16, 24],
        },
    ]
    return {
        "schema": PAYLOAD_SCHEMA,
        "episode_key": "Fixture/episode_000005",
        "source": source,
        "recipe_id": recipe["recipe_id"],
        "view_id": view,
        "view_plan": {
            "path": view + ".pt",
            "records": records,
            "state_records": mapping or [0, 0, 1],
        },
        "preprocessing": [
            {
                "content_box": [0, 0, 16, 16],
                "original_hw": [16, 24],
                "canvas_hw": [
                    recipe["preprocessing"]["height"],
                    recipe["preprocessing"]["width"],
                ],
            }
        ]
        * 2,
    }


def _completion(root, index):
    cache = root / "vae_cache"
    atomic_json(cache / "manifest.json", index, replace=True)
    atomic_json(
        cache / "COMPLETE.json",
        {
            "schema": COMPLETE_SCHEMA,
            "complete": True,
            "episode_key": index["episode_key"],
            "recipe_id": index["recipe"]["recipe_id"],
            "manifest_sha256": digest(cache / "manifest.json"),
        },
        replace=True,
    )


def _episode(tmp_path, views=None, *, dtype="float32", preprocessing=None):
    root = tmp_path / "episode"
    root.mkdir()
    (root / "episode_manifest.json").write_text('{"fixture":1}\n')
    (root / "COMPLETE.json").write_text('{"complete":true}\n')
    source = {
        "manifest_sha256": digest(root / "episode_manifest.json"),
        "complete_sha256": digest(root / "COMPLETE.json"),
        "schema": "fixture",
    }
    recipe = make_recipe(
        {"fake_encoder": "storage-fixture-only"}, preprocessing, storage_dtype=dtype
    )
    states = [
        {"state_ordinal": i, "logical_state_id": x, "frame": f}
        for i, (x, f) in enumerate([(2, 0), (7, 11), (29, 48)])
    ]
    if views is None:
        views = [
            "sixview/floor_top",
            "sixview/plus_X",
            "sixview/plus_Y",
            "islands/island_0_entity_18/plus_X",
            "islands/island_2_entity_42/minus_Y",
        ]
    index = {
        "schema": INDEX_SCHEMA,
        "episode_key": "Fixture/episode_000005",
        "source": source,
        "recipe": recipe,
        "states": states,
        "views": {},
    }
    for number, view in enumerate(views):
        metadata = _metadata(view, source, recipe)
        latent = (torch.arange(48).reshape(2, 2, 3, 4) + number * 100).to(
            getattr(torch, dtype)
        )
        record = write_view_payload(
            root / "vae_cache" / (view + ".pt"), metadata, latent
        )
        record.pop("metadata")
        record.update(
            path=view + ".pt", state_records=metadata["view_plan"]["state_records"]
        )
        index["views"][view] = record
    _completion(root, index)
    return root, index


@pytest.mark.parametrize("dtype", ["float32", "float16", "bfloat16"])
def test_complete_history_roundtrip_and_current_owner_are_separate(tmp_path, dtype):
    root, manifest = _episode(tmp_path, dtype=dtype)
    reader = ViewReader(open_episode_index(root))
    sample = reader.read_view("sixview/floor_top", 7)
    assert sample["logical_state_id"] == 7 and sample["logical_frame"] == 11
    assert sample["owner"]["owner_state_id"] == 2
    assert sample["owner"]["owner_frame"] == 0
    assert sample["record_index"] == 0
    assert sample["latent"].shape == (2, 3, 4)
    assert sample["latent"].dtype == getattr(torch, dtype)
    assert torch.equal(
        sample["latent"], torch.arange(24).reshape(2, 3, 4).to(getattr(torch, dtype))
    )
    assert torch.equal(
        reader.read_view("sixview/floor_top", 29)["latent"],
        torch.arange(24, 48).reshape(2, 3, 4).to(getattr(torch, dtype)),
    )
    file = root / "vae_cache/sixview/floor_top.pt"
    audited = inspect_view_payload(file)
    assert audited["sha256"] == manifest["views"]["sixview/floor_top"]["sha256"]
    assert len(audited["record_sha256"]) == 2


def test_request_three_views_opens_exactly_three_payloads_and_keeps_order(
    tmp_path, monkeypatch
):
    root, _ = _episode(tmp_path)
    opened = []
    real = torch.load

    def spy(path, **kwargs):
        opened.append(Path(path).relative_to(root / "vae_cache").as_posix())
        assert kwargs == {"map_location": "cpu", "weights_only": True, "mmap": True}
        return real(path, **kwargs)

    monkeypatch.setattr(torch, "load", spy)
    reader = ViewReader(open_episode_index(root))
    assert opened == []
    selected = [
        "sixview/plus_X",
        "islands/island_0_entity_18/plus_X",
        "sixview/floor_top",
    ]
    values = reader.read_many(7, selected)
    assert [x["view_id"] for x in values] == selected
    assert opened == [x + ".pt" for x in selected]
    reader.read_many(29, selected)
    assert len(opened) == 3


def test_duplicate_selected_view_reuses_one_read_and_one_row_copy(
    tmp_path, monkeypatch
):
    root, _ = _episode(tmp_path)
    real = torch.Tensor.clone
    copied = []

    def clone(tensor, *args, **kwargs):
        copied.append(tuple(tensor.shape))
        return real(tensor, *args, **kwargs)

    monkeypatch.setattr(torch.Tensor, "clone", clone)
    reader = ViewReader(open_episode_index(root))
    rows = reader.read_many(7, ["sixview/floor_top", "sixview/floor_top"])
    assert rows[0] is rows[1]
    assert copied == [(2, 3, 4)]  # No UCHW history is cloned.
    rows[0]["latent"].zero_()
    assert reader.read_view("sixview/floor_top", 7)["latent"].sum() > 0


def test_returned_nested_metadata_cannot_mutate_cached_provenance(tmp_path):
    root, manifest = _episode(tmp_path)
    view = "sixview/floor_top"
    path = root / "vae_cache" / (view + ".pt")
    value = torch.load(path, weights_only=True)
    value["metadata"]["view_plan"]["records"][0]["original_hw"] = [16, 24]
    path.unlink()
    record = write_view_payload(path, value["metadata"], value["latents"])
    record.pop("metadata")
    record.update(path=view + ".pt", state_records=[0, 0, 1])
    manifest["views"][view] = record
    _completion(root, manifest)
    original_bytes = path.read_bytes()
    reader = ViewReader(open_episode_index(root))
    sample = reader.read_view(view, 2)
    sample["owner"]["original_hw"][0] = 999
    sample["preprocessing"]["content_box"][0] = 999
    again = reader.read_view(view, 2)
    assert again["owner"]["original_hw"] == [16, 24]
    assert again["preprocessing"]["content_box"] == [0, 0, 16, 16]
    # The fixture's two preprocessing entries alias before serialization. Even
    # a different physical owner must not inherit caller changes to its sibling.
    assert reader.read_view(view, 29)["preprocessing"]["content_box"] == [0, 0, 16, 16]
    assert path.read_bytes() == original_bytes


def test_payload_header_binding_is_pure_and_does_not_reopen_files(
    tmp_path, monkeypatch
):
    root, _ = _episode(tmp_path)
    view = "sixview/floor_top"
    index = open_episode_index(root)
    entry = index.manifest["views"][view]
    info = inspect_view_payload(root / "vae_cache" / entry["path"])
    monkeypatch.setattr(
        Path, "open", lambda *a, **k: pytest.fail("header check opened a file")
    )
    assert validate_payload_binding(index, view, entry, info)
    # Same header, without whole-file facts, is the selected-only reader ABI.
    lazy = {k: info[k] for k in ("metadata", "shape", "dtype", "record_sha256")}
    assert validate_payload_binding(index, view, entry, lazy)


def test_preprocessing_header_binding_accepts_nondefault_canvas_without_io(
    tmp_path, monkeypatch
):
    view = "sixview/floor_top"
    root, _ = _episode(
        tmp_path, views=[view], preprocessing=preprocessing_recipe(32, 48)
    )
    index = open_episode_index(root)
    entry = index.manifest["views"][view]
    info = inspect_view_payload(root / "vae_cache" / entry["path"])
    prep = info["metadata"]["preprocessing"][0]
    assert prep["canvas_hw"] == [32, 48]
    assert prep["original_hw"] == [16, 24]
    monkeypatch.setattr(
        Path, "open", lambda *a, **k: pytest.fail("header check opened a file")
    )
    assert validate_payload_binding(index, view, entry, info)


@pytest.mark.parametrize(
    "field",
    [
        "recipe",
        "source",
        "episode_key",
        "states",
        "owner_frame",
        "owner_id",
        "png_path",
        "episode",
        "canvas_hw",
        "original_hw",
    ],
)
def test_header_binding_rejects_internal_identity_without_source_audit(tmp_path, field):
    root, manifest = _episode(tmp_path)
    view = "sixview/floor_top"
    path = root / "vae_cache" / (view + ".pt")
    value = torch.load(path, weights_only=True)
    meta = value["metadata"]
    if field == "recipe":
        meta["recipe_id"] = "f" * 64
    elif field == "source":
        meta["source"] = {**meta["source"], "manifest_sha256": "f" * 64}
    elif field == "episode_key":
        meta["episode_key"] = "DifferentTask/episode_000005"
    elif field == "states":
        meta["states"] = json.loads(json.dumps(manifest["states"]))
        meta["states"][0]["frame"] = 99
    elif field == "owner_frame":
        meta["view_plan"]["records"][0]["owner_frame"] = 99
    elif field == "owner_id":
        meta["view_plan"]["records"][0]["owner_state_id"] = 99
    elif field == "png_path":
        meta["view_plan"]["records"][0]["png_path"] = (
            "state_000000_frame_000000/sixview/plus_Y.png"
        )
    elif field == "canvas_hw":
        meta["preprocessing"][0]["canvas_hw"] = [999, 999]
    elif field == "original_hw":
        meta["preprocessing"][0]["original_hw"] = [999, 999]
    else:
        meta["episode"] = {"task_class": "DifferentTask", "episode_id": 5}
    path.unlink()
    record = write_view_payload(path, meta, value["latents"])
    record.pop("metadata")
    record.update(path=view + ".pt", state_records=[0, 0, 1])
    manifest["views"][view] = record
    _completion(root, manifest)
    index = open_episode_index(root)
    info = inspect_view_payload(path)
    # Shape/checksums and COMPLETE are internally sealed; the independent
    # cross-header relation still has to reject the wrong owner/source/recipe.
    with pytest.raises(CacheError):
        validate_payload_binding(index, view, index.manifest["views"][view], info)
    with pytest.raises(CacheError):
        ViewReader(index).read_view(view, 2)


def test_explicit_absence_does_not_open_payload_or_use_previous_owner(
    tmp_path, monkeypatch
):
    root, manifest = _episode(tmp_path)
    view = "sixview/floor_top"
    path = root / "vae_cache" / manifest["views"][view]["path"]
    value = torch.load(path, weights_only=True)
    path.unlink()
    value["metadata"]["view_plan"]["state_records"] = [0, None, 1]
    record = write_view_payload(path, value["metadata"], value["latents"])
    record.pop("metadata")
    record.update(path=view + ".pt", state_records=[0, None, 1])
    manifest["views"][view] = record
    _completion(root, manifest)
    reader = ViewReader(open_episode_index(root))
    monkeypatch.setattr(
        torch, "load", lambda *a, **k: pytest.fail("absent payload opened")
    )
    absent = reader.read_view(view, 7)
    assert absent["present"] is False and absent["latent"] is None
    assert absent["logical_frame"] == 11 and absent["owner"] is None
    assert reader.read_view("sixview/minus_X", 2)["present"] is False
    assert reader.cached_views == ()


def test_reader_lru_releases_its_mappings_and_enforces_bytes(tmp_path, monkeypatch):
    root, manifest = _episode(tmp_path)
    opened = []
    real = torch.load

    def spy(path, **kwargs):
        opened.append(Path(path).name)
        return real(path, **kwargs)

    monkeypatch.setattr(torch, "load", spy)
    reader = ViewReader(open_episode_index(root), max_views=1)
    retained = reader.read_view("sixview/floor_top", 2)["latent"]
    reader.read_view("sixview/plus_X", 2)
    assert reader.cached_views == ("sixview/plus_X",)
    assert retained.sum() > 0
    reader.read_view("sixview/floor_top", 2)
    assert len(opened) == 3
    assert len(reader.cached_views) == 1
    reader.close()
    assert reader.cached_bytes == 0 and not reader.cached_views
    small = ViewReader(open_episode_index(root), max_bytes=1)
    with pytest.raises(CacheError, match="budget"):
        small.read_view("sixview/floor_top", 2)
    assert len(opened) == 3  # Budget refusal precedes the torch payload open.
    capacity = (
        sum(
            manifest["views"][v]["bytes"]
            for v in ["sixview/floor_top", "sixview/plus_X"]
        )
        - 1
    )
    by_bytes = ViewReader(open_episode_index(root), max_bytes=capacity)
    by_bytes.read_view("sixview/floor_top", 2)
    by_bytes.read_view("sixview/plus_X", 2)
    assert len(by_bytes.cached_views) == 1 and by_bytes.cached_bytes <= capacity


def test_open_index_imports_no_torch_model_or_simulation(tmp_path):
    root, _ = _episode(tmp_path)
    code = """
import builtins, sys
real = builtins.__import__
def guard(name, *args, **kwargs):
    if name.split('.')[0] in ('torch','cosmos_framework','mujoco','rospy','OpenGL'):
        raise AssertionError('unexpected runtime import: '+name)
    return real(name,*args,**kwargs)
builtins.__import__=guard
from g2.latent_cache.storage import open_episode_index, ViewReader
index=open_episode_index(sys.argv[1])
reader=ViewReader(index)
assert reader.read_view('sixview/minus_Y',7)['present'] is False
print('INDEX_ONLY_PASS')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "INDEX_ONLY_PASS"


@pytest.mark.parametrize("target", ["source", "manifest", "complete", "recipe"])
def test_index_rejects_changed_source_incomplete_or_wrong_recipe(tmp_path, target):
    root, _manifest = _episode(tmp_path)
    if target == "source":
        (root / "episode_manifest.json").write_text('{"changed":true}')
    elif target == "manifest":
        with (root / "vae_cache/manifest.json").open("a") as f:
            f.write(" ")
    elif target == "complete":
        (root / "vae_cache/COMPLETE.json").unlink()
    else:
        with pytest.raises(CacheError, match="recipe"):
            open_episode_index(root, expected_recipe_id="0" * 64)
        return
    with pytest.raises(CacheError):
        open_episode_index(root)


@pytest.mark.parametrize(
    "field,value",
    [("state_records", [0, 0, 9]), ("path", "../unsafe.pt"), ("shape", [2, 0, 3, 4])],
)
def test_index_rejects_bounds_layout_and_path_even_with_updated_marker(
    tmp_path, field, value
):
    root, manifest = _episode(tmp_path)
    manifest["views"]["sixview/floor_top"][field] = value
    _completion(root, manifest)
    with pytest.raises(CacheError):
        open_episode_index(root)


def test_reader_rejects_symlink_payload_components_without_scanning_others(tmp_path):
    root, _ = _episode(tmp_path)
    folder = root / "vae_cache/sixview"
    folder.rename(root / "vae_cache/actual")
    folder.symlink_to("actual", target_is_directory=True)
    index = open_episode_index(root)  # No payload traversal here.
    with pytest.raises(CacheError, match="symbolic|symlink"):
        ViewReader(index).read_view("sixview/floor_top", 2)
    path = root / "COMPLETE.json"
    path.rename(root / "source_complete.json")
    path.symlink_to("source_complete.json")
    with pytest.raises(CacheError, match="symbolic|symlink"):
        open_episode_index(root)


def _damage_row(path, row_index):
    # Mutate one finite FP32 scalar without changing ZIP size or metadata.
    # This demonstrates selected-row integrity, rather than relying on a size check.
    with zipfile.ZipFile(path) as archive:
        info = next(x for x in archive.infolist() if x.filename.endswith("/data/0"))
    with path.open("r+b") as stream:
        stream.seek(info.header_offset + 26)
        name_length, extra_length = struct.unpack("<HH", stream.read(4))
        offset = info.header_offset + 30 + name_length + extra_length
        stream.seek(offset + row_index * 24 * 4)
        stream.write(struct.pack("<f", 1984.0))


def test_only_selected_row_is_read_and_checked_but_full_audit_catches_history(tmp_path):
    root, _ = _episode(tmp_path)
    path = root / "vae_cache/sixview/floor_top.pt"
    _damage_row(path, 1)
    reader = ViewReader(open_episode_index(root))
    assert reader.read_view("sixview/floor_top", 2)["latent"].sum() == 276
    with pytest.raises(CacheError, match="damaged"):
        reader.read_view("sixview/floor_top", 29)
    with pytest.raises(CacheError, match="damaged"):
        inspect_view_payload(path)


def test_changed_selected_file_after_mapping_is_refused(tmp_path):
    root, _ = _episode(tmp_path)
    reader = ViewReader(open_episode_index(root))
    reader.read_view("sixview/floor_top", 2)
    _damage_row(root / "vae_cache/sixview/floor_top.pt", 0)
    with pytest.raises(CacheError, match="changed"):
        reader.read_view("sixview/floor_top", 2)


def test_future_owner_is_refused(tmp_path):
    root, manifest = _episode(tmp_path)
    view = "sixview/floor_top"
    path = root / "vae_cache" / (view + ".pt")
    value = torch.load(path, weights_only=True)
    path.unlink()
    # A physically valid record at future ordinal2 must not serve logical ordinal0.
    value["metadata"]["view_plan"]["state_records"] = [1, 0, 1]
    with pytest.raises(CacheError, match="future"):
        write_view_payload(path, value["metadata"], value["latents"])
    # Simulate untrusted bytes, bypassing the guarded writer.
    torch.save(value, path)
    record = dict(manifest["views"][view])
    record.update(
        sha256=digest(path),
        bytes=path.stat().st_size,
        metadata_sha256=fingerprint(value["metadata"]),
        state_records=[1, 0, 1],
    )
    manifest["views"][view] = record
    _completion(root, manifest)
    with pytest.raises(CacheError, match="future"):
        ViewReader(open_episode_index(root)).read_view(view, 2)


@pytest.mark.parametrize("identity", ["source", "recipe_id", "episode_key"])
def test_payload_identity_cannot_disagree_even_with_updated_file_checksums(
    tmp_path, identity
):
    root, manifest = _episode(tmp_path)
    view = "sixview/floor_top"
    path = root / "vae_cache" / (view + ".pt")
    value = torch.load(path, weights_only=True)
    path.unlink()
    if identity == "source":
        value["metadata"]["source"] = {
            **manifest["source"],
            "manifest_sha256": "f" * 64,
        }
    else:
        value["metadata"][identity] = (
            "f" * 64 if identity == "recipe_id" else "Other/episode_000005"
        )
    record = write_view_payload(path, value["metadata"], value["latents"])
    record.pop("metadata")
    record.update(path=view + ".pt", state_records=[0, 0, 1])
    manifest["views"][view] = record
    _completion(root, manifest)
    with pytest.raises(CacheError, match="identity"):
        ViewReader(open_episode_index(root)).read_view(view, 2)


def test_entirely_absent_episode_has_no_numeric_payloads(tmp_path):
    root, _ = _episode(tmp_path, views=[])
    index = open_episode_index(root)
    assert index.manifest["views"] == {}
    assert not list((root / "vae_cache").rglob("*.pt"))
    assert ViewReader(index).read_view("sixview/floor_top", 29)["present"] is False


@pytest.mark.parametrize(
    "bad",
    [
        torch.ones(2, 3, 4),
        torch.ones(0, 2, 3, 4),
        torch.ones(2, 2, 3, 4, dtype=torch.float64),
        torch.full((2, 2, 3, 4), float("nan")),
    ],
)
def test_writer_rejects_wrong_layout_dtype_and_nonfinite_before_publication(
    tmp_path, bad
):
    recipe = make_recipe({"fake": True})
    source = {"manifest_sha256": "0" * 64, "complete_sha256": "1" * 64}
    target = tmp_path / "view.pt"
    with pytest.raises(CacheError):
        write_view_payload(target, _metadata("sixview/floor_top", source, recipe), bad)
    assert not target.exists()


def test_writer_is_exclusive_and_temp_interruption_does_not_publish(
    tmp_path, monkeypatch
):
    root, manifest = _episode(tmp_path)
    path = root / "vae_cache/sixview/floor_top.pt"
    old = path.read_bytes()
    with pytest.raises(CacheError, match="new"):
        write_view_payload(path, {}, torch.ones(2, 2, 3, 4))
    assert path.read_bytes() == old
    meta = _metadata("sixview/new", manifest["source"], manifest["recipe"])
    monkeypatch.setattr(
        torch,
        "save",
        lambda *a, **k: (_ for _ in ()).throw(OSError("interrupted fixture")),
    )
    target = root / "vae_cache/sixview/new.pt"
    with pytest.raises(OSError, match="interrupted"):
        write_view_payload(target, meta, torch.ones(2, 2, 3, 4))
    assert not target.exists()
    assert not list(target.parent.glob(".view-*.tmp"))


def test_duplicate_process_target_rejected_and_lock_inode_persists(tmp_path):
    cache = tmp_path / "vae_cache"
    code = """
import sys
from g2.latent_cache.storage import build_lock
from g2.latent_cache.contract import CacheError
try:
    with build_lock(sys.argv[1]): raise SystemExit(9)
except CacheError:
    print('BUSY')
"""
    with build_lock(cache):
        inode = (cache / ".build.lock").stat().st_ino
        p = subprocess.run(
            [sys.executable, "-c", code, str(cache)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert p.returncode == 0 and p.stdout.strip() == "BUSY", p.stderr
    assert (cache / ".build.lock").stat().st_ino == inode
    with build_lock(cache):
        assert (cache / ".build.lock").stat().st_ino == inode


def test_cache_lock_and_json_refuse_symlinks_and_default_overwrite(tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(CacheError, match="symlink"), build_lock(link):
        pytest.fail("symlink lock accepted")
    path = tmp_path / "index.json"
    atomic_json(path, {"safe": True})
    with pytest.raises(CacheError, match="exists"):
        atomic_json(path, {"safe": False})
    assert json.loads(path.read_text()) == {"safe": True}
