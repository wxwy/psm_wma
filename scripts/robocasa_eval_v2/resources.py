"""Read-only resource admission; allow GPU sharing without managing foreign processes."""

from __future__ import annotations

import subprocess
from pathlib import Path

from cosmos_framework.simulation.robocasa.render_devices import normalize_pci
from robocasa_processes import group_members

from robocasa_eval_v2.config import rendering


def check(cfg, processes=(), *, before_models=False, run=subprocess.run):
    render = rendering(cfg)
    selected_ids = sorted(set(cfg["gpu_ids"]) | set(render["gpu_ids"]))
    args = [
        "nvidia-smi",
        "-i",
        ",".join(map(str, selected_ids)),
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
    if any(g not in devices for g in selected_ids):
        raise RuntimeError("BLOCKED_RESOURCE: missing selected GPU")
    reserves = dict.fromkeys(selected_ids, 0)
    if before_models:
        for g in cfg["gpu_ids"]:
            reserves[g] += cfg.get("server_reserve_bytes", 20 * 1024**3)
        task_count = len(cfg["tasks"]) if isinstance(cfg.get("tasks"), list) else 18
        for g in render_slots(cfg, task_count).values():
            if g is not None:
                reserves[g] += cfg.get("render_reserve_bytes_per_sim", 1024**3)
    for g in selected_ids:
        _, total, used = devices[g]
        if used + reserves[g] > total * cfg["max_gpu_fraction"]:
            raise RuntimeError("BLOCKED_RESOURCE: GPU memory budget")
    if render["gpu_ids"]:
        apps = run(
            [
                "nvidia-smi",
                "-i",
                ",".join(map(str, sorted(set(render["gpu_ids"])))),
                "--query-compute-apps=gpu_uuid,pid",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout
        render_uuids = {devices[g][0] for g in render["gpu_ids"]}
        for line in apps.splitlines():
            uid, pid = [v.strip() for v in line.split(",")]
            if uid not in render_uuids or not pid.isdigit():
                raise RuntimeError(
                    "BLOCKED_RESOURCE: invalid render CUDA ownership probe"
                )
            if int(pid) not in allowed:
                raise RuntimeError(
                    "BLOCKED_RESOURCE: foreign CUDA workload on render GPU"
                )
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
    return {
        "gpus": devices,
        "owned_pids": sorted(allowed),
        "rss_bytes": rss,
        "reserves": reserves,
    }


def physical_slots(cfg, task_count):
    """Slot-major/GPU-minor useful identities; GPU count is not Session count."""
    if cfg.get("execution_profile", "phase_a") == "phase_a":
        return {f"GPU{g}": g for g in cfg["gpu_ids"][:task_count]}
    pairs = [
        (f"GPU{g}_S{s}", g) for s in range(cfg["sims_per_gpu"]) for g in cfg["gpu_ids"]
    ]
    return dict(pairs[:task_count])


def render_slots(cfg, task_count):
    policy = rendering(cfg)
    mapping = dict(zip(cfg["gpu_ids"], policy["gpu_ids"]))
    return {
        worker: mapping[gpu] if policy["backend"] == "egl" else None
        for worker, gpu in physical_slots(cfg, task_count).items()
    }


def gpu_identity(gpu, *, run=subprocess.run):
    """Resolve a physical nvidia-smi ID; never interpret it as an EGL ordinal."""
    raw = (
        run(
            [
                "nvidia-smi",
                "-i",
                str(gpu),
                "--query-gpu=index,uuid,pci.bus_id",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        .stdout.strip()
        .splitlines()
    )
    if len(raw) != 1:
        raise RuntimeError("one physical render GPU identity required")
    index, uid, pci = [v.strip() for v in raw[0].split(",")]
    if index != str(gpu) or not uid.startswith("GPU-"):
        raise RuntimeError("physical render GPU identity mismatch")
    return {"gpu_id": gpu, "uuid": uid, "pci_bus_id": normalize_pci(pci)}
