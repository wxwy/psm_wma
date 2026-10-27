"""Exercise real CLI/store/cache wiring with no HTTP/model/simulator execution."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import robocasa_resume_cli as cli
import v3_evaluation_identity as legacy_identity
from robocasa_episode_resume import model_identity

from tools.v3 import robocasa_resume_store_test as helpers


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    checkpoint = tmp_path / "checkpoint"
    helpers.make_model(checkpoint)
    config = tmp_path / "config.yaml"
    config.write_text("action_chunk_size: 16\n")
    tasks = []
    for name in ("CloseFridge", "NavigateKitchen"):
        directory = tmp_path / "datasets" / name
        (directory / "extras").mkdir(parents=True)
        (directory / "extras/dataset_meta.json").write_text(json.dumps({"env_args": {"env_name": name}}))
        tasks.append((name, directory))
    args = SimpleNamespace(
        checkpoint_path=checkpoint,
        config_file=config,
        output_dir=tmp_path / "run",
        dataset_root=tmp_path / "datasets",
        tasks="all",
        list_tasks=False,
        expected_tasks=2,
        gpus="0,1",
        resume=False,
        dry_run=False,
        allow_relocated_legacy_checkpoint=False,
        num_steps=30,
        action_horizon=16,
        guidance=1.0,
        seed=0,
        num_test_episodes=3,
        base_port=8880,
        server_python=Path(sys.executable),
        sim_python=Path(sys.executable),
        save_rollout_mp4=False,
        save_generated_video="none",
        save_init_png=False,
        server_lifecycle="per_task",
        on_infrastructure_error="stop",
        server_start_timeout_s=10,
        predict_request_timeout_s=10,
        episode_wall_timeout_s=10,
        task_wall_timeout_s=10,
        terminate_grace_s=1,
        vendor_lock=tmp_path / "not-read-lock",
        asset_manifest=None,
        resolved_config={"synthetic": True},
    )
    reads, execution_calls, ports = [], [], []

    def sha(path):
        reads.append(Path(path))
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def bundle(**kwargs):
        observed = kwargs["verified_model_identity"]
        model_identity.verify_model_observation(observed)
        runtime = {"schema": "psm_robocasa_runtime_v1", "synthetic": True}
        runtime["digest"] = hashlib.sha256(helpers.canonical(runtime)).hexdigest()
        body = {
            "schema": "psm_v3_eval_identity_vendor_v1",
            "root_sha": "1" * 40,
            "child_sha": "2" * 40,
            "checkpoint": str(checkpoint),
            "model_metadata_sha256": observed["parameters"]["checkpoint"]["metadata_sha256"],
            "model_shard_stat_witnesses": observed["observed_checkpoint_stats"],
            "config_sha256": sha(config),
            "tasks": [
                {"task": name, "dataset_dir": str(path), "env_metadata_sha256": sha(path / "extras/dataset_meta.json")}
                for name, path in tasks
            ],
            "protocol": kwargs["protocol"],
            "evaluation_runtime": runtime,
        }
        return {
            "manifest": {"identity": body, "digest": hashlib.sha256(helpers.canonical(body)).hexdigest()},
            "runtime_probe_evidence": {"mocked": True},
        }

    api = SimpleNamespace(
        ROOT=ROOT,
        CHILD=ROOT / "cosmos-framework",
        discover_task_datasets=lambda *args: tasks,
        launch_environment=lambda cache: {},
        build_verified_evaluation_identity=bundle,
        require_free_ports=lambda value: ports.append(value),
        atomic_write_json=helpers.write,
        task_video_files=lambda directory: {"rollout_mp4s": [], "generated_mp4s": []},
        export_videos=lambda *args, **kwargs: {"status": "NO_SYNTHETIC_MEDIA", "index_file": None},
        server_argv=lambda *args: ["not-executed-server"],
        simulator_argv=lambda *args: ["not-executed-simulator"],
        sha256_file=Mock(side_effect=AssertionError("per-batch full config/task hash forbidden")),
    )
    monkeypatch.setattr(
        cli,
        "_view_provenance",
        lambda queue_api: {"source_root": "1" * 40, "source_child": "2" * 40, "runtime_probed": False},
    )
    return args, api, config, tasks, reads, execution_calls, ports


def install_no_execution(monkeypatch, prepared, mutation=None):
    args, api, config, tasks, reads, calls, ports = prepared

    def execute(**kwargs):
        calls.append(len(kwargs["jobs"]))
        errors = []
        for job in kwargs["jobs"]:
            for phase in ("pre_model_load", "post_model_load", "pre_commit"):
                if mutation == phase:
                    config.write_text(config.read_text() + "# injected mutation\n")
                try:
                    kwargs["verify_inputs"](job, phase)
                except ValueError as error:
                    errors.append({"stage": phase, "task": job["task"], "error": str(error)})
                    break
        # No completion is invented: no native/model/server/Episode executed.
        return {"errors": errors, "jobs": [], "synthetic_execution_disabled": True}

    monkeypatch.setattr(cli, "execute_planned_batches", execute)


def test_real_cli_cold_and_warm_pending_resume_guard_multiple_batches_without_payload_or_hash_repeats(
    prepared, monkeypatch
):
    args, api, config, tasks, reads, calls, ports = prepared
    install_no_execution(monkeypatch, prepared)
    assert cli.prepare_resume(args, {}, queue_api=api) == 1  # PARTIAL, not fake successful Episodes.
    first = helpers.read(helpers.read(args.output_dir / "latest_invocation.json")["summary_path"])
    assert first["checkpoint_reads"][0]["cache_hit"] is False
    assert first["invocation_input_verification"]["subsequent_guard_checks"] == 8
    assert len(reads) == 3 and calls == [2] and len(ports) == 1
    args.resume = True
    monkeypatch.setattr(model_identity, "_read_hash", Mock(side_effect=AssertionError("warm model bytes read")))
    assert cli.prepare_resume(args, {}, queue_api=api) == 1
    second = helpers.read(helpers.read(args.output_dir / "latest_invocation.json")["summary_path"])
    assert second["checkpoint_reads"][0]["cache_hit"] is True
    assert second["checkpoint_reads"][0]["model_payload_bytes_read"] == 0
    assert len(reads) == 6  # One initial config+each task validation per invocation, no batch hashes.
    assert second["completed"] == second["executed"] == 0 and second["status"] == "PARTIAL"


@pytest.mark.parametrize("phase", ["pre_model_load", "post_model_load", "pre_commit"])
def test_real_cli_mutation_guard_still_denies_commit_and_writes_non_success(prepared, monkeypatch, phase):
    args, api, *_ = prepared
    install_no_execution(monkeypatch, prepared, mutation=phase)
    assert cli.prepare_resume(args, {}, queue_api=api) == 1
    report = helpers.read(helpers.read(args.output_dir / "latest_invocation.json")["summary_path"])
    assert report["status"] == "PARTIAL" and report["completed"] == 0
    assert any("config file changed during" in row["error"] for row in report["worker_errors"].values())


def test_real_cli_readonly_cold_and_warm_do_not_write_namespace_cache_or_locks(prepared, monkeypatch):
    args, api, *_ = prepared
    install_no_execution(monkeypatch, prepared)
    args.dry_run = True
    assert cli.prepare_resume(args, {}, queue_api=api) == 0
    assert not args.output_dir.exists()
    args.dry_run = False
    assert cli.prepare_resume(args, {}, queue_api=api) == 1
    before = helpers.snapshot(args.output_dir)
    args.dry_run, args.resume = True, True
    monkeypatch.setattr(model_identity, "_read_hash", Mock(side_effect=AssertionError("warm model read")))
    assert cli.prepare_resume(args, {}, queue_api=api) == 0
    assert helpers.snapshot(args.output_dir) == before


def test_manifest_reuses_verified_metadata_SHA_with_identical_legacy_identity(tmp_path, monkeypatch):
    checkpoint = tmp_path / "checkpoint"
    helpers.make_model(checkpoint)
    config = tmp_path / "config.yaml"
    config.write_text("synthetic")
    directory = tmp_path / "dataset"
    (directory / "extras").mkdir(parents=True)
    (directory / "extras/dataset_meta.json").write_text("{}")
    monkeypatch.setattr(
        legacy_identity,
        "_git",
        lambda root, *args: "160000 commit " + "b" * 40 + "\tcosmos-framework"
        if args[0] == "ls-tree"
        else ""
        if args[0] == "status"
        else "b" * 40,
    )
    monkeypatch.setattr(legacy_identity.subprocess, "check_output", lambda *args, **kwargs: "")
    params = dict(
        root=tmp_path,
        checkpoint=checkpoint,
        config_file=config,
        tasks=[("CloseFridge", directory)],
        protocol={"num_steps": 30, "R": 16, "guidance": 1.0},
    )
    original = legacy_identity.build_evaluation_identity(**params)
    observed = model_identity.build_model_identity(checkpoint=checkpoint, num_steps=30, action_horizon=16, guidance=1.0)
    sha = legacy_identity.sha256_file

    def forbid_model(path):
        assert not Path(path).is_relative_to(checkpoint), "bundle must not reread any model byte"
        return sha(path)

    monkeypatch.setattr(legacy_identity, "sha256_file", forbid_model)
    assert legacy_identity.build_evaluation_identity(**params, verified_model_identity=observed) == original
    wrong = copy.deepcopy(params)
    wrong["protocol"]["guidance"] = 2.0
    with pytest.raises(ValueError, match="differs from evaluation protocol"):
        legacy_identity.build_evaluation_identity(**wrong, verified_model_identity=observed)


def test_cold_bundle_failure_cannot_publish_a_success_cache(prepared):
    args, api, config, *_ = prepared
    original = api.build_verified_evaluation_identity

    def racing_bundle(**kwargs):
        result = original(**kwargs)
        config.write_text("changed after full config hash")
        return result

    api.build_verified_evaluation_identity = racing_bundle
    with pytest.raises(ValueError, match="changed during initial_verified_bundle"):
        cli.prepare_resume(args, {}, queue_api=api)
    assert not (args.output_dir / "_resume_v2/input_verification.json").exists()
    assert not (args.output_dir / "_resume_v2/model_identity.json").exists()
