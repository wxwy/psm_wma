"""Fake-environment CPU proofs, not RoboCasa physical sampling acceptance."""

from __future__ import annotations

import copy
import json
import random

import pytest

from tools.v3.episode_resume_prototype.scene_sampling import SAMPLER_VERSION, derive_episode_seed, plan_scene_sampling


def plan(*, seed=0, task="CloseFridge", indices=(3, 4), nonce="invocationA/attempt1", legacy=()):
    return plan_scene_sampling(
        task=task, requested_seed=seed, new_logical_indices=indices, attempt_nonce=nonce, legacy_sources=legacy
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
    for episode in result["new_episodes"]:
        env = FakeEnvironment(episode["effective_seed"])
        scene = env.reset()
        observed.append(
            {
                "logical_episode_index": episode["logical_episode_index"],
                "source_episode": 0,
                "actual_constructor_seed": env.seed,
                "actual_public_resets": env.resets,
                "fake_scene": scene,
            }
        )
    return observed


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
    result = plan(indices=range(10))
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
