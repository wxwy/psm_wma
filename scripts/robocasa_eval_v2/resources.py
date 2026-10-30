"""Read-only resource admission. Never kill or change a foreign GPU process."""

from __future__ import annotations

import subprocess
from pathlib import Path

from robocasa_processes import group_members


def check(cfg, processes=(), *, before_models=False, run=subprocess.run):
    args = [
        "nvidia-smi",
        "--query-gpu=index,uuid,memory.total,memory.used",
        "--format=csv,noheader,nounits",
    ]
    output = run(args, capture_output=True, text=True, check=True, timeout=10).stdout
    devices = {}
    for line in output.splitlines():
        index, uid, total, used = [x.strip() for x in line.split(",")]
        devices[int(index)] = (uid, int(total) * 1024**2, int(used) * 1024**2)
    allowed = set()
    for p in processes:
        allowed.update(group_members(p.pgid))
    active = run(
        [
            "nvidia-smi",
            "--query-compute-apps=gpu_uuid,pid",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout
    selected = {devices[g][0] for g in cfg["gpu_ids"] if g in devices}
    if len(selected) != len(cfg["gpu_ids"]):
        raise RuntimeError("BLOCKED_RESOURCE: missing selected GPU")
    for line in active.splitlines():
        uid, pid = [x.strip() for x in line.split(",")]
        if uid in selected and int(pid) not in allowed:
            raise RuntimeError("BLOCKED_RESOURCE: selected GPU has a foreign process")
    for g in cfg["gpu_ids"]:
        _, total, used = devices[g]
        reserve = 20 * 1024**3 if before_models else 0
        if used + reserve > total * cfg["max_gpu_fraction"]:
            raise RuntimeError("BLOCKED_RESOURCE: GPU memory budget")
    rss = 0
    for pid in allowed:
        try:
            for line in (Path("/proc") / str(pid) / "status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    rss += int(line.split()[1]) * 1024
        except FileNotFoundError:
            pass
    if rss > cfg["max_rss_bytes"]:
        raise RuntimeError("BLOCKED_RESOURCE: owned process RSS budget")
    return {"gpus": devices, "owned_pids": sorted(allowed), "rss_bytes": rss}


def physical_slots(cfg, task_count):
    """Slot-major/GPU-minor useful identities; GPU count is not Session count."""
    if cfg.get("execution_profile", "phase_a") == "phase_a":
        return {f"GPU{g}": g for g in cfg["gpu_ids"][:task_count]}
    pairs = [
        (f"GPU{g}_S{s}", g) for s in range(cfg["sims_per_gpu"]) for g in cfg["gpu_ids"]
    ]
    return dict(pairs[:task_count])
