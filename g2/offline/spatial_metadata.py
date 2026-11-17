"""Source-native projections and independently versioned renderer memberships."""

from __future__ import annotations

import re

import numpy as np

from g2.io import ContractError
from g2.latent_cache.contract import fingerprint, safe_relative


def asset_identity(path):
    p = safe_relative(path, ".png")
    if not re.fullmatch(
        r"(sixview/(rooms/[0-9]+/)?(floor_top(_w_rbs)?|upper_up|plus_X|minus_X|plus_Y|minus_Y)|islands/island_[0-9]+_entity_[0-9]+/(plus_X|minus_X|plus_Y|minus_Y))\.png",
        str(p),
    ):
        raise ContractError("unsupported full logical spatial path")
    if p.parts[0] not in ("sixview", "islands"):
        raise ContractError("unsupported spatial asset namespace")
    if p.stem not in {
        "floor_top",
        "floor_top_w_rbs",
        "upper_up",
        "plus_X",
        "minus_X",
        "plus_Y",
        "minus_Y",
    }:
        raise ContractError("unknown canonical spatial direction")
    if p.parts[0] == "islands" and p.stem in {
        "floor_top",
        "floor_top_w_rbs",
        "upper_up",
    }:
        raise ContractError("Island views have four horizontal directions only")
    marked = p.stem == "floor_top_w_rbs"
    if p.stem.endswith("_w_rbs") and not marked:
        raise ContractError("marker suffix only applies once to floor_top")
    canonical = p.with_name("floor_top.png") if marked else p
    return dict(
        view_id=str(p.with_suffix("")),
        canonical_view_id=str(canonical.with_suffix("")),
        variant="w_rbs" if marked else "clean",
        is_floor_top=canonical.stem == "floor_top",
    )


def projection_from_renderer(meta):
    required = {
        "axis",
        "reference_frame",
        "right_world",
        "up_world",
        "forward_world",
        "uv_min_room",
        "width",
        "height",
        "meters_per_pixel",
        "native_entity_ids",
    }
    if (
        not required <= set(meta)
        or meta.get("coordinate_frame") != "NATIVE_ROOM_REFERENCE"
    ):
        raise ContractError("native renderer projection evidence is incomplete")
    width, height, mpp = meta["width"], meta["height"], meta["meters_per_pixel"]
    if (
        type(width) is not int
        or type(height) is not int
        or min(width, height) < 1
        or type(mpp) not in (int, float)
        or not 0 < mpp < 1
    ):
        raise ContractError("invalid source projection dimensions")
    frame = meta["reference_frame"]
    axes = np.asarray(frame["axes_world"], float)
    origin = np.asarray(frame["origin_world"], float)
    basis = np.asarray(
        [meta[k] for k in ("right_world", "up_world", "forward_world")], float
    )
    uv = np.asarray(meta["uv_min_room"], float)
    if (
        axes.shape != (3, 3)
        or basis.shape != (3, 3)
        or origin.shape != (3,)
        or uv.shape != (2,)
        or not np.isfinite(
            np.concatenate([axes.ravel(), basis.ravel(), origin, uv])
        ).all()
        or not np.allclose(axes @ axes.T, np.eye(3), atol=1e-6)
        or not np.allclose(basis @ basis.T, np.eye(3), atol=1e-6)
    ):
        raise ContractError("invalid native projection frame/basis")
    result = dict(
        kind="ORTHOGRAPHIC_RAYS_NOT_UNIQUE_XYZ",
        units="m",
        axis=meta["axis"],
        reference_frame=frame,
        right_world=meta["right_world"],
        up_world=meta["up_world"],
        forward_world=meta["forward_world"],
        uv_min_room=meta["uv_min_room"],
        width_px=width,
        height_px=height,
        meters_per_pixel=float(mpp),
        physical_width_m=width * mpp,
        physical_height_m=height * mpp,
        pixel_center_span_m=[(width - 1) * mpp, (height - 1) * mpp],
        pixel_center_offset=0.5,
        rows_flipped=True,
        pixel_to_uv="u=uv_min[0]+(col+0.5)*mpp; v=uv_min[1]+(H-row-0.5)*mpp",
        room_bounds_min=meta.get("room_bounds_min"),
        room_bounds_max=meta.get("room_bounds_max"),
        depth_kind=meta.get("depth_kind"),
        crop="EXACT_RENDERER_FRAME_NO_VAE_PADDING",
    )
    result["projection_id"] = fingerprint(result)
    return result


def validate_raw_pose(pose, *, frame, world_frame):
    """Keep chassis xyz/+X without Stage-B normalization or yaw conversion."""
    if (
        not isinstance(pose, dict)
        or pose.get("source_frame") != frame
        or pose.get("frame") != frame
        or pose.get("coordinate_frame") != world_frame
        or not isinstance(pose.get("source_body"), str)
        or not pose["source_body"]
        or pose.get("forward_axis") != "body_local_positive_X"
    ):
        raise ContractError("actual current raw chassis pose provenance is missing")
    position = np.asarray(pose.get("position_world"), float)
    forward = np.asarray(pose.get("forward_world"), float)
    if (
        position.shape != (3,)
        or forward.shape != (3,)
        or not np.isfinite(position).all()
        or not np.isfinite(forward).all()
        or not np.isclose(np.linalg.norm(forward), 1.0, atol=1e-6)
        or np.linalg.norm(forward[:2]) < 1e-8
    ):
        raise ContractError("raw chassis xyz/forward is invalid")
    return pose


def state_metadata(snapshot, assets, member_plan, *, state_id, owner_rows):
    """asset's image-owner projection and current membership have separate IDs."""
    entities = {e["id"]: e for e in snapshot["entities"]}
    geometry = {
        key: snapshot[key]
        for key in ("scene_id", "source_sha256", "frame_id", "entities", "rooms")
    }
    geometry_id = fingerprint(geometry)
    views, reverse, object_reverse = {}, {}, {}
    for asset in assets:
        identity = asset_identity(asset["rgb_file"])
        vid = identity["view_id"]
        if vid in views:
            raise ContractError("duplicate logical spatial asset")
        native = asset["native_view"]
        if native not in member_plan:
            raise ContractError(
                "asset no longer has a current native renderer membership plan"
            )
        members = sorted(set(member_plan[native]["native_entity_ids"]))
        if set(members) - set(entities):
            raise ContractError("renderer member is not in current SG")
        owner = owner_rows[vid]
        if owner["state_id"] > state_id or owner["frame"] > snapshot["frame_id"]:
            raise ContractError("future image owner")
        projection = projection_from_renderer(owner["projection"])
        membership = dict(
            native_entity_ids=members,
            object_entity_ids=[k for k in members if entities[k]["kind"] == "object"],
            source="ACTUAL_RENDERER_MEMBER_PLAN_NOT_PIXEL_VISIBILITY",
        )
        views[vid] = dict(
            **identity,
            native_view=native,
            room_uid=member_plan[native]["room_uid"],
            island_id=member_plan[native]["island_id"],
            availability="reference" if owner["state_id"] < state_id else "ready",
            image_owner={k: v for k, v in owner.items() if k != "projection"},
            image_projection=projection,
            geometry_version=geometry_id,
            membership=membership,
            membership_version=fingerprint(membership),
            marker_drawn=asset.get("marker_drawn", False),
            marker_enabled=identity["variant"] == "w_rbs",
        )
        for eid in members:
            reverse.setdefault(eid, []).append(vid)
        for eid in membership["object_entity_ids"]:
            object_reverse.setdefault(eid, []).append(vid)
    result = dict(
        schema="g2_state_spatial_metadata_v1",
        state_id=state_id,
        frame=snapshot["frame_id"],
        scene_id=snapshot["scene_id"],
        world_frame=snapshot["world_frame"],
        geometry_provenance={
            key: snapshot.get(key)
            for key in (
                "source_mode",
                "geometry_source_mode",
                "structure_mode",
                "object_frontend_status",
                "source_sha256",
                "native_build_source_sha256",
            )
        },
        geometry_version=geometry_id,
        views=views,
        entity_to_view_ids={k: sorted(v) for k, v in sorted(reverse.items())},
        object_to_view_ids={k: sorted(v) for k, v in sorted(object_reverse.items())},
        unavailable_geometry="NOT_INFERRED_FROM_RGB",
    )
    result["spatial_metadata_id"] = fingerprint(result)
    return result


def select_views(metadata, task_set, *, top_variant):
    if top_variant not in ("clean", "w_rbs", "both"):
        raise ContractError("an explicit top-variant selection is required")
    if task_set["binding_status"] != "BOUND":
        raise ContractError(
            "unresolved task identities cannot silently select fallback views"
        )
    valid = {
        key: value
        for key, value in metadata["views"].items()
        if value["availability"] in ("ready", "reference")
    }
    mandatory = {
        vid
        for vid, v in valid.items()
        if v["is_floor_top"] and (top_variant == "both" or v["variant"] == top_variant)
    }
    if not mandatory:
        raise ContractError("mandatory selected top information unavailable")
    selected = set(mandatory)
    for eid in task_set["entity_ids"]:
        for vid in metadata["entity_to_view_ids"].get(eid, []):
            if vid not in valid:
                continue
            view = valid[vid]
            if (
                not view["is_floor_top"]
                or top_variant == "both"
                or view["variant"] == top_variant
            ):
                selected.add(vid)
    return dict(
        schema="g2_selected_views_v1",
        selected_view_ids=sorted(selected),
        mandatory_view_ids=sorted(mandatory),
        top_variant=top_variant,
        reasons={
            vid: dict(
                mandatory_top=vid in mandatory,
                task_entity_ids=sorted(
                    set(task_set["entity_ids"])
                    & set(valid[vid]["membership"]["native_entity_ids"])
                ),
            )
            for vid in sorted(selected)
        },
        selection_is_training_default=False,
        unassociated_task_entity_ids=sorted(
            eid
            for eid in task_set["entity_ids"]
            if not any(
                vid in selected for vid in metadata["entity_to_view_ids"].get(eid, [])
            )
        ),
        membership_ids={v: valid[v]["membership_version"] for v in sorted(selected)},
    )


def canonical_direction_count(paths):
    return len({asset_identity(str(p))["canonical_view_id"] for p in paths})


def view_catalog(snapshot, member_plan, spatial, profile, renderer_catalog):
    """Explicit disabled/absent directions; absence never fabricates RGB payloads."""
    multiple = len(snapshot["rooms"]) > 1
    result = {}
    for native, plan in sorted(member_plan.items()):
        parts = native.split("/")
        if plan["island_id"] is not None:
            vid = "islands/" + plan["island_id"] + "/" + parts[-1]
            enabled = profile.island_png or profile.view_vae
        else:
            vid = (
                "sixview/rooms/" + str(plan["room_uid"]) + "/"
                if multiple
                else "sixview/"
            ) + parts[-1]
            enabled = profile.sixview_png or profile.view_vae
        variants = [vid]
        if parts[-1] == "floor_top":
            variants.append(vid + "_w_rbs")
        for key in variants:
            marker_disabled = key.endswith("_w_rbs") and not profile.marker_variants
            existing = spatial["views"].get(key)
            raw = renderer_catalog.get(native)
            result[key] = dict(
                native_view=native,
                room_uid=plan["room_uid"],
                island_id=plan["island_id"],
                native_entity_ids=plan["native_entity_ids"],
                availability=(
                    "disabled"
                    if marker_disabled or not enabled
                    else existing["availability"]
                    if existing
                    else "absent"
                ),
                reason=(
                    "MARKER_VARIANT_DISABLED"
                    if marker_disabled
                    else "PRODUCT_DISABLED"
                    if not enabled
                    else None
                    if existing
                    else (raw or {}).get("reason", "NO_PNG_IN_RENDERED_SCENE_KEYFRAME")
                ),
                renderer_image_generated=raw.get("image_generated")
                if raw is not None
                else None,
                image_owner_state=existing["image_owner"]["state_id"]
                if existing
                else None,
            )
    return result
