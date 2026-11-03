"""Owner GPU placement policy: identity-only probes, no third-party task admission."""

import errno
import subprocess
from types import SimpleNamespace

import pytest
from robocasa_eval_v2 import resources

from tools.v3.eval_v2_batch_tests.render_mapping_test import resource_cfg


class NoGpuBudgetReads(dict):
    budget_keys = {
        "max_gpu_fraction",
        "server_reserve_bytes",
        "render_reserve_bytes_per_sim",
    }

    def __getitem__(self, key):
        assert key not in self.budget_keys, "GPU capacity is the Owner's decision"
        return super().__getitem__(key)

    def get(self, key, default=None):
        assert key not in self.budget_keys, "GPU capacity is the Owner's decision"
        return super().get(key, default)


def identity_probe(*, rows=None, missing=None):
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        assert args[0] == "nvidia-smi"
        assert args[1] == "-i" and args[3:] == [
            "--query-gpu=index,uuid",
            "--format=csv,noheader,nounits",
        ]
        assert not any("memory" in arg or "compute-apps" in arg for arg in args)
        selected = set(map(int, args[2].split(",")))
        assert selected <= {4, 5, 6, 7}, "GPU0-3 must not be queried"
        data = (
            rows
            if rows is not None
            else "\n".join(f"{i}, GPU-{i}" for i in sorted(selected) if i != missing)
        )
        return SimpleNamespace(stdout=data)

    return run, calls


@pytest.mark.parametrize("before_models", [False, True])
@pytest.mark.parametrize("backend", ["egl", "osmesa"])
def test_gpu_admission_never_reads_occupancy_process_list_or_reserve_limits(
    backend, before_models
):
    cfg = NoGpuBudgetReads(resource_cfg())
    cfg.update(
        max_gpu_fraction=1e-9,
        server_reserve_bytes=2**90,
        render_reserve_bytes_per_sim=2**90,
    )
    if backend == "osmesa":
        cfg.update(render_backend=backend, render_gpu_ids=None)
    run, calls = identity_probe()
    result = resources.check(cfg, before_models=before_models, run=run)
    selected = {4, 5, 6, 7} if backend == "egl" else {4, 5}
    assert result["gpus"] == {i: f"GPU-{i}" for i in selected}
    assert len(calls) == 1 and result["owned_pids"] == []


@pytest.mark.parametrize("missing", [4, 5, 6, 7])
def test_absent_selected_server_or_render_gpu_remains_blocked(missing):
    run, _ = identity_probe(missing=missing)
    with pytest.raises(RuntimeError, match="missing selected GPU"):
        resources.check(resource_cfg(), before_models=True, run=run)


@pytest.mark.parametrize(
    "rows", ["4, GPU-4\n4, GPU-duplicate", "0, GPU-unselected", "4, not-a-gpu-uuid"]
)
def test_unselected_duplicate_or_invalid_device_identity_is_rejected(rows):
    run, _ = identity_probe(rows=rows)
    with pytest.raises(RuntimeError, match="invalid selected GPU identity"):
        resources.check(resource_cfg(), run=run)


@pytest.mark.parametrize("over_budget", [False, True])
def test_only_owned_cpu_rss_is_accounted_for_and_still_has_its_own_limit(
    tmp_path, monkeypatch, over_budget
):
    cfg = resource_cfg()
    cfg["max_rss_bytes"] = 3 * 1024 if over_budget else 6 * 1024
    own_pid, own_group = 712345, 812345
    fake_proc = tmp_path / "proc"
    status = fake_proc / str(own_pid) / "status"
    status.parent.mkdir(parents=True)
    status.write_text("Name:\towned-cpu-double\nVmRSS:\t5 kB\n")
    groups = []

    def members(pgid):
        groups.append(pgid)
        assert pgid == own_group
        return {own_pid: "S"}

    monkeypatch.setattr(resources, "group_members", members)
    monkeypatch.setattr(
        resources,
        "Path",
        lambda path: fake_proc
        if path == "/proc"
        else pytest.fail("unexpected process read"),
    )
    run, calls = identity_probe()
    if over_budget:
        with pytest.raises(RuntimeError, match="owned process RSS budget"):
            resources.check(cfg, [SimpleNamespace(pgid=own_group)], run=run)
    else:
        result = resources.check(cfg, [SimpleNamespace(pgid=own_group)], run=run)
        assert result["owned_pids"] == [own_pid] and result["rss_bytes"] == 5 * 1024
    assert groups == [own_group] and len(calls) == 1


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.CalledProcessError(1, "nvidia-smi"),
        OSError(errno.ENODEV, "driver/device unavailable"),
    ],
)
def test_actual_device_probe_failure_is_not_silently_accepted(failure):
    def run(*args, **kwargs):
        raise failure

    with pytest.raises(type(failure)):
        resources.check(resource_cfg(), run=run)
