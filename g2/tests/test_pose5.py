# SPDX-License-Identifier: Apache-2.0
"""Shared DATA_B source-base world Pose5 contract / G1 official EEF parity."""

import math
from dataclasses import replace

import pytest
import torch

from g2.data.pose5 import (
    Pose5Recipe,
    build_pose5,
    build_state15_from_current,
    build_state15_from_window,
    compose_state15,
    source_base_rotation,
)


def state(yaw=math.pi / 2, z=0.7000):
    # Real RoboCasa layout: base position3/quaternion_xyzw4, EEF3/quat4/fingers2.
    return torch.tensor(
        [
            1.7235756,
            -0.8371568,
            z,
            0,
            0,
            math.sin(yaw / 2),
            math.cos(yaw / 2),
            0.25,
            -0.016,
            0.5975,
            -0.990923,
            -0.008656,
            -0.132317,
            0.022107,
            0.020564,
            -0.020503,
        ],
        dtype=torch.float64,
    )


def test_pose5_world_anchor_and_nonzero_z():
    s = state()
    p = build_pose5(s, recipe=Pose5Recipe())
    assert p.dtype == torch.float32 and p.shape == (5,)
    torch.testing.assert_close(p[:3], s[:3].float(), atol=0, rtol=0)
    torch.testing.assert_close(p[3:], torch.tensor([1.0, 0.0]), atol=1e-6, rtol=0)
    assert p[2] > 0.6


def test_yaw_uses_world_projection_of_body_plus_x():
    for yaw in (-math.pi, -math.pi / 2, 0.0, math.pi / 3, math.pi):
        s = state(yaw=yaw)
        p = build_pose5(s, recipe=Pose5Recipe())
        torch.testing.assert_close(
            p[3:],
            torch.tensor([math.sin(yaw), math.cos(yaw)]),
            atol=2e-6,
            rtol=0,
        )
        flipped = s.clone()
        flipped[3:7].neg_()
        torch.testing.assert_close(
            p, build_pose5(flipped, recipe=Pose5Recipe()), atol=0, rtol=0
        )
        r = source_base_rotation(s, recipe=Pose5Recipe())
        torch.testing.assert_close(
            r[:, 0].float()[:2],
            torch.tensor([math.cos(yaw), math.sin(yaw)]),
            atol=2e-6,
            rtol=0,
        )


def test_source_z_motion_preserved_not_silently_corrected():
    recipe = Pose5Recipe()
    z1 = build_pose5(state(z=0.7), recipe=recipe)
    z2 = build_pose5(state(z=0.7048), recipe=recipe)
    assert float(z2[2] - z1[2]) == pytest.approx(0.0048, abs=1e-7)
    assert torch.equal(z1[[0, 1, 3, 4]], z2[[0, 1, 3, 4]])


def test_train_online_and_official_G1_EEF10_exact():
    from cosmos_framework.data.generator.action.datasets.robocasa_lerobot_dataset import (
        RoboCasaLeRobotDataset,
    )

    s = state()
    window = s.repeat(17, 1).float()
    window[1:, 0] = 999.0
    proxy = object.__new__(RoboCasaLeRobotDataset)
    proxy._chunk_length = 16
    official_eef = RoboCasaLeRobotDataset._build_initial_state(proxy, window)
    recipe = Pose5Recipe()
    actual = build_state15_from_window(window, recipe=recipe)
    torch.testing.assert_close(actual[5:], official_eef, rtol=0, atol=0)
    torch.testing.assert_close(
        actual[:5], build_pose5(window[0], recipe=recipe), rtol=0, atol=0
    )
    torch.testing.assert_close(
        actual, build_state15_from_current(window[0], recipe=recipe), atol=0, rtol=0
    )
    torch.testing.assert_close(
        actual, compose_state15(window[0], official_eef, recipe=recipe), atol=0, rtol=0
    )
    assert actual.dtype == torch.float32 and tuple(actual.shape) == (15,)


def test_incorrect_layout_and_nonfinite_fail_closed():
    recipe = Pose5Recipe()
    for bad in (
        torch.zeros(15),
        torch.ones(17),
        torch.tensor([float("nan")] + [0] * 15),
        torch.tensor([1.0, 2.0, 3.0] + [0.0] * 13),
    ):
        with pytest.raises(ValueError):
            build_pose5(bad, recipe=recipe)
    bad = state()
    bad[3:7] = torch.tensor([0, 0, 0, 0])
    with pytest.raises(ValueError, match="unit length"):
        build_pose5(bad, recipe=recipe)
    with pytest.raises(ValueError):
        build_state15_from_window(state().repeat(16, 1), recipe=recipe)
    with pytest.raises(ValueError, match="EEF10"):
        compose_state15(state(), torch.ones(9), recipe=recipe)


def test_recipe_identity_and_no_implicit_world_to_wheel_alias():
    r = Pose5Recipe()
    assert len(r.recipe_id) == 64
    assert r.recipe_id == Pose5Recipe().recipe_id
    assert "base_world" in r.position_anchor
    assert "DIFFERENT_FROM_SOURCE" in r.marker_anchor
    with pytest.raises(ValueError, match="anchor"):
        replace(r, position_anchor="mobilebase0_wheeled_base")
    with pytest.raises(ValueError, match="version"):
        replace(r, version="unknown")
    with pytest.raises(TypeError):
        build_pose5(state(), recipe=None)
