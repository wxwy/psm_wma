"""Shared engine source lifecycle tests with transparent CPU-only batch fixture."""

import json
from pathlib import Path

import pytest

from g2.io import digest, read_json, write_json
from g2.latent_cache.batch_engine import (
    BatchEngine,
    CapacityWatchdog,
    IdleClock,
    discover_published,
    engine_config,
    initialize,
)
from g2.latent_cache.builder import verify_episode
from g2.latent_cache.contract import CacheError
from g2.latent_cache.storage import ViewReader, open_episode_index
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.tests.test_stage_a_package import stage_case

FACTORY = "g2.tests.batch_helpers:FakeBatchEncoder"


def init(tmp_path, *, mode="independent", fault=None, budget=4 * 1024**3):
    config = dict(
        gpus=[4, 5],
        batch_wait_ms=5,
        idle_timeout_s=0.15,
        discovery_interval_s=0.02,
        poll_interval_s=0.01,
        min_free_disk_bytes=0,
        test_crash_once=fault,
    )
    return initialize(
        tmp_path / "spool",
        weights=tmp_path / "test_only",
        cosmos_root=tmp_path,
        config=config,
        lifecycle="view_first_posthoc_v1" if mode == "independent" else "streaming_v1",
        _test_factory=FACTORY,
        allow_test=True,
        max_result_bytes=budget,
    )


def sample(tmp_path, *, vae=False):
    kwargs, _ = stage_case(
        tmp_path / "fixture", OutputProfile(selection_top_variant="clean", view_vae=vae)
    )
    target = tmp_path / "dataset/tasks/NavigateKitchen/episodes/episode_000000"
    package_stage_a(destination=target, compress_source=not vae, **kwargs)
    return target, kwargs


def test_idle600_is_not_all_complete_and_busy_resets():
    clock = IdleClock()
    assert not clock.observe(100, busy=False)
    assert not clock.observe(699.99, busy=False)
    assert clock.observe(700, busy=False)
    assert not clock.observe(701, busy=True)
    assert not clock.observe(999, busy=False)
    assert not clock.observe(1598, busy=False)
    assert not clock.observe(1599, busy=False, new_work=True)
    assert engine_config()["gpus"] == [4, 5, 6, 7]
    assert engine_config()["max_batch_size_per_gpu"] == 32


@pytest.mark.parametrize(
    "bad",
    [
        dict(gpus=[4, 4]),
        dict(gpus=[0, True]),
        dict(max_batch_size_per_gpu=33),
        dict(batch_wait_ms=float("nan")),
        dict(lease_s=10, heartbeat_s=5),
        dict(test_crash_once="after_ack:0"),
    ],
)
def test_config_rejects_ambiguous_unbounded_or_unscoped_fault(bad):
    with pytest.raises(CacheError):
        engine_config(bad)


def test_continuous_discovery_ignores_inprogress_then_published(tmp_path):
    data = tmp_path / "dataset"
    data.mkdir()
    assert discover_published(data) == []
    (data / "tasks/NewTask").mkdir(parents=True)
    assert discover_published(data) == []
    (data / "tasks/NewTask/episodes").mkdir()
    assert discover_published(data) == []
    partial = data / "tasks/NavigateKitchen/episodes/episode_000000"
    partial.mkdir(parents=True)
    (partial / "episode_manifest.json").write_text("{incomplete")
    assert discover_published(data) == []
    (partial / "episode_manifest.json").unlink()
    partial.rmdir()
    target, _ = sample(tmp_path)
    assert discover_published(data) == [target]


def test_independent_real_processes_cache_resume_and_selected_reader(tmp_path):
    target, _ = sample(tmp_path)
    before = {
        str(p.relative_to(target)): digest(p) for p in target.rglob("*") if p.is_file()
    }
    spool, spec = init(tmp_path)
    result = BatchEngine(
        spool, spec, mode="independent", dataset_root=tmp_path / "dataset"
    ).run()
    assert result["status"] == "IDLE_TIMEOUT" and result["spool"]["active_jobs"] == 0
    assert sum(g["records"] for g in result["batch"]["gpu"].values()) == 5
    assert (
        verify_episode(target, expected_recipe_id=spool.recipe["recipe_id"])[
            "records_checked"
        ]
        == 5
    )
    assert all(digest(target / p) == sha for p, sha in before.items())
    assert list((spool.root / "records").rglob("*.pt")) == []
    index = open_episode_index(target)
    with ViewReader(index, max_views=1) as reader:
        clean = reader.read_view("sixview/floor_top", 2)
        assert clean["present"] and list(clean["latent"].shape) == [48, 16, 16]
        assert reader.read_view("sixview/plus_Y", 2)["present"] is False
    first = {p: digest(p) for p in (target / "vae_cache").rglob("*") if p.is_file()}
    resumed = BatchEngine(
        spool, spec, mode="independent", dataset_root=tmp_path / "dataset", resume=True
    ).run()
    assert resumed["status"] == "IDLE_TIMEOUT"
    assert all(digest(p) == v for p, v in first.items())
    from g2.latent_cache.batch_verify import verify_replay
    from g2.tests.batch_helpers import FakeBatchEncoder

    replay = verify_replay(tmp_path / "dataset", FakeBatchEncoder())
    assert replay["records_checked"] == 5 and replay["max_abs_error"] == 0


def test_all_complete_requires_explicit_expected_and_stage_a_done(tmp_path):
    target, _ = sample(tmp_path)
    spool, spec = init(tmp_path)
    expected = tmp_path / "expected.json"
    signal = tmp_path / "stage_a_done.json"
    manifest = read_json(target / "episode_manifest.json")
    write_json(
        expected,
        dict(
            schema="g2_vae_expected_episodes_v1",
            episodes=[
                dict(
                    episode_key="NavigateKitchen/episode_000000",
                    source_fingerprint=manifest["source_fingerprint"],
                )
            ],
        ),
    )
    engine = BatchEngine(
        spool,
        spec,
        mode="independent",
        dataset_root=tmp_path / "dataset",
        expected=expected,
        producer_done=signal,
    )
    assert not engine._all_complete()
    write_json(
        signal,
        dict(
            schema="g2_view_publisher_done_v1",
            complete=True,
            expected_sha256=digest(expected),
            dataset_root=str(tmp_path / "dataset"),
            failed_episodes=[],
            episode_count=1,
        ),
    )
    # A publisher's signal alone cannot certify missing numerical files.
    with pytest.raises((CacheError, OSError)):
        engine._all_complete()
    assert engine.run()["status"] == "ALL_COMPLETE"


def test_sync_source_and_compact_owners_use_identical_batch_core(tmp_path):
    from g2.tests.test_stage_a_streaming import publish_raw

    spool, spec = init(tmp_path, mode="sync", fault="after_ack:0")
    profile = OutputProfile(selection_top_variant="clean", view_vae=True)
    kwargs, _ = stage_case(tmp_path / "fixture", profile)
    target = tmp_path / "published"
    job = spool.register(
        target,
        episode_key="NavigateKitchen/episode_000000",
        source_fingerprint=kwargs["source_fingerprint"],
        profile_id=profile.to_dict()["profile_id"],
    )
    publish_raw(kwargs, spool, job)
    package_stage_a(
        destination=target, event_sink=lambda event: spool.enqueue(job, event), **kwargs
    )
    spool.offer_source(job)
    engine = BatchEngine(spool, spec, mode="sync", stop_file=tmp_path / "stop")
    # The real coordinator loop exits only on the producer/supervisor stop signal.
    import threading
    import time

    def stop_after_publish():
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            if (target / "COMPLETE.json").exists():
                (tmp_path / "stop").write_text("{}")
                return
            time.sleep(0.05)
        (tmp_path / "stop").write_text("{}")

    t = threading.Thread(target=stop_after_publish, daemon=True)
    t.start()
    result = engine.run()
    t.join(1)
    assert result["status"] == "DRAINED"
    assert sum(result["worker_restarts"].values()) == 1
    assert validate_profile_episode(target)["profile_complete"]
    assert verify_episode(target)["records_checked"] == 5
    assert spool.stats()["completed_jobs"] == 1 and spool.stats()["active_records"] == 0
    index = open_episode_index(target)
    assert index.manifest["views"]["sixview/floor_top"]["state_records"] == [0, 0, 0]
    assert index.manifest["views"]["sixview/floor_top_w_rbs"]["state_records"] == [
        0,
        1,
        1,
    ]


def test_full_production_batch_adapter_and_explicit_resource_sharing(tmp_path):
    from g2.offline import full_production as full
    from g2.tests.test_one_shot_supervisor import config_case

    cfg, path = config_case(tmp_path)
    raw = json.loads(path.read_text())
    raw.update(vae_engine=dict(gpus=[4, 5, 6, 7]), allow_shared_gpu_processes=True)
    write_json(path, raw)
    cfg = full.load_config(path)
    cmd = full.consumer_command(cfg, "--execute", tmp_path / "stop")
    assert (
        "tools.g2.run_spatial_vae_engine" in cmd
        and "--serve" in cmd
        and "--resume" in cmd
    )
    assert cmd[cmd.index("--mode") + 1] == "sync"
    raw["vae_engine"]["gpus"] = [0]
    write_json(path, raw)
    with pytest.raises(CacheError, match="approved"):
        full.load_config(path)


def test_batch_cache_source_retirement_and_reentry_need_no_original_json(tmp_path):
    from g2.latent_cache.batch_verify import verify_replay
    from g2.latent_cache.posthoc import retire_view_first_cache
    from g2.tests.batch_helpers import FakeBatchEncoder
    from g2.tests.test_view_first_retirement import retirement_case

    target, policy = retirement_case(tmp_path / "fixture")
    spool, spec = init(tmp_path)
    data = Path(policy["output_root"])
    assert (
        BatchEngine(spool, spec, mode="independent", dataset_root=data).run()["status"]
        == "IDLE_TIMEOUT"
    )
    payloads = {p: digest(p) for p in (target / "vae_cache").rglob("*.pt")}
    assert retire_view_first_cache(
        target,
        spool_root=policy["spool_root"],
        source_policy=policy,
        expected_recipe_id=spool.recipe["recipe_id"],
    )["complete"]
    assert (
        not (target / "spatial_source.json").exists()
        and not (target / "spatial_source.json.gz").exists()
    )
    assert all(digest(p) == v for p, v in payloads.items())
    assert verify_replay(data, FakeBatchEncoder())["records_checked"] == 5
    assert (
        BatchEngine(
            spool, spec, mode="independent", dataset_root=data, resume=True
        ).run()["status"]
        == "IDLE_TIMEOUT"
    )


def test_capacity_wait_is_bounded_and_progress_or_gc_resets_it():
    clock = CapacityWatchdog(300)
    clock.observe(0, blocked=True, signature="completed32_pending3")
    clock.observe(299.9, blocked=True, signature="completed32_pending3")
    with pytest.raises(CacheError, match="numeric capacity.*source.*retained"):
        clock.observe(300, blocked=True, signature="completed32_pending3")
    clock.observe(301, blocked=True, signature="another_job_completed")
    clock.observe(599, blocked=True, signature="another_job_completed")
    clock.observe(600, blocked=False, signature=None)
    clock.observe(1000, blocked=True, signature="next_episode")


@pytest.mark.parametrize(
    "scope,accepted",
    [
        (dict(tasks=["DifferentTask"]), False),
        (dict(episodes=[999]), False),
        (dict(tasks=["NavigateKitchen"], episodes=[0]), True),
    ],
)
def test_direct_published_episode_honors_explicit_identity_scope(
    tmp_path, scope, accepted
):
    target, _ = sample(tmp_path)
    assert discover_published(target, **scope) == ([target] if accepted else [])


def test_engine_capacity_deadlock_fails_with_source_retained(tmp_path):
    import time

    target, _ = sample(tmp_path)
    before = {p: digest(p) for p in target.rglob("*") if p.is_file()}
    spool, spec = init(tmp_path, budget=1)
    engine = BatchEngine(
        spool,
        spec,
        mode="independent",
        dataset_root=tmp_path / "dataset",
        clock=lambda: time.monotonic() * 200,
    )
    with pytest.raises(CacheError, match="numeric capacity"):
        engine.run()
    assert all(digest(p) == sha for p, sha in before.items())
    assert spool.stats()["pending_inputs"] == 5
    assert read_json(spool.root / "engine_progress.json")["status"] == "FAILED"
    assert not (target / "vae_cache/COMPLETE.json").exists()
