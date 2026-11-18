"""DATA_B/C real-source optional gates. All private data stays on the server.

Ordinary CI without the env path skips; CPU evidence runner enables it using
pre-existing original LeRobot, G1 accepted index, complete View+Wan cache.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import torch

from g2.data.aligned_provider import CandidateAlignedG2Provider
from g2.data.episode_state import (
    DataBError,
    VerifiedRawEpisodes,
    verify_episode_state,
)
from g2.data.joint_index import DataCError, verify_joint_episode
from g2.data.pose5 import Pose5Recipe, build_state15_from_current

EPISODES = (9, 75, 104)
CHECK = (0, 16, 32, 48)
TASK = "CloseBlenderLid"


@pytest.fixture(scope="module")
def real():
    root = os.environ.get("PSM_G2_DATA_BC_REAL_ROOT")
    g1 = os.environ.get("PSM_G2_DATA_BC_G1_DATASETS")
    if not root or not g1:
        pytest.skip("set PSM_G2_DATA_BC_REAL_ROOT and PSM_G2_DATA_BC_G1_DATASETS")
    base = Path(root)
    g1 = Path(g1)
    raw = VerifiedRawEpisodes(
        base / "robocasa365-target-atomic",
        g1 / "robocasa365-target-atomic-verified-index-r1",
        g1 / "robocasa365-target-atomic-left_wrist-exact_window",
    )
    return {
        "base": base,
        "g1": g1,
        "raw": raw,
        "b": base / "robocasa365-target-atomic-state15",
        "c": base / "robocasa365-target-atomic-g2-data-c",
        "v": base / "robocasa365-target-atomic-6views",
    }


def test_data_b_all_actual_frames_byte_exact_official_eef(real):
    torch.set_num_threads(2)
    frames = 0
    for ep in EPISODES:
        rows = real["raw"].read(TASK, ep)
        v = verify_episode_state(
            real["b"], rows, expected_recipe=Pose5Recipe().recipe_id
        )
        loaded = torch.load(
            v["state15_path"], weights_only=True, mmap=True, map_location="cpu"
        )
        states = loaded["state15"]
        assert states.shape == (rows["source_frame_count"], 15)
        for i, row in enumerate(rows["rows"]):
            torch.testing.assert_close(
                states[i],
                build_state15_from_current(
                    row["observation.state"], recipe=Pose5Recipe()
                ),
                atol=0,
                rtol=0,
            )
        frames += len(states)
    assert frames == 1272


def test_data_c_all_real_windows_are_causal_and_g1_aligned(real):
    expected_counts = (477, 329, 418)
    total = 0
    for ep, expected in zip(EPISODES, expected_counts, strict=True):
        source = real["raw"].read(TASK, ep)
        v = verify_joint_episode(
            real["c"],
            source,
            real["b"],
            real["v"],
            expected_recipe_id="e8da63970bfe1f511afac45721fa12d75dc5803b07acac36d0a060c0f8d7cf0d",
        )
        assert v["window_count"] == expected
        assert v["training_ready"] is False
        total += expected
    assert total == 1224


def test_real_join_g2_adapter_r1_r2_and_no_leak(real):
    from cosmos_framework.data.generator.action.datasets.g2_training_adapter import (
        G2DataRecipe,
        G2TrainingDataAdapter,
    )
    from cosmos_framework.data.generator.action.datasets.robocasa_lerobot_dataset import (
        RoboCasaLeRobotDataset,
    )
    from cosmos_framework.model.generator.mot.g2_contracts import GlobalMemoryConfig

    p = CandidateAlignedG2Provider(
        data_c_root=real["c"],
        state15_root=real["b"],
        view_root=real["v"],
        global_memory_enabled=True,
    )
    cfg = p.corpus
    r1 = G2TrainingDataAdapter(
        p,
        G2DataRecipe(
            p.identity,
            cfg["alignment_version"],
            cfg["state15_recipe_id"],
            None,
            GlobalMemoryConfig(enabled=False),
        ),
    )
    r2 = G2TrainingDataAdapter(
        p,
        G2DataRecipe(
            p.identity,
            cfg["alignment_version"],
            cfg["state15_recipe_id"],
            cfg["view_recipe_id"],
            GlobalMemoryConfig(enabled=True, top_view_variant="with_robot"),
        ),
    )
    try:
        calls = 0
        for ep in EPISODES:
            rows = real["raw"].read(TASK, ep)["rows"]
            for t in CHECK:
                states17 = torch.tensor(
                    [row["observation.state"] for row in rows[t : t + 17]],
                    dtype=torch.float32,
                )
                raw12 = torch.tensor(
                    [row["action"] for row in rows[t : t + 16]], dtype=torch.float32
                )
                proxy = object.__new__(RoboCasaLeRobotDataset)
                proxy._chunk_length = 16
                eef10 = RoboCasaLeRobotDataset._build_initial_state(proxy, states17)
                a10 = RoboCasaLeRobotDataset._build_frame_wise_action(proxy, raw12)
                native = torch.cat(
                    (
                        torch.cat((torch.zeros(5), eef10))[None],
                        torch.cat((raw12[:, :5], a10), dim=1),
                    ),
                    dim=0,
                )
                sample = {
                    "task_class": TASK,
                    "episode_index": ep,
                    "start_frame": t,
                    "action": native,
                    "ai_caption": p.data[(TASK, ep)][0]["original_instruction"],
                    "source_binding_digest": real["raw"].source_binding,
                }
                before = p.view_read_count
                a = r1(sample)
                assert not a["g2_views"] and p.view_read_count == before
                b = r2(sample)
                assert len(b["g2_views"]) >= 1
                assert p.view_read_count == before + 1
                assert torch.equal(a["action"], b["action"])
                assert torch.equal(a["action"][1:], native[1:])
                assert torch.equal(a["action"][0, 5:], native[0, 5:])
                assert not torch.equal(a["action"][0, :5], native[0, :5])
                assert a["g2_sample_identity"] == b["g2_sample_identity"]
                assert all(x.identity.image_owner_frame <= t for x in b["g2_views"])
                calls += 1
        assert calls == 12
        assert p.evidence_scope != "verified_data_c"
    finally:
        p.close()


def test_negative_gates_do_not_mutate_real_data(real, tmp_path):
    from g2.data.episode_state import episode_path

    source = real["raw"].read(TASK, 9)
    state_path = episode_path(real["b"], TASK, 9)
    candidate = tmp_path / "data_b"
    out = episode_path(candidate, TASK, 9)
    out.mkdir(parents=True)
    # Make a genuine copy then corrupt only this scratch payload.
    for filename in ("state15.pt", "COMPLETE.json"):
        (out / filename).write_bytes((state_path / filename).read_bytes())
    with (out / "state15.pt").open("ab") as f:
        f.write(b"deliberate-corruption")
    with pytest.raises(DataBError, match="SHA"):
        verify_episode_state(candidate, source, expected_recipe=Pose5Recipe().recipe_id)
    p = CandidateAlignedG2Provider(
        data_c_root=real["c"], state15_root=real["b"], view_root=real["v"]
    )
    try:
        with pytest.raises(DataCError, match="decision frame outside"):
            p.read_common(task_class=TASK, episode_index=9, decision_frame=10_000)
        with pytest.raises(DataCError, match="episode absent"):
            p.read_common(task_class="AnotherTask", episode_index=9, decision_frame=16)
        identity = p.read_common(task_class=TASK, episode_index=9, decision_frame=16)[
            "identity"
        ]
        with pytest.raises(DataCError, match="top variant"):
            p.read_selected_views(identity, top_view_variant="without_robot")
        # Tamper a memory-only row, never the on-disk source.
        rows = p.data[(TASK, 9)][0]["windows"]
        old = rows[16]["spatial_state_frame"]
        rows[16]["spatial_state_frame"] = 10_000
        with pytest.raises(DataCError, match="no-future"):
            p.read_common(task_class=TASK, episode_index=9, decision_frame=16)
        rows[16]["spatial_state_frame"] = old
    finally:
        p.close()
