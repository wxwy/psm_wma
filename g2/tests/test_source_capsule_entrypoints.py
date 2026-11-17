"""Official supervisor/CLI and capacity contracts with synthetic source only."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from g2.io import read_json, write_json
from g2.latent_cache import final_source as final
from g2.latent_cache.contract import CacheError, make_recipe, preprocessing_recipe
from g2.latent_cache.retirement_policy import validate_policy
from g2.latent_cache.streaming import EventSpool
from g2.offline import atomic_6views_run as producer
from g2.offline import full_production as full
from g2.offline.source_capacity import capacity_report, corpus_bytes, episode_bytes
from g2.offline.stage_a import package_stage_a
from g2.offline.work_lifecycle import episode_work_path, producer_work
from g2.tests.test_one_shot_supervisor import config_case
from g2.tests.test_source_capsule import capsule_case, complete_working
from g2.tests.test_stage_a_streaming import setup_case
from tools.g2 import audit_spatial_capacity as capacity_cli
from tools.g2 import verify_spatial_source_index as verify_cli


def test_supervisor_v2_stops_resumes_original_queue_and_retires_after_work_release(
    tmp_path, monkeypatch
):
    _, path = config_case(tmp_path)
    kwargs, _, encoder, _, _ = setup_case(tmp_path / "fixture")
    raw = read_json(path)
    raw.update(
        sample_mode=True,
        tasks=["NavigateKitchen"],
        expected_selected_episodes=1,
        expected_task_count=1,
        expected_episode_ids=[0],
        renderer_gpus=[4],
        workers_per_gpu=1,
        vae_gpu=4,
        max_active_jobs=1,
        min_work_free_bytes=0,
        min_spool_free_bytes=0,
        min_output_free_bytes=0,
        admission_timeout_s=10,
        drain_timeout_s=25,
        monitor_interval_s=0.1,
        profile=kwargs["profile"].to_dict(),
        final_source_format="capsule_v2",
        expected_recipe_id=make_recipe(
            encoder.descriptor(), preprocessing_recipe(256, 256)
        )["recipe_id"],
    )
    write_json(path, raw)
    cfg = full.load_config(path)
    cfg["_config_path"] = str(path)
    row = dict(
        episode_id=0,
        task_class="NavigateKitchen",
        source_fingerprint=kwargs["source_fingerprint"],
        spatial_frames=[0, 10, 20],
        expected_relative_output="tasks/NavigateKitchen/episodes/episode_000000",
        layout_id=0,
        spatial_state_count=3,
    )
    target = Path(cfg["output_root"]) / row["expected_relative_output"]
    worker_cfg = SimpleNamespace(
        work_root=Path(cfg["work_root"]),
        output_root=Path(cfg["output_root"]),
        sim_direct_geometry_only=True,
        sim_color_only=True,
        keep_work=False,
    )
    monkeypatch.setattr(producer.plan, "discover", lambda *a, **k: ([row], {0: 1}))
    monkeypatch.setattr(
        full, "preflight", lambda cfg: dict(scope="TEST_ONLY_RESOURCE_PREFLIGHT")
    )
    monkeypatch.setattr(full.shutil, "which", lambda name: None)
    original = full.consumer_command
    allow = Path(cfg["run_root"]) / "ALLOW_TEST_CONSUME"
    code = """import sys,time
from pathlib import Path
import os
if '--execute' in sys.argv:
    stop=Path(sys.argv[sys.argv.index('--stop-file')+1])
    while not Path(sys.argv[1]).exists():
        if stop.exists(): raise SystemExit(75)
        time.sleep(.01)
from g2.tests.test_view_vae_builder import FakeEncoder
import g2.latent_cache.encoding as encoding
encoding.WanSingleFrameEncoder=lambda *a,**k:FakeEncoder()
from g2.latent_cache import ledger_archive
original_archive=ledger_archive.archive
def stop_once(phase):
    marker=Path(sys.argv[1]).parent/'CRASH_TEST_RETIRE_ONCE'
    if phase=='capsule_published:vae_cache/manifest.json' and marker.exists():
        marker.unlink()
        os._exit(77)
ledger_archive.archive=lambda *a,**k:original_archive(*a,**dict(k,failpoint=stop_once))
from tools.g2.consume_spatial_view_vae_events import main
raise SystemExit(main(sys.argv[2:]))
"""
    monkeypatch.setattr(
        full,
        "consumer_command",
        lambda cfg, action, stop: [
            sys.executable,
            "-c",
            code,
            str(allow),
            *original(cfg, action, stop)[3:],
        ],
    )
    first = [True]

    def native_worker(self, command, check=False):
        if producer._completed(full.producer_args(cfg), row, kwargs["profile"]):
            return subprocess.CompletedProcess(command, 0)
        spool = EventSpool.open(cfg["spool_root"])
        job = spool.register(
            target,
            episode_key="NavigateKitchen/episode_000000",
            source_fingerprint=row["source_fingerprint"],
            profile_id=kwargs["profile"].to_dict()["profile_id"],
        )
        with producer_work(row, worker_cfg, kwargs["profile"], spool, job) as work:
            (work / "TEST_ONLY_NATIVE_WORK").write_bytes(b"x" * 4096)
            if not target.exists():
                package_stage_a(
                    destination=target,
                    event_sink=lambda e: spool.enqueue(job, e),
                    **kwargs,
                )
            spool.offer_source(job)
            if first[0]:
                write_json(
                    Path(cfg["run_root"]) / "STOP_REQUESTED.json",
                    dict(config_id=cfg["config_id"]),
                )
                first[0] = False
        return subprocess.CompletedProcess(command, 75)

    monkeypatch.setattr(full.Supervisor, "worker", native_worker)
    assert full.run(cfg) == 75
    assert (target / final.FULL).exists() and not (target / final.CAPSULE).exists()
    allow.write_text("consume")
    (Path(cfg["run_root"]) / "CRASH_TEST_RETIRE_ONCE").write_text("one hard exit")
    with pytest.raises(CacheError, match="consumer exited"):
        full.run(cfg, resume=True)
    assert (
        (target / final.JOURNAL).exists()
        and (target / final.FULL).exists()
        and not (target / "COMPLETE.json").exists()
    )
    # The third invocation must repair the transaction before the real planner
    # attempts to inspect its temporarily mixed v1/v2 source/cache markers.
    assert full.run(cfg, resume=True) == 0
    assert not (target / final.FULL).exists() and (target / final.CAPSULE).is_file()
    assert not episode_work_path(row, worker_cfg, kwargs["profile"]).exists()
    spool = EventSpool.open(cfg["spool_root"])
    assert spool.stats()["completed_jobs"] == 1 and spool.stats()["active_jobs"] == 0
    assert read_json(Path(cfg["run_root"]) / "result.json")["phase"] == "DONE"
    assert verify_cli.main(["--episode-root", str(target), "--file-bytes"]) == 0


def test_capacity_counts_and_missing_task_coverage_hold_even_if_budget_fits(tmp_path):
    kwargs, target, encoder, spool, job = capsule_case(tmp_path / "case")
    complete_working(kwargs, target, encoder, spool, job)
    old = tmp_path / "old"
    old_target = old / "tasks/NavigateKitchen/episodes/episode_000000"
    import shutil

    shutil.copytree(target, old_target)
    other = old / "tasks/CloseFridge/episodes/episode_000001"
    other.mkdir(parents=True)
    write_json(
        other / "episode_manifest.json",
        dict(task_class="CloseFridge", episode_id=1, states=[]),
    )
    write_json(other / "COMPLETE.json", dict(complete=True))
    (other / "test.png").write_bytes(b"TEST_ONLY_COUNTED_BYTES_NOT_AN_IMAGE")
    assert spool.adopt_completed(job)
    report = capacity_report(
        old,
        Path(spool.source_policy["output_root"]),
        available_bytes=10**12,
        reserve_bytes=8 * 1024**3,
        expected_episodes=2,
        expected_tasks=2,
    )
    assert report["candidate_bound_fits"] and report["verdict"] == "HOLD_CAPACITY"
    assert (
        report["missing_new_task_samples"] == ["CloseFridge"]
        and report["full_production_authorized"] is False
    )
    counts = corpus_bytes(old)
    assert counts["episode_count"] == 2 and counts["task_count"] == 2
    assert counts["logical_bytes"] == sum(
        p.stat().st_size for p in old.rglob("*") if p.is_file()
    )
    assert counts["by_task"]["NavigateKitchen"]["files_by_category"]["png"] == 5
    before = episode_bytes(old_target, include_files=True)
    after = episode_bytes(target, include_files=True)
    assert (
        before["bytes_by_category"]["working_source"] > 0
        and after["bytes_by_category"].get("working_source", 0) == 0
    )
    assert after["bytes_by_category"]["latent"] == before["bytes_by_category"]["latent"]
    assert (
        capacity_cli.main(
            ["--old-root", str(old), "--output", str(old / "unsafe_report.json")]
        )
        == 2
    )
    out = tmp_path / "private_capacity.json"
    assert capacity_cli.main(["--old-root", str(old), "--output", str(out)]) == 0
    assert read_json(out)["logical_bytes"] == counts["logical_bytes"]
    assert capacity_cli.main(["--old-root", str(old), "--output", str(out)]) == 2


def test_retirement_policy_refuses_same_disk_archive_protected_paths_and_legacy(
    tmp_path,
):
    kwargs, target, encoder, spool, job = capsule_case(tmp_path)
    policy = dict(spool.source_policy)
    policy.update(
        keep_full_audit=True,
        audit_archive_root=str(tmp_path / "archive"),
        audit_retention_policy="TEST_ONLY_EXTERNAL_RETENTION",
    )
    with pytest.raises(CacheError, match="another filesystem"):
        validate_policy(policy, spool.root)
    policy.update(audit_archive_root=policy["output_root"])
    with pytest.raises(CacheError):
        validate_policy(policy, spool.root)
    policy = dict(
        spool.source_policy,
        keep_full_audit=False,
        audit_archive_root=str(tmp_path / "hidden_archive"),
    )
    with pytest.raises(CacheError, match="hide"):
        validate_policy(policy, spool.root)
    policy = dict(spool.source_policy, output_root=str(tmp_path / "fixture"))
    with pytest.raises(CacheError, match="protected"):
        validate_policy(policy, spool.root)
    link = tmp_path / "linked_output"
    link.symlink_to(spool.source_policy["output_root"], target_is_directory=True)
    with pytest.raises(CacheError, match="symlink"):
        validate_policy(dict(spool.source_policy, output_root=str(link)), spool.root)
    assert verify_cli.main(["--episode-root", str(tmp_path / "fixture/published")]) == 2


def test_new_tools_help_does_not_import_wan_or_load_model(tmp_path):
    for tool in (
        "verify_spatial_source_index",
        "audit_spatial_capacity",
        "resume_spatial_source_retirement",
    ):
        code = f"import runpy,sys;sys.argv=['{tool}','--help'];runpy.run_module('tools.g2.{tool}',run_name='__main__')"
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=20,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=""),
        )
        assert result.returncode == 0 and "usage:" in result.stdout
