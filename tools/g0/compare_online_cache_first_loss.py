#!/usr/bin/env python3
"""尝试比较在线 VAE 与 cache 的首训练前向 loss。

该工具固定随机种子和 ``--deterministic``，但在线 iterable dataloader 与
cache manifest dataloader 不保证产生相同的首 batch（episode/start 键及顺序
可能不同）。因此其 loss diff 不能单独作为 latent 等价或不等价的判据；应以
同一训练 batch 的 runtime guard 三路 latent 对比为准。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


_METRIC_RE = re.compile(
    r"iteration=(?P<iteration>\d+)\s+\|\s+train/loss=(?P<loss>[-+0-9.eE]+)"
    r"\s+\|\s+flow_matching_loss_vision=(?P<vision>[-+0-9.eE]+)"
    r"\s+\|\s+flow_matching_loss_action=(?P<action>[-+0-9.eE]+)"
)


def _run_once(
    *,
    name: str,
    cache_root: Path | None,
    args: argparse.Namespace,
    env_base: dict[str, str],
    work_root: Path,
) -> tuple[dict[str, float] | None, int, Path]:
    env = dict(env_base)
    env["IMAGINAIRE_OUTPUT_ROOT"] = str(work_root / name)
    env["OUTPUT_ROOT"] = str(work_root / name)
    env["LIBERO_LATENT_CACHE_VERIFY_RATIO"] = "0.0"
    if cache_root is None:
        env.pop("LIBERO_LATENT_CACHE_ROOT", None)
    else:
        env["LIBERO_LATENT_CACHE_ROOT"] = str(cache_root)

    overrides = [
        f"trainer.max_iter=1",
        "trainer.logging_iter=1",
        f"trainer.seed={args.seed}",
        "checkpoint.save_iter=1000",
        "job.wandb_mode=offline",
    ]
    log_path = work_root / f"{name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(args.repo_root / ".venv/bin/torchrun"),
        "--nproc_per_node=1",
        "-m",
        "cosmos_framework.scripts.train",
        "--deterministic",
        f"--sft-toml={args.sft_toml}",
        "--",
        *overrides,
    ]
    with log_path.open("w", encoding="utf-8") as log_file:
        completed = subprocess.run(command, cwd=args.repo_root, env=env, stdout=log_file, stderr=subprocess.STDOUT)

    metrics = None
    for match in _METRIC_RE.finditer(log_path.read_text(encoding="utf-8", errors="replace")):
        metrics = {key: float(match.group(key)) for key in ("loss", "vision", "action")}
        metrics["iteration"] = float(match.group("iteration"))
    return metrics, completed.returncode, log_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--libero-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[2] / "cosmos-framework"
    )
    parser.add_argument("--sft-toml", type=Path, default=Path("examples/toml/sft_config/action_policy_libero_edge_all.toml"))
    parser.add_argument("--base-checkpoint", type=Path, default=Path("examples/checkpoints/Cosmos3-Edge-Policy-DROID-dcp"))
    parser.add_argument("--edge-policy-checkpoint", type=Path, default=Path("/disk/rl/models/Cosmos3-Edge-Policy-DROID"))
    parser.add_argument("--vae-path", type=Path, default=Path("examples/checkpoints/wan22_vae/Wan2.2_VAE.pth"))
    parser.add_argument("--max-episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--atol", type=float, default=1e-6)
    args = parser.parse_args()
    if args.max_episodes <= 0:
        raise ValueError("--max-episodes must be positive")

    repo_root = args.repo_root.resolve()
    args.repo_root = repo_root
    sft_toml = args.sft_toml if args.sft_toml.is_absolute() else repo_root / args.sft_toml
    args.sft_toml = sft_toml
    if not sft_toml.is_file():
        raise FileNotFoundError(f"SFT TOML not found: {sft_toml}")
    for path in (args.cache_root, args.libero_root):
        if not path.is_dir():
            raise FileNotFoundError(path)

    venv_lib = repo_root / ".venv/lib/python3.13/site-packages"
    env_base = dict(os.environ)
    env_base.update(
        {
            "LIBERO_ROOT": str(args.libero_root),
            "LIBERO_MAX_EPISODES": str(args.max_episodes),
            "LIBERO_NUM_WORKERS": "0",
            "NPROC_PER_NODE": "1",
            "PYTHONHASHSEED": str(args.seed),
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
            "FLASH_ATTENTION_DETERMINISTIC": "1",
            "BASE_CHECKPOINT_PATH": str(args.base_checkpoint),
            "EDGE_POLICY_CHECKPOINT": str(args.edge_policy_checkpoint),
            "WAN_VAE_PATH": str(args.vae_path),
            "LD_LIBRARY_PATH": ":".join(
                str(path)
                for path in (
                    venv_lib / "nvidia/cu13/lib",
                    venv_lib / "nvidia/cudnn/lib",
                    venv_lib / "torch/lib",
                )
            )
            + (":" + env_base["LD_LIBRARY_PATH"] if env_base.get("LD_LIBRARY_PATH") else ""),
        }
    )
    args.work_root.mkdir(parents=True, exist_ok=True)
    online, online_returncode, online_log = _run_once(
        name="online", cache_root=None, args=args, env_base=env_base, work_root=args.work_root
    )
    cached, cached_returncode, cached_log = _run_once(
        name="cache", cache_root=args.cache_root, args=args, env_base=env_base, work_root=args.work_root
    )

    diffs = (
        {key: abs(online[key] - cached[key]) for key in ("loss", "vision", "action")}
        if online is not None and cached is not None
        else None
    )
    status = (
        "PASS"
        if online_returncode == 0
        and cached_returncode == 0
        and diffs is not None
        and all(value <= args.atol for value in diffs.values())
        else "FAIL"
    )
    result = {
        "schema_version": "online_cache_first_loss_v1",
        "status": status,
        "seed": args.seed,
        "iteration": 0,
        "max_episodes": args.max_episodes,
        "num_workers": 0,
        "deterministic_launch": True,
        "atol": args.atol,
        "online": {"returncode": online_returncode, "metrics": online, "log": str(online_log)},
        "cache": {"returncode": cached_returncode, "metrics": cached, "log": str(cached_log)},
        "abs_diff": diffs,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "abs_diff": diffs}, ensure_ascii=False))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
