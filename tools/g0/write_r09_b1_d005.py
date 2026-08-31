#!/usr/bin/env python3
"""Write immutable R09-B1 D005 launch provenance before a GPU command runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path


def _git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


_PHASE_PROFILES = {
    "gate_a_rebuild": ("smoke_batch1_gate_a", 1, 1),
    "b1_smoke": ("smoke_batch2_b1", 2, 1),
}


def _profile_overrides_exact(command_argv: list[str], max_samples: int, grad_accum: int) -> bool:
    prefix = "EXTRA_TAIL_OVERRIDES="
    values = [item.removeprefix(prefix).split() for item in command_argv if item.startswith(prefix)]
    expected = (
        f"dataloader_train.max_samples_per_batch={max_samples}",
        f"trainer.grad_accum_iter={grad_accum}",
    )
    return len(values) == 1 and all(values[0].count(item) == 1 for item in expected)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--phase", choices=("gate_a_rebuild", "b1_smoke"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--command-argv-json", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--libero-root", required=True)
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--output-checkpoint", required=True)
    parser.add_argument("--probe", default="")
    parser.add_argument("--expected-steps", type=int, required=True)
    parser.add_argument("--gpu-name", required=True)
    parser.add_argument("--gpu-total-memory-mib", type=int, required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--profile-max-samples", type=int, required=True)
    parser.add_argument("--profile-grad-accum", type=int, required=True)
    parser.add_argument("--history-evidence", default="")
    args = parser.parse_args()
    command_argv = json.loads(args.command_argv_json)
    if not isinstance(command_argv, list) or not all(isinstance(item, str) for item in command_argv):
        raise ValueError("--command-argv-json must be a JSON string array.")
    root = args.root.resolve()
    submodule = root / "cosmos-framework"
    expected_profile = _PHASE_PROFILES[args.phase]
    if (args.profile, args.profile_max_samples, args.profile_grad_accum) != expected_profile:
        raise ValueError(f"R09-B1 phase {args.phase} requires profile={expected_profile[0]}, max_samples={expected_profile[1]}, grad_accum={expected_profile[2]}.")
    if not _profile_overrides_exact(command_argv, args.profile_max_samples, args.profile_grad_accum):
        raise ValueError("--command-argv-json must contain the bounded smoke profile overrides exactly once.")
    history_evidence: dict[str, object] | None = None
    if args.phase == "b1_smoke":
        evidence_path = Path(args.history_evidence)
        if not evidence_path.is_file():
            raise ValueError("B1 requires an existing first-batch Local-history evidence JSON.")
        evidence = json.loads(evidence_path.read_text())
        if evidence.get("status") != "PASS" or evidence.get("effective_local_history_sample_count", 0) < 1:
            raise ValueError("B1 first-batch Local-history evidence must be PASS with an effective Local sample.")
        history_evidence = {
            "path": str(evidence_path),
            "sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            "status": evidence["status"],
            "effective_local_history_sample_count": evidence["effective_local_history_sample_count"],
        }
    elif args.history_evidence:
        raise ValueError("Gate-A must not carry B1 Local-history evidence.")
    dmesg = subprocess.run(
        ["dmesg", "--color=never"], text=True, capture_output=True, check=False
    )
    dmesg_tail = dmesg.stdout.splitlines()[-40:] if dmesg.returncode == 0 else []
    environment = {
        "PATH": args.path, "CUDA_VISIBLE_DEVICES": "0", "NPROC_PER_NODE": "1", "PSM_R08_LOCAL_HISTORY_ENABLED": "1", "PSM_R08_LOCAL_HISTORY_HORIZON": "16",
        "PSM_LOCAL_DUMMY_ENABLED": "0", "PSM_LOCAL_DUMMY_DIM": "32", "PSM_LOCAL_DUMMY_MODE": "normal",
        "PSM_R08_HISTORY_MODE": "normal", "PSM_R09_A1_ENABLED": "0", "PSM_R08_GATE_B_CAPTURE_ONLY": "0",
        "LIBERO_LATENT_CACHE_ROOT": args.cache_root, "LIBERO_LATENT_CACHE_VERIFY_RATIO": "0", "LIBERO_NUM_WORKERS": "0",
        "PSM_R09_B1_TTT_ENABLED": "1" if args.phase == "b1_smoke" else "0", "PSM_R09_B1_PROBE_OUTPUT": args.probe,
    }
    unset_environment = [
        "PSM_R09_A1_PROBE_OUTPUT", "PSM_R07_RUNTIME_PROBE_OUTPUT", "PSM_R07_PARITY_OUTPUT",
        "PSM_R07_PARITY_TENSOR_OUTPUT", "PSM_R08_GATE_A_PROBE_OUTPUT", "PSM_R08_GATE_B_PROVENANCE_OUTPUT",
        "ONLINE_VAE_PROBE_OUTPUT", "LIBERO_MAX_EPISODES",
    ]
    payload = {
        "schema_version": "r09_b1_d005_v3", "phase": args.phase, "network": False, "world_size": 1,
        "source": {"root_revision": _git(root, "rev-parse", "HEAD"), "submodule_revision": _git(submodule, "rev-parse", "HEAD"), "gitlink_revision": _git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2]},
        "cwd": str(root / "cosmos-framework"), "gpu": {"index": 0, "name": args.gpu_name, "total_memory_mib": args.gpu_total_memory_mib, "cap": "A100-80GB"}, "environment": environment, "unset_environment": unset_environment,
        "input": {"checkpoint": args.checkpoint, "libero_root": args.libero_root, "cache_root": args.cache_root},
        "output": {
            "root": args.run_root,
            "log": args.log,
            "checkpoint": args.output_checkpoint,
            "probe": args.probe,
        },
        "expected_steps": args.expected_steps,
        "smoke_profile": {
            "name": args.profile,
            "bounded_noncanonical": True,
            "dataloader_train.max_samples_per_batch": args.profile_max_samples,
            "trainer.grad_accum_iter": args.profile_grad_accum,
        },
        "b1_first_batch_history": history_evidence,
        "launch_diagnostics": {
            "started_unix": time.time(),
            "dmesg_returncode": dmesg.returncode,
            "dmesg_tail": dmesg_tail,
            "dmesg_stderr": dmesg.stderr.strip(),
        },
        "command": args.command,
        "command_argv": command_argv,
    }
    payload["command_sha256"] = hashlib.sha256(args.command.encode()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
