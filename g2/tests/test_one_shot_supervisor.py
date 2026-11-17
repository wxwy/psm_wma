"""CPU-only official CLI, original unified queue and resource/stop contracts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from g2.io import digest, write_json
from g2.latent_cache import ledger_archive
from g2.latent_cache.contract import CacheError
from g2.offline import atomic_6views_run as producer
from g2.offline import full_production as full
from g2.offline.process_control import owned_groups, start_owned, terminate_owned
from g2.offline.task_entities import FIXTURE_RULES, OBJECT_RULES
from g2.tests.test_one_shot_ledger import (
    seed_verified_rows,
    sql_spool,
    sqlite_only_proof,
)
from g2.tests.test_stage_a_streaming import setup_case


def config_case(tmp_path):
    dirs = (
        "nav_repo",
        "robocasa_repo",
        "robosuite_repo",
        "raw_root",
        "flat_root",
        "depth_root",
        "output_root",
        "work_root",
        "spool_root",
        "run_root",
    )
    cfg = {key: str(tmp_path / key) for key in dirs}
    for key in dirs:
        Path(cfg[key]).mkdir(parents=True)
    for key in ("nav_setup", "native_binary", "mapping", "weights"):
        parent = (
            Path(cfg["nav_repo"])
            if key in ("nav_setup", "native_binary")
            else Path(cfg["flat_root"])
            if key == "mapping"
            else tmp_path
        )
        path = parent / (key + ".fixture")
        path.write_bytes(b"TEST_ONLY_NEVER_EXECUTED")
        if key == "native_binary":
            path.chmod(0o755)
        cfg[key] = str(path)
    cfg.update(
        python=sys.executable,
        root_sha="a" * 40,
        child_sha="b" * 40,
        nav_sha="c" * 40,
        mapping_sha256=digest(cfg["mapping"]),
        renderer_pythonpath=[str(tmp_path / "egl_only")],
    )
    Path(cfg["renderer_pythonpath"][0]).mkdir()
    path = tmp_path / "config.json"
    write_json(path, cfg)
    value = full.load_config(path)
    value["_config_path"] = str(path)
    return value, path


def test_default_full_config_is_b1_one_corpus_and_no_implicit_batch_or_delete(tmp_path):
    cfg, path = config_case(tmp_path)
    args = full.producer_args(cfg)
    assert args.gpus == [4, 5, 6, 7] and args.workers_per_gpu == 8
    assert (
        args.expected == 9126
        and args.batch_size == 100
        and args.episodes_per_task is None
    )
    assert args.managed_work_cleanup and args.require_prebuilt and args.require_depth
    assert args.vae_spool == Path(cfg["spool_root"]) and args.renderer_pythonpath
    assert (
        cfg["expected_selected_episodes"] == 9126 and cfg["expected_task_count"] == 18
    )
    env = full.isolated_env(cfg)
    renderer = full.isolated_env(cfg, renderer=True)
    assert cfg["renderer_pythonpath"][0] not in env["PYTHONPATH"]
    assert cfg["renderer_pythonpath"][0] in renderer["PYTHONPATH"]
    with pytest.raises(SystemExit) as stopped:
        full.main(["run", "--config", str(path)])
    assert stopped.value.code == 2  # A valid plan still needs the explicit action.
    bad = json.loads(path.read_text())
    bad["max_batch_size"] = 8
    write_json(path, bad)
    with pytest.raises(CacheError, match="unknown"):
        full.load_config(path)
    assert full.main(["run", "--config", str(path)]) == 2  # Bad config never launches.


@pytest.mark.parametrize(
    "change",
    [
        dict(renderer_gpus=[0, 1]),
        dict(workers_per_gpu=4),
        dict(expected_selected_episodes=48),
        dict(root_sha="main"),
    ],
)
def test_full_configuration_conflicts_reject(tmp_path, change):
    cfg, path = config_case(tmp_path)
    raw = json.loads(path.read_text())
    raw.update(change)
    write_json(path, raw)
    with pytest.raises(CacheError):
        full.load_config(path)


def test_original_queue_consumes_all_92_plan_packages_once(tmp_path, monkeypatch):
    cfg, _ = config_case(tmp_path)
    tasks = sorted(set(FIXTURE_RULES) | set(OBJECT_RULES))
    rows = [
        dict(
            episode_id=i,
            task_class=tasks[i % 18],
            source_fingerprint=f"{i:064x}",
            expected_relative_output=f"tasks/{tasks[i % 18]}/episodes/episode_{i:06d}",
        )
        for i in range(9126)
    ]
    plan_root = Path(cfg["run_root"]) / "plan"
    plan_root.mkdir()
    for start in range(0, 9126, 100):
        write_json(
            plan_root / f"batch_{start // 100:03d}.json",
            dict(renderer="f27", episodes=rows[start : start + 100]),
        )
    index = dict(episodes_total=9126, batches_total=92)
    write_json(Path(cfg["run_root"]) / "profile.json", cfg["profile"])
    monkeypatch.setattr(producer.plan, "discover", lambda *a, **k: (rows, {}))
    monkeypatch.setattr(producer.plan, "build", lambda *a, **k: index)
    executed = set()
    admitted = []
    results = []
    monkeypatch.setattr(
        producer, "_completed", lambda args, row, profile: row["episode_id"] in executed
    )
    args = full.producer_args(cfg)

    def run(command, check=False):
        eid = int(command[command.index("--episode-id") + 1])
        executed.add(eid)
        assert (
            "--renderer-pythonpath" in command and "--managed-work-cleanup" in command
        )
        return subprocess.CompletedProcess(command, 0)

    assert (
        producer.schedule(
            args,
            admission=lambda row: admitted.append(row["episode_id"]) or True,
            on_result=lambda row, status: results.append((row["episode_id"], status)),
            run_worker=run,
        )
        == 0
    )
    assert len(admitted) == len(set(admitted)) == len(executed) == 9126
    assert len(results) == 9126 and set(s for _, s in results) == {"DONE"}
    assert len(list(plan_root.glob("batch_*.json"))) == 92


def test_low_disk_and_active_job_admission_backpressure_preserve_work(
    tmp_path, monkeypatch
):
    cfg, _ = config_case(tmp_path)
    cfg.update(admission_timeout_s=0.05, min_work_free_bytes=10**30)
    spool = sql_spool(tmp_path / "sql")
    supervisor = full.Supervisor(cfg, spool, [])
    keep = Path(cfg["work_root"]) / "evidence"
    keep.write_text("preserve")
    with pytest.raises(CacheError, match="backpressure"):
        supervisor.admit(dict(task_class="NavigateKitchen", episode_id=0))
    assert keep.read_text() == "preserve"
    cfg.update(
        admission_timeout_s=5,
        min_work_free_bytes=0,
        min_spool_free_bytes=0,
        min_output_free_bytes=0,
        max_active_jobs=1,
    )
    supervisor = full.Supervisor(cfg, spool, [])
    monkeypatch.setattr(ledger_archive, "published_proof", sqlite_only_proof)
    job, _, _ = seed_verified_rows(spool, tmp_path / "data", 0)
    result = []
    thread = threading.Thread(
        target=lambda: result.append(
            supervisor.admit(dict(task_class="NavigateKitchen", episode_id=1))
        )
    )
    thread.start()
    time.sleep(0.05)
    assert thread.is_alive()
    ledger_archive.archive(spool, job)
    thread.join(5)
    assert result == [True]
    cfg.update(admission_timeout_s=0.05, min_output_free_bytes=10**30)
    supervisor = full.Supervisor(cfg, spool, [])
    with pytest.raises(CacheError, match="backpressure"):
        supervisor.admit(dict(task_class="NavigateKitchen", episode_id=2))
    assert keep.read_text() == "preserve"


def test_stop_resume_controls_only_tagged_process_groups(tmp_path):
    token = "d" * 64
    other = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True
    )
    owned = start_owned(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        env=os.environ.copy(),
        run_id=token,
        cwd=tmp_path,
    )
    try:
        deadline = time.monotonic() + 3
        while (
            owned.pid
            not in {p for members in owned_groups(token).values() for p in members}
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        assert owned.pid in {
            p for members in owned_groups(token).values() for p in members
        }
        terminate_owned(token, grace_seconds=0.1)
        assert owned.wait(timeout=3) < 0 and other.poll() is None
        assert not owned_groups(token)
    finally:
        if owned.poll() is None:
            owned.kill()
        other.terminate()
        other.wait(timeout=3)


def test_old_output_paths_mapping_and_stop_configuration_reject(tmp_path):
    cfg, path = config_case(tmp_path)
    (Path(cfg["output_root"]) / "old.png").write_bytes(b"preserve")
    with pytest.raises(CacheError, match="old/unowned"):
        full.claim_output(cfg)
    assert (Path(cfg["output_root"]) / "old.png").read_bytes() == b"preserve"
    cfg["work_root"] = cfg["flat_root"]
    with pytest.raises(CacheError, match="overlap"):
        full.validate_paths(cfg)
    assert full.main(["stop", "--config", str(path)]) == 2


def test_repository_launcher_is_inert_for_help_and_requires_manual_start(tmp_path):
    script = Path("scripts/g2/run_stage_a_full.sh").absolute()
    result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(
        [sys.executable, "-m", "tools.g2.run_stage_a_production", "--help"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert (
        result.returncode == 0
        and "resume" in result.stdout
        and "preflight" in result.stdout
    )


def test_one_run_stop_resume_real_consumer_ack_cleanup_and_final_audit(
    tmp_path, monkeypatch
):
    """Actual child consumer, source/cache validators and managed GC; TEST_ONLY
    rendering/encoding and resource preflight, never Wan/F27/GPU acceptance.
    """
    from g2.io import read_json
    from g2.latent_cache.builder import verify_episode
    from g2.latent_cache.contract import make_recipe, preprocessing_recipe
    from g2.latent_cache.streaming import EventSpool
    from g2.offline.stage_a import package_stage_a, validate_profile_episode
    from g2.offline.work_lifecycle import episode_work_path, producer_work

    cfg, path = config_case(tmp_path)
    monkeypatch.setattr(full.shutil, "which", lambda name: None)
    kwargs, _, encoder, _, _ = setup_case(tmp_path / "source_fixture")
    raw = json.loads(path.read_text())
    raw.update(
        sample_mode=True,
        expected_selected_episodes=1,
        expected_task_count=1,
        renderer_gpus=[4],
        workers_per_gpu=1,
        vae_gpu=4,
        max_active_jobs=1,
        min_work_free_bytes=0,
        min_spool_free_bytes=0,
        min_output_free_bytes=0,
        admission_timeout_s=10,
        drain_timeout_s=20,
        monitor_interval_s=0.1,
        profile=kwargs["profile"].to_dict(),
        expected_recipe_id=make_recipe(
            encoder.descriptor(), preprocessing_recipe(256, 256)
        )["recipe_id"],
    )
    write_json(path, raw)
    cfg = full.load_config(path)
    cfg["_config_path"] = str(path)
    target = Path(cfg["output_root"]) / "published"
    row = dict(
        episode_id=0,
        task_class="NavigateKitchen",
        source_fingerprint=kwargs["source_fingerprint"],
        spatial_frames=[0, 10, 20],
        expected_relative_output="published",
        layout_id=0,
        spatial_state_count=3,
    )
    worker_cfg = SimpleNamespace(
        work_root=Path(cfg["work_root"]),
        output_root=Path(cfg["output_root"]),
        sim_direct_geometry_only=True,
        sim_color_only=True,
        keep_work=False,
    )
    monkeypatch.setattr(
        full, "preflight", lambda cfg: dict(scope="TEST_ONLY_RESOURCE_PREFLIGHT")
    )
    monkeypatch.setattr(producer.plan, "discover", lambda *a, **k: ([row], {0: 1}))
    command = full.consumer_command
    allow = Path(cfg["run_root"]) / "ALLOW_TEST_CONSUME"
    child_code = """import sys,time
from pathlib import Path
if '--execute' in sys.argv:
    stop=Path(sys.argv[sys.argv.index('--stop-file')+1])
    while not Path(sys.argv[1]).exists():
        if stop.exists(): raise SystemExit(75)
        time.sleep(.01)
from g2.tests.test_view_vae_builder import FakeEncoder
import g2.latent_cache.encoding as encoding
encoding.WanSingleFrameEncoder=lambda *a,**k: FakeEncoder()
from tools.g2.consume_spatial_view_vae_events import main
raise SystemExit(main(sys.argv[2:]))
"""
    monkeypatch.setattr(
        full,
        "consumer_command",
        lambda cfg, action, stop: [
            sys.executable,
            "-c",
            child_code,
            str(allow),
            *command(cfg, action, stop)[3:],
        ],
    )
    first = [True]

    def simulated_native_worker(self, command, check=False):
        assert "--manual-start" in command and "--allow-experimental" in command
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
            (work / "TEST_ONLY_NATIVE.bin").write_bytes(b"x" * 4096)
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

    monkeypatch.setattr(full.Supervisor, "worker", simulated_native_worker)
    assert full.run(cfg) == 75
    spool = EventSpool.open(cfg["spool_root"])
    assert spool.stats()["active_jobs"] == 1 and not (target / "COMPLETE.json").exists()
    work = episode_work_path(row, worker_cfg, kwargs["profile"])
    assert work.exists()
    stable_manifest = (Path(cfg["run_root"]) / "run_manifest.json").read_bytes()
    allow.write_text("consume")
    assert full.run(cfg, resume=True) == 0
    assert (Path(cfg["run_root"]) / "run_manifest.json").read_bytes() == stable_manifest
    assert not work.exists() and spool.stats()["active_jobs"] == 0
    assert spool.stats()["completed_jobs"] == 1 and spool.stats()["active_records"] == 0
    assert validate_profile_episode(target)["profile_complete"]
    checked = verify_episode(target, reencoder=encoder)
    assert checked["records_checked"] == 5 and checked["max_abs_error"] == 0
    result = read_json(Path(cfg["run_root"]) / "result.json")
    assert (
        result["phase"] == "DONE"
        and result["complete"]
        and not result["training_ready"]
    )
