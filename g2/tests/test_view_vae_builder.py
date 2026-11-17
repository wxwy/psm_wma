"""End-to-end CPU fixture cache tests; no real VAE, GPU or private episodes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import torch

from g2.latent_cache.builder import (
    build_episode,
    discover_episodes,
    plan_episode,
    verify_episode,
)
from g2.latent_cache.contract import CacheError, make_recipe, preprocessing_recipe
from g2.latent_cache.encoding import preprocess_rgb
from g2.latent_cache.storage import ViewReader, build_lock, open_episode_index
from g2.tests.test_view_vae_source import _fixture

PREPROCESS = preprocessing_recipe(32, 32)


class FakeEncoder:
    def __init__(self, fail_at=None, mutate=None, identity="a"):
        self.calls = 0
        self.fail_at = fail_at
        self.mutate = mutate
        self.identity = identity

    def descriptor(self):
        return {
            "implementation": "TEST_ONLY_FAKE",
            "test_only": True,
            "weights_sha256": self.identity * 64,
        }

    def encode(self, rgb, preprocessing):
        self.calls += 1
        if self.fail_at == self.calls:
            raise RuntimeError("controlled interruption")
        if self.mutate:
            self.mutate(self.calls)
        _, meta = preprocess_rgb(rgb, preprocessing)
        latent = torch.arange(18, dtype=torch.float32).reshape(3, 2, 3) / 7
        return latent + float(rgb[0, 0, 0]) / 255, meta


def _source_bytes(root):
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and "vae_cache" not in p.relative_to(root).parts
    }


def test_complete_all_views_owner_once_absent_and_logical_identity(tmp_path):
    ep = tmp_path / "ep"
    _fixture(ep)
    before = _source_bytes(ep)
    encoder = FakeEncoder()
    plan = plan_episode(ep, make_recipe(encoder.descriptor(), PREPROCESS))
    assert not (ep / "vae_cache").exists()
    assert plan["logical_view_count"] == 4
    assert plan["physical_image_count"] == 5
    assert plan["reference_count"] == 6
    result = build_episode(ep, encoder, preprocessing=PREPROCESS)
    assert encoder.calls == result["encoded_records"] == 5
    assert result["view_count"] == 4
    assert len(list((ep / "vae_cache").rglob("*.pt"))) == 4
    assert not (ep / "vae_cache/sixview/plus_Y.pt").exists()
    assert _source_bytes(ep) == before
    index = open_episode_index(ep)
    with ViewReader(index) as reader:
        sample = reader.read_view("sixview/floor_top", 30)
        assert sample["present"]
        assert sample["logical_frame"] == 17
        assert sample["owner"]["owner_state_id"] == 10
        assert sample["owner"]["owner_frame"] == 5
        assert list(sample["latent"].shape) == [3, 2, 3]
        assert not reader.read_view("islands/island_0_entity_18/plus_Y", 110)["present"]
        assert not reader.read_view("sixview/plus_Y", 110)["present"]
        selected = reader.read_many(
            110,
            [
                "sixview/floor_top",
                "sixview/plus_X",
                "islands/island_1_entity_27/minus_Y",
            ],
        )
        assert all(v["present"] for v in selected)
    checked = verify_episode(ep, reencoder=FakeEncoder())
    assert checked["records_checked"] == 5 and checked["max_abs_error"] == 0
    assert checked["training_ready"] is False


def test_resume_complete_does_not_encode_or_change_files(tmp_path):
    ep = tmp_path / "ep"
    _fixture(ep)
    build_episode(ep, FakeEncoder(), preprocessing=PREPROCESS)
    files = {p: p.read_bytes() for p in (ep / "vae_cache").rglob("*") if p.is_file()}
    encoder = FakeEncoder(fail_at=1)
    result = build_episode(ep, encoder, preprocessing=PREPROCESS, resume=True)
    assert result["already_complete"] and encoder.calls == 0
    assert all(p.read_bytes() == b for p, b in files.items())
    with pytest.raises(CacheError):
        build_episode(ep, FakeEncoder(), preprocessing=PREPROCESS)


def test_encoder_reused_output_buffer_does_not_overwrite_previous_owner(tmp_path):
    ep = tmp_path / "ep"
    _fixture(ep)

    class BufferEncoder(FakeEncoder):
        def __init__(self):
            super().__init__()
            self.buffer = torch.empty((3, 2, 3))

        def encode(self, rgb, preprocessing):
            self.calls += 1
            _, meta = preprocess_rgb(rgb, preprocessing)
            self.buffer.fill_(int(rgb[0, 0, 0]))
            return self.buffer, meta

    build_episode(ep, BufferEncoder(), preprocessing=PREPROCESS)
    with ViewReader(open_episode_index(ep)) as reader:
        assert torch.all(reader.read_view("sixview/floor_top", 10)["latent"] == 0)
        assert torch.all(reader.read_view("sixview/floor_top", 80)["latent"] == 40)


@pytest.mark.parametrize(
    "target", ["recipe_id", "episode_key", "source", "owner_frame"]
)
def test_skip_source_still_checks_cache_internal_identity(tmp_path, target):
    from g2.io import digest, read_json
    from g2.latent_cache.storage import (
        atomic_json,
        inspect_view_payload,
        write_view_payload,
    )

    ep = tmp_path / "ep"
    _fixture(ep)
    build_episode(ep, FakeEncoder(), preprocessing=PREPROCESS)
    cache = ep / "vae_cache"
    path = cache / "sixview/floor_top.pt"
    data = torch.load(path, weights_only=True, map_location="cpu")
    metadata = data["metadata"]
    if target == "recipe_id":
        metadata["recipe_id"] = "f" * 64
    elif target == "episode_key":
        metadata["episode_key"] = "Other/episode_000042"
    elif target == "source":
        metadata["source"]["manifest_sha256"] = "f" * 64
    else:
        metadata["view_plan"]["records"][0]["owner_frame"] = 100
    replacement = cache / "replacement.pt"
    write_view_payload(replacement, metadata, data["latents"])
    replacement.replace(path)
    info = inspect_view_payload(path)
    manifest = read_json(cache / "manifest.json")
    entry = manifest["views"]["sixview/floor_top"]
    manifest["views"]["sixview/floor_top"] = {
        **{k: v for k, v in info.items() if k != "metadata"},
        "path": entry["path"],
        "state_records": entry["state_records"],
    }
    atomic_json(cache / "manifest.json", manifest, replace=True)
    marker = read_json(cache / "COMPLETE.json")
    marker["manifest_sha256"] = digest(cache / "manifest.json")
    atomic_json(cache / "COMPLETE.json", marker, replace=True)
    with pytest.raises(CacheError):
        verify_episode(ep, check_source=False)


def test_resume_interruption_reuses_view_and_ignores_unpublished_temporary(tmp_path):
    ep = tmp_path / "ep"
    _fixture(ep)
    with pytest.raises(RuntimeError, match="controlled"):
        build_episode(ep, FakeEncoder(fail_at=2), preprocessing=PREPROCESS)
    cache = ep / "vae_cache"
    assert not (cache / "COMPLETE.json").exists()
    prior = {p: p.read_bytes() for p in cache.rglob("*.pt")}
    assert len(prior) == 1
    (cache / ".view-interrupted.tmp").write_bytes(b"not a numeric payload")
    encoder = FakeEncoder()
    result = build_episode(ep, encoder, preprocessing=PREPROCESS, resume=True)
    assert encoder.calls == 4 and result["reused_views"] == 1
    assert all(p.read_bytes() == b for p, b in prior.items())
    assert verify_episode(ep)["payloads_checked"] == 4


def test_orphan_atomic_payload_can_be_adopted_after_index_write_interruption(
    tmp_path, monkeypatch
):
    from g2.latent_cache import storage

    ep = tmp_path / "ep"
    _fixture(ep)
    real = storage.atomic_json

    def fail_index(path, value, **kwargs):
        if Path(path).name == "manifest.json" and value.get("views"):
            raise RuntimeError("crash after atomic payload, before index")
        return real(path, value, **kwargs)

    monkeypatch.setattr(storage, "atomic_json", fail_index)
    with pytest.raises(RuntimeError, match="crash"):
        build_episode(ep, FakeEncoder(), preprocessing=PREPROCESS)
    monkeypatch.setattr(storage, "atomic_json", real)
    assert len(list((ep / "vae_cache").rglob("*.pt"))) == 1
    encoder = FakeEncoder()
    result = build_episode(ep, encoder, preprocessing=PREPROCESS, resume=True)
    assert result["reused_views"] == 1 and encoder.calls == 4


@pytest.mark.parametrize("change", ["weights", "recipe", "png", "manifest"])
def test_resume_cannot_mix_different_dependencies(tmp_path, change):
    ep = tmp_path / "ep"
    _fixture(ep)
    with pytest.raises(RuntimeError):
        build_episode(ep, FakeEncoder(fail_at=2), preprocessing=PREPROCESS)
    encoder, prep = FakeEncoder(), PREPROCESS
    if change == "weights":
        encoder = FakeEncoder(identity="b")
    elif change == "recipe":
        prep = preprocessing_recipe(64, 32)
    elif change == "png":
        from PIL import Image

        p = next((ep / "state_000000_frame_000005").rglob("*.png"))
        Image.new("RGB", (12, 8), (1, 2, 3)).save(p)
    else:
        p = ep / "episode_manifest.json"
        p.write_bytes(p.read_bytes() + b" ")
    before = {p: p.read_bytes() for p in (ep / "vae_cache").rglob("*") if p.is_file()}
    with pytest.raises(ValueError):
        build_episode(ep, encoder, preprocessing=prep, resume=True)
    assert encoder.calls == 0
    assert all(p.read_bytes() == b for p, b in before.items())


def test_source_mutation_during_encode_never_writes_completion(tmp_path):
    ep = tmp_path / "ep"
    _fixture(ep)

    def mutate(count):
        if count == 1:
            p = ep / "episode_manifest.json"
            p.write_bytes(p.read_bytes() + b" ")

    with pytest.raises(ValueError):
        build_episode(ep, FakeEncoder(mutate=mutate), preprocessing=PREPROCESS)
    assert not (ep / "vae_cache/COMPLETE.json").exists()


def test_concurrent_build_refused_without_payload_write(tmp_path):
    ep = tmp_path / "ep"
    _fixture(ep)
    encoder = FakeEncoder()
    with build_lock(ep / "vae_cache"):
        with pytest.raises(CacheError, match="another builder"):
            build_episode(ep, encoder, preprocessing=PREPROCESS, resume=True)
    assert encoder.calls == 0 and not list((ep / "vae_cache").rglob("*.pt"))


def test_coverage_does_not_depend_on_task_instruction_or_candidates(tmp_path):
    from g2.tests.test_view_vae_source import _seal

    ep = tmp_path / "ep"
    _fixture(ep)
    encoder = FakeEncoder()
    recipe = make_recipe(encoder.descriptor(), PREPROCESS)
    a = plan_episode(ep, recipe)
    doc = json.loads((ep / "episode_manifest.json").read_text())
    doc.update(instruction="another task", candidates=[])
    _seal(ep, doc)
    b = plan_episode(ep, recipe)
    assert a["views"] == b["views"]
    assert a["physical_image_count"] == b["physical_image_count"] == 5


@pytest.mark.parametrize("dtype", ["float16", "bfloat16"])
def test_explicit_reduced_storage_records_error_without_lossless_claim(tmp_path, dtype):
    ep = tmp_path / "ep"
    _fixture(ep)
    build_episode(ep, FakeEncoder(), preprocessing=PREPROCESS, storage_dtype=dtype)
    index = open_episode_index(ep)
    with ViewReader(index) as reader:
        sample = reader.read_view("sixview/floor_top", 10)
        assert sample["latent"].dtype == getattr(torch, dtype)
        assert sample["preprocessing"]["storage_conversion"]["max_abs_error"] > 0
    with pytest.raises(CacheError, match="re-encoded"):
        verify_episode(ep, reencoder=FakeEncoder())


def test_discovery_uses_completed_package_membership(tmp_path):
    root = tmp_path / "dataset"
    ep = root / "tasks/NavigateKitchen/episodes/episode_000042"
    ep.parent.mkdir(parents=True)
    _fixture(ep)
    assert discover_episodes(root, tasks=["NavigateKitchen"], episodes=[42]) == [ep]
    for kwargs in [{"tasks": ["Unknown"]}, {"episodes": [123]}]:
        with pytest.raises(ValueError):
            discover_episodes(root, **kwargs)


def test_real_cli_plan_is_model_free_and_verify_is_encoder_free(tmp_path):
    ep = tmp_path / "ep"
    _fixture(ep)
    weights = tmp_path / "weights.pt"
    weights.write_bytes(b"CPU plan identity only; not real model weights")
    repo = Path(__file__).resolve().parents[2]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONPATH=str(repo))
    script = """
import sys
from tools.g2.build_spatial_view_vae_cache import main
rc=main(sys.argv[1:]);assert rc==0
assert not any(k=='torch' or k.startswith(('cosmos_framework','mujoco','rospy')) for k in sys.modules)
"""
    cmd = [
        sys.executable,
        "-c",
        script,
        "--dataset-root",
        str(ep),
        "--weights",
        str(weights),
        "--device",
        "cpu",
        "--dry-run",
        "--height",
        "32",
        "--width",
        "32",
    ]
    result = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["results"][0]["physical_image_count"] == 5
    assert not (ep / "vae_cache").exists()
    build_episode(ep, FakeEncoder(), preprocessing=PREPROCESS)
    script = """
import sys
from tools.g2.verify_spatial_view_vae_cache import main
rc=main(sys.argv[1:]);assert rc==0
assert not any(k.startswith(('g2.latent_cache.encoding','cosmos_framework','mujoco','rospy')) for k in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, "--dataset-root", str(ep)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["results"][0]["records_checked"] == 5


def test_corrupt_completed_file_rejected_by_auditor(tmp_path):
    ep = tmp_path / "ep"
    _fixture(ep)
    build_episode(ep, FakeEncoder(), preprocessing=PREPROCESS)
    p = next((ep / "vae_cache").rglob("*.pt"))
    p.write_bytes(b"corrupt payload")
    with pytest.raises(ValueError):
        verify_episode(ep)
