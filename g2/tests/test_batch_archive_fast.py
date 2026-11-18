"""Read-only archived VAE integrity and bounded discovery admission regression.

CPU fixture only. No production source, Wan CUDA or live Spool is touched.
"""

import pytest

from g2.io import read_json
from g2.latent_cache import batch_engine
from g2.latent_cache.batch_engine import BatchEngine
from g2.latent_cache.ledger_archive import verify_archived_payload_bytes
from g2.tests.test_batch_engine import init, sample


def test_completed_archive_fast_recheck_detects_pixel_pt_and_source_mutations(
    tmp_path, monkeypatch
):
    target, _ = sample(tmp_path)
    spool, spec = init(tmp_path)
    complete = BatchEngine(
        spool, spec, mode="independent", dataset_root=tmp_path / "dataset"
    ).run()
    assert complete["status"] == "IDLE_TIMEOUT"
    assert complete["spool"]["completed_jobs"] == 1
    assert verify_archived_payload_bytes(spool, target) is True

    # The cold-resume fast path must not silently run expensive tensor/source
    # re-encodes for a completed, already fully audited tombstone.
    def forbidden_full_audit(*_args, **_kwargs):
        raise AssertionError("archived identity used the slow full numerical audit")

    monkeypatch.setattr("g2.latent_cache.builder.verify_episode", forbidden_full_audit)
    resumed = BatchEngine(
        spool, spec, mode="independent", dataset_root=tmp_path / "dataset", resume=True
    )
    resumed._discover()
    assert str(target) in resumed._seen
    assert spool.stats()["active_jobs"] == 0

    profile = read_json(target / "episode_manifest.json")
    pixel = next(p for p in sorted(profile["files"]) if p.endswith(".png"))
    cache = read_json(target / "vae_cache/manifest.json")
    pt = next(iter(cache["views"].values()))["path"]

    for relative in (
        pixel,
        "vae_cache/" + pt,
        "spatial_source.json.gz",
        "episode_manifest.json",
    ):
        file = target / relative
        original = file.read_bytes()
        try:
            # Same length, changed bytes: a weak size-only shortcut must fail.
            file.write_bytes(bytes([original[0] ^ 1]) + original[1:])
            with pytest.raises((OSError, ValueError, KeyError, RuntimeError)):
                verify_archived_payload_bytes(spool, target)
        finally:
            file.write_bytes(original)
        assert verify_archived_payload_bytes(spool, target)


def test_full_active_ledger_prevents_useless_full_catalogue_discovery(
    tmp_path, monkeypatch
):
    target, _ = sample(tmp_path)
    spool, spec = init(tmp_path)
    manifest = read_json(target / "episode_manifest.json")
    spool.register(
        target,
        episode_key="NavigateKitchen/episode_000000",
        source_fingerprint=manifest["source_fingerprint"],
        profile_id=manifest["output_profile"]["profile_id"],
    )
    spec["max_active_jobs"] = 1

    def forbidden_catalogue(*_args, **_kwargs):
        raise AssertionError(
            "full active job ledger still scanned thousands of episodes"
        )

    monkeypatch.setattr(batch_engine, "discover_published", forbidden_catalogue)
    engine = BatchEngine(
        spool, spec, mode="independent", dataset_root=tmp_path / "dataset"
    )
    engine._discover()
    assert spool.stats()["active_jobs"] == 1
    assert spool.stats()["completed_jobs"] == 0
