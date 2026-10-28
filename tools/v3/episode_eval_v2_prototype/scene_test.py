"""Synthetic continuity within a stream; never promises old-scene reproduction."""

import random

from tools.v3.episode_eval_v2_prototype.admission import admit_scene
from tools.v3.episode_eval_v2_prototype.contract import EnvironmentOutcome, result_record, try_media
from tools.v3.episode_eval_v2_prototype.store import Store
from tools.v3.episode_eval_v2_prototype.store_test import bytes_of_results, close_streams, fresh


class FakeEnvironment:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.reset_calls = self.steps = 0

    def reset(self):
        self.steps = 0
        self.reset_calls += 1
        self.instruction = f"actual scene instruction {self.rng.random()}"

    def completed_action(self):
        self.rng.random()
        self.steps += 1

    def _check_success(self):
        return self.reset_calls % 2 == 1 and self.steps >= 1


def run_stream(value, task, stream, indices, media=None):
    env = FakeEnvironment(stream["seed"])
    scenes = []
    actions = []
    for ep in indices:
        a = value.begin_episode(task, ep)
        state, env = admit_scene(value, a, env, lambda *x: None)
        assert state["status"] == "admitted"
        scenes.append(env.instruction)
        outcome = EnvironmentOutcome(value.manifest["horizons"][task])
        for _ in range(outcome.horizon):
            actions.append(random.random())
            env.completed_action()
            if media is not None:
                try_media(media)
            if outcome.check_after_step(env):
                break
        value.commit(
            result_record(
                value.manifest,
                task=task,
                episode=ep,
                generation=a["generation"],
                attempt_id=a["attempt_id"],
                worker_id=a["worker_id"],
                stream_id=a["stream_id"],
                seed=a["seed"],
                reset_index=state["last_event"]["data"]["reset_index"],
                observation=outcome.finish(normal=True),
                instruction=env.instruction,
                replans=1,
                elapsed_seconds=0,
            )
        )
    return env, scenes, actions


def test_fresh50_uses_one_env_literal_seed_continuous_reset_no_per_episode_derived_seed(tmp_path):
    value = fresh(tmp_path, episodes=50)
    with value.locked():
        stream = value.begin_task("CloseFridge")
        env, scenes, _ = run_stream(value, "CloseFridge", stream, range(50))
        rows = value.rows("CloseFridge")
        assert env.reset_calls == len(scenes) == 50
        assert {r["seed"] for r in rows} == {7} and len({r["stream_id"] for r in rows}) == 1
        assert [r["reset_index"] for r in rows] == list(range(50))
        assert value.publish_views()["sr"] == 0.5
        close_streams(value, "CloseFridge")
    with Store(value.root, value.manifest).locked() as resumed:
        assert resumed.begin_task("CloseFridge")["action"] == "reuse_complete_task"


def test_episode37_resume_new_scene_no_replay_and_no_continuous_stream_claim(tmp_path):
    value = fresh(tmp_path, episodes=50)
    with value.locked():
        first = value.begin_task("CloseFridge")
        run_stream(value, "CloseFridge", first, range(37))
        before = bytes_of_results(value)
    with Store(value.root, value.manifest).locked() as resumed:
        close_streams(resumed, "CloseFridge")
        second = resumed.begin_task("CloseFridge", seed=10001)
        env, _, _ = run_stream(resumed, "CloseFridge", second, range(37, 50))
        assert env.reset_calls == 13
        assert second["stream_id"] != first["stream_id"] and second["kind"] == "resume_new_stream_no_scene_reproduction"
        after = bytes_of_results(resumed)
        assert all(after[k] == v for k, v in before.items())
        rows = resumed.rows("CloseFridge")
        assert rows[37]["reset_index"] == 0 and rows[37]["seed"] == 10001
        assert len(rows) == 50


def test_media_off_save_error_preserve_scene_and_policy_draws_without_SR_gate(tmp_path):
    values = []
    for name, media in [
        ("off", None),
        ("save", lambda: random.random()),
        ("error", lambda: (_ for _ in ()).throw(OSError("encoder"))),
    ]:
        path = tmp_path / name
        path.mkdir()
        value = fresh(path, episodes=5)
        random.seed(31)
        with value.locked():
            stream = value.begin_task("CloseFridge")
            _, scenes, actions = run_stream(value, "CloseFridge", stream, range(5), media)
            values.append((scenes, actions, random.getstate(), value.publish_views()["sr"]))
    assert values[0] == values[1] == values[2]
