"""Native CPU software-render regressions on tiny, synthetic MuJoCo scenes.

Run separately from the non-rendering Gate A suite with MUJOCO_GL=osmesa and
LIBGL_ALWAYS_SOFTWARE=1. No RoboCasa, recording, video or server data is used.
"""

from contextlib import contextmanager
import json
from types import SimpleNamespace

import mujoco
import numpy as np
import pytest

from tools.g2.rgbd_pose.replay import Replay


HEIGHT = WIDTH = 96
VERTICES = np.array(
    [
        [-0.4, -0.4, -0.15],
        [0.4, -0.4, -0.15],
        [0.4, 0.4, -0.15],
        [-0.4, 0.4, -0.15],
        [-0.4, -0.4, 0.15],
        [0.4, -0.4, 0.15],
        [0.4, 0.4, 0.15],
        [-0.4, 0.4, 0.15],
    ]
)
FACES = np.array(
    [
        [0, 2, 1],
        [0, 3, 2],
        [4, 5, 6],
        [4, 6, 7],
        [0, 1, 5],
        [0, 5, 4],
        [1, 2, 6],
        [1, 6, 5],
        [2, 3, 7],
        [2, 7, 6],
        [3, 0, 4],
        [3, 4, 7],
    ]
)


def _numbers(array):
    return " ".join(str(value) for value in np.asarray(array).ravel())


def _scene(kind, *, offsamples=4, rotation="0 0 0", scale="1 1 1"):
    asset = ""
    background = (
        '<geom name="background" type="box" pos="0 0 -.1" '
        'size="3 3 .1" rgba=".2 .2 .7 1"/>'
    )
    foreground = ""
    if kind == "tilted_plane":
        background = (
            '<geom name="background" type="plane" size="3 3 .1" '
            'euler="15 7 0" rgba=".2 .2 .7 1"/>'
        )
    elif kind in ("opaque", "transparent", "transparent_full"):
        alpha = ".3" if kind.startswith("transparent") else "1"
        size = "3 3 .15" if kind == "transparent_full" else ".4 .4 .15"
        foreground = (
            '<geom name="foreground" type="box" pos="0 0 .7" '
            f'size="{size}" rgba=".7 .1 .1 {alpha}"/>'
        )
    elif kind in ("outward", "inward", "compound"):
        vertices = VERTICES.copy()
        faces = FACES[:, ::-1] if kind == "inward" else FACES
        position = "0 0 .7"
        if kind == "compound":
            # The near box and far plate share one geom ID. Segmentation alone
            # cannot identify their multisampled depth discontinuity.
            near = VERTICES * [0.9, 0.9, 1] + [0.13, 0, 0.7]
            far = VERTICES * [5, 5, 1] + [0, 0, -0.15]
            vertices = np.concatenate([near, far])
            faces = np.concatenate([FACES, FACES + len(VERTICES)])
            position = "0 0 0"
            background = ""
        asset = (
            f'<asset><mesh name="test_mesh" vertex="{_numbers(vertices)}" '
            f'face="{_numbers(faces)}" scale="{scale}"/></asset>'
        )
        foreground = (
            '<geom name="foreground" type="mesh" mesh="test_mesh" '
            f'pos="{position}" euler="{rotation}" rgba=".7 .1 .1 1"/>'
        )
    elif kind != "plane":
        raise ValueError(kind)
    return (
        '<mujoco><visual><global offwidth="96" offheight="96"/>'
        f'<quality offsamples="{offsamples}"/><map znear=".01" zfar="30"/>'
        "</visual>"
        f'{asset}<worldbody><light pos="0 0 3"/>'
        '<camera name="test_camera" pos="0 0 2" fovy="60"/>'
        f"{background}{foreground}</worldbody></mujoco>"
    )


class SoftwareSim:
    """Small native renderer with the pinned robosuite readback conventions."""

    def __init__(self, xml, *, cull_face=True, rgb_fault=None):
        self.model = mujoco.MjModel.from_xml_string(xml)
        self.data = mujoco.MjData(self.model)
        mujoco.mj_forward(self.model, self.data)
        self.gl = mujoco.GLContext(WIDTH, HEIGHT)
        self.gl.make_current()
        self.scn = mujoco.MjvScene(self.model, maxgeom=100)
        self.scn.flags[mujoco.mjtRndFlag.mjRND_CULL_FACE] = int(cull_face)
        self.camera = mujoco.MjvCamera()
        self.camera.type = mujoco.mjtCamera.mjCAMERA_FIXED
        self.camera.fixedcamid = 0
        self.vopt = mujoco.MjvOption()
        self.vopt.geomgroup[:] = [1, 1, 1, 0, 0, 0]
        self.con = mujoco.MjrContext(self.model, mujoco.mjtFontScale.mjFONTSCALE_100)
        mujoco.mjr_setBuffer(mujoco.mjtFramebuffer.mjFB_OFFSCREEN, self.con)
        self.viewport = mujoco.MjrRect(0, 0, WIDTH, HEIGHT)
        self._render_context_offscreen = SimpleNamespace(
            vopt=self.vopt, scn=self.scn, con=self.con
        )
        self.rgb_fault = rgb_fault
        self.segmented = False
        self.render_calls = []

    def render(self, *, segmentation=False, depth=False, **kwargs):
        self.render_calls.append({"segmentation": segmentation, "depth": depth})
        mujoco.mjv_updateScene(
            self.model,
            self.data,
            self.vopt,
            None,
            self.camera,
            mujoco.mjtCatBit.mjCAT_ALL,
            self.scn,
        )
        if segmentation:
            self.scn.flags[mujoco.mjtRndFlag.mjRND_SEGMENT] = 1
            self.scn.flags[mujoco.mjtRndFlag.mjRND_IDCOLOR] = 1
        try:
            mujoco.mjr_render(self.viewport, self.scn, self.con)
        finally:
            if segmentation:
                self.scn.flags[mujoco.mjtRndFlag.mjRND_SEGMENT] = 0
                self.scn.flags[mujoco.mjtRndFlag.mjRND_IDCOLOR] = 0
        rgb = np.empty((HEIGHT, WIDTH, 3), dtype=np.uint8)
        buffer = np.empty((HEIGHT, WIDTH), dtype=np.float32) if depth else None
        mujoco.mjr_readPixels(rgb, buffer, self.viewport, self.con)
        if segmentation:
            packed = rgb.astype(np.int32)
            ids = packed[:, :, 0] + 256 * packed[:, :, 1] + 65536 * packed[:, :, 2]
            ids[ids >= self.scn.ngeom + 1] = 0
            lookup = np.full((self.scn.ngeom + 1, 2), -1, dtype=np.int32)
            for geom in self.scn.geoms[: self.scn.ngeom]:
                if geom.segid != -1:
                    lookup[geom.segid + 1] = [geom.objtype, geom.objid]
            rgb = lookup[ids]
            self.segmented = True
        elif (depth and self.rgb_fault == "depth_mode") or (
            self.segmented and self.rgb_fault == "segmentation"
        ):
            rgb = np.minimum(rgb.astype(np.int16) + 7, 255).astype(np.uint8)
        return (rgb, buffer) if depth else rgb

    def sample(self):
        _, buffer = self.render(depth=True)
        buffer = buffer[::-1].copy()
        near = float(self.model.vis.map.znear * self.model.stat.extent)
        far = float(self.model.vis.map.zfar * self.model.stat.extent)
        depth = near / (1 - buffer.astype(np.float64) * (1 - near / far))
        focal = HEIGHT / (2 * np.tan(np.pi / 6))
        transform = np.eye(4)
        transform[:3, :3] = self.data.cam_xmat[0].reshape(3, 3) @ np.diag([1, -1, -1])
        transform[:3, 3] = self.data.cam_xpos[0]
        return {
            "depth_m": depth,
            "valid": buffer < 1,
            "K": np.array([[focal, 0, WIDTH / 2], [0, focal, HEIGHT / 2], [0, 0, 1.0]]),
            "T_world_camera_cv": transform,
            "clip_near_m": near,
            "clip_far_m": far,
        }

    def check(self, sample=None):
        sample = self.sample() if sample is None else sample
        replay = object.__new__(Replay)
        replay.env = SimpleNamespace(sim=self)
        return replay.ray_check("test_camera", sample)

    def close(self):
        self.gl.make_current()
        self.con.free()
        self.gl.free()


@contextmanager
def software_scene(kind, **kwargs):
    render_kwargs = {
        key: kwargs.pop(key) for key in ("cull_face", "rgb_fault") if key in kwargs
    }
    sim = SoftwareSim(_scene(kind, **kwargs), **render_kwargs)
    try:
        yield sim
    finally:
        sim.close()


@pytest.mark.parametrize(
    ("kind", "kwargs"),
    [
        ("plane", {}),
        ("tilted_plane", {}),
        ("opaque", {}),
        ("outward", {}),
        ("inward", {}),
        ("inward", {"cull_face": False}),
        ("inward", {"rotation": "9 -12 13"}),
        ("inward", {"scale": "1.4 .8 .7", "rotation": "5 7 13"}),
        ("compound", {"rotation": "0 0 13", "offsamples": 0}),
        ("compound", {"rotation": "0 0 13", "offsamples": 4}),
        ("transparent", {}),
    ],
)
def test_native_render_depth_and_visible_ray_surfaces_agree(kind, kwargs):
    with software_scene(kind, **kwargs) as sim:
        result = sim.check()
    assert result["status"] == "PASS", result
    assert result["matching_geom_samples"] >= 16
    assert result["max_abs_z_error_m"] <= 0.01
    assert result["distance_converted_to_optical_Z"] is True


def test_only_transparent_segmentation_cannot_create_geometry_pass():
    with software_scene("transparent_full") as sim:
        result = sim.check()
    assert result["status"] == "INCONCLUSIVE", result
    assert result["matching_geom_samples"] < 16


@pytest.mark.parametrize("corruption", ["constant", "range", "vertical_flip"])
def test_wrong_cached_depth_is_rejected_without_cherry_picking(corruption):
    with software_scene("tilted_plane") as sim:
        sample = sim.sample()
        if corruption == "constant":
            sample["depth_m"] += 0.2
        elif corruption == "range":
            yy, xx = np.mgrid[:HEIGHT, :WIDTH]
            focal = sample["K"][0, 0]
            scale = np.sqrt(
                1
                + ((xx + 0.5 - WIDTH / 2) / focal) ** 2
                + ((yy + 0.5 - HEIGHT / 2) / focal) ** 2
            )
            sample["depth_m"] *= scale
        else:
            sample["depth_m"] = sample["depth_m"][::-1].copy()
        result = sim.check(sample)
    assert result["matching_geom_samples"] >= 16, result
    assert result["status"] == "FAIL", result
    assert result["max_abs_z_error_m"] > 0.01


@pytest.mark.parametrize("corruption", ["mirrored", "translated"])
def test_wrong_camera_pose_is_not_accepted(corruption):
    with software_scene("tilted_plane") as sim:
        sample = sim.sample()
        if corruption == "mirrored":
            sample["T_world_camera_cv"][:3, 0] *= -1
        else:
            sample["T_world_camera_cv"][2, 3] += 0.2
        result = sim.check(sample)
    assert result["status"] != "PASS", result


def test_software_render_diagnostics_are_scalar_json_and_rgb_modes_agree():
    with software_scene("compound", rotation="0 0 13") as sim:
        result = sim.check()
    diagnostics = result["rgb_render_diagnostics"]
    assert diagnostics["rgb_vs_rgbd"]["mae"] == 0.0
    assert diagnostics["segmentation_before_after"]["mae"] == 0.0
    assert diagnostics["rgb_vs_rgbd"]["identical"] is True
    assert diagnostics["segmentation_before_after"]["identical"] is True
    serialized = json.dumps(result, allow_nan=False)
    assert len(serialized) < 100_000


@pytest.mark.parametrize(
    ("fault", "key"),
    [
        ("depth_mode", "rgb_vs_rgbd"),
        ("segmentation", "segmentation_before_after"),
    ],
)
def test_rgb_diagnostics_expose_mode_or_segmentation_fault(fault, key):
    with software_scene("plane", rgb_fault=fault) as sim:
        result = sim.check()
    diagnostics = result["rgb_render_diagnostics"]
    assert diagnostics[key]["identical"] is False
    assert diagnostics[key]["mae"] > 0
    # RGB diagnostics do not redefine the independent geometry result.
    assert result["status"] == "PASS", result


@pytest.mark.parametrize("option", ["wireframe", "convex_hull", "changing_groups"])
def test_unsupported_or_changing_visibility_options_are_inconclusive(option):
    with software_scene("plane") as sim:
        if option == "wireframe":
            sim.scn.flags[mujoco.mjtRndFlag.mjRND_WIREFRAME] = 1
        elif option == "convex_hull":
            sim.vopt.flags[mujoco.mjtVisFlag.mjVIS_CONVEXHULL] = 1
        else:
            render = sim.render

            def changing(**kwargs):
                output = render(**kwargs)
                if kwargs.get("segmentation"):
                    sim.vopt.geomgroup[0] = 0
                return output

            sim.render = changing
        result = sim.check()
    assert result["status"] == "INCONCLUSIVE", result
    assert "unsupported or changing" in result["reason"]


def test_one_bad_eligible_ray_is_not_removed_to_make_a_pass(monkeypatch):
    original = mujoco.mj_ray
    calls = []

    def one_bad_ray(*args, **kwargs):
        distance = original(*args, **kwargs)
        if distance >= 0:
            calls.append(distance)
            if len(calls) == 1:
                return distance + 0.2
        return distance

    monkeypatch.setattr(mujoco, "mj_ray", one_bad_ray)
    with software_scene("plane") as sim:
        result = sim.check()
    assert len(calls) == result["matching_geom_samples"] >= 16
    assert result["status"] == "FAIL", result
    assert result["max_abs_z_error_m"] > 0.01
