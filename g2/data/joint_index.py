"""G2 DATA_C: causal, source-bound per-episode joint index for G1 and G2 assets.

This is the offline index and evidence layer. It references immutable payloads:
DATA_B state15, original G1 17-frame video/action exact windows,
Spatial State/SG, a single initial static task text, and selected real Wan VAE.
It never embeds full video, latent, or repeated per-frame state tensors.
"""

from __future__ import annotations

import bisect
import gzip
import json

from g2.data.episode_state import (
    atomic_write_json,
    canonical,
    digest,
    episode_path,
    json_load,
    require_regular,
    verify_episode_state,
)


class DataCError(ValueError):
    pass


def join_episode_path(root, task_class, ep):
    return episode_path(root, task_class, ep)


def _one_text(lang: dict, *, expected_text: str, ep: int):
    if (
        lang.get("schema") != "g2_episode_text_bank_v1"
        or len(lang.get("texts", {})) != 1
    ):
        raise DataCError("one static task text per atomic episode is required")
    text_id, text = next(iter(lang["texts"].items()))
    if not text.get("original_preserved") or text.get("original_text") != expected_text:
        raise DataCError("enhanced original task instruction differs from source")
    if not isinstance(text.get("enhanced_text"), str) or not text["enhanced_text"]:
        raise DataCError("missing static enhanced task text")
    for entry in lang["states"]:
        if (
            entry["text_id"] != text_id
            or entry["caption_source"]["original_text"] != expected_text
            or entry["caption_source"]["episode_index"] != ep
        ):
            raise DataCError("language text changed in middle of atomic task")
    return text_id, text


def _owner_view(index, reader, episode_root, s, ordinal, view_id, *, recipe_id):
    """Validate native ViewReader logical-to-physical owner, geometry and content."""
    v = reader.read_view(view_id, s["state_id"])
    if not v["present"]:
        raise DataCError(f"selected view absent: {view_id}")
    owner = v["owner"]
    if owner["owner_frame"] > s["frame"] or owner["owner_state_ordinal"] > ordinal:
        raise DataCError("future View physical owner")
    meta = json_load(episode_root / s["spatial_metadata"])
    desc = meta["views"].get(view_id)
    if not desc:
        raise DataCError("selected view unavailable in spatial metadata")
    if (
        desc["image_owner"]["frame"] != owner["owner_frame"]
        or desc["image_owner"]["sha256"] != owner["png_sha256"]
        or desc["membership_version"]
        != s["selection"]["membership_ids"].get(
            "sixview/floor_top" if view_id == "sixview/floor_top_w_rbs" else view_id,
        )
    ):
        # The top with_robot variant's member plan must match the selected clean
        # top, while the source image content identity is distinct.
        raise DataCError("selected View owner or membership differs from source")
    projection = desc["image_projection"]
    if (
        projection["units"] != "m"
        or projection["reference_frame"]["geometry_coordinates"] != "world"
        or projection["meters_per_pixel"] <= 0
        or not projection["projection_id"]
    ):
        raise DataCError("selected spatial geometry metadata invalid")
    vae_view = index.manifest["views"][view_id]
    record_index = vae_view["state_records"][ordinal]
    if record_index != v["record_index"]:
        raise DataCError("VAE logical-owner mapping differs")
    return {
        "view_id": view_id,
        "physical_owner_frame": owner["owner_frame"],
        "physical_owner_state": owner["owner_state_id"],
        "physical_owner_ordinal": owner["owner_state_ordinal"],
        "physical_png_sha256": owner["png_sha256"],
        "cache_file": vae_view["path"],
        "cache_file_sha256": vae_view["sha256"],
        "record_index": record_index,
        "record_sha256": vae_view["record_sha256"][record_index],
        "vae_recipe_id": recipe_id,
        "projection_id": projection["projection_id"],
        "membership_version": desc["membership_version"],
        "geometry_version": desc["geometry_version"],
        "spatial_metadata_relpath": s["spatial_metadata"],
        "view_scope": "floor"
        if desc.get("is_floor_top")
        else ("island" if desc.get("island_id") is not None else "room"),
        "room_id": str(desc.get("room_uid")),
        "island_id": desc.get("island_id"),
        "top_variant": (
            "with_robot"
            if view_id == "sixview/floor_top_w_rbs"
            else "without_robot"
            if view_id == "sixview/floor_top"
            else None
        ),
        "direction": view_id.rsplit("/", 1)[-1].removesuffix("_w_rbs"),
    }



def _assert_dual_top(state):
    """Verify both published tops share geometry but not assumed content/owner."""
    tops = state.get("top_views")
    if not isinstance(tops, dict) or set(tops) != {"with_robot", "without_robot"}:
        raise DataCError("dual top state requires both physical references")
    if any(
        v.get("top_variant") != name
        or v.get("view_id") != (
            "sixview/floor_top_w_rbs" if name == "with_robot" else "sixview/floor_top"
        )
        or v.get("view_scope") != "floor"
        or v["physical_owner_frame"] > state["frame"]
        for name, v in tops.items()
    ):
        raise DataCError("dual top reference identity/owner invalid")
    a, b = tops["with_robot"], tops["without_robot"]
    if any(
        a[k] != b[k]
        for k in ("projection_id", "geometry_version", "membership_version", "vae_recipe_id")
    ):
        raise DataCError("dual top views do not share spatial geometry/recipe")
    if any(v.get("top_variant") is not None for v in state["selected_views"]):
        raise DataCError("dual top state cannot contain duplicate top in side views")


def _state_views(state):
    """All selected physical references, exactly once per variant."""
    if "top_views" in state:
        _assert_dual_top(state)
        return (
            *state["selected_views"],
            state["top_views"]["with_robot"],
            state["top_views"]["without_robot"],
        )
    return tuple(state["selected_views"])


def make_joint_recipe(*, state_recipe_id: str, view_recipe_id: str, top_variant: str):
    """Single source of truth for the original immutable G2 joint recipe."""
    if top_variant not in ("with_robot", "without_robot", "both"):
        raise DataCError("unknown top variant")
    if not view_recipe_id or not state_recipe_id:
        raise DataCError("missing state/View recipe identity")
    return {
        "schema": (
            "g2_data_c_joint_recipe_v2"
            if top_variant == "both"
            else "g2_data_c_joint_recipe_v1"
        ),
        "state15_recipe_id": state_recipe_id,
        "view_recipe_id": view_recipe_id,
        "top_variant": top_variant,
        **(
            {"top_variants": ["with_robot", "without_robot"]}
            if top_variant == "both"
            else {}
        ),
        "alignment": "source_20hz_decision_to_most_recent_eligible_spatial_state",
        "horizon": 16,
        "spatial_update_policy": "no_future_owner",
        "state15_source": "source_base_world",
        "static_text_policy": "candidate_episode_static_initial_text",
    }


def build_episode_joint(
    *,
    task_class: str,
    episode_index: int,
    raw_source: dict,
    state15_root,
    view_root,
    data_c_root,
    state_recipe_id: str,
    view_recipe_id: str | None,
    top_variant: str = "with_robot",
    resume: bool = True,
):
    """Create a complete *candidate* joint index for every legal 20Hz window."""
    if top_variant not in {"with_robot", "without_robot", "both"}:
        raise DataCError("top variant must be explicit")
    if not view_recipe_id:
        raise DataCError("R2 joint index requires actual per-view Wan VAE recipe")
    from g2.latent_cache.storage import ViewReader, open_episode_index

    b = verify_episode_state(state15_root, raw_source, expected_recipe=state_recipe_id)
    epdir = episode_path(view_root, task_class, episode_index)
    complete = json_load(epdir / "COMPLETE.json")
    manifest_path = epdir / "episode_manifest.json"
    require_regular(manifest_path)
    if complete.get("complete") is not True or complete.get(
        "episode_manifest_sha256"
    ) != digest(manifest_path):
        raise DataCError("G2 view-first episode was not fully published")
    spatial = json_load(manifest_path)
    if spatial["episode_id"] != episode_index or spatial["state_count"] != len(
        spatial["states"]
    ):
        raise DataCError("G2 spatial episode identity mismatch")
    src_ready = json_load(epdir / "SPATIAL_SOURCE_READY.json")
    if src_ready.get("complete_spatial_source") is not True:
        raise DataCError("spatial source is not sealed")
    lang_path = epdir / "language.json"
    require_regular(lang_path)
    lang = json_load(lang_path)
    text_id, text = _one_text(
        lang, expected_text=raw_source["instruction"], ep=episode_index
    )
    idx = open_episode_index(epdir, expected_recipe_id=view_recipe_id)
    if idx.episode_key != f"{task_class}/episode_{episode_index:06d}":
        raise DataCError("VAE episode key differs from raw source")
    if len(spatial["states"]) != len(idx.manifest["states"]):
        raise DataCError("VAE spatial timeline length mismatch")
    for ordinal, (state, record) in enumerate(
        zip(spatial["states"], idx.manifest["states"], strict=True)
    ):
        if (
            state["state_id"] != record["logical_state_id"]
            or state["frame"] != record["frame"]
            or record["state_ordinal"] != ordinal
        ):
            raise DataCError("VAE and spatial source logical states differ")
    frames = [int(s["frame"]) for s in spatial["states"]]
    if not frames or frames[0] != 0 or frames != sorted(set(frames)):
        raise DataCError("spatial state timestamps not strictly ordered")
    if frames[-1] != raw_source["source_frame_count"] - 1:
        raise DataCError("final spatial state must bind terminal original frame")
    states = []
    with ViewReader(idx, max_views=16, max_bytes=256 * 1024 * 1024) as reader:
        for ordinal, s in enumerate(spatial["states"]):
            selection = s["selection"]
            if selection["top_variant"] != "clean":
                raise DataCError("unknown original selection top variant")
            canonical_ids = list(selection["selected_view_ids"])
            if not canonical_ids or "sixview/floor_top" not in canonical_ids:
                raise DataCError("missing canonical mandatory top")
            if (
                canonical_ids.count("sixview/floor_top") != 1
                or len(canonical_ids) != len(set(canonical_ids))
            ):
                raise DataCError("selected canonical top must be unique")
            ids = [
                "sixview/floor_top_w_rbs"
                if v == "sixview/floor_top" and top_variant == "with_robot"
                else v
                for v in canonical_ids
                if top_variant != "both" or v != "sixview/floor_top"
            ]
            if (
                len(ids) != len(set(ids))
                or sum(
                    v in {"sixview/floor_top", "sixview/floor_top_w_rbs"} for v in ids
                )
                != (0 if top_variant == "both" else 1)
            ):
                raise DataCError("selected top view variant count invalid")
            for required in (s["scene_graph"], s["spatial_metadata"]):
                require_regular(epdir / required)
            with gzip.open(epdir / s["scene_graph"], "rt") as input:
                sg = json.load(input)
            if sg.get("frame_id") != s["frame"] or sg.get("world_frame") != "world":
                raise DataCError("Scene Graph identity/world frame mismatch")
            views = [
                _owner_view(idx, reader, epdir, s, ordinal, v, recipe_id=view_recipe_id)
                for v in ids
            ]
            state_record = {
                "logical_state_id": s["state_id"],
                "frame": s["frame"],
                "scene_graph_file": s["scene_graph"],
                "spatial_metadata_file": s["spatial_metadata"],
                "geometry_version": s["geometry_version"],
                "selected_views": views,
                "text_id": text_id,
            }
            if top_variant == "both":
                state_record["top_views"] = {
                    "with_robot": _owner_view(
                        idx,
                        reader,
                        epdir,
                        s,
                        ordinal,
                        "sixview/floor_top_w_rbs",
                        recipe_id=view_recipe_id,
                    ),
                    "without_robot": _owner_view(
                        idx,
                        reader,
                        epdir,
                        s,
                        ordinal,
                        "sixview/floor_top",
                        recipe_id=view_recipe_id,
                    ),
                }
                _assert_dual_top(state_record)
            states.append(state_record)
    length = raw_source["source_frame_count"]
    if raw_source["exact_window_count"] != length - 16:
        raise DataCError("G1 verified exact-window count differs from original frames")
    # One index row per legal G1 decision frame; shared spatial states refer
    # to prior or current logical state only, never the nearest future state.
    windows = []
    for frame in range(length - 16):
        ordinal = bisect.bisect_right(frames, frame) - 1
        record = states[ordinal]
        if record["frame"] > frame:
            raise DataCError("spatial state future leak")
        if any(v["physical_owner_frame"] > frame for v in _state_views(record)):
            raise DataCError("VAE future physical owner leak")
        windows.append(
            {
                "decision_frame": frame,
                "state15_frame": frame,
                "action_start_frame": frame,
                "action_last_frame": frame + 15,
                "observation_last_frame": frame + 16,
                "spatial_state_ordinal": ordinal,
                "spatial_state_frame": record["frame"],
                "text_id": text_id,
            }
        )
    recipe = make_joint_recipe(
        state_recipe_id=state_recipe_id,
        view_recipe_id=view_recipe_id,
        top_variant=top_variant,
    )
    payload = {
        "schema": (
            "g2_data_c_joint_episode_v2"
            if top_variant == "both"
            else "g2_data_c_joint_episode_v1"
        ),
        "task_class": task_class,
        "episode_index": episode_index,
        "recipe": recipe,
        "recipe_id": canonical(recipe),
        "source_binding_digest": raw_source["source_binding_digest"],
        "original_instruction": raw_source["instruction"],
        "source_frame_count": length,
        "g1_video_cache_manifest_sha256": raw_source["cache_manifest_sha256"],
        "data_b_sha256": b["state15_sha256"],
        "data_b_relpath": f"tasks/{task_class}/episodes/episode_{episode_index:06d}/state15.pt",
        "view_episode_manifest_sha256": digest(manifest_path),
        "view_vae_manifest_sha256": digest(epdir / "vae_cache/manifest.json"),
        "view_vae_recipe_id": view_recipe_id,
        "static_text": {
            "text_id": text_id,
            "original_instruction": text["original_text"],
            "enhanced_instruction": text["enhanced_text"],
            "text_template_recipe_id": text["recipe"]["recipe_id"],
            "original_sha256": text["original_sha256"],
            "production_template_frozen": text["recipe"]["production_template_frozen"],
        },
        "spatial_states": states,
        "windows": windows,
        # Explicitly not a formal model/training approval; immutable index
        # proves truthful joins even before text/split/train receipts freeze.
        "training_ready": False,
        "readiness_reasons": [
            "initial_spatial_text_template_is_not_production_frozen",
            "G2_exact_window_train_val_split_receipt_not_approved",
            "formal_data_c_provider_not_yet_admitted_by_G2RunRecipe",
        ],
    }
    target_dir = join_episode_path(data_c_root, task_class, episode_index)
    target = target_dir / "joint_index.json"
    marker_path = target_dir / "COMPLETE.json"
    if marker_path.exists():
        if not resume:
            raise FileExistsError(marker_path)
        return verify_joint_episode(
            data_c_root,
            raw_source,
            state15_root,
            view_root,
            expected_recipe_id=payload["recipe_id"],
        )
    if target_dir.exists() and any(target_dir.iterdir()):
        raise DataCError("DATA_C partial output: refuse overwrite")
    target_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(target, payload)
    marker = {
        "schema": (
            "g2_data_c_complete_v2"
            if top_variant == "both"
            else "g2_data_c_complete_v1"
        ),
        "complete": True,
        "joint_sha256": digest(target),
        "task_class": task_class,
        "episode_index": episode_index,
        "recipe_id": payload["recipe_id"],
        "source_binding_digest": raw_source["source_binding_digest"],
        "frame_count": length,
        "decision_window_count": len(windows),
        "training_ready": False,
    }
    atomic_write_json(marker_path, marker)
    return verify_joint_episode(
        data_c_root,
        raw_source,
        state15_root,
        view_root,
        expected_recipe_id=payload["recipe_id"],
    )


def verify_joint_episode(
    data_c_root, raw_source, state15_root, view_root, *, expected_recipe_id: str
) -> dict:
    """Read-only critical receipt/identity checks; no render, VAE or backfill."""
    task, ep = raw_source["task_class"], raw_source["episode_index"]
    root = join_episode_path(data_c_root, task, ep)
    target, marker_path = root / "joint_index.json", root / "COMPLETE.json"
    require_regular(target)
    require_regular(marker_path)
    marker = json_load(marker_path)
    value = json_load(target)
    if (
        marker.get("schema")
        not in {"g2_data_c_complete_v1", "g2_data_c_complete_v2"}
        or marker.get("complete") is not True
    ):
        raise DataCError("DATA_C completion marker invalid")
    if (
        marker["joint_sha256"] != digest(target)
        or marker["source_binding_digest"] != raw_source["source_binding_digest"]
        or marker["recipe_id"] != expected_recipe_id
        or value["recipe_id"] != expected_recipe_id
        or value["recipe_id"] != canonical(value["recipe"])
    ):
        raise DataCError("DATA_C recipe/source/immutable file checksum mismatch")
    if (
        value.get("schema")
        not in {"g2_data_c_joint_episode_v1", "g2_data_c_joint_episode_v2"}
        or (
            value.get("schema") == "g2_data_c_joint_episode_v2"
            and (
                marker.get("schema") != "g2_data_c_complete_v2"
                or value["recipe"].get("top_variant") != "both"
            )
        )
        or value["episode_index"] != ep
        or value["task_class"] != task
        or value["source_frame_count"] != raw_source["source_frame_count"]
        or value["original_instruction"] != raw_source["instruction"]
        or len(value["windows"]) != raw_source["exact_window_count"]
    ):
        raise DataCError("DATA_C original source contract mismatch")
    if value["view_episode_manifest_sha256"] != digest(
        episode_path(view_root, task, ep) / "episode_manifest.json"
    ) or value["view_vae_manifest_sha256"] != digest(
        episode_path(view_root, task, ep) / "vae_cache/manifest.json"
    ):
        raise DataCError("DATA_C view source or VAE manifest changed")
    b = verify_episode_state(
        state15_root, raw_source, expected_recipe=value["recipe"]["state15_recipe_id"]
    )
    if b["state15_sha256"] != value["data_b_sha256"]:
        raise DataCError("DATA_C DATA_B state15 payload changed")
    for expected_frame, window in enumerate(value["windows"]):
        if (
            window["decision_frame"] != expected_frame
            or window["state15_frame"] != expected_frame
            or window["action_start_frame"] != expected_frame
            or window["observation_last_frame"] != expected_frame + 16
            or window["action_last_frame"] != expected_frame + 15
            or window["spatial_state_frame"] > expected_frame
        ):
            raise DataCError("DATA_C future leak, gap or G1 exact-window mismatch")
        st = value["spatial_states"][window["spatial_state_ordinal"]]
        if st["frame"] != window["spatial_state_frame"] or any(
            v["physical_owner_frame"] > window["spatial_state_frame"]
            for v in _state_views(st)
        ):
            raise DataCError("DATA_C future view owner or spatial index mismatch")
    return {
        "episode_root": str(root),
        "joint_index": str(target),
        "joint_sha256": marker["joint_sha256"],
        "state15_sha256": value["data_b_sha256"],
        "recipe_id": value["recipe_id"],
        "frame_count": value["source_frame_count"],
        "window_count": len(value["windows"]),
        "spatial_states": len(value["spatial_states"]),
        "training_ready": False,
    }
