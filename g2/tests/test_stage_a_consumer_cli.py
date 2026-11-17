"""A2 CLI/producer resume on CPU synthetic data; no model or GPU."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from g2.latent_cache.streaming import EventConsumer
from g2.offline import atomic_6views_run as producer
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.tests.test_stage_a_streaming import setup_case
from tools.g2 import build_spatial_view_vae_cache as build_cli
from tools.g2 import consume_spatial_view_vae_events as consume_cli
from tools.g2 import verify_spatial_view_vae_cache as verify_cli


def test_consumer_init_preflight_no_torch_model_or_gpu(tmp_path):
    weights = tmp_path / "weights.pth"
    weights.write_bytes(b"TEST_ONLY_DESCRIPTOR_NOT_A_CHECKPOINT")
    code = """import sys
from tools.g2.consume_spatial_view_vae_events import main
rc=main(sys.argv[1:])
assert 'torch' not in sys.modules
assert not any('wan' in x and 'tokenizer' in x for x in sys.modules)
raise SystemExit(rc)
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            "--spool-root",
            str(tmp_path / "spool"),
            "--weights",
            str(weights),
            "--device",
            "cpu",
            "--initialize",
        ],
        capture_output=True,
        text=True,
        timeout=20,
        env=dict(os.environ, CUDA_VISIBLE_DEVICES=""),
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["model_loaded"] is False and receipt["steps"] == 0


def test_new_profile_build_cli_plan_does_not_wait_for_complete(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(destination=target, **kwargs)
    weights = tmp_path / "weights.pth"
    weights.write_bytes(b"TEST_ONLY_NO_MODEL")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.g2.build_spatial_view_vae_cache",
            "--dataset-root",
            str(target),
            "--weights",
            str(weights),
            "--device",
            "cpu",
            "--height",
            "32",
            "--width",
            "32",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["vae_loaded"] is False
    assert receipt["results"][0]["physical_image_count"] == 5
    assert (
        not (target / "vae_cache").exists() and not (target / "COMPLETE.json").exists()
    )


def test_existing_posthoc_cli_publishes_new_profile_via_same_core(
    tmp_path, monkeypatch, capsys
):
    import g2.latent_cache.encoding as encoding

    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(destination=target, **kwargs)
    monkeypatch.setattr(encoding, "WanSingleFrameEncoder", lambda *a, **k: encoder)
    assert (
        build_cli.main(
            [
                "--dataset-root",
                str(target),
                "--weights",
                str(tmp_path / "TEST_ONLY"),
                "--device",
                "cpu",
                "--height",
                "32",
                "--width",
                "32",
                "--execute",
            ]
        )
        == 0
    )
    assert encoder.calls == 5 and validate_profile_episode(target)["profile_complete"]
    assert verify_cli.main(["--dataset-root", str(target)]) == 0
    assert '"records_checked": 5' in capsys.readouterr().out


def test_consumer_cli_one_resident_model_resume_and_pending_exit(
    tmp_path, monkeypatch, capsys
):
    import g2.latent_cache.encoding as encoding

    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(
        destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
    )
    monkeypatch.setattr(encoding, "WanSingleFrameEncoder", lambda *a, **k: encoder)
    args = [
        "--spool-root",
        str(spool.root),
        "--weights",
        str(tmp_path / "TEST_ONLY"),
        "--device",
        "cpu",
        "--height",
        "32",
        "--width",
        "32",
        "--idle-seconds",
        "0",
    ]
    assert consume_cli.main(args + ["--once"]) == 75
    assert encoder.calls == 1 and not (target / "COMPLETE.json").exists()
    spool.seal(job)
    assert consume_cli.main(args + ["--execute"]) == 0
    assert encoder.calls == 5 and validate_profile_episode(target)["profile_complete"]
    assert consume_cli.main(args + ["--execute"]) == 0
    assert encoder.calls == 5
    assert '"unfinished_jobs": 0' in capsys.readouterr().out


def test_original_producer_ready_resume_enqueues_without_rendering(
    tmp_path, monkeypatch
):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(destination=target, **kwargs)
    config = producer.WorkerConfig(
        nav_repo=tmp_path / "nav",
        nav_setup=tmp_path / "setup",
        native_binary=tmp_path / "native",
        python=Path(sys.executable),
        output_root=tmp_path,
        work_root=tmp_path / "work",
        keep_work=True,
        min_z=0.1,
        max_z=1.5,
        port=1234,
        gpu=0,
        robocasa_repo=tmp_path / "robocasa",
        robosuite_repo=tmp_path / "robosuite",
        output_profile=kwargs["profile"],
        vae_spool=spool.root,
    )

    def no_render(*a, **k):
        raise AssertionError("ready-source resume must not replay original producer")

    monkeypatch.setattr(producer, "stage", no_render)
    row = dict(
        episode_id=0,
        task_class="NavigateKitchen",
        source_fingerprint="a" * 64,
        expected_relative_output="published",
    )
    result = producer.produce_one(row, config)
    assert not result["profile_complete"] and spool.job_status(job) == "source_ready"
    while EventConsumer(spool, encoder).step():
        pass
    assert producer.produce_one(row, config)["profile_complete"]
    assert encoder.calls == 5


def test_consumer_failure_exit_is_not_success(tmp_path, monkeypatch):
    import g2.latent_cache.encoding as encoding

    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(
        destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
    )
    monkeypatch.setattr(encoding, "WanSingleFrameEncoder", lambda *a, **k: encoder)
    encoder.fail_at = 1
    args = [
        "--spool-root",
        str(spool.root),
        "--weights",
        str(tmp_path / "TEST_ONLY"),
        "--device",
        "cpu",
        "--height",
        "32",
        "--width",
        "32",
        "--idle-seconds",
        "0",
        "--execute",
    ]
    assert consume_cli.main(args) == 2
    assert (
        consume_cli.main(args) == 2
    )  # Existing failed job is reported, not silently skipped as success.
    assert not (target / "COMPLETE.json").exists()
    encoder.fail_at = None
    spool.retry(job)
    spool.seal(job)
    assert consume_cli.main(args) == 0
