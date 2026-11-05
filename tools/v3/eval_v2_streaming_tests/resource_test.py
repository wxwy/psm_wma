"""Owned-only compute+graphics VRAM and bounded concurrent startup admission."""

from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest
from robocasa_eval_v2.resources import owned_gpu_memory, owned_group_pids
from robocasa_eval_v2.startup import StartupBudget
from tools.v3.eval_v2_streaming_tests.capacity_test import streaming_config


class NVML:
    def nvmlInit(self):
        pass

    def nvmlShutdown(self):
        self.shutdown = True

    def nvmlDeviceGetHandleByIndex(self, gpu):
        return gpu

    def nvmlDeviceGetComputeRunningProcesses(self, handle):
        return [
            SimpleNamespace(pid=1, usedGpuMemory=10),
            SimpleNamespace(pid=999, usedGpuMemory=2**64 - 1),
        ]

    def nvmlDeviceGetGraphicsRunningProcesses(self, handle):
        return [
            SimpleNamespace(pid=1, usedGpuMemory=10),
            SimpleNamespace(pid=2, usedGpuMemory=20),
        ]


def test_owned_compute_and_graphics_are_counted_once_and_foreign_occupancy_ignored():
    nvml = NVML()
    assert owned_gpu_memory([4, 5], {1, 2}, nvml=nvml) == {4: 30, 5: 30}
    assert nvml.shutdown


def test_all_owned_groups_one_proc_snapshot_includes_descendants_not_foreign(tmp_path):
    for pid, group in ((5, 5), (6, 6), (20, 6), (21, 12)):
        directory = tmp_path / str(pid)
        directory.mkdir()
        (directory / "stat").write_text(f"{pid} (name with spaces) S 0 {group} 0 0")
    assert owned_group_pids(
        [SimpleNamespace(pgid=5), SimpleNamespace(pgid=6)], proc=tmp_path
    ) == {5, 6, 20}


@pytest.mark.parametrize("failure", ["init", "unknown", "unsupported"])
def test_unknown_meter_is_blocked_not_zero_or_foreign_memory_gate(failure):
    nvml = NVML()
    if failure == "init":
        nvml.nvmlInit = lambda: (_ for _ in ()).throw(
            RuntimeError("driver unavailable")
        )
    elif failure == "unknown":
        nvml.nvmlDeviceGetGraphicsRunningProcesses = lambda _: [
            SimpleNamespace(pid=2, usedGpuMemory=2**64 - 1)
        ]
    else:
        nvml.nvmlDeviceGetGraphicsRunningProcesses = lambda _: (_ for _ in ()).throw(
            RuntimeError("unsupported")
        )
    with pytest.raises(RuntimeError, match="BLOCKED_RESOURCE"):
        owned_gpu_memory([4], {1, 2}, nvml=nvml)
    assert getattr(nvml, "shutdown", False) == (failure != "init")


def test_concurrent_startup_reservations_cannot_both_spend_same_budget():
    cfg = streaming_config(max_rss_bytes=1_500_000)
    cfg["streaming_resources"]["sim_startup_rss_bytes"] = 1_000_000
    budget = StartupBudget(cfg, lambda: {"rss_bytes": 0, "owned_gpu_bytes": {6: 0}})
    entered, release = threading.Event(), threading.Event()

    def first():
        with budget.reserve("first", "sim", 6):
            entered.set()
            assert release.wait(5)

    with ThreadPoolExecutor(2) as pool:
        task = pool.submit(first)
        assert entered.wait(5)
        try:
            with pytest.raises(RuntimeError, match="startup RSS"):
                with budget.reserve("second", "sim", 6):
                    raise AssertionError("must not admit")
        finally:
            release.set()
        task.result(5)
    assert not budget.pending


def test_startup_failure_releases_reservation_and_gpu_limit_stays_strict():
    cfg = streaming_config()
    budget = StartupBudget(
        cfg,
        lambda: {
            "rss_bytes": 0,
            "owned_gpu_bytes": {6: cfg["streaming_resources"]["max_owned_gpu_bytes"]},
        },
    )
    with pytest.raises(RuntimeError, match="startup GPU"):
        with budget.reserve("too_large", "server", 6):
            raise AssertionError("must not admit")
    budget = StartupBudget(cfg, lambda: {"rss_bytes": 0, "owned_gpu_bytes": {6: 0}})
    with pytest.raises(ValueError, match="controlled"):
        with budget.reserve("failed", "sim", 6):
            raise ValueError("controlled startup failure")
    assert not budget.pending
