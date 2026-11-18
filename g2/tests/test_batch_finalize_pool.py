"""Parallel CPU-only completion of real fixture batches and original ACK protocol."""

import json

import pytest

from g2.io import digest
from g2.latent_cache.batch_engine import BatchEngine
from g2.latent_cache.builder import verify_episode
from g2.latent_cache.contract import CacheError
from g2.tests.test_batch_engine import init, sample
from g2.tests.test_stage_a_package import stage_case
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a


def _dataset(tmp_path, n):
    roots = []
    for eid in range(n):
        kwargs, _ = stage_case(
            tmp_path / f"source{eid}",
            OutputProfile(selection_top_variant="clean", view_vae=False),
        )
        kwargs["episode_id"] = eid
        for caption in kwargs["captions"].values():
            caption["episode_index"] = eid
        root = (
            tmp_path / "dataset/tasks/NavigateKitchen/episodes"
            / f"episode_{eid:06d}"
        )
        package_stage_a(
            destination=root,
            compress_source=True,
            **kwargs,
        )
        roots.append(root)
    return roots


def test_independent_cpu_finalizers_keep_exact_original_acks_and_resume(tmp_path):
    roots = _dataset(tmp_path, 4)
    before = [
        {str(p.relative_to(root)): digest(p) for p in root.rglob("*") if p.is_file()}
        for root in roots
    ]
    spool, spec = init(tmp_path)
    result = BatchEngine(
        spool,
        spec,
        mode="independent",
        dataset_root=tmp_path / "dataset",
        finalize_workers=2,
    ).run()
    assert result["status"] == "IDLE_TIMEOUT"
    assert result["cpu_finalize_workers"] == 2
    assert result["spool"]["completed_jobs"] == 4
    assert result["spool"]["failed_jobs"] == 0
    assert result["spool"]["active_jobs"] == 0
    assert result["cpu_finalizing_jobs"] == 0
    for root, files in zip(roots, before):
        assert verify_episode(root, expected_recipe_id=spool.recipe["recipe_id"])[
            "records_checked"
        ] == 5
        assert all(digest(root / name) == sha for name, sha in files.items())
    # All completed rows are archived and their original contexts replayable.
    with spool._db() as db:
        assert db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM completed").fetchone()[0] == 4

    complete_hashes = [
        digest(root / "vae_cache/COMPLETE.json") for root in roots
    ]
    resumed = BatchEngine(
        spool,
        spec,
        mode="independent",
        dataset_root=tmp_path / "dataset",
        finalize_workers=2,
        resume=True,
    ).run()
    assert resumed["status"] == "IDLE_TIMEOUT"
    assert resumed["spool"]["completed_jobs"] == 4
    assert [digest(root / "vae_cache/COMPLETE.json") for root in roots] == complete_hashes


def test_cpu_finalization_rejects_other_lifecycle_and_bad_budget(tmp_path):
    spool, spec = init(tmp_path, mode="sync")
    for n in (-1, 9, True, 2.5):
        with pytest.raises(CacheError, match="finalizers"):
            BatchEngine(
                spool,
                spec,
                mode="sync",
                finalize_workers=n,
            )
    with pytest.raises(CacheError, match="finalizers"):
        BatchEngine(spool, spec, mode="sync", finalize_workers=1)


def test_cpu_finalizer_descriptor_is_not_an_encoder():
    from g2.latent_cache.batch_finalize import DescriptorOnlyEncoder

    descriptor = {"schema": "test", "mutable": ["one"]}
    encoder = DescriptorOnlyEncoder(descriptor)
    encoder.descriptor()["mutable"].append("two")
    assert encoder.descriptor() == descriptor
    with pytest.raises(CacheError, match="never encode"):
        encoder.encode("frame")
