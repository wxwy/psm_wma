"""CPU-only launcher argv and off-mode inference identity. Never starts a server."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from serve_v3_matched_no_ttt import GENERATION_KEYS, main, server_command

ROOT = Path(__file__).resolve().parents[2]


def profile(tmp_path, *, world_size=8, ga=2):
    job = tmp_path / "no_ttt_job"
    model = job / "checkpoints/iter_000000100/model"
    model.mkdir(parents=True)
    (model / ".metadata").write_bytes(b"synthetic metadata marker, no real DCP")
    (model / "__0_0.distcp").write_bytes(b"synthetic shard marker, not model weights")
    config = {
        "model": {
            "config": {
                "local_memory_enabled": False,
                "parallelism": {
                    "data_parallel_shard_degree": world_size,
                    "data_parallel_replicate_degree": 1,
                },
            },
        },
        "optimizer": {"keys_to_select": GENERATION_KEYS},
        "trainer": {"grad_accum_iter": ga},
    }
    config["dataloader_train"] = {
        "dataloader": {
            "datasets": {
                "robocasa": {
                    "dataset": {
                        "chunk_length": 16,
                        "camera_set": "left_wrist",
                        "use_state": True,
                        "use_base_action": True,
                        "base_encoding": "raw",
                        "max_action_dim": 64,
                        "mode": "wam",
                        "action_normalization": None,
                        "fps": 20,
                    }
                }
            }
        }
    }
    config_path = job / "config.yaml"
    config_path.write_text(yaml.safe_dump(config))
    semantic = {
        "training_profile": "matched_no_ttt_v1",
        "contract": {
            "raw_action_dim": 15,
            "state_dim": 15,
            "h_pred": 16,
            "consumer_frames": 17,
            "t": 16,
            "b": 8,
            "ga": ga,
            "world_size": world_size,
        },
    }
    identity = {
        "schema": "corrected_phase5_f0_v1",
        "namespace": str(job),
        "semantic": semantic,
        "semantic_digest": hashlib.sha256(
            json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "diagnostic_only_do_not_resume": False,
        "canonical_config_sha256": {"config.yaml": hashlib.sha256(config_path.read_bytes()).hexdigest()},
    }
    (job / "v3_job_identity.json").write_text(json.dumps(identity))
    value = yaml.safe_load((ROOT / "configs/eval/robocasa_matched_no_ttt.example.yaml").read_text())
    value.update(checkpoint=str(model.parent), config_file=str(config_path))
    path = tmp_path / "profile.yaml"
    path.write_text(yaml.safe_dump(value))
    return path, value, job, config, identity


def test_server_dry_run_binds_off_raw15_state_config_and_chunk16(tmp_path, capsys, monkeypatch):
    path, value, job, *_ = profile(tmp_path)
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    def forbidden(*args):
        pytest.fail("dry-run launched a server")

    monkeypatch.setattr(os, "execv", forbidden)
    main(["--config", str(path), "--dry-run"])
    result = json.loads(capsys.readouterr().out)
    args = result["argv"]
    assert args[args.index("--local-memory-mode") + 1] == "off"
    assert args[args.index("--action-chunk-size") + 1] == "16"
    assert args[args.index("--raw-action-dim") + 1] == "15"
    assert args[args.index("--config-file") + 1] == str(job / "config.yaml")
    assert result["model_loaded"] is False
    assert {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize(("world_size", "ga"), [(8, 2), (4, 4)])
def test_off_inference_accepts_both_approved_batch_matched_profiles(tmp_path, world_size, ga):
    path, _values, _job, _config, _identity = profile(tmp_path, world_size=world_size, ga=ga)
    command = server_command(path)
    assert "--local-memory-mode" in command
    assert command[command.index("--local-memory-mode") + 1] == "off"
    assert command[command.index("--action-chunk-size") + 1] == "16"


@pytest.mark.parametrize(
    "damage",
    [
        "world_only",
        "ga_only",
        "fsdp_shard_only",
        "grad_accum_only",
        "replicate_degree",
    ],
)
def test_world4_off_inference_rejects_cross_profile_or_saved_config_drift(tmp_path, damage):
    path, _values, job, config, identity = profile(tmp_path, world_size=4, ga=4)
    if damage == "world_only":
        identity["semantic"]["contract"]["world_size"] = 8
    elif damage == "ga_only":
        identity["semantic"]["contract"]["ga"] = 2
    elif damage == "fsdp_shard_only":
        config["model"]["config"]["parallelism"]["data_parallel_shard_degree"] = 8
    elif damage == "grad_accum_only":
        config["trainer"]["grad_accum_iter"] = 2
    else:
        config["model"]["config"]["parallelism"]["data_parallel_replicate_degree"] = 2
    if damage.endswith("_only") and damage in {"world_only", "ga_only"}:
        identity["semantic_digest"] = hashlib.sha256(
            json.dumps(identity["semantic"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    else:
        config_file = job / "config.yaml"
        config_file.write_text(yaml.safe_dump(config))
        identity["canonical_config_sha256"]["config.yaml"] = hashlib.sha256(config_file.read_bytes()).hexdigest()
    (job / "v3_job_identity.json").write_text(json.dumps(identity))
    with pytest.raises(ValueError, match="No-TTT"):
        server_command(path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("local_memory_mode", "required"),
        ("local_memory_mode", False),
        ("action_chunk_size", 32),
        ("raw_action_dim", 12),
        ("fps", 15),
        ("max_action_dim", 15),
        ("num_steps", 0),
        ("port", 65536),
        ("guidance", float("nan")),
    ],
)
def test_reject_wrong_inference_profile(tmp_path, field, value):
    path, values, *_ = profile(tmp_path)
    values[field] = value
    path.write_text(yaml.safe_dump(values))
    with pytest.raises(ValueError):
        server_command(path)


@pytest.mark.parametrize(
    "damage",
    [
        "g1_identity",
        "enabled_local",
        "wrong_optimizer",
        "config_changed",
        "foreign_checkpoint",
        "missing_metadata",
        "missing_shards",
        "diagnostic",
        "semantic_digest",
    ],
)
def test_reject_g1_or_wrong_checkpoint_config_identity(tmp_path, damage):
    path, values, job, config, identity = profile(tmp_path)
    if damage == "g1_identity":
        identity["semantic"] = {"root": "G1"}
    elif damage in ("enabled_local", "wrong_optimizer"):
        config = deepcopy(config)
        if damage == "enabled_local":
            config["model"]["config"]["local_memory_enabled"] = True
        else:
            config["optimizer"]["keys_to_select"].append("local_memory")
        (job / "config.yaml").write_text(yaml.safe_dump(config))
        identity["canonical_config_sha256"]["config.yaml"] = hashlib.sha256(
            (job / "config.yaml").read_bytes()
        ).hexdigest()
    elif damage == "config_changed":
        with (job / "config.yaml").open("a") as out:
            out.write("# changed canonical\n")
    elif damage == "foreign_checkpoint":
        values["checkpoint"] = str(tmp_path / "g1/checkpoints/iter_000012000")
    elif damage == "missing_metadata":
        (Path(values["checkpoint"]) / "model/.metadata").unlink()
    elif damage == "missing_shards":
        (Path(values["checkpoint"]) / "model/__0_0.distcp").unlink()
    elif damage == "diagnostic":
        identity["diagnostic_only_do_not_resume"] = True
    else:
        identity["semantic_digest"] = "wrong"
    (job / "v3_job_identity.json").write_text(json.dumps(identity))
    path.write_text(yaml.safe_dump(values))
    with pytest.raises((ValueError, FileNotFoundError)):
        server_command(path)


@pytest.mark.parametrize("phase,until", [("fresh", "30000"), ("fresh", "100"), ("resume", "500")])
def test_launcher_exact_world8_matched_contract_without_torchrun(tmp_path, phase, until):
    fake = tmp_path / "capture_python"
    fake.write_text(
        f'#!{sys.executable}\nimport json, os, sys\nprint(json.dumps({{"argv": sys.argv[1:], "cwd": os.getcwd(), "offline": os.environ["HF_HUB_OFFLINE"]}}))\n'
    )
    fake.chmod(0o755)
    env = dict(os.environ, PYTHON=str(fake), JOB_NAME="no_ttt_contract_test")
    for key in (
        "OUTPUT_ROOT",
        "SOURCE_ROOT",
        "CACHE_ROOT",
        "DATASET_INDEX_ROOT",
        "EDGE_POLICY_CHECKPOINT",
        "WAN_VAE_PATH",
        "BASE_CHECKPOINT_PATH",
        "EXPECTED_ROOT",
        "EXPECTED_CHILD",
    ):
        env[key] = str(tmp_path / (key + " with spaces"))
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/train_v3_matched_no_ttt.sh"), phase, until],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
        check=True,
    )
    payload = json.loads(result.stdout)
    argv = payload["argv"]
    assert "--no-ttt" in argv and "--nproc_per_node=8" in argv
    for key, value in {
        "--t": "16",
        "--b": "8",
        "--ga": "2",
        "--k": "4",
        "--world-size": "8",
        "--max-iter": "30000",
        "--warmup": "500",
        "--save-iter": "100",
        "--num-workers": "0",
        "--formal-execution-until": until,
        "--phase": phase,
        "--job-name": "no_ttt_contract_test",
    }.items():
        assert argv[argv.index(key) + 1] == value
    assert argv[argv.index("--base-checkpoint") + 1] == env["BASE_CHECKPOINT_PATH"]
    assert payload["cwd"] == str(ROOT / "cosmos-framework") and payload["offline"] == "1"


def test_launcher_rejects_g1_job_before_any_python():
    env = dict(os.environ, JOB_NAME="packed128_droid_fresh_g1_20261019", PYTHON="/must/not/run")
    for key in (
        "OUTPUT_ROOT",
        "SOURCE_ROOT",
        "CACHE_ROOT",
        "DATASET_INDEX_ROOT",
        "EDGE_POLICY_CHECKPOINT",
        "WAN_VAE_PATH",
        "BASE_CHECKPOINT_PATH",
        "EXPECTED_ROOT",
        "EXPECTED_CHILD",
    ):
        env[key] = "/synthetic"
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/train_v3_matched_no_ttt.sh"), "fresh", "30000"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert result.returncode == 2 and "no_ttt_" in result.stderr


@pytest.mark.parametrize(
    "key,value",
    [
        ("chunk_length", 32),
        ("use_state", False),
        ("camera_set", "left"),
        ("use_base_action", False),
        ("base_encoding", "ego"),
        ("action_normalization", "minmax"),
        ("fps", 15),
    ],
)
def test_rehashed_canonical_config_still_must_match_dataset_contract(tmp_path, key, value):
    path, _, job, config, identity = profile(tmp_path)
    config["dataloader_train"]["dataloader"]["datasets"]["robocasa"]["dataset"][key] = value
    (job / "config.yaml").write_text(yaml.safe_dump(config))
    identity["canonical_config_sha256"]["config.yaml"] = hashlib.sha256((job / "config.yaml").read_bytes()).hexdigest()
    (job / "v3_job_identity.json").write_text(json.dumps(identity))
    with pytest.raises(ValueError, match="dataset"):
        server_command(path)


@pytest.mark.parametrize("key,value", [("state_dim", 16), ("h_pred", 32), ("b", 128), ("ga", 1), ("world_size", 1)])
def test_resigned_semantic_identity_still_must_be_matched_profile(tmp_path, key, value):
    path, _, job, _, identity = profile(tmp_path)
    identity["semantic"]["contract"][key] = value
    identity["semantic_digest"] = hashlib.sha256(
        json.dumps(identity["semantic"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    (job / "v3_job_identity.json").write_text(json.dumps(identity))
    with pytest.raises(ValueError, match="Packed128"):
        server_command(path)

@pytest.mark.parametrize("phase,until", [("fresh", "100"), ("resume", "500"), ("fresh", "30000")])
def test_world4_ga4_launcher_uses_only_cuda_4567_and_does_not_request_git_sources(tmp_path, phase, until):
    fake = tmp_path / "capture_python4"
    fake.write_text(
        f'#!{sys.executable}\nimport json,os,sys\n'
        'print(json.dumps({"argv":sys.argv[1:],'
        '"cwd":os.getcwd(),"devices":os.environ["CUDA_VISIBLE_DEVICES"],'
        '"offline":os.environ["HF_HUB_OFFLINE"]}))\n'
    )
    fake.chmod(0o755)
    env = dict(os.environ, PYTHON=str(fake), JOB_NAME="no_ttt_contract_world4_ga4")
    for key in (
        "OUTPUT_ROOT",
        "SOURCE_ROOT",
        "CACHE_ROOT",
        "DATASET_INDEX_ROOT",
        "EDGE_POLICY_CHECKPOINT",
        "WAN_VAE_PATH",
        "BASE_CHECKPOINT_PATH",
    ):
        env[key] = str(tmp_path / (key + " with spaces"))
    # Obsolete pins must NOT control this standalone four-GPU launch.
    env.update(EXPECTED_ROOT="outdated", EXPECTED_CHILD="outdated", CUDA_VISIBLE_DEVICES="4,5,6,7")
    run = subprocess.run(
        ["bash", str(ROOT / "scripts/train_v3_matched_no_ttt_4gpu.sh"), phase, until],
        capture_output=True, text=True, env=env, check=True, timeout=15,
    )
    payload = json.loads(run.stdout)
    argv = payload["argv"]
    assert payload["devices"] == "4,5,6,7" and payload["offline"] == "1"
    assert payload["cwd"] == str(ROOT / "cosmos-framework")
    assert "--no-ttt" in argv and "--nproc_per_node=4" in argv
    for key, value in {
        "--world-size": "4",
        "--ga": "4",
        "--b": "8",
        "--t": "16",
        "--k": "4",
        "--num-workers": "0",
        "--max-iter": "30000",
        "--warmup": "500",
        "--save-iter": "100",
        "--formal-execution-until": until,
        "--phase": phase,
        "--job-name": "no_ttt_contract_world4_ga4",
    }.items():
        assert argv[argv.index(key) + 1] == value
    assert "--expected-root" not in argv and "--expected-child" not in argv
    assert argv[argv.index("--root-worktree") + 1] == str(ROOT)


def test_world4_launcher_runs_from_nongit_root_with_untracked_eval_docs_and_uses_project_venv(tmp_path):
    # Reproduce the DS_PRO blocker without touching the actual repository:
    # no .git at all, plus dirty-style untracked docs/eval/ reports.
    root = tmp_path / "psm_wma_v3"
    scripts = root / "scripts"
    child = root / "cosmos-framework"
    scripts.mkdir(parents=True)
    (child / "examples").mkdir(parents=True)
    (root / "docs/eval").mkdir(parents=True)
    (root / "docs/eval/robocasa_realrun_preflight_report_20261024.md").write_text("DS report\n")
    (child / "examples/psm_wma_robocasa_corrected_phase5.py").write_text("placeholder\n")
    launcher = scripts / "train_v3_matched_no_ttt_4gpu.sh"
    launcher.write_text((ROOT / "scripts/train_v3_matched_no_ttt_4gpu.sh").read_text())
    fake = child / ".venv/bin/python"
    fake.parent.mkdir(parents=True)
    fake.write_text(
        f'#!{sys.executable}\nimport json,os,sys\n'
        'print(json.dumps({"argv":sys.argv[1:],"exe":sys.argv[0],'
        '"visible":os.environ["CUDA_VISIBLE_DEVICES"]}))\n'
    )
    fake.chmod(0o755)
    env = dict(os.environ, JOB_NAME="no_ttt_simulated_world4_ga4", CUDA_VISIBLE_DEVICES="4,5,6,7")
    env.pop("PYTHON", None)
    for key in (
        "OUTPUT_ROOT", "SOURCE_ROOT", "CACHE_ROOT", "DATASET_INDEX_ROOT",
        "EDGE_POLICY_CHECKPOINT", "WAN_VAE_PATH", "BASE_CHECKPOINT_PATH",
    ):
        env[key] = str(tmp_path / key)
    call = subprocess.run(
        ["bash", str(launcher), "fresh", "100"],
        capture_output=True, text=True, check=True, env=env, timeout=10,
    )
    payload = json.loads(call.stdout)
    assert payload["visible"] == "4,5,6,7"
    assert payload["exe"] == str(fake)
    assert payload["argv"][payload["argv"].index("--root-worktree") + 1] == str(root)
    assert "--expected-root" not in payload["argv"]
    assert "--expected-child" not in payload["argv"]


@pytest.mark.parametrize(
    ("job", "devices"),
    [
        ("packed128_droid_fresh_g1_20261019", "4,5,6,7"),
        ("no_ttt_packed128_droid_fresh_30k", "4,5,6,7"),
        ("no_ttt_contract_world4_ga4", "0,1,2,3"),
    ],
)
def test_world4_launcher_rejects_g1_world8_or_wrong_gpus_before_python(tmp_path, job, devices):
    env = dict(
        os.environ, PYTHON="/must/not/run", JOB_NAME=job, CUDA_VISIBLE_DEVICES=devices,
    )
    for key in (
        "OUTPUT_ROOT",
        "SOURCE_ROOT",
        "CACHE_ROOT",
        "DATASET_INDEX_ROOT",
        "EDGE_POLICY_CHECKPOINT",
        "WAN_VAE_PATH",
        "BASE_CHECKPOINT_PATH",
    ):
        env[key] = str(tmp_path / key)
    run = subprocess.run(
        ["bash", str(ROOT / "scripts/train_v3_matched_no_ttt_4gpu.sh"), "fresh", "30000"],
        capture_output=True, text=True, env=env, timeout=10,
    )
    assert run.returncode == 2
    assert "4GPU profile" in run.stderr
