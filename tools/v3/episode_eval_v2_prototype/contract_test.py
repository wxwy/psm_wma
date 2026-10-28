"""Design contract tests, fake environment only; no simulator/model/server."""

import copy
import random
from types import SimpleNamespace

import numpy as np
import pytest

from tools.v3.episode_eval_v2_prototype.contract import (
    EnvironmentOutcome,
    build_manifest,
    result_record,
    try_media,
    validate_manifest,
    validate_result,
)


def manifest(tasks=("CloseFridge",), episodes=3, formal=False):
    return build_manifest(
        tasks=tasks,
        episodes=episodes,
        seed=7,
        horizons={t: 2 for t in tasks},
        formal=formal,
        experiment={
            "model_digest": "1" * 64,
            "config_sha256": "2" * 64,
            "runtime_digest": "3" * 64,
            "root_sha": "a" * 40,
            "child_sha": "b" * 40,
            "task_metadata": {t: "4" * 64 for t in tasks},
        },
    )


def record(m, state, episode, *, success=True, invalid=False):
    observation = EnvironmentOutcome(m["horizons"][state["task"]])
    env = SimpleNamespace(_check_success=lambda: success)
    while not observation.check_after_step(env):
        if len(observation.checks) == observation.horizon:
            break
    return result_record(
        m,
        task=state["task"],
        episode=episode,
        generation=state["generation"],
        stream_id=state["stream_id"],
        observation=observation.finish(normal=not invalid),
        instruction="close the fridge / 实际指令",
        replans=1,
        elapsed_seconds=0.5,
    )


def test_environment_success_latch_and_horizon_failure_never_use_reward():
    high_reward = SimpleNamespace(reward=100, _check_success=lambda: False)
    result = EnvironmentOutcome(2)
    assert result.check_after_step(high_reward) is False
    assert result.check_after_step(high_reward) is False
    assert result.finish(normal=True)["outcome"] == "failure"
    success = EnvironmentOutcome(2)
    assert success.check_after_step(SimpleNamespace(reward=-100, _check_success=lambda: np.bool_(True)))
    assert success.finish(normal=True)["outcome"] == "success"
    with pytest.raises(ValueError, match="latch"):
        success.check_after_step(high_reward)


def test_environment_predicate_exception_is_invalid_not_behavioral_failure():
    def fail():
        raise RuntimeError("predicate failed")

    observation = EnvironmentOutcome(2)
    with pytest.raises(RuntimeError, match="predicate failed"):
        observation.check_after_step(SimpleNamespace(_check_success=fail))
    row = observation.finish(normal=False, error="RuntimeError: predicate failed")
    assert row["outcome"] == "invalid" and row["steps"] == 0


@pytest.mark.parametrize("value", [None, 1, "success", [], {}])
def test_invalid_success_types_never_coerce_to_success(value):
    with pytest.raises(ValueError):
        EnvironmentOutcome(2).check_after_step(SimpleNamespace(_check_success=lambda: value))


@pytest.mark.parametrize(
    "normal,error,cleanup", [(False, None, True), (True, "inference error", True), (True, None, False)]
)
def test_runtime_or_local_error_is_invalid_even_if_environment_latched(normal, error, cleanup):
    observation = EnvironmentOutcome(2)
    observation.check_after_step(SimpleNamespace(_check_success=lambda: True))
    row = observation.finish(normal=normal, error=error, cleanup_ok=cleanup)
    assert row["environment_success"] is True and row["outcome"] == "invalid"


def test_early_normal_exit_without_success_is_invalid_not_horizon_failure():
    observation = EnvironmentOutcome(2)
    observation.check_after_step(SimpleNamespace(_check_success=lambda: False))
    assert observation.finish(normal=True)["outcome"] == "invalid"


@pytest.mark.parametrize(
    "bad",
    [
        "outcome",
        "environment_success",
        "steps",
        "seed",
        "completion",
        "reset_index",
        "manifest_digest",
        "checks",
        "duration",
    ],
)
def test_complete_result_cannot_contradict_authority_or_identity(bad):
    m = manifest()
    state = dict(task="CloseFridge", generation=0, stream_id="1" * 32)
    row = record(m, state, 0)
    if bad == "checks":
        row["success_checks"] = [True, False]
    elif bad == "duration":
        row["elapsed_seconds"] = float("nan")
    else:
        row[bad] = {
            "outcome": "failure",
            "environment_success": False,
            "steps": True,
            "seed": 8,
            "completion": "official_horizon",
            "reset_index": 1,
            "manifest_digest": "0" * 64,
        }[bad]
    with pytest.raises(ValueError):
        validate_result(m, row)


@pytest.mark.parametrize(
    "key", ["model_digest", "config_sha256", "runtime_digest", "root_sha", "child_sha", "task_metadata"]
)
def test_every_experiment_binding_changes_new_run_identity(key):
    value = manifest()
    before = value["digest"]
    experiment = copy.deepcopy(value["experiment"])
    if key == "task_metadata":
        experiment[key]["CloseFridge"] = "5" * 64
    else:
        experiment[key] = "c" * (40 if key.endswith("_sha") else 64)
    new = build_manifest(tasks=value["tasks"], episodes=3, seed=7, horizons=value["horizons"], experiment=experiment)
    assert new["digest"] != before


def test_formal900_is_an_exact_new_plan_not_canary_or_extended_old_run():
    tasks = tuple(f"Task{i:02d}" for i in range(18))
    m = manifest(tasks, 50, formal=True)
    assert m["scope"] == "formal900_design"
    with pytest.raises(ValueError, match="18Task"):
        manifest(tasks, 49, formal=True)
    changed = copy.deepcopy(m)
    changed["protocol"]["resume"] = "skip_reset_stream"
    with pytest.raises(ValueError):
        validate_manifest(changed)


@pytest.mark.parametrize("failure", [False, True])
def test_media_does_not_change_result_or_python_numpy_rng(failure):
    m = manifest()
    row = record(m, dict(task="CloseFridge", generation=0, stream_id="1" * 32), 0)
    before = copy.deepcopy(row)
    random.seed(9)
    np.random.seed(9)
    python_rng, numpy_rng = random.getstate(), np.random.get_state()

    def writer():
        random.random()
        np.random.rand()
        if failure:
            raise OSError("encoder failed")

    diagnostic = try_media(writer)
    assert diagnostic["status"] == ("error" if failure else "saved")
    assert random.getstate() == python_rng
    assert np.array_equal(np.random.get_state()[1], numpy_rng[1])
    assert row == before


def test_interrupt_during_media_is_not_swallowed_and_rng_is_restored():
    before = random.getstate()

    def interrupted():
        random.random()
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        try_media(interrupted)
    assert random.getstate() == before


@pytest.mark.parametrize("failure", [False, True])
def test_media_preserves_already_loaded_torch_cpu_rng_without_cuda(failure):
    import torch

    torch.manual_seed(41)
    before = torch.get_rng_state().clone()

    def writer():
        torch.rand(8)
        if failure:
            raise RuntimeError("diagnostic failure")

    assert try_media(writer)["status"] == ("error" if failure else "saved")
    assert torch.equal(torch.get_rng_state(), before)
    assert not torch.cuda.is_initialized()
