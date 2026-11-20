"""Opt-in F27 diagnostics from the current native and MuJoCo state."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from g2.io import ContractError, digest, read_json, sha, write_json
from g2.latent_cache.contract import fingerprint
from g2.offline.direct_source import prepare_live_visual_specs
from g2.offline.scene_view_event_index import (
    SceneViewCursor,
    index_state,
    robot_pose_xy_yaw,
)
from g2.offline.spatial_metadata import (
    asset_identity,
    state_metadata,
    validate_raw_pose,
)
from g2.views.direct_color import close_gpu_renderers, save_direct_material_views
from g2.views.render_connections import renderer_member_sets
from g2.views.robot_pose_marker import chassis_pose, overlay_final_top_views
from g2.views.surface_registry import compile_surface_registry
from g2.views.surface_renderer import SurfaceRenderer


def _fixed_geoms(model, specs):
    """Only cache Geoms whose complete body ancestry is fixed."""
    fixed = []
    for spec in specs:
        geom = spec["g"]
        body = int(model.geom_bodyid[geom])
        while body and model.body_jntnum[body] == 0 and model.body_mocapid[body] < 0:
            body = int(model.body_parentid[body])
        if body == 0:
            fixed.append(geom)
    return fixed


class LiveF27:
    """Keep only the active clean scene and active marked image owners on disk."""

    def __init__(self, *, root, model, role_map, model_sha256, restore_camera):
        if not callable(restore_camera):
            raise ContractError(
                "live F27 requires the current Actor's EGL camera context"
            )
        self.restore_camera = restore_camera
        self.root = Path(root)
        self.root.mkdir()
        self.model = model
        self.role_map = role_map
        self.model_sha256 = sha(model_sha256)
        self.cursor = None
        self.renderer = None
        self.step = 0
        self.owners = {}
        self.keyframe = None
        self.room_references = None

    def publish(self, snapshot, *, data, snapshot_path):
        proof = snapshot.get("full_map_source", {})
        frame = snapshot["frame_id"]
        if (
            proof.get("live_frame") is not True
            or snapshot.get("surface_color_source")
            != "MUJOCO_GT_VISUAL_MESH_DIRECT_ONLY"
            or snapshot.get("surface_transport_mode")
            != "SOURCE_GT_GEOMETRY_ONLY_NO_PRESCAN"
            or self.role_map.get("scene_id") != snapshot["scene_id"]
            or self.role_map.get("state_source", {}).get("model_source_sha256")
            != self.model_sha256
            or (self.step == 0 and frame != 0)
        ):
            raise ContractError(
                "F27 requires the current reset's verified native snapshot"
            )
        state_sha = sha(proof.get("live_state_sha256"))
        source = snapshot["source_sha256"]
        if self.cursor is None:
            if state_sha != self.role_map["state_source"]["states_sha256"]:
                raise ContractError(
                    "F27 reset roles differ from native frame-zero provenance"
                )
            self.specs = prepare_live_visual_specs(self.model, snapshot, self.role_map)
            self.cursor = SceneViewCursor([spec["g"] for spec in self.specs])
            self.renderer = SurfaceRenderer(
                self.model,
                source,
                _fixed_geoms(self.model, self.specs),
                backend="gpu",
                lazy_texel_decode=True,
            )
        elif self.renderer.source_sha256 != source:
            raise ContractError("F27 source identity changed within the episode")

        pose = chassis_pose(self.model, data)
        room_refs = {r["uid"]: r["reference_frame"] for r in snapshot["rooms"]}
        geom_ids = self.cursor.ids
        event = self.cursor.observe(
            self.step,
            frame,
            np.asarray(data.geom_xpos)[geom_ids],
            np.asarray(data.geom_xmat)[geom_ids],
            robot_pose_xy_yaw(pose),
            force_scene_update=self.room_references is not None
            and self.room_references != room_refs,
        )
        member_plan = renderer_member_sets(snapshot)
        snapshot_hash = digest(snapshot_path)
        stage = self.root / f"frame_{frame}"
        if event.scene_rerender:
            registry = compile_surface_registry(self.model, data, self.specs, snapshot)
            by_room = {
                uid: {
                    "scene_id": snapshot["scene_id"],
                    "source_sha256": source,
                    "frame_id": frame,
                    "room_uid": uid,
                    "source_model_sha256": self.model_sha256,
                    "surface_registry": registry,
                    "surface_renderer": self.renderer,
                }
                for uid in room_refs
            }
            manifest = {
                "version_sha256": snapshot_hash,
                "source_scope": {
                    "status": proof["status"],
                    "full_scene_source_certified": False,
                    "live_frame": True,
                },
            }
            try:
                save_direct_material_views(
                    Path(snapshot_path).parent,
                    manifest,
                    snapshot,
                    stage,
                    visual_mesh_by_room=by_room,
                    keep_gpu_context=True,
                )
            finally:
                # Robosuite creates the camera context once and its render/read
                # methods assume it stays current. F27 binds its own EGL context.
                self.restore_camera()
            overlay_final_top_views(stage, pose, preserve_clean=True)
            self.keyframe = stage
        elif event.redraw_robot_arrow:
            report = read_json(self.keyframe / "direct_color_views.json")
            report.update(frame_id=frame, gpu_render_and_export_s=0.0)
            stage.mkdir()
            write_json(stage / "direct_color_views.json", report)
            overlay_final_top_views(
                stage, pose, preserve_clean=True, base_root=self.keyframe
            )

        report = read_json(self.keyframe / "direct_color_views.json")
        index = index_state(
            event, [view["rgb_file"] for view in report["views"]], marker_variants=True
        )
        if index["view_pngs"]:
            self.owners[self.step] = (stage, frame)
        native_catalog = read_json(self.keyframe / "g2_original_gpu" / "views.json")[
            "views"
        ]
        reports = {
            owner: {
                asset["rgb_file"]: asset
                for asset in read_json(root / "direct_color_views.json")["views"]
            }
            for owner, (root, _) in self.owners.items()
        }
        assets, owner_rows = [], {}
        for view in report["views"]:
            rel = view["rgb_file"]
            vid = asset_identity(rel)["view_id"]
            owner_id = index["view_refs"].get(rel, {}).get("ref_state", self.step)
            owner_root, owner_frame = self.owners[owner_id]
            asset = reports[owner_id].get(rel)
            if asset is None or digest(owner_root / rel) != asset["sha256"]:
                raise ContractError(
                    "live F27 image owner bytes differ from the renderer receipt"
                )
            assets.append(asset)
            owner_rows[vid] = {
                "path": str((owner_root / rel).relative_to(self.root)),
                "state_id": owner_id,
                "frame": owner_frame,
                "sha256": asset["sha256"],
                "projection": native_catalog[asset["native_view"]],
            }

        metadata = state_metadata(
            snapshot, assets, member_plan, state_id=self.step, owner_rows=owner_rows
        )
        live = {
            "schema": "g2_online_f27_views_v1",
            "spatial_metadata": metadata,
            "source_sha256": source,
            "live_state_sha256": state_sha,
            "native_snapshot_sha256": snapshot_hash,
            "source_model_sha256": self.model_sha256,
            "episode_id": proof["online_episode_id"],
            "simulation_timestamp_ns": snapshot["timestamp_ns"],
            "event": event.mode,
            "view_version": fingerprint(
                {
                    vid: {
                        "image_owner": view["image_owner"],
                        "image_projection": view["image_projection"]["projection_id"],
                    }
                    for vid, view in metadata["views"].items()
                    if view["availability"] != "absent"
                }
            ),
            "unmaterialized_native_views": sorted(
                member_plan.keys() - {asset["native_view"] for asset in assets}
            ),
            # The projection owner's pose can intentionally be older than this
            # independently observed chassis source pose on REUSE_ALL.
            "raw_robot_pose": validate_raw_pose(
                dict(
                    pose,
                    frame=frame,
                    source_frame=frame,
                    coordinate_frame=snapshot["world_frame"],
                ),
                frame=frame,
                world_frame=snapshot["world_frame"],
            ),
        }
        temp = self.root / ".latest_spatial_views.json"
        write_json(temp, live)
        temp.replace(self.root / "latest_spatial_views.json")

        retain = {event.scene_source_state, event.final_floor_source_state}
        for owner in self.owners.keys() - retain:
            old, _ = self.owners.pop(owner)
            shutil.rmtree(old)
        self.room_references = room_refs
        self.step += 1
        return live

    def close(self):
        if self.renderer is not None:
            self.renderer = None
            try:
                close_gpu_renderers()
            finally:
                self.restore_camera()
