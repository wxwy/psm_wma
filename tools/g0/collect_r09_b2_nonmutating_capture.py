#!/usr/bin/env python3
"""Generate CPU-only concrete P2 isolation mutation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from unittest import mock

import torch

import cosmos_framework.callbacks.r09_b2_capture as capture_module
from cosmos_framework.callbacks.r09_b2_capture import R09B2NonMutatingCaptureCallback, take_isolation_snapshot


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def protected_values() -> dict[str, object]:
    return {
        "parameters": {"weight": torch.tensor([1.0])}, "buffers": {"buffer": torch.tensor([1.0])},
        "optimizer": {"state": torch.tensor([1.0])}, "scheduler": {"step": 1},
        "batch_metadata": {"ordinal": 0, "epoch": 0, "microbatch": 0},
        "recurrent_state": {"hidden": torch.tensor([1.0])},
        "ttt_state": {key: torch.tensor([1.0]) for key in ("W", "pending_evidence", "last_evidence", "initialized", "segment_progress")},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    framework = root / "cosmos-framework"
    checks: dict[str, dict[str, object]] = {}
    for name in protected_values():
        values = protected_values()
        callback = R09B2NonMutatingCaptureCallback("normal", lambda: take_isolation_snapshot(**values))
        original = capture_module.clone_local_payload

        def mutate_then_clone(payload, mode):
            value = values[name]
            key = next(iter(value))
            value[key] = value[key] + 1
            return original(payload, mode)

        with mock.patch.object(capture_module, "clone_local_payload", mutate_then_clone):
            try:
                callback.on_training_step_end(
                    object(), {"local_memory": [torch.tensor([3.0])], "b2_stream_ordinal": torch.tensor(0),
                               "b2_stream_epoch": torch.tensor(0), "b2_stream_microbatch": torch.tensor(0)},
                    {}, torch.tensor(0.0),
                )
            except RuntimeError as error:
                checks[name] = {"callback_entrypoint": True, "rejected": name in str(error), "error": str(error)}
            else:
                checks[name] = {"callback_entrypoint": True, "rejected": False, "error": ""}
    result = {
        "schema_version": "r09_b2_nonmutating_capture_cpu_v3",
        "status": "PASS" if all(item["rejected"] for item in checks.values()) else "FAIL",
        "mutation_checks": checks,
        "source": {
            "root_revision": git(root, "rev-parse", "HEAD"),
            "submodule_revision": git(framework, "rev-parse", "HEAD"),
            "gitlink_revision": git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2],
            "collector_sha256": sha256(Path(__file__).resolve()),
            "verifier_sha256": sha256(Path(__file__).with_name("verify_r09_b2_nonmutating_capture.py")),
            "capture_source_sha256": sha256(framework / "cosmos_framework/callbacks/r09_b2_capture.py"),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "count": len(checks)}))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
