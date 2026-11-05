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


def _rgb_difference(first, second):
    first, second = np.asarray(first), np.asarray(second)
    if (
        first.shape != second.shape
        or first.ndim != 3
        or first.shape[2] != 3
        or first.dtype != np.uint8
        or second.dtype != np.uint8
    ):
        raise ValueError("RGB diagnostic requires matching uint8 HWC images")
    difference = np.abs(first.astype(np.int16) - second.astype(np.int16))
    return {
        "identical": bool(not difference.any()),
        "mae": float(difference.mean()),
        "max_abs": int(difference.max()),
    }


def _front_face_mesh_distance(model, data, geom, origin, direction):
    """Independent ray/triangle intersection matching GL back-face culling.

    MuJoCo's mj_rayMesh intersects both sides. Compiled mesh vertices are already
    centered, rotated and scaled; only the live geom transform is applied here.
    Selection never uses the cached depth or the observed validation error.
    """
    mesh = int(model.geom_dataid[geom])
    vertex_start, face_start = model.mesh_vertadr[mesh], model.mesh_faceadr[mesh]
    vertices = model.mesh_vert[vertex_start : vertex_start + model.mesh_vertnum[mesh]]
    faces = model.mesh_face[face_start : face_start + model.mesh_facenum[mesh]]
    triangles = vertices[faces].astype(np.float64)
    rotation = np.asarray(data.geom_xmat[geom]).reshape(3, 3)
    point = (origin - data.geom_xpos[geom]) @ rotation
    vector = direction @ rotation
    edge1, edge2 = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    cross = np.cross(vector, edge2)
    determinant = np.einsum("ij,ij->i", edge1, cross)
    nonparallel_front = determinant > (
        1e-12 * np.linalg.norm(edge1, axis=1) * np.linalg.norm(edge2, axis=1)
    )
    if not nonparallel_front.any():
        return None
    delta = point - triangles[nonparallel_front, 0]
    inverse = 1.0 / determinant[nonparallel_front]
    u = np.einsum("ij,ij->i", delta, cross[nonparallel_front]) * inverse
    q = np.cross(delta, edge1[nonparallel_front])
    v = (q @ vector) * inverse
    distance = np.einsum("ij,ij->i", edge2[nonparallel_front], q) * inverse
    inside = (u >= 0) & (v >= 0) & (u + v <= 1) & (distance >= 0)
    return float(distance[inside].min()) if inside.any() else None


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

        mj_ray is double-sided and sees translucent geoms; the RGB depth pass
        culls back faces and does not write transparent surfaces to its buffer.
        Eligibility uses only the fresh renderer, never cached depth/ray errors.
        The unchanged tolerance and sample minimum apply after those filters.
        """
        diagnostics = {}
        try:
            import mujoco

            sim = self.env.sim
            context = sim._render_context_offscreen
            groups = np.asarray(context.vopt.geomgroup, dtype=np.uint8).copy()
            if groups.shape != (6,):
                raise ValueError("unknown renderer geometry-group filter")
            height, width = sample["valid"].shape
            render_args = dict(height=height, width=width, camera_name=camera)
            rgb_before = sim.render(**render_args)
            rgb_with_depth, raw = sim.render(**render_args, depth=True)
            scene = context.scn
            flags_before = np.asarray(scene.flags).copy()
            segmentation = np.asarray(sim.render(**render_args, segmentation=True))[
                ::-1
            ]
            rgb_after = sim.render(**render_args)
            flags_after = np.asarray(scene.flags).copy()
            model = getattr(sim.model, "_model", sim.model)
            data = getattr(sim.data, "_data", sim.data)
            diagnostics = {
                "rgb_vs_rgbd": _rgb_difference(rgb_before, rgb_with_depth),
                "segmentation_before_after": _rgb_difference(rgb_before, rgb_after),
                "render_context": {
                    "geomgroup": groups.tolist(),
                    "sitegroup": np.asarray(context.vopt.sitegroup).tolist(),
                    "vopt_flags": np.asarray(context.vopt.flags).tolist(),
                    "scene_flags_before": flags_before.tolist(),
                    "scene_flags_after": flags_after.tolist(),
                    "offscreen_samples": int(context.con.offSamples),
                },
                "model_visual_fingerprints": {
                    field: {
                        "shape": list(value.shape),
                        "dtype": str(value.dtype),
                        "sha256": hashlib.sha256(value.tobytes()).hexdigest(),
                    }
                    for field in (
                        "geom_rgba",
                        "mat_rgba",
                        "light_pos",
                        "light_dir",
                        "light_diffuse",
                        "light_specular",
                        "site_rgba",
                    )
                    if (value := np.ascontiguousarray(getattr(model, field))).size
                },
            }
            if (
                not np.array_equal(flags_before, flags_after)
                or not np.array_equal(groups, context.vopt.geomgroup)
                or context.vopt.flags[mujoco.mjtVisFlag.mjVIS_CONVEXHULL]
                or scene.flags[mujoco.mjtRndFlag.mjRND_WIREFRAME]
            ):
                raise ValueError("unsupported or changing renderer visibility options")
            if segmentation.shape != (height, width, 2):
                raise ValueError("unknown rendered geometry identity representation")
            near = float(sim.model.vis.map.znear * sim.model.stat.extent)
            far = float(sim.model.vis.map.zfar * sim.model.stat.extent)
            fresh, fresh_valid = depth_buffer_to_z(np.asarray(raw)[::-1], near, far)
            if fresh.shape != (height, width):
                raise ValueError("fresh diagnostic depth shape mismatch")
            opaque = {}
            for geom in list(scene.geoms)[: scene.ngeom]:
                if geom.objtype == int(mujoco.mjtObj.mjOBJ_GEOM):
                    acceptable = not geom.transparent and geom.rgba[3] >= 1
                    opaque[geom.objid] = opaque.get(geom.objid, True) and acceptable
            # Segmentation disables MSAA, normal depth does not. Even one mesh
            # can contain two depth layers with the SAME geom id at an edge.
            # Use fresh (not cached) depth to choose stable interior pixels.
            # Inverse Z is affine across a planar surface, so this does not
            # reject a correctly slanted plane merely for having a large slope.
            eligible = fresh_valid & sample["valid"]
            stable = fresh_valid.copy()
            if context.con.offSamples:
                stable[[0, -1], :] = False
                stable[:, [0, -1]] = False
                inverse = np.divide(
                    1, fresh, out=np.zeros_like(fresh), where=fresh_valid
                )
                for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    for sign in (-1, 1):
                        shift = (sign * dy, sign * dx)
                        stable &= np.roll(fresh_valid, shift, axis=(0, 1))
                        # MSAA depth resolve can choose an off-center sample,
                        # even inside one smooth face. Bound that footprint
                        # before comparing against a pixel-center ray.
                        stable &= (
                            np.abs(np.roll(fresh, shift, axis=(0, 1)) - fresh) <= atol_m
                        )
                        stable &= np.all(
                            segmentation == np.roll(segmentation, shift, axis=(0, 1)),
                            axis=2,
                        )
                    predicted_inverse = (
                        np.roll(inverse, (dy, dx), axis=(0, 1))
                        + np.roll(inverse, (-dy, -dx), axis=(0, 1))
                    ) / 2
                    predicted = np.divide(
                        1,
                        predicted_inverse,
                        out=np.zeros_like(fresh),
                        where=predicted_inverse > 0,
                    )
                    stable &= np.abs(predicted - fresh) <= atol_m / 2
            known_opaque = np.isin(
                segmentation[..., 1], [int(g) for g, value in opaque.items() if value]
            ) & (segmentation[..., 0] == int(mujoco.mjtObj.mjOBJ_GEOM))
            eligible &= stable & known_opaque
            rows, columns = np.nonzero(eligible)
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
            errors, mismatches, mesh_corrections = [], 0, 0
            cull_faces = bool(scene.flags[mujoco.mjtRndFlag.mjRND_CULL_FACE])
            for j, pick in enumerate(picks):
                rendered_type, rendered_id = segmentation[rows[pick], columns[pick]]
                if rendered_type != int(mujoco.mjtObj.mjOBJ_GEOM) or rendered_id < 0:
                    mismatches += 1
                    continue
                hit = np.array([-1], dtype=np.int32)
                near_distance = near * norms[j]
                ray_origin = origin + directions[j] * near_distance
                distance = mujoco.mj_ray(
                    model, data, ray_origin, directions[j].copy(), groups, True, -1, hit
                )
                if distance < 0 or hit[0] != rendered_id:
                    mismatches += 1
                    continue
                if (
                    cull_faces
                    and model.geom_type[rendered_id] == mujoco.mjtGeom.mjGEOM_MESH
                ):
                    distance = _front_face_mesh_distance(
                        model, data, rendered_id, ray_origin, directions[j]
                    )
                    if distance is None:
                        mismatches += 1
                        continue
                    mesh_corrections += 1
                # Convert ray distance back to optical Z before comparing.
                z = float(sample["depth_m"][rows[pick], columns[pick]])
                errors.append(abs((float(distance) + near_distance) / norms[j] - z))
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
                "front_face_mesh_samples": mesh_corrections,
                "renderer_eligibility": {
                    "fresh_valid_pixels": int(fresh_valid.sum()),
                    "stable_interior_pixels": int((fresh_valid & stable).sum()),
                    "opaque_eligible_pixels": int(eligible.sum()),
                    "selection_uses_cached_depth": False,
                    "fresh_plane_prediction_max_error_m": atol_m / 2,
                    "fresh_neighborhood_center_max_change_m": atol_m,
                    "back_face_culling": cull_faces,
                    "near_clip_m": near,
                },
                "rgb_render_diagnostics": diagnostics,
            }
        except (AttributeError, ImportError, ValueError, RuntimeError) as exc:
            return {
                "status": "INCONCLUSIVE",
                "reason": f"{type(exc).__name__}: {exc}",
                "rgb_render_diagnostics": diagnostics,
            }

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
