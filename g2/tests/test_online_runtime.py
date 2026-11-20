"""CPU source/frontier checks for the R1 EvalV2 runtime."""

from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from g2.data.pose5 import Pose5Recipe, build_pose5
from g2.io import ContractError, read_json
from g2.online import runtime


def _observation(frame):
    return {
        "robot0_base_pos": np.array([frame / 10, -0.5, 0.7]),
        "robot0_base_quat": np.array([0.0, 0.0, 0.0, 1.0]),
        "robot0_base_to_eef_pos": np.array([0.25, 0.05, 0.55]),
        "robot0_base_to_eef_quat": np.array([0.0, 0.0, 0.0, 1.0]),
        "robot0_gripper_qpos": np.array([0.02, -0.02]),
    }


class NativeFixture:
    def __init__(self, tmp_path):
        self.work = tmp_path
        self.published = []
        self.closed = False

    def observe(self, env, frame):
        if env.frame != frame:
            raise ContractError("fixture time differs")
        return np.array([frame / 20], dtype="<f8")

    def start(self, env, *, episode_id, ep_meta):
        return self.publish(0, self.observe(env, 0))

    def publish(self, frame, row):
        self.published.append(frame)
        return {
            "scene_id": "live_fixture",
            "source_sha256": "a" * 64,
            "world_frame": "world",
            "frame_id": frame,
            "entities": [
                {
                    "id": "entity_7",
                    "label": "Drawer",
                    "source_instance_id": "fixture:oak_drawer",
                    "source_category_id": "Drawer",
                    "source_part_id": "whole",
                    "kind": "object",
                    "room_uid": 0,
                    "bbox_min": [0.0, 0.0, 0.1],
                    "bbox_max": [1.0, 1.0, 0.6],
                    "root_affiliations": [],
                    "floor_member": False,
                    "upper_member": False,
                    "island_id": None,
                }
            ],
            "rooms": [
                {
                    "uid": 0,
                    "center": [0, 0, 0],
                    "label": "Kitchen",
                    "footprint": [[0, 0]],
                }
            ],
            "connections": {},
            "relations": [],
        }

    def close(self):
        self.closed = True


@pytest.fixture
def online(tmp_path, monkeypatch):
    # EEF already has exact parity coverage in test_pose5. Keep this
    # Actor/runtime unit independent of Child dataset import dependencies.
    monkeypatch.setattr(
        runtime,
        "build_state15_from_current",
        lambda state, *, recipe: torch.cat(
            (build_pose5(state, recipe=recipe), torch.zeros(10))
        ),
    )
    env = SimpleNamespace(
        frame=0,
        get_ep_meta=lambda: {
            "lang": "Open the drawer.",
            "fixtures": {"oak_drawer": {"cls": "Drawer"}},
            "fixture_refs": {"drawer": "oak_drawer"},
            "object_cfgs": [],
        },
    )
    native = NativeFixture(tmp_path)
    adapter = runtime.OnlineG2DataAdapter(
        native, data_version="0" * 64, alignment_version="g2_causal_latest_spatial_v1"
    )
    adapter.reset(
        env,
        _observation(0),
        episode_id="episode_0/attempt_0",
        task="OpenDrawer",
        instruction="Open the drawer.",
        frame=0,
        episode_index=0,
        ep_meta=env.get_ep_meta(),
    )
    return env, native, adapter


def _decide(adapter, frame, observation=None):
    return adapter.decision(
        _observation(frame) if observation is None else observation,
        frame=frame,
        composite=None,
        local_memory={"episode_id": "episode_0/attempt_0", "consumer_step": frame},
    )


def _step(env, adapter, *, before, after):
    env.frame = after
    adapter.record_completed(
        env,
        _observation(after),
        source_frame=before,
        canonical_raw15=np.zeros(15),
        submitted_env12=np.zeros(12),
    )


def test_live_observation_matches_official_state_slices():
    obs = _observation(3)
    np.testing.assert_array_equal(
        runtime.source_state16(obs),
        [0.3, -0.5, 0.7, 0, 0, 0, 1, 0.25, 0.05, 0.55, 0, 0, 0, 1, 0.02, -0.02],
    )
    for key in obs:
        invalid = deepcopy(obs)
        del invalid[key]
        with pytest.raises(ContractError, match=key):
            runtime.source_state16(invalid)
    obs["robot0_base_pos"][0] = np.nan
    with pytest.raises(ContractError, match="robot0_base_pos"):
        runtime.source_state16(obs)


def test_latest_spatial_frame_and_static_cap2(online):
    env, native, adapter = online
    first = _decide(adapter, 0)
    assert "Open the drawer." in first["prompt"]
    assert "entity_7" in first["prompt"]
    evidence = read_json(native.work / "initial_condition.json")
    assert evidence["task_set"]["roles"][0]["entity_ids"] == ["entity_7"]
    assert first["g2"]["identity"]["state15_recipe_id"] == Pose5Recipe().recipe_id
    assert set(first["g2"]) == {"identity", "static_text"}
    for frame in range(1, 42):
        _step(env, adapter, before=frame - 1, after=frame)
        decision = _decide(adapter, frame)
        identity = decision["g2"]["identity"]
        assert identity["decision_frame"] == frame
        assert identity["logical_state_frame"] == frame // 20 * 20
        assert decision["g2"]["static_text"] == first["g2"]["static_text"]
        assert decision["state"][0] == pytest.approx(frame / 10)
    assert native.published == [0, 20, 40]


def test_stale_future_and_duplicate_frames_fail(online):
    env, native, adapter = online
    with pytest.raises(ContractError, match="frontier"):
        _decide(adapter, 1)
    _step(env, adapter, before=0, after=1)
    with pytest.raises(ContractError, match="frontier"):
        _decide(adapter, 1, _observation(0))
    with pytest.raises(ContractError, match="frontier"):
        _step(env, adapter, before=0, after=1)
    assert native.published == [0]
    assert _decide(adapter, 1)["g2"]["identity"]["decision_frame"] == 1


def test_invalid_simulation_time_never_publishes_or_continues(online):
    env, native, adapter = online
    with pytest.raises(ContractError, match="fixture time"):
        _step(env, adapter, before=0, after=2)
    assert native.closed
    assert native.published == [0]
    with pytest.raises(ContractError, match="frontier"):
        _decide(adapter, 0)


def test_current_mocap_geometry_is_bound_to_the_native_state(tmp_path, monkeypatch):
    mujoco = pytest.importorskip("mujoco")
    from g2.online import nav_session

    model = mujoco.MjModel.from_xml_string(
        '<mujoco><worldbody><body name="marker" mocap="true">'
        '<geom name="source" type="box" size=".1 .1 .1"/>'
        "</body></worldbody></mujoco>"
    )
    data = mujoco.MjData(model)
    data.mocap_pos[0] = [1, 2, 3]
    env = SimpleNamespace(
        control_freq=20,
        sim=SimpleNamespace(
            model=SimpleNamespace(_model=model), data=SimpleNamespace(_data=data)
        ),
    )
    monkeypatch.setattr(
        nav_session.subprocess,
        "check_output",
        lambda argv, **_: "a" * 40 if "rev-parse" in argv else "",
    )
    native_tree = tmp_path / "mapping_8_3" / "mapping" / "src"
    native_tree.mkdir(parents=True)
    (native_tree / "fixture.cpp").write_text("")
    session = nav_session.NativeSession(
        nav_checkout=tmp_path,
        nav_revision="a" * 40,
        ros_setup=tmp_path,
        scratch_root=tmp_path,
    )

    class ReachedNativeClassification(Exception):
        pass

    def inspect_private_data(selected_model, metadata, *, state_data, **_):
        assert selected_model is model
        assert state_data is not data
        np.testing.assert_array_equal(state_data.geom_xpos[0], [1, 2, 3])
        raise ReachedNativeClassification

    monkeypatch.setattr(nav_session, "derive", inspect_private_data)
    with pytest.raises(ReachedNativeClassification):
        session.start(env, episode_id="mocap-regression", ep_meta={})

    first = session.observe(env, 0)
    data.mocap_pos[0, 0] = 2
    second = session.observe(env, 0)
    assert not np.array_equal(first, second)
    session._forward(second)
    np.testing.assert_array_equal(session.data.geom_xpos[0], [2, 2, 3])
    assert first[0] == second[0] == 0
    session.close()
