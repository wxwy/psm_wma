"""Native-producer Stage-A packaging, separate from strict legacy compact schemas.

Publishes declared spatial products and seals immutable input independently.
VAE profiles stay SOURCE_READY until the shared A2 consumer/posthoc verifier
finishes every owner and atomically publishes the final profile marker.
"""

from __future__ import annotations

import gzip
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from g2.io import ContractError, digest, read_json, write_json
from g2.latent_cache.contract import contained, fingerprint, safe_relative
from g2.latent_cache.storage import atomic_json, build_lock
from g2.latent_cache.streaming import (
    ConsumerLimits,
    decode_final_png,
    final_pixel_event,
    seal_source,
)
from g2.views.render_connections import renderer_member_sets

from .language_context import LanguageRecipe, TextBank
from .output_profile import PRODUCTS, SCHEMA, SOURCE_SCHEMA, OutputProfile, completion
from .spatial_metadata import (
    asset_identity,
    projection_from_renderer,
    select_views,
    state_metadata,
    validate_raw_pose,
    view_catalog,
)
from .task_entities import RULE_VERSION, bind_task_entities, source_entity_index

RAW_SCHEMA = "g2_stage_a_raw_episode_v1"


def _bound(ref):
    path = Path(ref["path"]).resolve(strict=True)
    if digest(path) != ref["sha256"]:
        raise ContractError("native producer input changed: " + str(path))
    return read_json(path)


def validate_profile_episode(
    root, *, require_complete=True, expected_profile=None, _check_cache=True
):
    root = Path(root).absolute()
    manifest = read_json(contained(root, "episode_manifest.json"))
    from g2.latent_cache import final_source as final

    is_final = manifest.get("schema") == final.PROFILE_SCHEMA
    if manifest.get("schema") not in (SCHEMA, final.PROFILE_SCHEMA):
        raise ContractError("expected new Stage-A profile; no legacy reinterpretation")
    profile = OutputProfile.from_dict(manifest["output_profile"])
    if expected_profile is not None and profile != expected_profile:
        raise ContractError("existing Stage-A profile differs")
    if is_final:
        source, _ = final.validate_profile_header(root, manifest)
    else:
        source = read_json(contained(root, "spatial_source.json"))
        ready = read_json(contained(root, "SPATIAL_SOURCE_READY.json"))
    if not is_final and (
        source.get("schema") != SOURCE_SCHEMA
        or ready.get("source_manifest_sha256") != digest(root / "spatial_source.json")
        or source.get("source_id")
        != fingerprint({k: v for k, v in source.items() if k != "source_id"})
        or ready.get("source_id") != source["source_id"]
        or source["profile_id"] != profile.to_dict()["profile_id"]
        or manifest["source_id"] != source["source_id"]
        or ready.get("complete_spatial_source") is not True
        or ready.get("profile_complete") is not False
        or any(
            source.get(k) != manifest.get(k)
            for k in (
                "episode_id",
                "task_class",
                "source_fingerprint",
                "states",
                "files",
            )
        )
    ):
        raise ContractError("sealed spatial source identity differs")
    from g2.latent_cache.sealed_source import released_inputs

    released = released_inputs(root, source)
    for path, sha in manifest["files"].items():
        candidate = contained(root, path, allow_missing=True)
        if not candidate.exists() and released.get(path) == sha:
            continue
        if digest(candidate) != sha:
            raise ContractError("declared Stage-A artifact damaged: " + path)
    states = manifest["states"]
    if (
        not states
        or [r["state_id"] for r in states] != list(range(len(states)))
        or manifest.get("state_count") != len(states)
        or any(type(s["frame"]) is not int or s["frame"] < 0 for s in states)
        or [s["frame"] for s in states] != sorted({s["frame"] for s in states})
    ):
        raise ContractError("Stage-A state coverage differs")
    expected_status = {
        p: ("pending" if p == "view_vae" else "ready")
        if getattr(profile, p)
        else "disabled"
        for p in PRODUCTS
    }
    for product, prefix in (("sixview_png", "sixview/"), ("island_png", "islands/")):
        if getattr(profile, product) and not any(
            v.startswith(prefix) for v in source["views"]
        ):
            expected_status[product] = "absent"
    vae_receipt = manifest.get("vae_receipt")
    if vae_receipt is not None:
        from g2.latent_cache.production import cache_receipt

        if _check_cache and cache_receipt(root) != vae_receipt:
            raise ContractError("final VAE receipt differs from verified cache")
        expected_status["view_vae"] = "ready"
    decision = completion(
        profile,
        expected_status,
        source_sealed=source["source_id"],
        vae_receipt=vae_receipt,
    )
    if manifest["products"] != expected_status or any(
        manifest.get(k) != v for k, v in decision.items()
    ):
        raise ContractError(
            "declared profile completion/statuses differ from artifacts"
        )

    def artifact(path):
        if not isinstance(path, str) or path not in manifest["files"]:
            raise ContractError("required artifact missing from sealed file inventory")
        return contained(root, path)

    tasks = (
        read_json(artifact("task_entities.json"))["sets"]
        if profile.task_entities
        else {}
    )
    for tid, task in tasks.items():
        if task.get("rule_version") != RULE_VERSION:
            raise ContractError(
                "GT task rule version differs; refuse stale role metadata on resume"
            )
        if (
            task.get("task_entity_set_id") != tid
            or task.get("binding_status") != "BOUND"
            or task.get("task_class") != manifest["task_class"]
            or fingerprint({k: v for k, v in task.items() if k != "task_entity_set_id"})
            != tid
        ):
            raise ContractError("GT task entity set identity differs")
    language = read_json(artifact("language.json")) if profile.language else None
    if language is not None and len(language["states"]) != len(states):
        raise ContractError("language state coverage differs")
    verified_pngs = set()
    for vid, view in source["views"].items():
        if asset_identity(vid + ".png")["view_id"] != vid or not view["owners"]:
            raise ContractError("invalid sealed logical View")
        if len(view["state_records"]) != len(states):
            raise ContractError("sealed View index coverage differs")
        for ordinal, index in enumerate(view["state_records"]):
            if index is None:
                continue
            if type(index) is not int or not 0 <= index < len(view["owners"]):
                raise ContractError("sealed View index out of range")
            owner = view["owners"][index]
            if (
                type(owner["state_id"]) is not int
                or not 0 <= owner["state_id"] <= ordinal
                or owner["frame"] != states[owner["state_id"]]["frame"]
                or type(owner["scene_geometry_source_state"]) is not int
                or not 0 <= owner["scene_geometry_source_state"] <= owner["state_id"]
                or owner["scene_geometry_source_frame"]
                != states[owner["scene_geometry_source_state"]]["frame"]
            ):
                raise ContractError("sealed future View owner")
            if owner.get("path") is not None:
                key = (
                    owner["path"],
                    owner["sha256"],
                    owner["projection"]["width"],
                    owner["projection"]["height"],
                )
                if key not in verified_pngs:
                    candidate = contained(root, owner["path"], allow_missing=True)
                    if (
                        not candidate.exists()
                        and released.get(owner["path"]) == owner["sha256"]
                    ):
                        pass  # Verified immutable numerical owner and original byte hash.
                    else:
                        path = artifact(owner["path"])
                        if digest(path) != owner["sha256"]:
                            raise ContractError("sealed final pixel source changed")
                        decode_final_png(path.read_bytes(), expected_size=key[2:])
                    verified_pngs.add(key)
            elif profile.view_vae or (
                profile.sixview_png
                if vid.startswith("sixview/")
                else profile.island_png
            ):
                raise ContractError(
                    "enabled finalized View has no immutable pixel source"
                )
            projection_from_renderer(owner["projection"])
            event = source["final_pixel_events"].get(owner["event_id"])
            if (
                not event
                or event["view_id"] != vid
                or event["rgb_sha256"] != owner["sha256"]
            ):
                raise ContractError("final pixel event/owner differs")
    for ordinal, state in enumerate(states):
        pngs, refs, islands = [], {}, set()
        for vid, view in source["views"].items():
            index = view["state_records"][ordinal]
            if index is None or not (
                profile.sixview_png
                if vid.startswith("sixview/")
                else profile.island_png
            ):
                continue
            owner = view["owners"][index]
            relative = vid + ".png"
            expected = (
                f"state_{owner['state_id']:06d}_frame_{owner['frame']:06d}/" + relative
            )
            if owner["path"] != expected:
                raise ContractError(
                    "published PNG path differs from direct physical owner"
                )
            if owner["state_id"] == ordinal:
                pngs.append(relative)
            else:
                refs[relative] = dict(ref_state=owner["state_id"], path=relative)
            if vid.startswith("islands/"):
                islands.add(vid.split("/")[1])
        if (
            state.get("view_pngs") != sorted(pngs)
            or state.get("view_refs") != refs
            or state.get("islands") != sorted(islands)
        ):
            raise ContractError(
                "viewer physical/reference index differs from sealed owners"
            )
        task = tasks.get(state["task_entity_set_id"]) if profile.task_entities else None
        if profile.task_entities and task is None:
            raise ContractError("state references missing GT task set")
        graph = None
        if profile.scene_graph:
            with gzip.open(artifact(state.get("scene_graph")), "rt") as stream:
                graph = json.load(stream)
            if graph.get("frame_id") != state["frame"]:
                raise ContractError("SG belongs to another state")
            if task is not None and task[
                "source_instance_part_to_entity_ids"
            ] != source_entity_index(graph):
                raise ContractError(
                    "task source-to-SG mapping differs from current graph"
                )
        if profile.spatial_metadata:
            spatial = read_json(artifact(state.get("spatial_metadata")))
            if (
                spatial.get("state_id") != ordinal
                or spatial.get("frame") != state["frame"]
                or spatial["spatial_metadata_id"]
                != fingerprint(
                    {k: v for k, v in spatial.items() if k != "spatial_metadata_id"}
                )
            ):
                raise ContractError("state spatial metadata identity differs")
            reverse, objects = {}, {}
            for vid, value in spatial["views"].items():
                view = source["views"].get(vid)
                index = view["state_records"][ordinal] if view else None
                if index is None:
                    if (
                        not view
                        or value.get("current_member_plan_present") is not False
                        or value["membership"]["native_entity_ids"]
                        or value["availability"] not in ("absent", "disabled")
                    ):
                        raise ContractError(
                            "spatial View references an absent source owner"
                        )
                    matches = [
                        i
                        for i, owner in enumerate(view["owners"])
                        if {k: v for k, v in owner.items() if k != "projection"}
                        == value["image_owner"]
                    ]
                    if len(matches) != 1 or value["image_owner"]["state_id"] >= ordinal:
                        raise ContractError(
                            "retired Island has no unique historical image owner"
                        )
                    index = matches[0]
                owner = view["owners"][index]
                if value["image_owner"] != {
                    k: v for k, v in owner.items() if k != "projection"
                }:
                    raise ContractError("image owner differs from sealed source")
                if value["image_projection"] != projection_from_renderer(
                    owner["projection"]
                ):
                    raise ContractError("image projection differs from owner geometry")
                membership = value["membership"]
                if value["membership_version"] != fingerprint(membership):
                    raise ContractError("renderer membership version differs")
                for eid in membership["native_entity_ids"]:
                    reverse.setdefault(eid, []).append(vid)
                for eid in membership["object_entity_ids"]:
                    objects.setdefault(eid, []).append(vid)
            if spatial["entity_to_view_ids"] != {
                k: sorted(v) for k, v in reverse.items()
            } or spatial["object_to_view_ids"] != {
                k: sorted(v) for k, v in objects.items()
            }:
                raise ContractError("bidirectional renderer membership differs")
            if profile.selection and state["selection"] != select_views(
                spatial, task, top_variant=profile.selection_top_variant
            ):
                raise ContractError(
                    "selected Views differ from current task/membership union"
                )
        if profile.robot_pose:
            validate_raw_pose(
                state.get("raw_robot_pose"),
                frame=state["frame"],
                world_frame=source["world_frame"],
            )
        if language is not None:
            from .language_context import enhance_caption, split_text_record

            row = language["states"][ordinal]
            text = language["texts"].get(row["text_id"])
            if (
                row["state_id"] != ordinal
                or row["frame"] != state["frame"]
                or not text
                or row["caption_source"]["frame_index"] != state["frame"]
                or row["caption_source"]["episode_index"] != manifest["episode_id"]
            ):
                raise ContractError("language causal index differs")
            recipe = LanguageRecipe(
                **{k: text["recipe"][k] for k in LanguageRecipe.__dataclass_fields__}
            )
            expected_text, context = split_text_record(
                enhance_caption(
                    row["caption_source"]["original_text"], graph, task, recipe
                )
            )
            if text != expected_text or row["fact_context"] != context:
                raise ContractError(
                    "candidate language does not reproduce from current trusted facts"
                )
    complete_path = root / "COMPLETE.json"
    if complete_path.exists():
        complete = read_json(contained(root, "COMPLETE.json"))
        if (
            not manifest["profile_complete"]
            or complete.get("schema") != (final.PROFILE_SCHEMA if is_final else SCHEMA)
            or complete.get("episode_manifest_sha256")
            != digest(root / "episode_manifest.json")
            or complete.get("source_id") != source["source_id"]
            or complete.get("complete") is not True
            or complete.get("episode_id") != manifest["episode_id"]
            or complete.get("state_count") != len(states)
        ):
            raise ContractError("invalid Stage-A completion")
    else:
        repairing = False
        journal = root / "VAE_PROFILE_PUBLISH_PENDING.json"
        if profile.view_vae and manifest["profile_complete"] and journal.exists():
            prepared = read_json(contained(root, journal.name))
            repairing = prepared == dict(
                schema="g2_vae_profile_publish_pending_v1",
                source_id=source["source_id"],
                next_manifest_sha256=digest(root / "episode_manifest.json"),
                cache_receipt=manifest.get("vae_receipt"),
            )
        if require_complete or (manifest["profile_complete"] and not repairing):
            raise ContractError("Stage-A source ready but declared profile incomplete")
    return manifest


def package_stage_a(
    inputs,
    rendered,
    destination,
    *,
    profile,
    episode_id,
    task_class,
    ep_meta,
    source_fingerprint,
    captions=None,
    caption_authority=None,
    language_recipe=None,
    event_sink=None,
    limits=ConsumerLimits(),
    source_guards=None,
):
    """Consume original producer inputs/reports, never repair an old final package."""
    if not isinstance(profile, OutputProfile):
        raise ContractError("explicit typed output profile required")
    if not isinstance(source_fingerprint, str) or not re.fullmatch(
        r"[0-9a-f]{64}", source_fingerprint
    ):
        raise ContractError("bound episode source fingerprint is required")
    inputs = Path(inputs).resolve(strict=True)
    input_sha = digest(inputs)
    config = read_json(inputs)
    guards = {inputs: input_sha}
    guards.update(
        {Path(p).resolve(strict=True): sha for p, sha in (source_guards or {}).items()}
    )
    for row in config["states"]:
        for key in ("snapshot", "scene_graph"):
            if row.get(key):
                path = Path(row[key]["path"]).resolve(strict=True)
                guards[path] = row[key]["sha256"]
    frames = [r["frame"] for r in config["states"]]
    if (
        not frames
        or any(type(frame) is not int or frame < 0 for frame in frames)
        or frames != sorted(set(frames))
    ):
        raise ContractError("causal source frames required")
    destination = Path(destination).absolute()
    rendered = Path(rendered).resolve(strict=True) if rendered is not None else None
    if profile.render_rgb:
        if rendered is None:
            raise ContractError("RGB-dependent profile has no native renderer output")
        receipt = read_json(rendered / "episode_receipt.json")
        guards[rendered / "episode_receipt.json"] = digest(
            rendered / "episode_receipt.json"
        )
        if (
            receipt.get("schema") != RAW_SCHEMA
            or receipt.get("output_profile_id") != profile.to_dict()["profile_id"]
            or receipt.get("complete") is not True
            or receipt.get("source_inputs_sha256") != digest(inputs)
            or [r["frame"] for r in receipt["states"]] != frames
        ):
            raise ContractError("new-profile raw renderer receipt differs from source")
    if profile.language and (captions is None or set(captions) != set(frames)):
        raise ContractError("authoritative current-frame captions required")
    if rendered is not None and (
        destination == rendered
        or rendered in destination.parents
        or destination in rendered.parents
    ):
        raise ContractError("profile destination overlaps renderer source")
    if destination.is_symlink() or any(p.is_symlink() for p in destination.parents):
        raise ContractError("profile destination must not traverse symlinks")
    if any(
        destination == p or destination in p.parents or p in destination.parents
        for p in guards
    ):
        raise ContractError("profile destination overlaps source inputs")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with build_lock(destination.parent / (".stage-a-lock-" + destination.name)):
        if destination.exists() or destination.is_symlink():
            raise ContractError("Stage-A destination exists; never overwrite old data")
        temporary = Path(tempfile.mkdtemp(prefix="._stage_a_", dir=destination.parent))
        files, rows, views, task_sets, events = {}, [], {}, {}, {}
        bank = TextBank()
        spool_bytes = 0
        scene_identity = None

        def save(path, value):
            safe_relative(path)
            (temporary / path).parent.mkdir(parents=True, exist_ok=True)
            write_json(temporary / path, value)
            files[path] = digest(temporary / path)

        try:
            for ordinal, row in enumerate(config["states"]):
                frame = row["frame"]
                snapshot = _bound(row["snapshot"])
                graph = (
                    _bound(row["scene_graph"]) if row.get("scene_graph") else snapshot
                )
                identity = (
                    snapshot["scene_id"],
                    snapshot["source_sha256"],
                    snapshot["world_frame"],
                )
                if scene_identity is not None and identity != scene_identity:
                    raise ContractError(
                        "stable source scene/world frame changed across episode"
                    )
                scene_identity = identity
                if (
                    snapshot["frame_id"] != frame
                    or graph["frame_id"] != frame
                    or graph["scene_id"] != snapshot["scene_id"]
                ):
                    raise ContractError("current graph/snapshot source frame differs")
                # The old SG summary omitted this field. The current native
                # snapshot is its explicit frame authority; never guess "map".
                graph = dict(graph, world_frame=snapshot["world_frame"])
                prefix = f"state_{ordinal:06d}_frame_{frame:06d}"
                source_dir = rendered / prefix if rendered is not None else None
                report = (
                    read_json(source_dir / "direct_color_views.json")
                    if profile.render_rgb
                    else {}
                )
                if profile.render_rgb:
                    guards[source_dir / "direct_color_views.json"] = digest(
                        source_dir / "direct_color_views.json"
                    )
                if profile.render_rgb and report.get("frame_id") != frame:
                    raise ContractError(
                        "renderer report belongs to another source state"
                    )
                assets = report.get("views", [])
                if len({a["rgb_file"] for a in assets}) != len(assets):
                    raise ContractError("duplicate source RGB assets")
                owners = {}
                for entry in views.values():
                    entry["state_records"].append(None)
                materialized = set(
                    report.get(
                        "scene_materialized_views", [a["rgb_file"] for a in assets]
                    )
                )
                refs = report.get("scene_view_refs", {})
                for asset in assets:
                    identity = asset_identity(asset["rgb_file"])
                    vid = identity["view_id"]
                    record = views.setdefault(
                        vid, dict(owners=[], state_records=[None] * (ordinal + 1))
                    )
                    enabled_png = (
                        profile.sixview_png
                        if asset["rgb_file"].startswith("sixview/")
                        else profile.island_png
                    )
                    retained = enabled_png or profile.view_vae
                    if asset["rgb_file"] in materialized:
                        original = contained(source_dir, asset["rgb_file"])
                        if digest(original) != asset["sha256"]:
                            raise ContractError("final material/marker pixels changed")
                        guards[original] = asset["sha256"]
                        native_path = (
                            source_dir
                            / "g2_original_gpu"
                            / safe_relative(asset["native_view"])
                            / "view.json"
                        )
                        meta = read_json(native_path.resolve(strict=True))
                        guards[native_path.resolve(strict=True)] = digest(
                            native_path.resolve(strict=True)
                        )
                        if rendered not in native_path.resolve(strict=True).parents:
                            raise ContractError(
                                "projection reference escapes this source episode"
                            )
                        projection = projection_from_renderer(meta)
                        scene_state = report.get("scene_source_state", ordinal)
                        if (
                            type(scene_state) is not int
                            or not 0 <= scene_state <= ordinal
                        ):
                            raise ContractError(
                                "invalid/future rendered geometry source state"
                            )
                        geometry_source = config["states"][scene_state]
                        marker_identity = (
                            report.get("robot_pose_marker", {}).get("appearance_sha256")
                            if identity["variant"] == "w_rbs"
                            else None
                        )
                        key = fingerprint(
                            dict(
                                rgb=asset["sha256"],
                                projection=projection["projection_id"],
                                marker=marker_identity,
                            )
                        )
                        prior = record["owners"][-1] if record["owners"] else None
                        if prior is not None and prior["content_projection_key"] == key:
                            owner = prior
                        else:
                            location = (
                                prefix + "/" + asset["rgb_file"]
                                if enabled_png
                                else "_spatial_inputs/"
                                + str(ordinal)
                                + "/"
                                + asset["rgb_file"]
                                if retained
                                else None
                            )
                            if location is not None:
                                if not enabled_png:
                                    spool_bytes += original.stat().st_size
                                    if spool_bytes > limits.max_spool_bytes:
                                        raise ContractError(
                                            "source spool budget exceeded; A2 consumer/backpressure required"
                                        )
                                target = temporary / location
                                target.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copyfile(original, target)
                                files[location] = digest(target)
                            event = final_pixel_event(
                                original,
                                episode_key=f"{task_class}/episode_{episode_id:06d}",
                                view_id=vid,
                                canonical_view_id=identity["canonical_view_id"],
                                variant=identity["variant"],
                                source_fingerprint=source_fingerprint,
                                profile_id=profile.to_dict()["profile_id"],
                                expected_size=(
                                    projection["width_px"],
                                    projection["height_px"],
                                ),
                            )
                            owner = dict(
                                state_id=ordinal,
                                frame=frame,
                                path=location,
                                sha256=asset["sha256"],
                                projection=meta,
                                content_projection_key=key,
                                event_id=event.event_id,
                                scene_geometry_source_state=scene_state,
                                scene_geometry_source_frame=geometry_source["frame"],
                                scene_geometry_snapshot_sha256=geometry_source[
                                    "snapshot"
                                ]["sha256"],
                                native_projection_sha256=digest(
                                    native_path.resolve(strict=True)
                                ),
                                marker_drawn=asset.get("marker_drawn", False),
                            )
                            record["owners"].append(owner)
                            events[event.event_id] = event.descriptor()
                            if profile.view_vae and event_sink is not None:
                                event_sink(
                                    event
                                )  # Failure/backpressure propagates; never forges completion.
                    else:
                        ref = refs.get(asset["rgb_file"])
                        if (
                            not isinstance(ref, dict)
                            or ref.get("path") != asset["rgb_file"]
                            or type(ref.get("ref_state")) is not int
                            or not 0 <= ref["ref_state"] < ordinal
                        ):
                            raise ContractError(
                                "missing or future source asset reference"
                            )
                        index = record["state_records"][ref["ref_state"]]
                        if index is None:
                            raise ContractError(
                                "source reference points to absent View"
                            )
                        owner = record["owners"][index]
                        if asset["sha256"] != owner["sha256"]:
                            raise ContractError(
                                "reference content does not match final image owner"
                            )
                    owners[vid] = owner
                    record["state_records"][ordinal] = record["owners"].index(owner)
                members = (
                    renderer_member_sets(snapshot) if profile.spatial_metadata else {}
                )
                spatial = (
                    state_metadata(
                        snapshot, assets, members, state_id=ordinal, owner_rows=owners
                    )
                    if profile.spatial_metadata
                    else None
                )
                if spatial is not None:
                    for vid, value in spatial["views"].items():
                        if not value["current_member_plan_present"]:
                            views[vid]["state_records"][ordinal] = None
                        kind = (
                            profile.sixview_png
                            if vid.startswith("sixview/")
                            else profile.island_png
                        )
                        if not kind and not profile.view_vae:
                            value["availability"] = "disabled"
                        value["marker_drawn"] = owners[vid]["marker_drawn"]
                    spatial["view_catalog"] = view_catalog(
                        snapshot,
                        members,
                        spatial,
                        profile,
                        report.get("renderer_view_catalog", {}),
                    )
                    spatial["spatial_metadata_id"] = fingerprint(
                        {k: v for k, v in spatial.items() if k != "spatial_metadata_id"}
                    )
                    save(prefix + "/spatial_metadata.json", spatial)
                task = (
                    bind_task_entities(task_class, ep_meta, graph)
                    if profile.task_entities
                    else None
                )
                if task is not None:
                    if task["binding_status"] != "BOUND":
                        save("TASK_BINDING_FAILED.json", task)
                        raise ContractError("GT initialization task binding unresolved")
                    task_sets[task["task_entity_set_id"]] = task
                state_row = dict(
                    state_id=ordinal,
                    frame=frame,
                    geometry_version=spatial["geometry_version"] if spatial else None,
                    task_entity_set_id=task["task_entity_set_id"] if task else None,
                    spatial_metadata=prefix + "/spatial_metadata.json"
                    if spatial
                    else None,
                )
                state_row.update(view_pngs=[], view_refs={}, islands=[])
                for vid, owner in owners.items():
                    if views[vid]["state_records"][ordinal] is None:
                        continue
                    png_enabled = (
                        profile.sixview_png
                        if vid.startswith("sixview/")
                        else profile.island_png
                    )
                    if not png_enabled:
                        continue
                    relative = vid + ".png"
                    if owner["state_id"] == ordinal:
                        state_row["view_pngs"].append(relative)
                    else:
                        state_row["view_refs"][relative] = dict(
                            ref_state=owner["state_id"], path=relative
                        )
                    if vid.startswith("islands/"):
                        state_row["islands"].append(vid.split("/")[1])
                state_row["view_pngs"].sort()
                state_row["islands"] = sorted(set(state_row["islands"]))
                if profile.scene_graph:
                    path = prefix + "/scene_graph.json.gz"
                    (temporary / prefix).mkdir(exist_ok=True)
                    with gzip.open(temporary / path, "wb", compresslevel=3) as stream:
                        stream.write(
                            (
                                json.dumps(graph, sort_keys=True, allow_nan=False)
                                + "\n"
                            ).encode()
                        )
                    files[path] = digest(temporary / path)
                    state_row["scene_graph"] = path
                if profile.selection:
                    state_row["selection"] = select_views(
                        spatial, task, top_variant=profile.selection_top_variant
                    )
                if profile.robot_pose:
                    pose = report.get("raw_robot_pose", row.get("raw_robot_pose"))
                    validate_raw_pose(
                        pose, frame=frame, world_frame=snapshot["world_frame"]
                    )
                    state_row["raw_robot_pose"] = pose
                if profile.language:
                    bank.add(
                        ordinal,
                        frame,
                        captions[frame],
                        graph,
                        task,
                        language_recipe or LanguageRecipe(),
                    )
                rows.append(state_row)
            if profile.task_entities:
                save(
                    "task_entities.json",
                    dict(schema="g2_episode_task_entities_v1", sets=task_sets),
                )
            if profile.language:
                save(
                    "language.json",
                    dict(
                        schema="g2_episode_text_bank_v1",
                        texts=bank.texts,
                        states=bank.states,
                        caption_authority=caption_authority,
                    ),
                )
            if any(digest(path) != sha for path, sha in guards.items()):
                raise ContractError(
                    "original producer inputs changed during publication"
                )
            source_id = seal_source(
                temporary,
                dict(
                    schema=SOURCE_SCHEMA,
                    episode_id=episode_id,
                    task_class=task_class,
                    source_fingerprint=source_fingerprint,
                    source_inputs_sha256=digest(inputs),
                    world_frame=snapshot["world_frame"],
                    profile_id=profile.to_dict()["profile_id"],
                    states=rows,
                    views=views,
                    files=dict(files),
                    final_pixel_events=events,
                    vae_adapter_status="SHARED_ENCODE1_SEALED_SOURCE_V1",
                ),
            )
            statuses = {
                p: ("pending" if p == "view_vae" else "ready")
                if getattr(profile, p)
                else "disabled"
                for p in PRODUCTS
            }
            if profile.island_png and not any(v.startswith("islands/") for v in views):
                statuses["island_png"] = "absent"
            if profile.sixview_png and not any(v.startswith("sixview/") for v in views):
                statuses["sixview_png"] = "absent"
            decision = completion(profile, statuses, source_sealed=source_id)
            manifest = dict(
                schema=SCHEMA,
                episode_id=episode_id,
                task_class=task_class,
                source_fingerprint=source_fingerprint,
                source_id=source_id,
                output_profile=profile.to_dict(),
                states=rows,
                state_count=len(rows),
                files=files,
                products=statuses,
                **decision,
            )
            atomic_json(temporary / "episode_manifest.json", manifest)
            if decision["profile_complete"]:
                atomic_json(
                    temporary / "COMPLETE.json",
                    dict(
                        schema=SCHEMA,
                        episode_id=episode_id,
                        state_count=len(rows),
                        source_id=source_id,
                        episode_manifest_sha256=digest(
                            temporary / "episode_manifest.json"
                        ),
                        complete=True,
                    ),
                )
            validate_profile_episode(
                temporary, require_complete=False, expected_profile=profile
            )
            os.rename(temporary, destination)
            return manifest
        except BaseException as exc:
            # Preserve source inputs and any partial diagnostics. No final COMPLETE.
            (temporary / "COMPLETE.json").unlink(missing_ok=True)
            atomic_json(
                temporary / "FAILED.json",
                dict(
                    schema=SCHEMA,
                    profile_complete=False,
                    error_type=type(exc).__name__,
                    error=str(exc),
                    source_inputs_sha256=input_sha,
                ),
            )
            raise
