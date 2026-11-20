"""Causal G2 conditions for the existing RoboCasa EvalV2 Actor."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from g2.data.pose5 import Pose5Recipe, build_state15_from_current
from g2.data.task_entities import bind_task_entities
from g2.io import ContractError, canonical, digest, read_json, sha
from g2.language.initial_context import InitialLanguageRecipe, build_initial_language
from g2.nav_bridge.snapshot import summarize_source_graph

from .nav_session import STATE_ENCODING, NativeSession
from .spatial_source import LIVE_VIEWS, PERIOD_FRAMES, task_binding_identity

# PandaOmron_modality.json, through RoboCasa's official LeRobot exporter.
PANDA_OMRON_STATE = (
    ("robot0_base_pos", 3),
    ("robot0_base_quat", 4),
    ("robot0_base_to_eef_pos", 3),
    ("robot0_base_to_eef_quat", 4),
    ("robot0_gripper_qpos", 2),
)


def source_state16(observation):
    values = []
    for name, size in PANDA_OMRON_STATE:
        if name not in observation:
            raise ContractError(f"current PandaOmron observation is missing {name}")
        value = np.asarray(observation[name])
        if (
            value.shape != (size,)
            or value.dtype.kind not in "fiu"
            or not np.isfinite(value).all()
        ):
            raise ContractError(f"invalid current PandaOmron observation {name}")
        values.append(value)
    return np.concatenate(values, dtype=np.float64)


def _metadata_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(
        f"unexpected value in RoboCasa reset metadata: {type(value).__name__}"
    )


class OnlineG2DataAdapter:
    def __init__(self, native, *, data_version, alignment_version, top_variant=None):
        self.native = native
        self.data_version = data_version
        self.alignment_version = alignment_version
        self.top_variant = top_variant
        self.pose_recipe = Pose5Recipe()
        self.language_recipe = InitialLanguageRecipe()
        self.frame = None
        self.spatial_frame = None
        self.closed = False

    def reset(
        self,
        env,
        observation,
        *,
        episode_id,
        task,
        instruction,
        frame,
        episode_index,
        ep_meta,
    ):
        if (
            self.closed
            or self.frame is not None
            or type(frame) is not int
            or frame != 0
            or type(episode_index) is not int
            or episode_index < 0
            or not isinstance(episode_id, str)
            or not 0 < len(episode_id) <= 256
        ):
            raise ContractError(
                "a fresh G2 runtime requires one canonical Episode reset"
            )
        try:
            self.state = source_state16(observation)
            if not isinstance(ep_meta, dict) or ep_meta.get("lang") != instruction:
                raise ContractError(
                    "EvalV2 instruction differs from official reset caption"
                )
            ep_meta = json.loads(
                json.dumps(ep_meta, allow_nan=False, default=_metadata_value)
            )
            snapshot = self.native.start(env, episode_id=episode_id, ep_meta=ep_meta)
            graph = summarize_source_graph(
                snapshot, self.native.observe(env, 0), 0, snapshot["source_sha256"], 0
            )
            graph.update(
                schema="g2_robocasa_live_spatial_scene_graph_v1",
                live_state_sha256=graph.pop("original_state_row_sha256"),
                state_encoding=STATE_ENCODING,
                world_frame=snapshot["world_frame"],
                room_source="CURRENT_EPISODE_LIVE_NATIVE_NAV_SG",
                room_footprint_update_policy="NATIVE_NAV_SG_ONLINE",
            )
            task_set = bind_task_entities(task, ep_meta, graph)
            if task_set["binding_status"] != "BOUND":
                raise ContractError(
                    f"RoboCasa task roles unresolved: {task_set['failures']}"
                )
            text = build_initial_language(
                original_instruction=instruction,
                scene_graph=graph,
                task_set=task_set,
                task_class=task,
                episode_index=episode_index,
                recipe=self.language_recipe,
            )
            self.entity_ids = self._entities(snapshot)
            self.spatial_frame = self.frame = 0
            self.snapshot = snapshot
            self.episode_id = episode_id
            self.scene_id = snapshot["scene_id"]
            self.subtask_id = f"atomic_{episode_index:06d}"
            self.task_binding_id = task_binding_identity(
                episode_id, snapshot["source_sha256"], task_set, text["text_id"]
            )
            self.static_text = {
                "original_instruction": instruction,
                "enhanced_instruction": text["augmented_instruction"],
                "episode_id": episode_id,
                "subtask_id": self.subtask_id,
                "template_identity": self.language_recipe.recipe_id,
                "source_identity": snapshot["source_sha256"],
                "initial_context_identity": text["text_id"],
                "context_scope": "initial_spatial_context",
            }
            # Diagnose actual task grounding and provider recipe on the
            # episode's private scratch path, including any candidate text.
            (self.native.work / "initial_condition.json").write_bytes(
                canonical(
                    {
                        "task_set": task_set,
                        "text": text,
                        "data_version": self.data_version,
                        "alignment_version": self.alignment_version,
                        "state15_recipe_id": self.pose_recipe.recipe_id,
                        "initial_state15": build_state15_from_current(
                            self.state, recipe=self.pose_recipe
                        ).tolist(),
                    }
                )
            )
            self._capture_spatial_source()
        except Exception:
            self.close()
            raise

    @staticmethod
    def _entities(snapshot):
        result = {
            (entity["source_instance_id"], entity["source_part_id"]): entity["id"]
            for entity in snapshot["entities"]
        }
        if len(result) != len(snapshot["entities"]):
            raise ContractError(
                "native source instance and part must uniquely identify entities"
            )
        return result

    def _capture_spatial_source(self):
        if self.top_variant is None:
            return
        source = self.native.work / LIVE_VIEWS
        self.spatial_source = dict(
            path=source.relative_to(self.native.scratch_root).as_posix(),
            sha256=digest(source),
        )

    def decision(self, observation, *, frame, composite, local_memory):
        if (
            self.closed
            or self.frame is None
            or type(frame) is not int
            or frame != self.frame
            or local_memory.get("episode_id") != self.episode_id
            or local_memory.get("consumer_step") != frame
            or not np.array_equal(source_state16(observation), self.state)
        ):
            raise ContractError(
                "G2 decision does not match the completed observation frontier"
            )
        request = {
            "state": build_state15_from_current(
                self.state, recipe=self.pose_recipe
            ).tolist(),
            "prompt": self.static_text["enhanced_instruction"],
            "g2": {
                "identity": {
                    "episode_id": self.episode_id,
                    "scene_id": self.scene_id,
                    "subtask_id": self.subtask_id,
                    "decision_frame": frame,
                    "logical_state_frame": self.spatial_frame,
                    "data_version": self.data_version,
                    "alignment_version": self.alignment_version,
                    "state15_recipe_id": self.pose_recipe.recipe_id,
                    "task_binding_id": self.task_binding_id,
                },
                "static_text": dict(self.static_text),
            },
        }
        if self.top_variant is not None:
            request["g2"].update(
                top_variant=self.top_variant, spatial_source=dict(self.spatial_source)
            )
        return request

    def record_completed(
        self, env, observation, *, source_frame, canonical_raw15, submitted_env12
    ):
        if (
            self.closed
            or self.frame is None
            or type(source_frame) is not int
            or source_frame != self.frame
            or np.shape(canonical_raw15) != (15,)
            or np.shape(submitted_env12) != (12,)
            or not np.isfinite(canonical_raw15).all()
            or not np.isfinite(submitted_env12).all()
        ):
            raise ContractError(
                "only the just-completed canonical action can advance the frontier"
            )
        try:
            frame = source_frame + 1
            row = self.native.observe(env, frame)
            state = source_state16(observation)
            if frame % PERIOD_FRAMES == 0:
                snapshot = self.native.publish(frame, row)
                if self._entities(snapshot) != self.entity_ids:
                    raise ContractError(
                        "native entity IDs changed within the live Episode"
                    )
                self.snapshot, self.spatial_frame = snapshot, frame
                self._capture_spatial_source()
            self.state, self.frame = state, frame
        except Exception:
            self.close()
            raise

    def close(self):
        if not self.closed:
            self.closed = True
            self.native.close()


def create_episode_runtime(*, profile, settings):
    if profile not in ("g2_r1", "g2_r2"):
        raise ContractError("live runtime requires an explicit G2 profile")
    global_enabled = profile == "g2_r2"
    required = {
        "run_recipe",
        "nav_checkout",
        "nav_revision",
        "ros_setup",
        "scratch_root",
    }
    if (
        not isinstance(settings, dict)
        or not required <= settings.keys() <= required | {"render_f27"}
        or type(settings.get("render_f27", False)) is not bool
    ):
        raise ContractError("exact G2 online settings are required")
    recipe = read_json(Path(settings["run_recipe"]), limit=1 << 20)
    top_variant = (
        recipe["global_memory"]["top_view_variant"] if global_enabled else None
    )
    if (
        recipe["training"]["profile"] != ("R2" if global_enabled else "R1")
        or recipe["global_memory"]["enabled"] is not global_enabled
        or (
            global_enabled
            and (
                settings.get("render_f27") is not True
                or top_variant not in ("with_robot", "without_robot")
            )
        )
        or recipe["training"]["state15_recipe_identity"] != Pose5Recipe().recipe_id
        or recipe["provider_kwargs"]["initial_language_recipe_id"]
        != InitialLanguageRecipe().recipe_id
        or recipe["alignment_version"] != "g2_causal_latest_spatial_v1"
    ):
        raise ContractError(
            "materialized G2 training recipe differs from the online ABI"
        )
    return OnlineG2DataAdapter(
        NativeSession(**{k: v for k, v in settings.items() if k != "run_recipe"}),
        data_version=sha(recipe["training"]["data_identity"], "training data identity"),
        alignment_version=recipe["alignment_version"],
        top_variant=top_variant,
    )
