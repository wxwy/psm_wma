"""G2 DATA_B state15: one source-base/world recipe for offline and online.

The source base anchor is observation.state[0:3], in MuJoCo world metres.
It is deliberately NOT the visual marker's mobilebase0_wheeled_base body:
the two anchors are offset and have dynamic Z differences. No guessed
extrinsic, 2 Hz spatial interpolation, global action normalization, or
future-frame data enters this module.

The EEF10 encoding remains the exact existing RoboCasa G1 helper; this
module does not reimplement quaternion->rot6d or gripper processing.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, fields
from typing import Any

import torch

SOURCE_STATE_DIM = 16
STATE_DIM = 15
EEF_DIM = 10
WINDOW_T = 16
POSE_VERSION = "g2_pose5_source_base_world_v1"


@dataclass(frozen=True)
class Pose5Recipe:
    """Frozen proposal, with a hash-bound physical reference-frame contract."""

    version: str = POSE_VERSION
    source_schema: str = "robocasa_observation_state16_v3"
    position_anchor: str = "observation.state[0:3]_base_world"
    position_reference: str = "mujoco_world_metres"
    orientation_source: str = "observation.state[3:7]_quat_xyzw"
    yaw_convention: str = (
        "atan2(world_positive_X_of_body_X_y,world_positive_X_of_body_X_x)"
    )
    marker_anchor: str = "mobilebase0_wheeled_base_DIFFERENT_FROM_SOURCE"
    eef_encoding: str = "G1_official_RoboCasaLeRobotDataset._build_initial_state"
    time_source: str = "current_20Hz_observation_not_2Hz_spatial"
    output_dtype: str = "float32"

    def __post_init__(self) -> None:
        if self.version != POSE_VERSION:
            raise ValueError("unknown Pose5 recipe version")
        if any(getattr(self, f.name) != f.default for f in fields(self)):
            raise ValueError("Pose5 anchor/frame/encoding cannot drift silently")

    @property
    def recipe_id(self) -> str:
        encoded = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _state16(raw: Any, *, shape: tuple[int, ...]) -> torch.Tensor:
    if isinstance(raw, torch.Tensor) and raw.device.type != "cpu":
        raise ValueError("DATA_B/online state conversion requires host-side state16")
    try:
        value = torch.as_tensor(raw, dtype=torch.float64, device="cpu")
    except (TypeError, RuntimeError, ValueError) as exc:
        raise ValueError("state16 must be a numerical CPU sequence") from exc
    if tuple(value.shape) != shape or not bool(torch.isfinite(value).all()):
        raise ValueError(f"expected finite raw observation.state {shape}")
    return value


def _checked_recipe(recipe: Pose5Recipe) -> None:
    if type(recipe) is not Pose5Recipe:
        raise TypeError("G2 state builder requires an explicit Pose5Recipe")


def source_base_rotation(raw: Any, *, recipe: Pose5Recipe) -> torch.Tensor:
    """Return source-base-to-world R (float64), for diagnostics only."""
    _checked_recipe(recipe)
    s = _state16(raw, shape=(SOURCE_STATE_DIM,))
    x, y, z, w = (float(v) for v in s[3:7])
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if abs(norm - 1.0) > 1e-3:
        raise ValueError("base quaternion is not unit length")
    x, y, z, w = (v / norm for v in (x, y, z, w))
    return torch.tensor(
        (
            (1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)),
            (2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)),
            (2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)),
        ),
        dtype=torch.float64,
    )


def build_pose5(raw: Any, *, recipe: Pose5Recipe) -> torch.Tensor:
    """[x_world,y_world,z_world,sin(yaw),cos(yaw)] on SOURCE base anchor.

    The robot's forward direction is body-local +X. Yaw is the projection
    of this forward vector into world XY; Z is not erased/offset/normalised.
    """
    _checked_recipe(recipe)
    s = _state16(raw, shape=(SOURCE_STATE_DIM,))
    r = source_base_rotation(s, recipe=recipe)
    forward_x, forward_y = (float(r[0, 0]), float(r[1, 0]))
    xy_norm = math.hypot(forward_x, forward_y)
    if xy_norm < 1e-6:
        raise ValueError("base +X has undefined projection onto world XY")
    out = torch.tensor(
        [
            float(s[0]),
            float(s[1]),
            float(s[2]),
            forward_y / xy_norm,
            forward_x / xy_norm,
        ],
        dtype=torch.float32,
    )
    if not bool(torch.isfinite(out).all()):
        raise ValueError("invalid Pose5 output")
    return out


def compose_state15(
    raw_state16: Any,
    official_eef10: torch.Tensor,
    *,
    recipe: Pose5Recipe,
) -> torch.Tensor:
    """Compose state15 without changing the G1 10D EEF encoding."""
    pose5 = build_pose5(raw_state16, recipe=recipe)
    if (
        not isinstance(official_eef10, torch.Tensor)
        or official_eef10.device.type != "cpu"
        or tuple(official_eef10.shape) != (EEF_DIM,)
        or not official_eef10.is_floating_point()
        or not bool(torch.isfinite(official_eef10).all())
    ):
        raise ValueError("requires finite CPU official EEF10")
    return torch.cat([pose5, official_eef10.to(torch.float32)], dim=0).contiguous()


def build_state15_from_window(
    raw_states17: Any, *, recipe: Pose5Recipe
) -> torch.Tensor:
    """Training: official source window [17,16] with current state at row 0."""
    _checked_recipe(recipe)
    states = _state16(raw_states17, shape=(WINDOW_T + 1, SOURCE_STATE_DIM))
    # The canonical G1 helper reads the earliest pre-action state at -17;
    # it is intentionally reused, not copied with a divergent EEF recipe.
    from cosmos_framework.data.generator.action.datasets.robocasa_lerobot_dataset import (
        RoboCasaLeRobotDataset,
    )

    proxy = object.__new__(RoboCasaLeRobotDataset)
    proxy._chunk_length = WINDOW_T
    official_eef10 = RoboCasaLeRobotDataset._build_initial_state(
        proxy, states.to(torch.float32).contiguous()
    )
    return compose_state15(states[0], official_eef10, recipe=recipe)


def build_state15_from_current(
    raw_state16: Any, *, recipe: Pose5Recipe
) -> torch.Tensor:
    """Serving: same physical recipe and official EEF10 from one current state.

    Repeating the current observation creates a 17-row WINDOW only to call
    G1's existing earliest-state helper; it never introduces future evidence.
    """
    state = _state16(raw_state16, shape=(SOURCE_STATE_DIM,))
    return build_state15_from_window(
        state.unsqueeze(0).expand(WINDOW_T + 1, -1).contiguous(),
        recipe=recipe,
    )
