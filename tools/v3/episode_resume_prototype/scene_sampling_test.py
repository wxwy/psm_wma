"""Fake-environment CPU proofs, not RoboCasa physical sampling acceptance."""

from __future__ import annotations

import copy
import json
import random

import pytest

from tools.v3.episode_resume_prototype.scene_sampling import (
    FRESH_SAMPLER_VERSION,
    SAMPLER_VERSION,
    derive_episode_seed,
    plan_scene_sampling,
)


def plan(
    *,
    seed=0,
    task="CloseFridge",
    indices=(3, 4),
    nonce="invocationA/attempt1",
    legacy=None,
    mode="resume_gap_independent",
):
    if legacy is None:
        legacy = (
            []
            if mode == "fresh_task_stream"
            else [{"logical_episode_index": index, "source_episode": index, "effective_seed": 0} for index in range(3)]
        )
    return plan_scene_sampling(
        task=task,
        requested_seed=seed,
        new_logical_indices=indices,
        attempt_nonce=nonce,
        legacy_sources=legacy,
        sampling_mode=mode,
    )


def test_same_logical_slot_replays_across_attempts_and_execution_order():
    original = plan(indices=(4, 3))
    retry = plan(indices=(3, 4), nonce="invocationB/attempt2")
    assert [row["logical_episode_index"] for row in original["new_episodes"]] == [3, 4]
    for old, new in zip(original["new_episodes"], retry["new_episodes"], strict=True):
        assert old["attempt_nonce"] != new["attempt_nonce"]
        for key in ("effective_seed", "seed_material_sha256", "seed_family"):
            assert old[key] == new[key]
        assert old["source_episode"] == new["source_episode"] == 0
    independent = plan(indices=(4,), nonce="worker_gpu7_invocationC")
    assert independent["new_episodes"][0]["effective_seed"] == retry["new_episodes"][1]["effective_seed"]


def test_task_logical_index_and_requested_seed_have_separate_hash_material():
    rows = [
        derive_episode_seed(requested_seed=seed, task=task, logical_episode_index=index)
        for seed in (0, 1)
        for task in ("CloseFridge", "NavigateKitchen")
        for index in (0, 1, 3, 4)
    ]
    assert len({row["seed_material_sha256"] for row in rows}) == len(rows)
    # Concrete fixture is collision-free; the plan makes no universal uint32 or
    # physical-scenario uniqueness claim from this finite sample.
    assert len({row["effective_seed"] for row in rows}) == len(rows)
    assert all(type(row["effective_seed"]) is int and 0 <= row["effective_seed"] < 2**32 for row in rows)
    assert all(row["seed_family"]["sampler_version"] == SAMPLER_VERSION for row in rows)


def test_legacy_seed_zero_unknown_and_source_indices_are_never_rewritten():
    legacy = [
        {
            "logical_episode_index": 0,
            "source_episode": 0,
            "effective_seed": 0,
            "sampling_strategy": "legacy_sequential_resets",
            "reset_ordinal": 0,
            "source": "old/CloseFridge/attempt_0001/rollout00_episode.json",
        },
        {
            "logical_episode_index": 1,
            "source_episode": 1,
            "effective_seed": None,
            "generation_rng_state": "UNKNOWN",
            "reset_ordinal": 1,
        },
        {"logical_episode_index": 2, "source_episode": 0, "effective_seed": "UNKNOWN", "old_attempt": "attempt_0002"},
    ]
    before = copy.deepcopy(legacy)
    result = plan(seed=1, legacy=legacy)
    assert result["legacy_sources"] == legacy == before
    assert [row["effective_seed"] for row in result["legacy_sources"]] == [0, None, "UNKNOWN"]
    assert [row["requested_seed"] for row in result["new_episodes"]] == [1, 1]
    result["legacy_sources"][0]["effective_seed"] = 999
    assert legacy == before


def test_all_reused_plan_has_no_new_scene_or_synthetic_seed_assignment():
    legacy = [{"source_episode": 0, "effective_seed": 0}]
    result = plan(seed=1, indices=(), legacy=legacy)
    assert result["requested_seed"] == 1
    assert result["new_episodes"] == []
    assert result["legacy_sources"] == legacy


def test_known_legacy_seed_collision_is_reported_without_changing_stable_slot_seed():
    expected = derive_episode_seed(requested_seed=0, task="CloseFridge", logical_episode_index=3)
    legacy = [{"source_episode": 0, "effective_seed": expected["effective_seed"]}]
    result = plan(indices=(3,), legacy=legacy)
    assert result["new_episodes"][0]["effective_seed"] == expected["effective_seed"]
    assert "DERIVED_SEED_MATCHES_A_KNOWN_LEGACY_ENVIRONMENT_SEED" in result["warnings"]
    assert result["legacy_sources"] == legacy


class FakeEnvironment:
    """Constructor/reset/action may all consume RNG, as a real env is free to do."""

    def __init__(self, seed):
        self.seed = seed
        self.rng = random.Random(seed)
        self.rng.random()  # Constructor draw: not a promised public reset.
        self.resets = 0

    def reset(self):
        self.resets += 1
        return self.rng.getrandbits(128)

    def action(self):
        self.rng.random()


def execute_fake_plan(result):
    observed = []
    for batch in result["execution_batches"]:
        env = FakeEnvironment(batch["effective_seed"])
        for episode in batch["episodes"]:
            scene = env.reset()
            observed.append(
                {
                    "logical_episode_index": episode["logical_episode_index"],
                    "source_episode": episode["source_episode"],
                    "actual_constructor_seed": env.seed,
                    "actual_public_resets": env.resets,
                    "environment_index": batch["batch_index"],
                    "fake_scene": scene,
                }
            )
            for _ in range(episode["logical_episode_index"] % 3 + 1):
                env.action()
    return observed


def legacy_task_trace(seed, episodes):
    env = FakeEnvironment(seed)
    observed = []
    for episode in range(episodes):
        scene = env.reset()
        observed.append(
            {
                "logical_episode_index": episode,
                "source_episode": episode,
                "actual_constructor_seed": seed,
                "actual_public_resets": env.resets,
                "environment_index": 0,
                "fake_scene": scene,
            }
        )
        for _ in range(episode % 3 + 1):
            env.action()
    return observed


@pytest.mark.parametrize("seed", [0, 1, 2**64])
def test_fresh_five_episode_task_exactly_preserves_literal_seed_one_env_and_old_reset_stream(seed):
    result = plan(seed=seed, indices=range(5), mode="fresh_task_stream")
    assert execute_fake_plan(result) == legacy_task_trace(seed, 5)
    assert result["sampler_version"] == FRESH_SAMPLER_VERSION == "legacy_task_stream"
    assert result["sampling_mode"] == "fresh_task_stream"
    assert result["warnings"] == []
    assert len(result["execution_batches"]) == 1
    batch = result["execution_batches"][0]
    assert batch["environment_constructions"] == 1 and batch["public_reset_calls"] == 5
    assert batch["effective_seed"] == seed
    assert [row["source_episode"] for row in result["new_episodes"]] == list(range(5))
    assert all(row["effective_seed"] == seed and row["seed_material_sha256"] is None for row in result["new_episodes"])


def test_four_to_eighteen_new_tasks_keep_fourteen_standard_fresh_task_streams():
    old_sources = {f"Task{task}": legacy_task_trace(0, 5) for task in range(4)}
    before = copy.deepcopy(old_sources)
    created, resets = 0, 0
    for task in range(4, 18):
        result = plan(task=f"Task{task}", indices=range(5), mode="fresh_task_stream")
        assert execute_fake_plan(result) == legacy_task_trace(0, 5)
        created += sum(batch["environment_constructions"] for batch in result["execution_batches"])
        resets += sum(batch["public_reset_calls"] for batch in result["execution_batches"])
        assert result["warnings"] == []
    assert created == 14 and resets == 70
    assert old_sources == before


@pytest.mark.parametrize("seed", [0, 1])
def test_partial_three_to_five_uses_derived_one_episode_gap_batches_only(seed):
    history = [{"logical_episode_index": index, "source_episode": index, "effective_seed": 0} for index in range(3)]
    before = copy.deepcopy(history)
    result = plan(seed=seed, legacy=history)
    assert result["legacy_sources"] == before == history
    assert result["sampling_mode"] == "resume_gap_independent"
    assert result["sampler_version"] == SAMPLER_VERSION
    assert len(result["execution_batches"]) == 2
    assert sum(batch["environment_constructions"] for batch in result["execution_batches"]) == 2
    assert all(batch["public_reset_calls"] == 1 for batch in result["execution_batches"])
    assert [row["logical_episode_index"] for row in result["new_episodes"]] == [3, 4]
    assert all(row["source_episode"] == 0 and row["requested_seed"] == seed for row in result["new_episodes"])
    assert "NOT_HISTORICAL_RNG_STREAM_CONTINUATION" in result["warnings"]
    assert execute_fake_plan(result) == execute_fake_plan(plan(seed=seed, legacy=history, nonce="retry"))
    if seed == 1:
        prior_seed_gap = plan(seed=0, legacy=history)
        assert [row["effective_seed"] for row in result["new_episodes"]] != [
            row["effective_seed"] for row in prior_seed_gap["new_episodes"]
        ]


@pytest.mark.parametrize(
    "indices,legacy",
    [
        ((3, 4), []),
        ((0, 2), []),
        ((1,), []),
        (range(5), [{"logical_episode_index": 0, "effective_seed": 0}]),
        ((), [{"source_episode": 0, "effective_seed": None}]),
    ],
)
def test_fresh_mode_refuses_resume_gaps_or_completed_history(indices, legacy):
    with pytest.raises(ValueError, match="fresh task requires"):
        plan(indices=indices, legacy=legacy, mode="fresh_task_stream")


def test_fresh_task_without_completed_episodes_restarts_full_literal_stream():
    first = plan(indices=range(5), mode="fresh_task_stream", nonce="failed-before-any-complete-episode")
    retry = plan(indices=range(5), mode="fresh_task_stream", nonce="fresh-task-retry")
    assert execute_fake_plan(first) == execute_fake_plan(retry) == legacy_task_trace(0, 5)


def test_fresh_zero_work_has_no_batch_or_derived_seed_warning():
    result = plan(indices=(), mode="fresh_task_stream")
    assert result["new_episodes"] == result["execution_batches"] == result["warnings"] == []


def test_independent_gap_requires_completed_history_instead_of_silently_changing_a_new_task():
    with pytest.raises(ValueError, match="resume gap requires"):
        plan(indices=range(5), legacy=[])


@pytest.mark.parametrize("mode", [None, "", "auto", "derived_for_every_episode"])
def test_sampling_mode_must_be_explicit(mode):
    with pytest.raises(ValueError, match="sampling_mode"):
        plan(mode=mode)


def test_omitting_sampling_mode_is_not_an_implicit_derived_seed_default():
    with pytest.raises(TypeError, match="sampling_mode"):
        plan_scene_sampling(task="CloseFridge", requested_seed=0, new_logical_indices=range(5), attempt_nonce="attempt")


def test_new_episodes_use_fresh_derived_seed_and_one_public_reset_without_replaying_legacy_prefix():
    first = execute_fake_plan(plan(seed=0))
    retry = execute_fake_plan(plan(seed=0, nonce="new attempt"))
    assert first == retry
    assert [row["logical_episode_index"] for row in first] == [3, 4]
    assert all(row["source_episode"] == 0 and row["actual_public_resets"] == 1 for row in first)
    restarted_legacy = FakeEnvironment(0).reset()
    assert all(row["fake_scene"] != restarted_legacy for row in first)


def test_burning_only_resets_is_not_a_proof_of_the_historical_rng_stream():
    historical = FakeEnvironment(0)
    historical.reset()
    historical.action()  # Missing action consumption makes reset-only replay different.
    historical.action()
    original_second_scene = historical.reset()
    replay = FakeEnvironment(0)
    replay.reset()
    incorrectly_claimed_second_scene = replay.reset()
    assert incorrectly_claimed_second_scene != original_second_scene
    assert "NOT_HISTORICAL_RNG_STREAM_CONTINUATION" in plan()["warnings"]


def test_distinct_seeds_do_not_prove_distinct_physical_scenes():
    # Deliberately finite scene catalog; a valid sampler can revisit one scene.
    result = plan(indices=range(3, 13))
    finite_scenes = [FakeEnvironment(row["effective_seed"]).reset() % 2 for row in result["new_episodes"]]
    assert len(set(finite_scenes)) < len(finite_scenes)
    assert "DISTINCT_PHYSICAL_SCENES_NOT_GUARANTEED" in result["warnings"]
    assert result["prototype_only"] is True
    assert "not a continuous" in result["benchmark_qualification"]


@pytest.mark.parametrize("seed", [0, 1, 2**32 - 1, 2**64, 2**128])
def test_current_nonnegative_seed_family_is_preserved_without_an_invented_upper_bound(seed):
    result = plan(seed=seed)
    assert result["requested_seed"] == seed
    assert all(row["requested_seed"] == seed and 0 <= row["effective_seed"] < 2**32 for row in result["new_episodes"])
    assert json.loads(json.dumps(result, allow_nan=False)) == result


@pytest.mark.parametrize("seed", [-1, True, False, None, 1.0, "0"])
def test_invalid_requested_seed_rejected(seed):
    with pytest.raises(ValueError, match="requested_seed"):
        plan(seed=seed)


@pytest.mark.parametrize("indices", [[-1], [True], [1.0], ["1"], [3, 3]])
def test_ambiguous_or_duplicate_logical_slots_rejected(indices):
    with pytest.raises(ValueError):
        plan(indices=indices)


@pytest.mark.parametrize("task", ["", " ", "../task", "task/other", " CloseFridge", "."])
def test_invalid_task_identity_rejected(task):
    with pytest.raises(ValueError, match="task"):
        plan(task=task)


@pytest.mark.parametrize("nonce", [None, "", "  ", "x" * 257])
def test_attempt_nonce_is_required_provenance_not_a_silent_seed_source(nonce):
    with pytest.raises(ValueError, match="attempt_nonce"):
        plan(nonce=nonce)
