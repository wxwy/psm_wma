"""Selected GPU identity and owned RSS checks; GPU placement is the Owner's choice."""

from __future__ import annotations

import subprocess
from pathlib import Path

from cosmos_framework.simulation.robocasa.render_devices import normalize_pci
from cosmos_framework.evaluation.robocasa_v2.contract import STREAMING_SCHEDULE
from robocasa_processes import group_members

from robocasa_eval_v2.config import rendering


def check(cfg, processes=(), *, before_models=False, run=subprocess.run):
    # Keep the launcher signature; legacy GPU budgets are no longer admission inputs.
    render = rendering(cfg)
    selected_ids = sorted(set(cfg["gpu_ids"]) | set(render["gpu_ids"]))
    args = [
        "nvidia-smi",
        "-i",
        ",".join(map(str, selected_ids)),
        "--query-gpu=index,uuid",
        "--format=csv,noheader,nounits",
    ]
    output = run(args, capture_output=True, text=True, check=True, timeout=10).stdout
    devices = {}
    for line in output.splitlines():
        index, uid = [x.strip() for x in line.split(",")]
        index = int(index)
        if index not in selected_ids or index in devices or not uid.startswith("GPU-"):
            raise RuntimeError("BLOCKED_RESOURCE: invalid selected GPU identity")
        devices[index] = uid
    allowed = set()
    if cfg.get("scheduling_protocol") == STREAMING_SCHEDULE:
        allowed = owned_group_pids(processes)
    else:
        for p in processes:
            allowed.update(group_members(p.pgid))
    if any(g not in devices for g in selected_ids):
        raise RuntimeError("BLOCKED_RESOURCE: missing selected GPU")
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
    result = {
        "gpus": devices,
        "owned_pids": sorted(allowed),
        "rss_bytes": rss,
    }
    if cfg.get("scheduling_protocol") == STREAMING_SCHEDULE:
        result["owned_gpu_bytes"] = owned_gpu_memory(selected_ids, allowed)
        if any(
            v > cfg["streaming_resources"]["max_owned_gpu_bytes"]
            for v in result["owned_gpu_bytes"].values()
        ):
            raise RuntimeError("BLOCKED_RESOURCE: owned GPU memory budget")
    return result


def owned_group_pids(processes, *, proc=Path("/proc")):
    """One /proc scan for all owned groups, rather than one scan per Sim."""
    groups = {p.pgid for p in processes}
    result = set()
    for entry in proc.iterdir() if groups else ():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) in groups:
                result.add(int(entry.name))
        except (FileNotFoundError, ProcessLookupError):
            continue
    return result


def owned_gpu_memory(selected_ids, allowed, *, nvml=None):
    """Only our compute/graphics PIDs; unknown measurements fail closed."""
    result = {}
    initialized = False
    try:
        if nvml is None:
            import pynvml as nvml
        nvml.nvmlInit()
        initialized = True
        for gpu in selected_ids:
            handle = nvml.nvmlDeviceGetHandleByIndex(gpu)
            values = {}
            for query in (
                nvml.nvmlDeviceGetComputeRunningProcesses,
                nvml.nvmlDeviceGetGraphicsRunningProcesses,
            ):
                for process in query(handle):
                    if process.pid not in allowed:
                        continue
                    size = process.usedGpuMemory
                    if type(size) is not int or not 0 <= size < 2**63:
                        raise ValueError("unavailable owned PID GPU memory")
                    values[process.pid] = max(values.get(process.pid, 0), size)
            result[gpu] = sum(values.values())
    except Exception as error:
        raise RuntimeError(
            "BLOCKED_RESOURCE: owned GPU memory measurement unavailable"
        ) from error
    finally:
        if initialized:
            nvml.nvmlShutdown()
    return result


def physical_slots(cfg, task_count):
    """Slot-major/GPU-minor useful identities; GPU count is not Session count."""
    if cfg.get("execution_profile", "phase_a") == "phase_a":
        return {f"GPU{g}": g for g in cfg["gpu_ids"][:task_count]}
    pairs = [
        (f"GPU{g}_S{s}", g) for s in range(cfg["sims_per_gpu"]) for g in cfg["gpu_ids"]
    ]
    return dict(
        pairs
        if cfg.get("scheduling_protocol") == STREAMING_SCHEDULE
        else pairs[:task_count]
    )


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
