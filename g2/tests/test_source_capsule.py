"""CPU synthetic publication/retirement proofs, never a real F27/Wan gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from g2.io import digest, read_json, write_json
from g2.latent_cache import final_source as final
from g2.latent_cache.builder import verify_episode
from g2.latent_cache.contract import CacheError, make_recipe
from g2.latent_cache.production import build_profile
from g2.latent_cache.retirement_policy import SCHEMA as POLICY_SCHEMA
from g2.latent_cache.storage import ViewReader, open_episode_index
from g2.latent_cache.streaming import EventSpool
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.tests.test_stage_a_streaming import setup_case
from g2.tests.test_view_vae_builder import PREPROCESS


def capsule_case(tmp_path, *, large_audit=False, archive_root=None):
    kwargs, _, encoder, _, _ = setup_case(tmp_path / "fixture")
    if large_audit:
        for p in kwargs["rendered"].rglob("view.json"):
            value = read_json(p)
            value["stage_static"] = dict(TEST_ONLY_REPEATED_AUDIT="x" * 150000)
            value["stage_dynamic"] = dict(TEST_ONLY_TIMING=[1, 2, 3])
            value["alpha"] = [1, 1, 1]
            write_json(p, value)
    output = tmp_path / "owned_output"
    output.mkdir()
    config_id = "e" * 64
    write_json(
        output / ".g2_stage_a_dataset_root.json",
        dict(
            schema="g2_owned_production_output_v1",
            config_id=config_id,
            output=str(output),
        ),
    )
    policy = dict(
        schema=POLICY_SCHEMA,
        format="capsule_v2",
        output_root=str(output),
        work_root=str(tmp_path / "work"),
        spool_root=str(tmp_path / "spool"),
        config_id=config_id,
        mapping_sha256="f" * 64,
        source_versions=dict(root="a" * 40, child="b" * 40, nav="c" * 40),
        protected_roots=[
            str(tmp_path / "fixture"),
            str(Path(__file__).resolve().parents[2]),
        ],
        keep_full_audit=False,
        audit_archive_root=None,
        audit_retention_policy=None,
    )
    if archive_root is not None:
        policy.update(
            keep_full_audit=True,
            audit_archive_root=str(archive_root),
            audit_retention_policy="TEST_ONLY_REMOVE_TEMP_ARCHIVE_AFTER_VERIFICATION",
        )
    spool = EventSpool(
        tmp_path / "spool",
        make_recipe(encoder.descriptor(), PREPROCESS),
        source_policy=policy,
    )
    target = output / "tasks/NavigateKitchen/episodes/episode_000000"
    job = spool.register(
        target,
        episode_key="NavigateKitchen/episode_000000",
        source_fingerprint=kwargs["source_fingerprint"],
        profile_id=kwargs["profile"].to_dict()["profile_id"],
    )
    return kwargs, target, encoder, spool, job


def complete_working(kwargs, target, encoder, spool, job):
    package_stage_a(destination=target, **kwargs)
    build_profile(target, encoder, preprocessing=PREPROCESS, cleanup=True)
    spool.offer_source(job)


def tensors(root):
    index = open_episode_index(root)
    with ViewReader(index, max_views=1) as reader:
        return {
            (s["logical_state_id"], v): reader.read_view(v, s["logical_state_id"])
            for s in index.manifest["states"]
            for v in index.manifest["views"]
        }


def test_capsule_preserves_all_products_pt_bytes_projection_and_lazy_reader(tmp_path):
    kwargs, target, encoder, spool, job = capsule_case(tmp_path, large_audit=True)
    complete_working(kwargs, target, encoder, spool, job)
    manifest = validate_profile_episode(target)
    products = {p: digest(target / p) for p in manifest["files"]}
    payloads = {
        str(p.relative_to(target)): digest(p)
        for p in (target / "vae_cache").rglob("*.pt")
    }
    before = tensors(target)
    original_source_bytes = (target / final.FULL).stat().st_size
    original_source_sha = digest(target / final.FULL)
    assert spool.adopt_completed(job)
    assert (
        not (target / final.FULL).exists()
        and not (target / "SPATIAL_SOURCE_READY.json").exists()
    )
    assert validate_profile_episode(target)["schema"] == final.PROFILE_SCHEMA
    assert open_episode_index(target).manifest["schema"] == final.INDEX_SCHEMA
    assert products == {p: digest(target / p) for p in products}
    assert payloads == {p: digest(target / p) for p in payloads}
    capsule = read_json(target / final.CAPSULE)
    assert capsule["working_source"]["manifest_sha256"] == original_source_sha
    assert (target / final.CAPSULE).stat().st_size < original_source_bytes / 4
    assert "TEST_ONLY_REPEATED_AUDIT" not in (target / final.CAPSULE).read_text()
    checked = verify_episode(target, reencoder=encoder)
    assert checked["records_checked"] == 5 and checked["max_abs_error"] == 0
    after = tensors(target)
    for key, left in before.items():
        right = after[key]
        assert left.keys() == right.keys()
        assert left["present"] == right["present"]
        if left["present"]:
            assert (
                left["latent"].equal(right["latent"])
                and left["owner"] == right["owner"]
                and left["preprocessing"] == right["preprocessing"]
            )
    receipt = spool.completed_receipt(job)
    assert receipt["schema"] == "g2_published_episode_tombstone_v2"
    assert final.FULL not in receipt["verification"]["identity_files"]
    assert receipt["verification"]["identity_files"][final.CAPSULE] == digest(
        target / final.CAPSULE
    )
    assert spool.stats()["completed_jobs"] == 1 and spool.stats()["active_records"] == 0
    assert (
        spool.register(
            target,
            episode_key="NavigateKitchen/episode_000000",
            source_fingerprint=kwargs["source_fingerprint"],
            profile_id=kwargs["profile"].to_dict()["profile_id"],
        )
        == job
    )


def test_pending_source_is_not_retired_and_legacy_full_source_stays_strict(tmp_path):
    kwargs, target, encoder, spool, job = capsule_case(tmp_path)
    package_stage_a(destination=target, **kwargs)
    before = (target / final.FULL).read_bytes()
    with pytest.raises(CacheError, match="before final"):
        spool.reap(job)
    assert (target / final.FULL).read_bytes() == before and not (
        target / final.CAPSULE
    ).exists()
    # Legacy files do not become capsules by deletion or by a cache flag.
    build_profile(target, encoder, preprocessing=PREPROCESS)
    (target / final.FULL).unlink()
    with pytest.raises(CacheError):
        open_episode_index(target)


def test_active_reader_defers_retirement_then_old_index_must_reopen(tmp_path):
    kwargs, target, encoder, spool, job = capsule_case(tmp_path)
    complete_working(kwargs, target, encoder, spool, job)
    index = open_episode_index(target)
    with ViewReader(index) as reader:
        before = reader.read_view("sixview/floor_top", 0)["latent"]
        assert not spool.adopt_completed(job)
        assert (target / final.FULL).exists() and not (target / final.CAPSULE).exists()
        assert before.equal(reader.read_view("sixview/floor_top", 0)["latent"])
    assert spool.reap(job)
    with pytest.raises(CacheError, match="reopen"):
        ViewReader(index)
    with ViewReader(open_episode_index(target)) as reader:
        assert before.equal(reader.read_view("sixview/floor_top", 0)["latent"])


def test_v2_json_open_is_light_and_reader_only_opens_requested_views(
    tmp_path, monkeypatch
):
    import os
    import subprocess
    import sys

    import g2.latent_cache.storage as storage

    kwargs, target, encoder, spool, job = capsule_case(tmp_path)
    complete_working(kwargs, target, encoder, spool, job)
    assert spool.adopt_completed(job)
    code = """import sys
from g2.latent_cache.storage import open_episode_index
open_episode_index(sys.argv[1])
assert not {'torch','mujoco','g2.offline.stage_a','g2.views.render_connections','g2.latent_cache.encoding'} & set(sys.modules)
"""
    run = subprocess.run(
        [sys.executable, "-c", code, str(target)],
        capture_output=True,
        text=True,
        timeout=20,
        env=dict(os.environ, CUDA_VISIBLE_DEVICES=""),
    )
    assert run.returncode == 0, run.stderr
    index = open_episode_index(target)
    views = list(index.manifest["views"])
    selected = views[:3]
    opened = []
    load = storage._load

    def track(path, **kwargs):
        opened.append(Path(path).name)
        return load(path, **kwargs)

    monkeypatch.setattr(storage, "_load", track)
    other = target / "vae_cache" / index.manifest["views"][views[3]]["path"]
    other.write_bytes(b"TEST_ONLY_CORRUPT_UNSELECTED_PAYLOAD")
    with ViewReader(index, max_views=3) as reader:
        assert len(reader.read_many(0, selected)) == 3
        assert len(opened) == 3 and other.name not in opened
        with pytest.raises(CacheError):
            reader.read_view(views[3], 0)


def test_optional_full_audit_is_lossless_and_outside_output_filesystem(tmp_path):
    import gzip
    import tempfile

    if (
        not Path("/dev/shm").is_dir()
        or Path("/dev/shm").stat().st_dev == tmp_path.stat().st_dev
    ):
        pytest.skip(
            "existing distinct temporary filesystem unavailable; no mount/environment created"
        )
    with tempfile.TemporaryDirectory(
        prefix="g2-issue63-audit-", dir="/dev/shm"
    ) as archive:
        kwargs, target, encoder, spool, job = capsule_case(
            tmp_path, large_audit=True, archive_root=archive
        )
        complete_working(kwargs, target, encoder, spool, job)
        source = (target / final.FULL).read_bytes()
        assert spool.adopt_completed(job)
        capsule = read_json(target / final.CAPSULE)
        ref = capsule["full_audit_archive"]
        with gzip.open(ref["path"], "rb") as stream:
            assert stream.read() == source
        assert Path(ref["path"]).stat().st_dev != target.stat().st_dev
        assert all(
            p.name != "spatial_source.json.gz" for p in target.rglob("*.json.gz")
        )
    assert open_episode_index(target).manifest["schema"] == final.INDEX_SCHEMA
