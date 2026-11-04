"""Thin adapter around RoboCasa's official state playback and camera helpers.

Native dependencies are imported only by the explicit server-side replay path.
A fresh environment per episode avoids cross-episode model/object residue.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import inspect
import json
from copy import deepcopy

import numpy as np

from .geometry import backproject_world, check_calibration, depth_buffer_to_z, rays_cv


def function_identity(function):
    return {
        "module": function.__module__,
        "name": function.__name__,
        "source_sha256": hashlib.sha256(
            inspect.getsource(function).encode()
        ).hexdigest(),
    }


class Replay:
    def __init__(self, source, *, make=None, reset_to=None, camera_utils=None):
        injected = make is not None or reset_to is not None or camera_utils is not None
        if injected and any(x is None for x in (make, reset_to, camera_utils)):
            raise ValueError(
                "CPU boundary injection requires make/reset_to/camera_utils together"
            )
        if not injected:
            import robocasa  # noqa: F401 (registers task environments)
            import robosuite
            from robocasa.scripts.dataset_scripts.playback_dataset_hdf5 import reset_to
            from robosuite.utils import camera_utils

            make = robosuite.make
        self.source, self.reset_to, self.camera_utils = source, reset_to, camera_utils
        self.env = None
        self.identity = (
            {"kind": "explicit_cpu_test_double"}
            if injected
            else {
                "kind": "official_state_replay",
                "packages": {
                    name: importlib.metadata.version(name)
                    for name in ("robocasa", "robosuite", "mujoco", "numpy")
                },
                "functions": [
                    function_identity(f)
                    for f in (
                        reset_to,
                        camera_utils.get_camera_intrinsic_matrix,
                        camera_utils.get_camera_extrinsic_matrix,
                        camera_utils.get_real_depth_map,
                    )
                ],
            }
        )
        kwargs = deepcopy(source.env_metadata["env_kwargs"])
        cameras = list(source.camera_shapes)
        kwargs.update(
            env_name=source.env_metadata["env_name"],
            has_renderer=False,
            has_offscreen_renderer=True,
            use_camera_obs=False,
            camera_depths=True,
            camera_names=cameras,
            camera_heights=[source.camera_shapes[c][0] for c in cameras],
            camera_widths=[source.camera_shapes[c][1] for c in cameras],
        )
        try:
            self.env = make(**kwargs)
            self.reset_to(
                self.env,
                {
                    "model": source.model_xml,
                    "ep_meta": json.dumps(source.ep_meta),
                    "states": source.states[0],
                },
            )
        except BaseException:
            self.close()
            raise

    def restore(self, frame):
        requested = self.source.states[frame]
        self.reset_to(self.env, {"states": requested})
        actual = np.asarray(self.env.sim.get_state().flatten())
        if actual.shape != requested.shape or not np.isfinite(actual).all():
            raise ValueError("restored simulator state shape/finite mismatch")
        error = float(np.max(np.abs(actual - requested)))
        if error > 1e-8:
            raise ValueError(f"restored simulator state differs: max_abs={error}")
        return {"state_max_abs_error": error, "sim_time": float(self.env.sim.data.time)}

    def render(self, camera):
        sim = self.env.sim
        height, width = self.source.camera_shapes[camera]
        rgb, raw_buffer = sim.render(
            height=height, width=width, camera_name=camera, depth=True
        )
        rgb, buffer = (
            np.asarray(rgb)[::-1].copy(),
            np.asarray(raw_buffer, dtype=np.float64)[::-1].copy(),
        )
        if (
            rgb.shape != (height, width, 3)
            or rgb.dtype != np.uint8
            or buffer.shape != (height, width)
        ):
            raise ValueError(
                "renderer RGB/depth dimensions or dtype differ from source camera"
            )
        near = float(sim.model.vis.map.znear * sim.model.stat.extent)
        far = float(sim.model.vis.map.zfar * sim.model.stat.extent)
        depth, valid = depth_buffer_to_z(buffer, near, far)
        official = self.camera_utils.get_real_depth_map(sim, np.where(valid, buffer, 0))
        if not np.allclose(official[valid], depth[valid], rtol=1e-6, atol=1e-6):
            raise ValueError(
                "metric depth disagrees with official robosuite conversion"
            )
        K = self.camera_utils.get_camera_intrinsic_matrix(sim, camera, height, width)
        index = sim.model.camera_name2id(camera)
        T_gl = np.eye(4)
        T_gl[:3, :3] = np.asarray(sim.data.cam_xmat[index]).reshape(3, 3)
        T_gl[:3, 3] = np.asarray(sim.data.cam_xpos[index])
        # The official helper ALREADY corrects GL to the CV optical frame.
        T_cv = self.camera_utils.get_camera_extrinsic_matrix(sim, camera)
        check_calibration(K, T_gl, T_cv)
        return {
            "rgb": rgb,
            "depth_m": depth,
            "valid": valid,
            "K": K,
            "T_world_camera_gl": T_gl,
            "T_world_camera_cv": T_cv,
            "clip_near_m": near,
            "clip_far_m": far,
        }

    def ray_check(self, camera, sample, *, atol_m=0.01, min_samples=16):
        """Independent geometry check; renderer/ray visibility mismatch is inconclusive.

        mj_ray returns distance along a UNIT ray, not optical-axis Z. Only hits
        matching the renderer's actual geom identity are compared. Render geom
        group options must be available; an unknown filter never means PASS.
        """
        try:
            import mujoco

            sim = self.env.sim
            context = sim._render_context_offscreen
            groups = np.asarray(context.vopt.geomgroup, dtype=np.uint8).copy()
            if groups.shape != (6,):
                raise ValueError("unknown renderer geometry-group filter")
            height, width = sample["valid"].shape
            segmentation = np.asarray(
                sim.render(
                    height=height, width=width, camera_name=camera, segmentation=True
                )
            )[::-1]
            if segmentation.shape != (height, width, 2):
                raise ValueError("unknown rendered geometry identity representation")
            rows, columns = np.nonzero(sample["valid"])
            picks = (
                np.unique(np.linspace(0, len(rows) - 1, min(128, len(rows)), dtype=int))
                if len(rows)
                else []
            )
            positions = np.array(
                [[columns[i] + 0.5, rows[i] + 0.5] for i in picks]
            ).reshape(-1, 2)
            T = sample["T_world_camera_cv"]
            rays = rays_cv(sample["K"], positions)
            norms = np.linalg.norm(rays, axis=1)
            directions = (rays / norms[:, None]) @ T[:3, :3].T
            origin = np.asarray(T[:3, 3], dtype=np.float64)
            errors, mismatches = [], 0
            model = getattr(sim.model, "_model", sim.model)
            data = getattr(sim.data, "_data", sim.data)
            for j, pick in enumerate(picks):
                rendered_type, rendered_id = segmentation[rows[pick], columns[pick]]
                if rendered_type != int(mujoco.mjtObj.mjOBJ_GEOM) or rendered_id < 0:
                    mismatches += 1
                    continue
                hit = np.array([-1], dtype=np.int32)
                distance = mujoco.mj_ray(
                    model, data, origin, directions[j].copy(), groups, True, -1, hit
                )
                if distance < 0 or hit[0] != rendered_id:
                    mismatches += 1
                    continue
                # Convert ray distance back to optical Z before comparing.
                z = float(sample["depth_m"][rows[pick], columns[pick]])
                errors.append(abs(float(distance) / norms[j] - z))
            enough = len(errors) >= min_samples
            maximum = max(errors) if errors else None
            status = (
                "INCONCLUSIVE"
                if not enough
                else ("PASS" if maximum <= atol_m else "FAIL")
            )
            return {
                "status": status,
                "matching_geom_samples": len(errors),
                "visibility_filter_mismatches": mismatches,
                "max_abs_z_error_m": maximum,
                "atol_m": atol_m,
                "min_samples": min_samples,
                "geomgroup": groups.tolist(),
                "static_geoms_included": True,
                "bodyexclude": -1,
                "distance_converted_to_optical_Z": True,
            }
        except (AttributeError, ImportError, ValueError, RuntimeError) as exc:
            return {"status": "INCONCLUSIVE", "reason": f"{type(exc).__name__}: {exc}"}

    def close(self):
        if self.env is not None:
            env, self.env = self.env, None
            env.close()


def original_rgb(reference, frame):
    """Decode an explicit original frame index; never re-encode RGB or seek by state time."""
    import imageio.v2 as imageio

    with imageio.get_reader(reference["video"], format="ffmpeg") as reader:
        return np.asarray(reader.get_data(frame))


def reprojection_error(sample):
    from .geometry import project_world

    rows, columns = np.nonzero(sample["valid"])
    if not len(rows):
        return None
    picks = np.unique(np.linspace(0, len(rows) - 1, min(32, len(rows)), dtype=int))
    pixels = np.c_[columns[picks] + 0.5, rows[picks] + 0.5]
    z = sample["depth_m"][rows[picks], columns[picks]]
    world = backproject_world(sample["K"], sample["T_world_camera_cv"], pixels, z)
    return float(
        np.max(
            np.abs(
                project_world(sample["K"], sample["T_world_camera_cv"], world) - pixels
            )
        )
    )
