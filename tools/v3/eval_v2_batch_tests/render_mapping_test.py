"""Config, resource admission and real actor-config wiring without GPUs."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from cosmos_framework.evaluation.robocasa_v2.contract import (
    build_manifest,
    validate_manifest,
)
from cosmos_framework.evaluation.robocasa_v2.store import Store, save
from robocasa_eval_v2 import resources
from robocasa_eval_v2.cli import main
from robocasa_eval_v2.config import execution, rendering, resolve
from robocasa_eval_v2.identity import ATOMIC_TASKS
from robocasa_eval_v2.runtime import Runtime

from tools.v3.eval_v2_batch_tests.rollout_policy_test import configuration
from tools.v3.eval_v2_production_tests.contract_test import manifest


def resolved(tmp_path, **changes):
    path = configuration(
        tmp_path,
        execution_profile="phase_b",
        gpu_ids=[4, 5],
        render_gpu_ids=[6, 7],
        render_backend="egl",
        sims_per_gpu=8,
        max_infer_batch_size=2,
        tasks="all",
    )
    raw = yaml.safe_load(path.read_text())
    raw.update(changes)
    path.write_text(yaml.safe_dump(raw))
    return path, resolve(["dry-run", "--config", str(path)])[1]


@pytest.mark.parametrize(
    "gpus,renders,m,b",
    [([4, 5], [6, 7], 8, 2), ([2], [3], 1, 1), ([2, 3, 4], [5, 5, 6], 3, 4)],
)
def test_counts_roles_and_batch_remain_independent(tmp_path, gpus, renders, m, b):
    _, cfg = resolved(
        tmp_path,
        gpu_ids=gpus,
        render_gpu_ids=renders,
        sims_per_gpu=m,
        max_infer_batch_size=b,
    )
    slots = resources.physical_slots(cfg, 18)
    mapping = dict(zip(gpus, renders))
    assert len(slots) == min(len(gpus) * m, 18)
    assert resources.render_slots(cfg, 18) == {s: mapping[g] for s, g in slots.items()}
    assert cfg["max_infer_batch_size"] == b


@pytest.mark.parametrize(
    "field,value",
    [
        ("render_backend", "glfw"),
        ("render_backend", True),
        ("render_gpu_ids", []),
        ("render_gpu_ids", [6]),
        ("render_gpu_ids", [6, -1]),
        ("render_gpu_ids", [6, True]),
        ("render_gpu_ids", "6,7"),
        ("render_gpu_ids", [6.0, 7]),
        ("server_reserve_bytes", -1),
        ("server_reserve_bytes", True),
        ("render_reserve_bytes_per_sim", 0.5),
    ],
)
def test_bad_render_policy_is_rejected_before_runtime(tmp_path, field, value):
    with pytest.raises(ValueError):
        resolved(tmp_path, **{field: value})
    assert not (tmp_path / "run").exists()


def test_osmesa_and_legacy_environment_defaults_are_explicit(tmp_path, monkeypatch):
    path, cfg = resolved(tmp_path, render_backend="osmesa", render_gpu_ids=None)
    assert rendering(cfg) == {"backend": "osmesa", "gpu_ids": []}
    assert set(resources.render_slots(cfg, 18).values()) == {None}
    with pytest.raises(ValueError, match="OSMesa"):
        resolved(tmp_path, render_backend="osmesa")
    raw = yaml.safe_load(path.read_text())
    raw.pop("render_backend")
    raw.pop("render_gpu_ids")
    path.write_text(yaml.safe_dump(raw))
    monkeypatch.setenv("MUJOCO_GL", "osmesa")
    cfg = resolve(["dry-run", "--config", str(path)])[1]
    assert cfg["render_backend"] == "osmesa" and cfg["render_gpu_ids"] == []
    monkeypatch.setenv("MUJOCO_GL", "egl")
    cfg = resolve(["dry-run", "--config", str(path)])[1]
    assert cfg["render_gpu_ids"] == cfg["gpu_ids"]


def test_cli_render_overrides_and_preview_have_no_hardware_side_effects(
    tmp_path, capsys
):
    path, cfg = resolved(tmp_path)
    for task in ATOMIC_TASKS:
        metadata = (
            tmp_path / f"absent_inputs/dataset/{task}/lerobot/extras/dataset_meta.json"
        )
        metadata.parent.mkdir(parents=True)
        metadata.write_text(json.dumps({"env_args": {"env_name": task}}))

    def forbidden(*a, **k):
        pytest.fail("preview must not probe a GPU or load a model")

    assert (
        main(
            ["dry-run", "--config", str(path), "--render-gpus", "7,6"],
            prepare_inputs=forbidden,
            runtime_type=forbidden,
        )
        == 0
    )
    preview = json.loads(capsys.readouterr().out)
    assert len(preview["physical_slots"]) == 16
    assert set(preview["physical_slots"].values()) == {4, 5}
    assert set(preview["render_slots"].values()) == {6, 7}
    assert preview["render_slots"]["GPU4_S0"] == 7
    assert preview["resolved"]["render_gpu_ids"] == [7, 6]
    assert preview["models_loaded"] == preview["environments_created"] == 0
    assert not (tmp_path / "run").exists()


def store_cfg(tmp_path):
    _, cfg = resolved(tmp_path)
    m = manifest(tasks=ATOMIC_TASKS, episodes=50)
    m = build_manifest(
        tasks=m["tasks"],
        episodes=50,
        seed=m["seed"],
        horizons=m["horizons"],
        experiment=m["experiment"],
        execution=execution(cfg),
    )
    store = Store(tmp_path / "run", m)
    store.create()
    save(
        store.root / "_internal/invocations/0001.json",
        {"mode": "fresh", "resolved": cfg},
    )
    return store, cfg


@pytest.mark.parametrize(
    "change",
    [{"render_gpu_ids": [7, 6]}, {"render_backend": "osmesa", "render_gpu_ids": []}],
)
def test_same_run_render_drift_is_rejected_and_correct_resume_still_works(
    tmp_path, change
):
    store, cfg = store_cfg(tmp_path)
    changed = {**cfg, **change}
    save(
        store.root / "_internal/invocations/0000.json",
        {"mode": "resume", "resolved": changed},
    )
    with pytest.raises(ValueError, match="render policy differs"):
        Runtime(store, changed, {}, {})
    Runtime(store, cfg, {}, {})


def test_old_run_cannot_silently_adopt_explicit_render_roles(tmp_path):
    store, cfg = store_cfg(tmp_path)
    old = copy.deepcopy(cfg)
    old.pop("render_backend")
    old.pop("render_gpu_ids")
    path = store.root / "_internal/invocations/0001.json"
    path.unlink()  # Synthetic record replacement only.
    save(path, {"mode": "fresh", "resolved": old})
    with pytest.raises(ValueError, match="requires a new Run"):
        Runtime(store, cfg, {}, {})


def test_actual_actor_configuration_and_environment_use_independent_roles(
    tmp_path, monkeypatch
):
    store, cfg = store_cfg(tmp_path)
    runtime = Runtime(
        store,
        cfg,
        {
            "tasks": {t: "/unread/" + t for t in ATOMIC_TASKS},
            "simulation_libraries": {},
            "runtime": {"digest": "1" * 64},
        },
        {"MUJOCO_EGL_DEVICE_ID": "99"},
    )
    monkeypatch.setattr(runtime, "_server", lambda w: (None, {}, 8912))
    monkeypatch.setattr(
        resources,
        "gpu_identity",
        lambda g: {"gpu_id": g, "uuid": f"GPU-{g}", "pci_bus_id": f"0000:{g:02x}:00.0"},
    )
    launches = []

    class BeforeProcess(Exception):
        pass

    def start(command, **kw):
        assert command[2:4] == [
            "-m",
            "cosmos_framework.simulation.robocasa.eval_v2_worker",
        ]
        path = command[command.index("--config") + 1]
        launches.append((json.loads(Path(path).read_text()), kw["env"]))
        raise BeforeProcess

    monkeypatch.setattr(runtime.registry, "start", start)
    try:
        with store.locked():
            for worker in runtime.workers:
                with pytest.raises(BeforeProcess):
                    runtime._actor({"task": ATOMIC_TASKS[0], "physical_worker": worker})
    finally:
        for stream in runtime.logs:
            stream.close()
    assert len(launches) == 16
    for actor, env in launches:
        server_gpu = actor["gpu_id"]
        assert server_gpu in (4, 5)
        assert actor["rendering"]["server_gpu_id"] == server_gpu
        assert actor["rendering"]["render_gpu_id"] == {4: 6, 5: 7}[server_gpu]
        assert actor["rendering"]["expected_device"]["gpu_id"] in (6, 7)
        assert env["CUDA_VISIBLE_DEVICES"] == ""
        assert env["MUJOCO_GL"] == env["PYOPENGL_PLATFORM"] == "egl"
        assert (
            "MUJOCO_EGL_DEVICE_ID" not in env
        )  # Worker must resolve the EGL enumeration.


def resource_cfg():
    return {
        "gpu_ids": [4, 5],
        "render_gpu_ids": [6, 7],
        "render_backend": "egl",
        "execution_profile": "phase_b",
        "sims_per_gpu": 8,
        "tasks": "all",
        "max_gpu_fraction": 0.85,
        "max_rss_bytes": 2**40,
        "server_reserve_bytes": 10 * 1024**3,
        "render_reserve_bytes_per_sim": 800 * 1024**2,
    }


def probe(*, missing=False, used_render=0, apps=""):
    calls = []

    def run(args, **kw):
        calls.append(args)
        if any("query-compute-apps" in a for a in args):
            return SimpleNamespace(stdout=apps)
        rows = [
            f"{i}, GPU-{i}, 81920, {used_render if i in (6, 7) else 0}"
            for i in (4, 5, 6, 7)
            if not (missing and i == 6)
        ]
        return SimpleNamespace(stdout="\n".join(rows))

    return run, calls


def test_union_memory_admission_budgets_roles_without_querying_gpu_zero_to_three():
    run, calls = probe()
    result = resources.check(resource_cfg(), before_models=True, run=run)
    assert result["reserves"] == {
        4: 10 * 1024**3,
        5: 10 * 1024**3,
        6: 8 * 800 * 1024**2,
        7: 8 * 800 * 1024**2,
    }
    assert calls[0][1:3] == ["-i", "4,5,6,7"]
    assert calls[1][1:3] == ["-i", "6,7"]


@pytest.mark.parametrize(
    "options", [{"missing": True}, {"used_render": 70000}, {"apps": "GPU-6, 123456"}]
)
def test_missing_render_gpu_budget_or_foreign_cuda_is_blocked(options):
    run, _ = probe(**options)
    with pytest.raises(RuntimeError, match="BLOCKED_RESOURCE"):
        resources.check(resource_cfg(), before_models=True, run=run)


def test_owned_model_cuda_on_a_deliberately_shared_render_gpu_is_permitted(monkeypatch):
    cfg = resource_cfg()
    cfg["render_gpu_ids"] = [4, 5]
    run, _ = probe(apps="GPU-4, 123456")
    monkeypatch.setattr(resources, "group_members", lambda pgid: {123456})
    result = resources.check(cfg, [SimpleNamespace(pgid=123456)], run=run)
    assert result["owned_pids"] == [123456]


def test_physical_identity_uses_pci_and_uuid_not_an_assumed_egl_index():
    def run(args, **kw):
        assert args[1:3] == ["-i", "6"]
        return SimpleNamespace(stdout="6, GPU-render-six, 00000000:AF:00.0")

    assert resources.gpu_identity(6, run=run) == {
        "gpu_id": 6,
        "uuid": "GPU-render-six",
        "pci_bus_id": "0000:af:00.0",
    }


@pytest.mark.parametrize(
    "policy",
    [
        {"backend": "egl", "gpu_ids": [6, 7]},
        {"backend": "egl", "gpu_ids": [7, 6]},
        {"backend": "osmesa", "gpu_ids": []},
    ],
)
def test_new_run_manifest_digest_binds_backend_and_ordered_render_roles(policy):
    m = manifest()
    args = dict(
        tasks=m["tasks"],
        episodes=m["episodes_per_task"],
        seed=m["seed"],
        horizons=m["horizons"],
        experiment=m["experiment"],
    )
    old = build_manifest(**args)
    new = build_manifest(**args, rendering=policy)
    assert validate_manifest(new) == new
    assert old["digest"] != new["digest"]
    other = {"backend": "egl", "gpu_ids": [8, 9]}
    assert new["digest"] != build_manifest(**args, rendering=other)["digest"]


@pytest.mark.parametrize(
    "policy",
    [
        {"backend": "egl", "gpu_ids": []},
        {"backend": "osmesa", "gpu_ids": [6]},
        {"backend": "egl", "gpu_ids": [True]},
        {"backend": "egl", "gpu_ids": [-1]},
        {"backend": "egl", "gpu_ids": [6], "ignored": True},
    ],
)
def test_manifest_rejects_incomplete_or_malformed_render_identity(policy):
    m = manifest()
    with pytest.raises(ValueError, match="render backend"):
        build_manifest(
            tasks=m["tasks"],
            episodes=3,
            seed=m["seed"],
            horizons=m["horizons"],
            experiment=m["experiment"],
            rendering=policy,
        )


def test_runtime_refuses_render_roles_different_from_frozen_manifest(tmp_path):
    store, cfg = store_cfg(tmp_path)
    m = store.manifest
    changed = build_manifest(
        tasks=m["tasks"],
        episodes=50,
        seed=m["seed"],
        horizons=m["horizons"],
        experiment=m["experiment"],
        execution=execution(cfg),
        rendering={"backend": "egl", "gpu_ids": [7, 6]},
    )
    store = Store(tmp_path / "different-frozen-run", changed)
    with pytest.raises(ValueError, match="frozen manifest"):
        Runtime(store, cfg, {}, {})
