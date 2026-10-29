"""CPU launcher/profile admission; fake Python, no torchrun/model invocation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cosmos-framework"))
from cosmos_framework.utils.no_ttt_loader_profile import profile_from_args  # noqa: E402 - explicit worktree bootstrap
from examples import psm_wma_robocasa_corrected_phase5 as phase5  # noqa: E402
from examples.psm_wma_robocasa_phase5_f0_test import Serializer, _args, _config, _report  # noqa: E402


def setup(tmp_path):
    root = tmp_path / "not-a-git-worktree"
    (root / "scripts").mkdir(parents=True)
    child = root / "cosmos-framework"
    (child / "examples").mkdir(parents=True)
    (child / "examples/psm_wma_robocasa_corrected_phase5.py").write_text(
        "# not executed\n"
    )
    script = root / "scripts/train_v3_matched_no_ttt_4gpu.sh"
    script.write_bytes((ROOT / "scripts/train_v3_matched_no_ttt_4gpu.sh").read_bytes())
    fake = tmp_path / "fake-python"
    fake.write_text(
        f'#!{sys.executable}\nimport sys,json,os\nprint(json.dumps({{"argv":sys.argv[1:],"cwd":os.getcwd()}}))\n'
    )
    fake.chmod(0o755)
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("NOTTT_")
        and key not in ("JOB_NAME", "CUDA_VISIBLE_DEVICES")
    }
    env["PYTHON"] = str(fake)
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
    return script, env


@pytest.mark.parametrize("workers", [0, 1, 2, 4, 8])
def test_true_worker_flags_in_nongit_source_and_unchanged_zero_launcher(
    tmp_path, workers
):
    script, env = setup(tmp_path)
    env["NOTTT_LOADER_WORKERS"] = str(workers)
    result = subprocess.run(
        ["bash", str(script), "fresh", "100"],
        env=env,
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )
    payload = json.loads(result.stdout)
    argv = payload["argv"]
    assert "--expected-root" not in argv and "--expected-child" not in argv
    assert (
        argv[argv.index("--ga") + 1] == "4"
        and argv[argv.index("--world-size") + 1] == "4"
    )
    assert argv[argv.index("--num-workers") + 1] == "0"
    if workers:
        assert argv[argv.index("--no-ttt-loader-workers") + 1] == str(workers)
        assert (
            argv[argv.index("--job-name") + 1]
            == "no_ttt_packed128_droid_fresh_30k_world4_ga4"
        )
        parsed = phase5.parser().parse_args(argv[argv.index("--no-ttt") :])
        assert profile_from_args(parsed).persistent_workers is True
    else:
        assert "--no-ttt-loader-workers" not in argv
        baseline = subprocess.check_output(
            [
                "git",
                "show",
                "e6ae2084305a8c24d763d82b517984660cc73c30:scripts/train_v3_matched_no_ttt_4gpu.sh",
            ],
            cwd=ROOT,
        )
        script.write_bytes(baseline)
        old = subprocess.run(
            ["bash", str(script), "fresh", "100"],
            env=env,
            text=True,
            capture_output=True,
            check=True,
            timeout=10,
        )
        assert json.loads(old.stdout) == payload


@pytest.mark.parametrize(
    "change",
    [
        {"NOTTT_LOADER_WORKERS": "3"},
        {"NOTTT_LOADER_WORKERS": "4", "JOB_NAME": "no_ttt_wrong_world8_ga2"},
        {"NOTTT_LOADER_WORKERS": "8", "JOB_NAME": "packed128_droid_fresh_g1_20261019"},
        {"NOTTT_PREFETCH_FACTOR": "1"},
        {"NOTTT_PERSISTENT_WORKERS": "1"},
        {"NOTTT_LOADER_TIMEOUT_S": "1"},
        {"NOTTT_LOADER_WORKERS": "1", "NOTTT_PERSISTENT_WORKERS": "bad"},
    ],
)
def test_invalid_loader_or_non_nott_job_options_rejected_before_python(
    tmp_path, change
):
    script, env = setup(tmp_path)
    env.update(change)
    env["PYTHON"] = "/must/not/run"
    result = subprocess.run(
        ["bash", str(script), "resume", "500"],
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 2


@pytest.mark.parametrize("original_workers", [0, 2, 8])
def test_same_job_identity_ignores_loader_runtime_changes_but_still_checks_semantics(
    tmp_path, original_workers
):
    # Exercise an ordinary strict Job. The historical formal Job has an
    # explicit Owner identity exemption, independently covered by Phase5 tests.
    args = _args(
        tmp_path,
        "--no-ttt",
        "--world-size",
        "4",
        "--ga",
        "4",
        "--job-name",
        "no_ttt_worker_runtime_contract_world4_ga4",
    )
    semantic = {
        "training_profile": "matched_no_ttt_v1",
        "contract": {"world_size": 4, "ga": 4},
    }
    args.no_ttt_loader_workers = original_workers
    args.no_ttt_prefetch_factor = 1 if original_workers else None
    args.no_ttt_persistent_workers = True if original_workers else None
    args.no_ttt_loader_timeout_s = 120 if original_workers else None
    lifecycle = phase5.JobLifecycle(args, _report(args, semantic))
    lifecycle.write_config(_config(args), Serializer)
    lifecycle.close()
    path = phase5.job_namespace(args)
    before = {str(p): p.read_bytes() for p in path.rglob("*") if p.is_file()}
    args.phase = "resume"

    for workers, factor, persistent, timeout in (
        (0, None, None, None),
        (1, 1, True, 120),
        (2, 2, False, 90),
        (4, 1, True, 30),
        (8, 2, True, 180),
    ):
        args.no_ttt_loader_workers = workers
        args.no_ttt_prefetch_factor = factor
        args.no_ttt_persistent_workers = persistent
        args.no_ttt_loader_timeout_s = timeout
        assert profile_from_args(args).workers == workers
        assert phase5.check_job_namespace(args, semantic)["semantic"] == semantic

    assert {str(p): p.read_bytes() for p in path.rglob("*") if p.is_file()} == before
    assert (
        phase5._expected_source_identity(args)
        == ("nottt_world4_ga4_source_head_not_verified",) * 2
    )
    wrong = {
        "training_profile": "matched_no_ttt_v1",
        "contract": {"world_size": 8, "ga": 4},
    }
    with pytest.raises(ValueError, match="semantic"):
        phase5.check_job_namespace(args, wrong)


@pytest.mark.parametrize("from_workers,to_workers", [(0, 8), (8, 0), (2, 4), (8, 1)])
def test_launcher_resume_same_job_with_different_worker_count(
    tmp_path, from_workers, to_workers
):
    script, env = setup(tmp_path)

    def invoke(workers, phase):
        settings = dict(env, NOTTT_LOADER_WORKERS=str(workers))
        for key in (
            "NOTTT_PREFETCH_FACTOR",
            "NOTTT_PERSISTENT_WORKERS",
            "NOTTT_LOADER_TIMEOUT_S",
        ):
            settings.pop(key, None)
        result = subprocess.run(
            ["bash", str(script), phase, "500"],
            env=settings,
            text=True,
            capture_output=True,
            check=True,
            timeout=10,
        )
        argv = json.loads(result.stdout)["argv"]
        return argv, argv[argv.index("--job-name") + 1]

    fresh, original_job = invoke(from_workers, "fresh")
    resumed, resumed_job = invoke(to_workers, "resume")
    assert original_job == resumed_job == "no_ttt_packed128_droid_fresh_30k_world4_ga4"
    assert (
        fresh[fresh.index("--num-workers") + 1]
        == resumed[resumed.index("--num-workers") + 1]
        == "0"
    )
    if to_workers:
        assert resumed[resumed.index("--no-ttt-loader-workers") + 1] == str(to_workers)
    else:
        assert "--no-ttt-loader-workers" not in resumed


def test_explicit_prefetch_and_nonpersistent_cli_are_real_profile_options(tmp_path):
    script, env = setup(tmp_path)
    env.update(
        NOTTT_LOADER_WORKERS="2",
        NOTTT_PREFETCH_FACTOR="2",
        NOTTT_PERSISTENT_WORKERS="0",
        NOTTT_LOADER_TIMEOUT_S="30",
    )
    result = subprocess.run(
        ["bash", str(script), "fresh", "100"],
        env=env,
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )
    argv = json.loads(result.stdout)["argv"]
    args = phase5.parser().parse_args(argv[argv.index("--no-ttt") :])
    profile = profile_from_args(args)
    assert (
        profile.workers == 2
        and profile.prefetch_factor == 2
        and profile.persistent_workers is False
    )
    assert profile.timeout_s == 30
