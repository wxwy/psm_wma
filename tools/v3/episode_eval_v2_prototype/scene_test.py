"""Synthetic reset-stream witness, not RoboCasa physics/RNG equivalence."""

import random

from tools.v3.episode_eval_v2_prototype.contract import EnvironmentOutcome, result_record, try_media
from tools.v3.episode_eval_v2_prototype.contract_test import manifest
from tools.v3.episode_eval_v2_prototype.store import Store


class FakeEnvironment:
    def __init__(self, seed):
        self.rng, self.episode, self.steps = random.Random(seed), -1, 0
        self.reset_calls = 0

    def reset(self):
        self.episode += 1
        self.steps = 0
        self.reset_calls += 1
        self.instruction = f"actual language for scene_{self.rng.random():.12f}"

    def completed_action(self):
        self.rng.random()  # Stepping can advance state needed for later resets.
        self.steps += 1

    def _check_success(self):
        return self.episode % 2 == 0 and self.steps >= 1


def mock_task(store, state, media=None, limit=None):
    assert state["action"] != "reuse_complete_task"
    env = FakeEnvironment(store.manifest["seed"])
    scenes, policy_draws = [], []
    for index in range(limit or store.manifest["episodes_per_task"]):
        env.reset()
        scenes.append(env.instruction)
        observation = EnvironmentOutcome(store.manifest["horizons"][state["task"]])
        for _ in range(observation.horizon):
            policy_draws.append(random.random())
            env.completed_action()
            if media is not None:
                try_media(media)
            if observation.check_after_step(env):
                break
        store.commit(
            result_record(
                store.manifest,
                task=state["task"],
                episode=index,
                generation=state["generation"],
                stream_id=state["stream_id"],
                observation=observation.finish(normal=True),
                instruction=env.instruction,
                replans=1,
                elapsed_seconds=0,
            )
        )
    return env, scenes, policy_draws


def test_single_construction_50_continuous_resets_no_per_episode_derived_seed(tmp_path):
    m = manifest(episodes=50)
    store = Store(tmp_path / "fifty", m)
    store.create()
    with store.locked():
        state = store.begin_task("CloseFridge")
        env, scenes, _ = mock_task(store, state)
        assert env.reset_calls == len(scenes) == 50
        rows = store.rows("CloseFridge")
        assert {row["seed"] for row in rows} == {7}
        assert [row["reset_index"] for row in rows] == list(range(50))
        assert len({row["stream_id"] for row in rows}) == 1
        assert store.publish_views()["sr"] == 0.5
    with Store(store.root, m).locked() as resumed:
        assert resumed.begin_task("CloseFridge")["action"] == "reuse_complete_task"


def test_restart_replays_full_task_seed_instead_of_fake_gap_scene_continuation(tmp_path):
    m = manifest(episodes=5)
    store = Store(tmp_path / "interrupted", m)
    store.create()
    with store.locked():
        first = store.begin_task("CloseFridge")
        _, old, _ = mock_task(store, first, limit=2)
    with Store(store.root, m).locked() as resumed:
        second = resumed.begin_task("CloseFridge")
        env, full, _ = mock_task(resumed, second)
        assert full[:2] == old and second["stream_id"] != first["stream_id"]
        assert len(resumed.rows("CloseFridge")) == 5 and env.reset_calls == 5
    reset_only = FakeEnvironment(7)
    for _ in range(3):
        reset_only.reset()
    assert reset_only.instruction != full[2], "reset-only skipping is not proven equivalent to stepped RNG"


def test_media_options_or_encoder_failure_leave_same_scene_actions_and_rng_draws(tmp_path):
    m = manifest(episodes=5)
    values = []
    for name, media in (
        ("off", None),
        ("save", lambda: random.random()),
        ("error", lambda: (_ for _ in ()).throw(OSError("encoder error"))),
    ):
        store = Store(tmp_path / name, m)
        store.create()
        random.seed(31)
        with store.locked():
            state = store.begin_task("CloseFridge")
            _, scenes, actions = mock_task(store, state, media=media)
            values.append((scenes, actions, random.getstate(), store.publish_views()["sr"]))
    assert values[0] == values[1] == values[2]
