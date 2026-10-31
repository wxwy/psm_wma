"""Issue14: real config/runtime/adapter paths; synthetic inputs and no encoder."""

import json
import sys
from pathlib import Path

import pytest
import yaml
from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest
from cosmos_framework.evaluation.robocasa_v2.media import MediaSink
from cosmos_framework.evaluation.robocasa_v2.store import Store, write
from cosmos_framework.simulation.robocasa import closed_loop_eval as native
from cosmos_framework.simulation.robocasa.eval_v2_adapter import NativeEpisode
from robocasa_eval_v2 import runtime as runtime_module
from robocasa_eval_v2.cli import main
from robocasa_eval_v2.config import execution, resolve
from robocasa_eval_v2.runtime import Runtime

from tools.v3.eval_v2_production_tests.contract_test import manifest
from tools.v3.eval_v2_production_tests import native_test
from tools.v3.eval_v2_production_tests.native_test import Env, server

FIELD = "rollout_mp4_first_n_per_task"
TASKS = ("CloseFridge", "OpenCabinet")


def configuration(tmp_path, **changes):
    inputs = tmp_path / "absent_inputs"
    cfg = {
        "checkpoint": str(inputs / "checkpoint"),
        "config_file": str(inputs / "model.yaml"),
        "dataset_root": str(inputs / "dataset"),
        "vendor_lock": str(inputs / "vendor.lock"),
        "output_dir": str(tmp_path / "run"),
        "server_python": sys.executable,
        "sim_python": sys.executable,
        "tasks": list(TASKS),
        "episodes_per_task": 50,
        **changes,
    }
    path = tmp_path / "eval.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return path


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("explicit_null", [False, True])
def test_omitted_and_null_preserve_legacy_boolean(tmp_path, enabled, explicit_null):
    changes = {"save_rollout_mp4": enabled}
    if explicit_null:
        changes[FIELD] = None
    path = configuration(tmp_path, **changes)
    _, cfg = resolve(["dry-run", "--config", str(path)])
    assert cfg[FIELD] is None and cfg["save_rollout_mp4"] is enabled


@pytest.mark.parametrize("limit", [0, 3, 50])
def test_exact_integer_limits_are_accepted(tmp_path, limit):
    path = configuration(tmp_path, **{FIELD: limit})
    _, cfg = resolve(["dry-run", "--config", str(path)])
    assert type(cfg[FIELD]) is int and cfg[FIELD] == limit


@pytest.mark.parametrize("limit", [-1, 51, 3.0, "3", True, False, [3], {"n": 3}])
def test_invalid_limit_types_and_range_are_rejected(tmp_path, limit):
    path = configuration(tmp_path, **{FIELD: limit})
    with pytest.raises(ValueError, match=FIELD):
        resolve(["dry-run", "--config", str(path)])
    assert not (tmp_path / "run").exists()


@pytest.mark.parametrize("limit", [0, 3, 50])
def test_disabled_rollout_with_any_nonnull_limit_is_rejected(tmp_path, limit):
    path = configuration(tmp_path, save_rollout_mp4=False, **{FIELD: limit})
    with pytest.raises(ValueError, match=FIELD):
        resolve(["fresh", "--config", str(path)])


def test_limit_is_checked_after_cli_episode_override(tmp_path):
    path = configuration(tmp_path, **{FIELD: 3})
    with pytest.raises(ValueError, match=FIELD):
        resolve(["resume", "--config", str(path), "--episodes", "2"])
    _, cfg = resolve(["resume", "--config", str(path), "--episodes", "3"])
    assert cfg[FIELD] == cfg["episodes_per_task"] == 3


def test_public_dry_run_reports_policy_without_model_or_runtime(tmp_path, capsys):
    path = configuration(tmp_path, episodes_per_task=5, **{FIELD: 3})
    for task in TASKS:
        meta = (
            tmp_path / f"absent_inputs/dataset/{task}/lerobot/extras/dataset_meta.json"
        )
        meta.parent.mkdir(parents=True)
        meta.write_text(json.dumps({"env_args": {"env_name": task}}))

    def forbidden(*a, **kw):
        pytest.fail("dry-run cannot prepare model inputs or start runtime")

    assert (
        main(
            ["dry-run", "--config", str(path)],
            prepare_inputs=forbidden,
            runtime_type=forbidden,
        )
        == 0
    )
    preview = json.loads(capsys.readouterr().out)
    assert preview["resolved"][FIELD] == 3
    assert preview["resolved"]["save_generated_video"] == "first"
    assert preview["slots"] == [[task, ep] for ep in range(5) for task in TASKS]
    assert preview["models_loaded"] == preview["environments_created"] == 0
    assert not Path(preview["resolved"]["checkpoint"]).exists()
    assert not Path(preview["resolved"]["config_file"]).exists()
    assert not (tmp_path / "run").exists()


def runtime_inputs(tmp_path, limit, *, profile="phase_a", legacy=False):
    path = configuration(
        tmp_path,
        execution_profile=profile,
        gpu_ids=[4, 5],
        sims_per_gpu=2 if profile == "phase_b" else 1,
        **{FIELD: limit},
    )
    _, cfg = resolve(["fresh", "--config", str(path)])
    m = manifest(tasks=TASKS, episodes=50)
    m = build_manifest(
        tasks=m["tasks"],
        episodes=m["episodes_per_task"],
        seed=m["seed"],
        horizons=m["horizons"],
        experiment=m["experiment"],
        execution=execution(cfg),
    )
    store = Store(Path(cfg["output_dir"]), m)
    store.create()
    initial = dict(cfg)
    if legacy:
        initial.pop(FIELD)
    write(
        store.root / "_internal/invocations/0001.json",
        {"mode": "fresh", "resolved": initial},
    )
    return store, cfg


@pytest.mark.parametrize("before,after", [(3, 0), (3, None), (None, 3), (0, None)])
def test_resume_cap_drift_is_rejected_and_bad_invocation_cannot_poison_anchor(
    tmp_path, monkeypatch, before, after
):
    store, cfg = runtime_inputs(tmp_path, before, legacy=before is None)
    anchor = (store.root / "_internal/invocations/0001.json").read_bytes()
    changed = {**cfg, FIELD: after}
    # A rejected Resume is still an invocation in the existing CLI. Give it an
    # earlier filename too: selection must use mode=fresh, not filename order.
    write(
        store.root / "_internal/invocations/0000.json",
        {"mode": "resume", "resolved": changed},
    )
    with monkeypatch.context() as patch:
        patch.setattr(
            runtime_module,
            "Registry",
            lambda *a: pytest.fail("drift must fail before process setup"),
        )
        with pytest.raises(ValueError, match="rollout cap differs"):
            Runtime(store, changed, {}, {})
    Runtime(store, cfg, {}, {})
    assert (store.root / "_internal/invocations/0001.json").read_bytes() == anchor


def test_legacy_missing_cap_keeps_boolean_and_generated_resume_choices(tmp_path):
    store, cfg = runtime_inputs(tmp_path, None, legacy=True)
    Runtime(
        store,
        {**cfg, "save_rollout_mp4": False, "save_generated_video": "none"},
        {},
        {},
    )


def test_nonnull_cap_cannot_adopt_run_without_fresh_record(tmp_path):
    store, cfg = runtime_inputs(tmp_path, 3)
    (store.root / "_internal/invocations/0001.json").unlink()
    with pytest.raises(ValueError, match="Fresh Run configuration record"):
        Runtime(store, cfg, {}, {})
    Runtime(store, {**cfg, FIELD: None}, {}, {})  # Legacy null behavior remains.


def test_corrupt_boolean_in_initial_cap_is_not_equal_to_integer_one(tmp_path):
    store, cfg = runtime_inputs(tmp_path, 1)
    # Retained synthetic corruption, not a production/history edit.
    path = store.root / "_internal/invocations/0001.json"
    row = json.loads(path.read_text())
    row["resolved"][FIELD] = True
    path.write_text(json.dumps(row))
    with pytest.raises(ValueError, match="rollout cap differs"):
        Runtime(store, cfg, {}, {})


@pytest.mark.parametrize("profile", ["phase_a", "phase_b"])
@pytest.mark.parametrize("limit", [None, 0, 3])
def test_every_physical_actor_receives_static_limit(
    tmp_path, monkeypatch, profile, limit
):
    store, cfg = runtime_inputs(tmp_path, limit, profile=profile)
    inputs = {
        "tasks": {task: "/unread/synthetic/" + task for task in TASKS},
        "simulation_libraries": {},
        "runtime": {"digest": "1" * 64},
    }
    runtime = Runtime(store, cfg, inputs, {})
    monkeypatch.setattr(runtime, "_server", lambda worker: (None, {}, 8912))
    captured = []

    class CapturedBeforeProcess(Exception):
        pass

    def capture(path, value):
        assert path.parent.name == "actor_configs"
        captured.append(value)
        raise CapturedBeforeProcess

    monkeypatch.setattr(runtime_module, "write", capture)
    for worker in runtime.workers:
        with pytest.raises(CapturedBeforeProcess):
            runtime._actor({"task": TASKS[0], "physical_worker": worker})
    assert {row["physical_worker"] for row in captured} == set(runtime.workers)
    for row in captured:
        assert row["settings"][FIELD] == limit
        assert row["settings"]["save_generated_video"] == "first"
    assert not runtime.actors and not runtime.logs


class CapturedMedia(MediaSink):
    """Keep real frame/prediction selection; replace only encoder submission."""

    def __init__(self, directory, *, rollout, generated, grace_s):
        self.rollout, self.generated = rollout, generated
        self.errors, self.queued = [], []
        self.dropped = 0

    def _submit(self, kind, payload):
        self.queued.append(kind)  # No queue, subprocess, decoding or video copy.

    def close(self):
        return {"errors": self.errors, "helper_pids": []}


@pytest.mark.parametrize(
    "limit,enabled", [(None, True), (None, False), (0, True), (3, True), (50, True)]
)
@pytest.mark.parametrize("generated", ["none", "first", "all"])
def test_reused_native_episode_uses_task_logical_index_not_completion_order(
    tmp_path, monkeypatch, limit, enabled, generated
):
    monkeypatch.setattr(native, "build_state_token", lambda _: [0.0] * 15)
    sinks = []

    def media_factory(*a, **kw):
        sinks.append(CapturedMedia(*a, **kw))
        return sinks[-1]

    def policy(*a, **kw):
        prediction = kw["on_prediction"]
        kw["on_prediction"] = lambda result, latency: prediction(
            {**result, "video": ["synthetic diagnostic payload; never decoded"]},
            latency,
        )
        return native.run_policy(*a, **kw)

    env = Env()
    # Two Task names in Episode-major order, then a Retry/Resume of the same
    # logical index with fresh attempt IDs. One engine/settings is reused.
    slots = [(task, ep) for ep in (0, 1, 2, 3, 49) for task in TASKS]
    slots += [(TASKS[0], 1), (TASKS[1], 3)]
    with server() as (url, calls):
        engine = NativeEpisode(
            env,
            {
                "server_url": url,
                "horizon": 2,
                "predict_timeout_s": 2.0,
                "save_rollout_mp4": enabled,
                FIELD: limit,
                "save_generated_video": generated,
            },
            policy=policy,
            media_factory=media_factory,
        )
        for order, (task, episode) in enumerate(slots):
            env.success_at = 1 if episode % 2 == 0 else 100
            assert engine.initialize()["initial_success"] is False
            directory = tmp_path / f"attempt_{order}"
            result = engine.execute(
                {
                    "task": task,
                    "episode": episode,
                    "attempt_id": f"{order:032x}",
                    "stream_id": "1" * 32,
                    "seed": 7,
                    "manifest_digest": "2" * 64,
                },
                reset_index=order,
                directory=directory,
            )
            expected = enabled and (limit is None or episode < limit)
            assert sinks[-1].rollout is expected
            assert ("frame" in sinks[-1].queued) is expected
            assert ("prediction" in sinks[-1].queued) is (generated != "none")
            assert result["observation"]["outcome"] == (
                "success" if episode % 2 == 0 else "failure"
            )
            assert result["local_session"]["reset_ack"] is True
            diagnostics = json.loads((directory / "media_diagnostics.json").read_text())
            assert diagnostics["rollout_requested"] is expected
            assert diagnostics[FIELD] == limit
            assert calls[-1]["_local_memory_command"] == "reset"
        assert len(sinks) == len(slots)
        assert sum(row.get("_local_memory_command") == "reset" for row in calls) == len(
            slots
        )
    assert not list(tmp_path.rglob("*.mp4"))  # Encoder replaced; no actual MP4s.


@pytest.mark.parametrize("failure", ["constructor", "callbacks"])
def test_media_failure_with_cap_zero_preserves_real_core_commit_and_local_reset(
    tmp_path, monkeypatch, failure
):
    def capped_engine(env, settings, **kw):
        return NativeEpisode(
            env,
            {
                **settings,
                "save_rollout_mp4": True,
                FIELD: 0,
                "save_generated_video": "first",
            },
            **kw,
        )

    def broken_factory(*a, **kw):
        raise OSError("synthetic encoder initialization failure")

    monkeypatch.setattr(native_test, "NativeEpisode", capped_engine)
    row, _, calls, store = native_test.native_execute(
        tmp_path,
        monkeypatch,
        media_factory=broken_factory
        if failure == "constructor"
        else native_test.BadMedia,
    )
    assert row["outcome"] == "success" and row["steps"] == 2
    assert calls[-1]["_local_memory_command"] == "reset"
    assert len(store.rows("CloseFridge")) == 1
    diagnostic = json.loads(
        (store._slot("CloseFridge", 0) / "media_diagnostics.json").read_text()
    )
    assert diagnostic["rollout_requested"] is False and diagnostic[FIELD] == 0
    assert not list(store.root.rglob("*.mp4"))
