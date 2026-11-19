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
    file_identity,
    json_load,
    read_bound_json,
    require_regular,
    verify_episode_state,
)
from g2.latent_cache.contract import safe_relative


class DataCError(ValueError):
    pass


TOP_VIEW_IDS = {
    "with_robot": "sixview/floor_top_w_rbs",
    "without_robot": "sixview/floor_top",
}


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


def _owner_view(
    index, reader, episode_root, s, ordinal, view_id, *, recipe_id, metadata=None
):
    """Validate native ViewReader logical-to-physical owner, geometry and content."""
    v = reader.read_view(view_id, s["state_id"])
    if not v["present"]:
        raise DataCError(f"selected view absent: {view_id}")
    owner = v["owner"]
    if owner["owner_frame"] > s["frame"] or owner["owner_state_ordinal"] > ordinal:
        raise DataCError("future View physical owner")
    rel = safe_relative(s["spatial_metadata"], suffix=".json")
    meta = metadata if metadata is not None else read_bound_json(episode_root / rel)[0]
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
        or v.get("view_id") != TOP_VIEW_IDS[name]
        or v.get("view_scope") != "floor"
        or v["physical_owner_frame"] > state["frame"]
        for name, v in tops.items()
    ):
        raise DataCError("dual top reference identity/owner invalid")
    a, b = tops["with_robot"], tops["without_robot"]
    if any(
        a[k] != b[k]
        for k in (
            "projection_id",
            "geometry_version",
            "membership_version",
            "vae_recipe_id",
        )
    ):
        raise DataCError("dual top views do not share spatial geometry/recipe")
    if any(
        v.get("top_variant") is not None
        or v.get("view_scope") == "floor"
        or v.get("view_id") in TOP_VIEW_IDS.values()
        for v in state["selected_views"]
    ):
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


def validate_joint_timeline(value):
    """One window/owner check for producer resume, certification and consumption."""
    length = value["source_frame_count"]
    windows, states = value["windows"], value["spatial_states"]
    text = value["static_text"]["text_id"]
    if (
        type(length) is not int
        or length < 17
        or not isinstance(windows, list)
        or len(windows) != length - 16
        or not isinstance(states, list)
        or not states
    ):
        raise DataCError("DATA_C F-16 window count or spatial timeline is invalid")
    frames = [s["frame"] for s in states]
    ids = [s["logical_state_id"] for s in states]
    if (
        any(type(f) is not int for f in frames)
        or any(type(i) is not int or i < 0 for i in ids)
        or len(set(ids)) != len(ids)
        or frames != sorted(set(frames))
        or frames[0] != 0
        or frames[-1] != length - 1
    ):
        raise DataCError(
            "DATA_C spatial states must span frame 0 to the original terminal frame"
        )
    variant = value["recipe"]["top_variant"]
    for ordinal, state in enumerate(states):
        safe_relative(state["scene_graph_file"], suffix=".gz")
        safe_relative(state["spatial_metadata_file"], suffix=".json")
        if state["text_id"] != text or ("top_views" in state) != (variant == "both"):
            raise DataCError("DATA_C state text or top schema differs from the episode")
        refs = _state_views(state)
        view_ids = [ref["view_id"] for ref in refs]
        if len(view_ids) != len(set(view_ids)):
            raise DataCError("DATA_C selected View is duplicated")
        if variant != "both" and [
            v for v in view_ids if v in TOP_VIEW_IDS.values()
        ] != [TOP_VIEW_IDS[variant]]:
            raise DataCError("DATA_C stored top does not match the selected variant")
        for ref in refs:
            owner = ref["physical_owner_ordinal"]
            if (
                type(owner) is not int
                or not 0 <= owner <= ordinal
                or ref["physical_owner_frame"] != frames[owner]
                or ref["physical_owner_state"] != ids[owner]
                or ref["spatial_metadata_relpath"] != state["spatial_metadata_file"]
                or ref["top_variant"]
                != next(
                    (k for k, v in TOP_VIEW_IDS.items() if v == ref["view_id"]), None
                )
                or ref["vae_recipe_id"] != value["view_vae_recipe_id"]
            ):
                raise DataCError("DATA_C future or mismatched View owner/state/recipe")
    ordinal = 0
    for frame, window in enumerate(windows):
        while ordinal + 1 < len(frames) and frames[ordinal + 1] <= frame:
            ordinal += 1
        expected = dict(
            decision_frame=frame,
            state15_frame=frame,
            action_start_frame=frame,
            action_last_frame=frame + 15,
            observation_last_frame=frame + 16,
            spatial_state_ordinal=ordinal,
            spatial_state_frame=frames[ordinal],
            text_id=text,
        )
        if any(
            type(window.get(k)) is not type(v) or window[k] != v
            for k, v in expected.items()
        ):
            raise DataCError(
                "DATA_C exact window does not reference its latest causal spatial state"
            )


def read_joint_episode(
    folder,
    *,
    task,
    episode,
    recipe_id,
    source_binding_digest,
    expected_sha256=None,
    window_count=None,
):
    path = folder / "joint_index.json"
    value, joint_sha, _ = read_bound_json(path, expected_sha256=expected_sha256)
    marker, _, _ = read_bound_json(folder / "COMPLETE.json")
    recipe = value["recipe"]
    version = 2 if recipe["top_variant"] == "both" else 1
    length = value["source_frame_count"]
    if (
        value.get("schema") != f"g2_data_c_joint_episode_v{version}"
        or value.get("episode_index") != episode
        or value.get("task_class") != task
        or value.get("training_ready") is not False
        or value.get("recipe_id") != recipe_id
        or recipe_id != canonical(recipe)
        or value.get("view_vae_recipe_id") != recipe.get("view_recipe_id")
        or value.get("source_binding_digest") != source_binding_digest
        or marker.get("schema") != f"g2_data_c_complete_v{version}"
        or marker.get("complete") is not True
        or marker.get("training_ready") is not False
        or marker.get("joint_sha256") != joint_sha
        or marker.get("recipe_id") != recipe_id
        or marker.get("source_binding_digest") != source_binding_digest
        or marker.get("task_class") != task
        or marker.get("episode_index") != episode
        or marker.get("frame_count") != length
        or marker.get("decision_window_count") != len(value["windows"])
        or (window_count is not None and len(value["windows"]) != window_count)
    ):
        raise DataCError("DATA_C episode completion/source/recipe binding differs")
    validate_joint_timeline(value)
    return value, joint_sha


def open_joint_view_source(root, joint):
    """Bind the two published indexes to DATA_C without opening any latent file."""
    from g2.latent_cache.storage import open_episode_index

    path = root / "episode_manifest.json"
    marker_path = root / "COMPLETE.json"
    cache_files = (root / "vae_cache/manifest.json", root / "vae_cache/COMPLETE.json")
    manifest, sha, token = read_bound_json(
        path, expected_sha256=joint["view_episode_manifest_sha256"]
    )
    marker, _, marker_token = read_bound_json(marker_path)
    states = manifest["states"]
    if (
        marker.get("schema") != manifest.get("schema")
        or marker.get("complete") is not True
        or marker.get("episode_manifest_sha256") != sha
        or marker.get("source_id") != manifest.get("source_id")
        or marker.get("episode_id") != joint["episode_index"]
        or manifest.get("episode_id") != joint["episode_index"]
        or manifest.get("task_class") != joint["task_class"]
        or marker.get("state_count") != len(states)
        or manifest.get("state_count") != len(states)
        or len(states) != len(joint["spatial_states"])
    ):
        raise DataCError("DATA_C spatial profile completion/source differs")
    witnesses = {path: token, marker_path: marker_token}
    witnesses.update((path, file_identity(path)) for path in cache_files)
    index = open_episode_index(root, expected_recipe_id=joint["view_vae_recipe_id"])
    if (
        index.manifest_sha256 != joint["view_vae_manifest_sha256"]
        or index.episode_key
        != f"{joint['task_class']}/episode_{joint['episode_index']:06d}"
        or len(index.manifest["states"]) != len(states)
        or any(file_identity(path) != token for path, token in witnesses.items())
    ):
        raise DataCError("DATA_C View or latent index changed")
    return manifest, index, witnesses


def verify_joint_view_refs(joint, manifest, index):
    """Compare all DATA_C state and selected View references with published indexes."""
    for ordinal, (state, original, cached) in enumerate(
        zip(
            joint["spatial_states"],
            manifest["states"],
            index.manifest["states"],
            strict=True,
        )
    ):
        if (
            state["frame"] != original["frame"]
            or state["frame"] != cached["frame"]
            or state["logical_state_id"] != original["state_id"]
            or state["logical_state_id"] != cached["logical_state_id"]
            or state["scene_graph_file"] != original["scene_graph"]
            or state["spatial_metadata_file"] != original["spatial_metadata"]
            or state["geometry_version"] != original["geometry_version"]
            or not {original["scene_graph"], original["spatial_metadata"]}
            <= manifest["files"].keys()
        ):
            raise DataCError("DATA_C state differs from its Scene Graph/View source")
        refs = _state_views(state)
        if joint["recipe"]["top_variant"] == "both" and (
            {ref["view_id"] for ref in refs} - {TOP_VIEW_IDS["with_robot"]}
            != set(original["selection"]["selected_view_ids"])
        ):
            raise DataCError(
                "DATA_C View selection differs from the published selection"
            )
        for ref in refs:
            entry = index.manifest["views"].get(ref["view_id"])
            record = entry["state_records"][ordinal] if entry else None
            if (
                record is None
                or ref["record_index"] != record
                or ref["record_sha256"] != entry["record_sha256"][record]
                or ref["cache_file"] != entry["path"]
                or ref["cache_file_sha256"] != entry["sha256"]
                or ref["membership_version"]
                != original["selection"]["membership_ids"].get(
                    TOP_VIEW_IDS["without_robot"]
                    if ref["top_variant"]
                    else ref["view_id"]
                )
            ):
                raise DataCError("DATA_C View cache record or membership differs")


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
    complete, _, _ = read_bound_json(epdir / "COMPLETE.json")
    manifest_path = epdir / "episode_manifest.json"
    if complete.get("complete") is not True or not complete.get(
        "episode_manifest_sha256"
    ):
        raise DataCError("G2 view-first episode was not fully published")
    spatial, spatial_sha, _ = read_bound_json(
        manifest_path, expected_sha256=complete["episode_manifest_sha256"]
    )
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
            if canonical_ids.count("sixview/floor_top") != 1 or len(
                canonical_ids
            ) != len(set(canonical_ids)):
                raise DataCError("selected canonical top must be unique")
            ids = [
                "sixview/floor_top_w_rbs"
                if v == "sixview/floor_top" and top_variant == "with_robot"
                else v
                for v in canonical_ids
                if top_variant != "both" or v != "sixview/floor_top"
            ]
            if len(ids) != len(set(ids)) or sum(
                v in {"sixview/floor_top", "sixview/floor_top_w_rbs"} for v in ids
            ) != (0 if top_variant == "both" else 1):
                raise DataCError("selected top view variant count invalid")
            for required in (s["scene_graph"], s["spatial_metadata"]):
                safe_relative(required)
                require_regular(epdir / required)
            metadata, _, _ = read_bound_json(
                epdir / s["spatial_metadata"],
                expected_sha256=spatial["files"][s["spatial_metadata"]],
            )
            with gzip.open(epdir / s["scene_graph"], "rt") as input:
                sg = json.load(input)
            if sg.get("frame_id") != s["frame"] or sg.get("world_frame") != "world":
                raise DataCError("Scene Graph identity/world frame mismatch")
            views = [
                _owner_view(
                    idx,
                    reader,
                    epdir,
                    s,
                    ordinal,
                    v,
                    recipe_id=view_recipe_id,
                    metadata=metadata,
                )
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
                        metadata=metadata,
                    ),
                    "without_robot": _owner_view(
                        idx,
                        reader,
                        epdir,
                        s,
                        ordinal,
                        "sixview/floor_top",
                        recipe_id=view_recipe_id,
                        metadata=metadata,
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
        "view_episode_manifest_sha256": spatial_sha,
        "view_vae_manifest_sha256": idx.manifest_sha256,
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
    target = root / "joint_index.json"
    value, joint_sha = read_joint_episode(
        root,
        task=task,
        episode=ep,
        recipe_id=expected_recipe_id,
        source_binding_digest=raw_source["source_binding_digest"],
        window_count=raw_source["exact_window_count"],
    )
    if (
        value["source_frame_count"] != raw_source["source_frame_count"]
        or value["original_instruction"] != raw_source["instruction"]
        or value["g1_video_cache_manifest_sha256"]
        != raw_source["cache_manifest_sha256"]
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
    return {
        "episode_root": str(root),
        "joint_index": str(target),
        "joint_sha256": joint_sha,
        "state15_sha256": value["data_b_sha256"],
        "recipe_id": value["recipe_id"],
        "frame_count": value["source_frame_count"],
        "window_count": len(value["windows"]),
        "spatial_states": len(value["spatial_states"]),
        "training_ready": False,
    }
