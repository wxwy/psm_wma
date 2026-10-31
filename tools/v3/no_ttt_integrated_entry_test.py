"""Minimal shell -> console -> approved CPU Trainer-binding composition checks.

The torchrun executable is replaced, not the shell, console, profile parser or
Trainer.bind_grouped_stream. No model/optimizer/training/DCP or GPU is started.
Only AsyncRecipe metadata and the Producer inputs are synthetic. Worker spawn
and full-state Resume remain covered by the separately approved Issue12 gate.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _receive_launch():
    import torch

    from cosmos_framework.model.generator.mot.robocasa_exact_window_local import (
        ExactWindowRankPlanner,
    )
    from cosmos_framework.trainer import matched_no_ttt as module
    from cosmos_framework.trainer.no_ttt_async_loader import NoTTTAsyncLoader
    from cosmos_framework.trainer.no_ttt_async_recipe import AsyncRecipe
    from cosmos_framework.trainer.no_ttt_async_test_support import (
        SyntheticAsyncRecipe,
        build_synthetic_producer,
    )
    from cosmos_framework.trainer.no_ttt_cpu_loader import (
        RawRecipe,
        _require_same_rng,
        _rng_snapshot,
    )
    from cosmos_framework.utils.no_ttt_loader_profile import profile_from_args

    assert torch.version.cuda is None  # Never let this shim become a GPU smoke.
    assert Path(module.__file__).resolve().is_relative_to(ROOT / "cosmos-framework")
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-ttt", action="store_true")
    parser.add_argument("--no-ttt-loader-workers", type=int, default=0)
    parser.add_argument("--no-ttt-prefetch-factor", type=int)
    parser.add_argument("--no-ttt-loader-timeout-s", type=float)
    parser.add_argument(
        "--no-ttt-persistent-workers", action="store_true", default=None
    )
    parser.add_argument("--job-name")
    for name in ("world-size", "ga", "b", "t"):
        parser.add_argument("--" + name, type=int)
    args, _ = parser.parse_known_args()
    profile = profile_from_args(args)  # Production profile and namespace checks.
    producer = build_synthetic_producer(count=64, t=args.t, world=args.world_size)
    planner = ExactWindowRankPlanner(
        producer.catalog,
        rank=0,
        world_size=args.world_size,
        b_stream=args.b,
        active_ga=args.ga,
        seed=83,
    )
    trainer = object.__new__(module.MatchedNoTTTTrainer)
    trainer.config = SimpleNamespace(trainer=SimpleNamespace(grad_accum_iter=args.ga))
    trainer.callbacks = SimpleNamespace(_callbacks=[])
    metadata_calls = []

    def metadata(cls, selected, selected_profile):
        assert selected is producer and selected_profile is profile
        metadata_calls.append(profile.workers)
        return SyntheticAsyncRecipe(count=64, t=args.t, world=args.world_size)

    with (
        patch.object(AsyncRecipe, "from_producer", classmethod(metadata)),
        patch.object(
            RawRecipe, "from_producer", side_effect=AssertionError("old RAW path")
        ),
    ):
        before = _rng_snapshot()
        trainer.bind_grouped_stream(
            planner,
            producer,
            config_digest=producer.config_digest,
            loader_profile=profile,
        )
        _require_same_rng(before)
    loader = trainer._no_ttt_loader
    try:
        if profile.workers:
            assert type(loader) is NoTTTAsyncLoader
            assert loader.iterator is None and loader.context.processes == []
            assert metadata_calls == [profile.workers]
        else:
            assert loader is None and metadata_calls == []
        assert trainer.callbacks._callbacks[0].checkpoint_component == "dataloader"
        observation = dict(
            argv=sys.argv[1:],
            cwd=os.getcwd(),
            profile=profile.identity(),
            binding=module._binding(trainer),
            loader=None if loader is None else type(loader).__name__,
            metadata_calls=metadata_calls,
            imported_trainer=str(Path(module.__file__).resolve()),
            unbuffered=os.environ["PYTHONUNBUFFERED"],
            cpu_only=torch.version.cuda is None,
        )
    finally:
        if loader is not None:
            loader.close()
            assert loader.closed and loader.context.processes == []
    Path(os.environ["COMPOSITION_CAPTURE"]).write_text(json.dumps(observation))
    os.write(1, b"[NoTTT][cpu_loader] synthetic receiver bound\n")
    os.write(2, b"[rank1] diagnostic retained by the actual console wrapper\n")
    os.write(1, b"[CorrectedV3][progress] composition step=0/30000\n")
    if os.environ["COMPOSITION_EXIT"] != "0":
        os.write(2, b"Traceback: injected failure after successful async binding\n")
    raise SystemExit(int(os.environ["COMPOSITION_EXIT"]))


@pytest.mark.parametrize(
    "world,workers,phase,code",
    [
        (4, 8, "fresh", 0),
        (4, 8, "resume", 0),
        (8, 0, "fresh", 0),
        (8, 0, "resume", 0),
        (4, 0, "resume", 0),
        (4, 8, "resume", 7),
    ],
)
def test_approved_launcher_console_and_actual_receiver_compose(
    tmp_path, world, workers, phase, code
):
    capture = tmp_path / "receiver.json"
    fake_python = tmp_path / "CPU torchrun substitute"
    fake_python.write_text(
        f"#!{sys.executable}\nimport runpy\n"
        f"runpy.run_path({str(Path(__file__).resolve())!r},run_name='__main__')\n"
    )
    fake_python.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith("NOTTT_")}
    env.pop("CUDA_VISIBLE_DEVICES", None)
    job = (
        "no_ttt_composition_world4_ga4"
        if world == 4
        else "no_ttt_composition_world8_ga2"
    )
    output = tmp_path / "output with spaces"
    env.update(
        PYTHON=str(fake_python),
        OUTPUT_ROOT=str(output),
        JOB_NAME=job,
        COMPOSITION_CAPTURE=str(capture),
        COMPOSITION_EXIT=str(code),
    )
    for name in (
        "SOURCE_ROOT",
        "CACHE_ROOT",
        "DATASET_INDEX_ROOT",
        "EDGE_POLICY_CHECKPOINT",
        "WAN_VAE_PATH",
        "BASE_CHECKPOINT_PATH",
        "EXPECTED_ROOT",
        "EXPECTED_CHILD",
    ):
        env[name] = str(tmp_path / (name + " synthetic only"))
    if workers:
        env.update(
            NOTTT_LOADER_WORKERS=str(workers),
            NOTTT_PREFETCH_FACTOR="1",
            NOTTT_PERSISTENT_WORKERS="1",
            NOTTT_LOADER_TIMEOUT_S="120",
        )
    name = (
        "train_v3_matched_no_ttt_4gpu.sh"
        if world == 4
        else "train_v3_matched_no_ttt.sh"
    )
    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / name), phase, "12220"],
        capture_output=True,
        env=env,
        timeout=60,
    )
    (tmp_path / "console.stdout").write_bytes(result.stdout)
    (tmp_path / "console.stderr").write_bytes(result.stderr)
    assert result.returncode == code, result.stderr
    assert result.stdout.splitlines()[0].startswith(b"[NoTTT][log] full log: ")
    assert result.stdout.splitlines()[1:] == [
        b"[CorrectedV3][progress] composition step=0/30000"
    ]
    data = json.loads(capture.read_text())
    assert data["loader"] == ("NoTTTAsyncLoader" if workers else None)
    assert data["profile"]["workers"] == workers
    assert data["metadata_calls"] == ([workers] if workers else [])
    assert data["cpu_only"] and data["unbuffered"] == "1"
    assert data["cwd"] == str(ROOT / "cosmos-framework")
    argv = data["argv"]
    assert argv[:4] == [
        "-m",
        "torch.distributed.run",
        "--standalone",
        f"--nproc_per_node={world}",
    ]
    for flag, value in {
        "--phase": phase,
        "--formal-execution-until": "12220",
        "--world-size": str(world),
        "--ga": "4" if world == 4 else "2",
        "--b": "8",
        "--t": "16",
        "--max-iter": "30000",
        "--save-iter": "100",
        "--root-worktree": str(ROOT),
        "--job-name": job,
    }.items():
        assert argv[argv.index(flag) + 1] == value
    if workers:
        assert argv[argv.index("--no-ttt-loader-workers") + 1] == "8"
        assert data["profile"]["persistent_workers"] is True
        assert data["profile"]["prefetch_factor"] == 1
        assert data["profile"]["timeout_s"] == 120
    else:
        assert "--no-ttt-loader-workers" not in argv
    logs = list((output / "_launch_logs" / job).glob("launch_*.log"))
    assert len(logs) == 1
    raw = logs[0].read_bytes()
    assert b"[NoTTT][cpu_loader] synthetic receiver bound\n" in raw
    assert b"[rank1] diagnostic retained by the actual console wrapper\n" in raw
    assert b"[CorrectedV3][progress] composition step=0/30000\n" in raw
    assert not (output / job).exists()  # No real Fresh or Resume side effects.
    if code:
        assert b"[NoTTT][failed] exit=7" in result.stderr
        assert b"injected failure after successful async binding" in result.stderr
        assert b"injected failure after successful async binding" in raw
    else:
        assert not result.stderr


if __name__ == "__main__":
    _receive_launch()
