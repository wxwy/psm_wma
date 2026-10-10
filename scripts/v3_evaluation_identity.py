#!/usr/bin/env python3
"""Immutable evaluation identity. Never deserialize a DCP or reuse a foreign result."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def validate_root_source_status(porcelain: str) -> None:
    """Permit owner notes, not uncommitted evaluation code or a changed Gitlink."""
    for row in porcelain.split("\0"):
        if not row:
            continue
        if len(row) < 4 or row[2] != " ":
            raise ValueError("invalid Root status record")
        status, name = row[:2], row[3:]
        note = name in {"SESSION.md", "TODO.md"} and not any(flag in status for flag in "DR")
        evidence = (
            status == "??"
            and name.startswith(("artifacts/", "docs/collab/chatgpt/DS_PRO_"))
            and Path(name).suffix in {".json", ".jsonl", ".log", ".txt", ".md", ".png", ".csv", ".xml"}
        )
        if not note and not evidence:
            raise ValueError(f"evaluation Root has uncommitted source changes: {row}")


def build_evaluation_identity(*, root: Path, checkpoint: Path, config_file: Path, tasks, protocol: dict) -> dict:
    root = root.resolve()
    child = root / "cosmos-framework"
    root_sha, child_sha = _git(root, "rev-parse", "HEAD"), _git(child, "rev-parse", "HEAD")
    link = _git(root, "ls-tree", "HEAD", "cosmos-framework").split()
    if len(link) < 3 or link[0] != "160000" or link[2] != child_sha:
        raise ValueError("evaluation Root/Child/Gitlink mismatch")
    if _git(child, "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("evaluation child is not clean")
    # _git strips leading whitespace; do not use it for porcelain status columns.
    root_status = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1", "-z", "--untracked-files=all"], text=True
    )
    validate_root_source_status(root_status)
    checkpoint = checkpoint.resolve()
    model_dir = checkpoint / "model"
    metadata = model_dir / ".metadata"
    if (
        not metadata.is_file()
        or metadata.stat().st_size == 0
        or not metadata.resolve().is_relative_to(model_dir.resolve())
    ):
        raise ValueError("checkpoint model metadata absent/empty")
    shards = []
    for path in sorted(model_dir.glob("*.distcp")):
        st = path.stat()
        if not path.is_file() or st.st_size <= 0 or not path.resolve().is_relative_to(model_dir.resolve()):
            raise ValueError("invalid model shard")
        shards.append([path.name, st.st_size, st.st_mtime_ns, st.st_ctime_ns])
    if not shards:
        raise ValueError("checkpoint model has no nonempty shards")
    task_rows = []
    for name, directory in tasks:
        if not isinstance(name, str) or not name or name in {".", ".."} or any(c in name for c in ("/", "\\", "\0")):
            raise ValueError("invalid evaluation task name")
        path = Path(directory).resolve() / "extras/dataset_meta.json"
        task_rows.append(
            {"task": name, "dataset_dir": str(Path(directory).resolve()), "env_metadata_sha256": sha256_file(path)}
        )
    if len({v["task"] for v in task_rows}) != len(task_rows):
        raise ValueError("duplicate evaluation task names")
    identity = {
        "schema": "psm_v3_eval_identity_v1",
        "root_sha": root_sha,
        "child_sha": child_sha,
        "checkpoint": str(checkpoint),
        "model_metadata_sha256": sha256_file(metadata),
        "model_shard_stat_witnesses": shards,
        "checkpoint_identity_scope": "metadata_hash_and_shard_stats_not_full_payload_hash",
        "config_sha256": sha256_file(config_file.resolve()),
        "tasks": sorted(task_rows, key=lambda v: v["task"]),
        "protocol": protocol,
    }
    return {"identity": identity, "digest": hashlib.sha256(_canonical(identity)).hexdigest()}


def claim_evaluation_run(output: Path, manifest: dict, *, resume: bool) -> str:
    identity, digest = manifest.get("identity"), manifest.get("digest")
    if digest != hashlib.sha256(_canonical(identity)).hexdigest():
        raise ValueError("manifest identity digest mismatch")
    output.mkdir(parents=True, exist_ok=True)
    path = output / "evaluation_manifest.json"
    if path.is_symlink():
        raise ValueError("evaluation manifest must not be a symlink")
    if path.exists():
        if not resume:
            raise FileExistsError("evaluation already exists; explicit same-identity resume required")
        observed = json.loads(path.read_text())
        if observed != manifest:
            raise ValueError("evaluation identity changed: checkpoint/source/config/protocol/task/seed/R")
        return digest
    if any(output.iterdir()):
        raise ValueError("legacy/nonempty output has no identity; use a new directory, never import its results")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(_canonical(manifest) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    return digest


def validate_task_results(rows: Any, *, digest: str, expected_trials: int) -> None:
    if type(expected_trials) is not int or expected_trials <= 0:
        raise ValueError("expected trial count must be a positive integer")
    if not isinstance(rows, list) or len(rows) != expected_trials:
        raise ValueError("incomplete evaluation result; do not silently skip a task")
    for index, row in enumerate(rows):
        if (
            not isinstance(row, dict)
            or type(row.get("ep")) is not int
            or row.get("ep") != index
            or row.get("evaluation_run_digest") != digest
        ):
            raise ValueError("foreign/duplicate/out-of-order evaluation episode")
        if type(row.get("policy")) is not bool or row.get("outcome") not in {
            "success",
            "behavioral_failure",
            "runtime_error",
        }:
            raise ValueError("evaluation result missing typed outcome")
        if row["outcome"] == "runtime_error":
            if row["policy"] or not isinstance(row.get("error"), str) or not row["error"]:
                raise ValueError("runtime error cannot be counted as success")
        elif row.get("error") is not None or (row["outcome"] == "success") != row["policy"]:
            raise ValueError("inconsistent evaluation result")


def screening_metrics(results: dict, *, tasks: list[str], expected_trials: int) -> dict:
    if type(expected_trials) is not int or expected_trials <= 0 or len(tasks) != len(set(tasks)):
        raise ValueError("invalid screening plan")
    ordered = {name: results[name] for name in tasks if name in results}
    for row in ordered.values():
        n, k = row.get("trials", 0), row.get("successes", 0)
        if type(n) is not int or type(k) is not int or not 0 <= k <= n <= expected_trials:
            raise ValueError("invalid screening counts")
    planned = len(tasks) * expected_trials
    observed = sum(int(row.get("trials", 0)) for row in ordered.values())
    successes = sum(int(row.get("successes", 0)) for row in ordered.values())
    complete = len(ordered) == len(tasks) and all(row.get("trials") == expected_trials for row in ordered.values())
    return {
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "planned_trials": planned,
        "completed_tasks": len(ordered),
        "total_trials": observed,
        "total_successes": successes,
        "sr": successes / planned if complete and planned else None,
        "partial_sr": successes / observed if observed else None,
        "task_failures": sum(row.get("error") is not None for row in ordered.values()),
        "missing_tasks": [name for name in tasks if name not in ordered],
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("root-worktree", "checkpoint", "config-file", "dataset-dir", "output-dir"):
        parser.add_argument("--" + flag, type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--action-horizon", type=int, required=True)
    parser.add_argument("--num-trials", type=int, required=True)
    parser.add_argument("--num-steps", type=int, required=True)
    parser.add_argument("--guidance", type=float, required=True)
    parser.add_argument("--local-memory-mode", choices=("off", "required"), required=True)
    args = parser.parse_args()
    meta = json.loads((args.dataset_dir / "extras/dataset_meta.json").read_text())
    task = meta["env_args"]["env_name"]
    manifest = build_evaluation_identity(
        root=args.root_worktree,
        checkpoint=args.checkpoint,
        config_file=args.config_file,
        tasks=[(task, args.dataset_dir)],
        protocol={
            "seed": args.seed,
            "R": args.action_horizon,
            "H_pred": 16,
            "num_steps": args.num_steps,
            "guidance": args.guidance,
            "trials": args.num_trials,
            "fps": 20,
            "camera_set": "left_wrist",
            "image_size": 256,
            "cam_size": 256,
            "use_state": True,
            "base_encoding": "raw",
            "local_memory_mode": args.local_memory_mode,
            "success_latch": 1,
        },
    )
    print(claim_evaluation_run(args.output_dir, manifest, resume=False))


if __name__ == "__main__":
    main()
