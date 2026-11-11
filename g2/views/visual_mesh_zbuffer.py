"""Full Map G2 source Visual-Mesh geometry + native 10mm visual color.

Unlike the legacy ColorCloudMap -> Collision Mesh projection, this renderer
makes both occlusion and owner from SOURCE VISUAL GEOM MESH (MuJoCo GT), and
accepts only source 10mm color surfels consistent with that visual depth.

Opaque source is strictly separated from translucent source, which must render
as an independent alpha layer. No change to nav_sg collision map or SG.

Material/geom identity source is signed by the source manifest; the fused
native 10mm RGB frame doesn't carry per-geom IDs, so sub-geom color remains
unverified at shared-owner seams. NO TRAINING ACCEPTANCE.
"""

import numpy as np

from g2.io import ContractError
from g2.views.render import AXES


def compile_visual_geom_frame(
    model, data, specs, room, native_ids, *, block_unbound=True
):
    """Preserve each compiled source visual geom as distinct Z-buffer entity."""
    from g2.sim.source_geometry import effective_rgba

    axes = np.asarray(room["reference_frame"]["axes_world"], dtype=np.float64)
    center = np.asarray(room["reference_frame"]["origin_world"], dtype=np.float64)
    if axes.shape != (3, 3) or center.shape != (3,) or not np.isfinite(axes).all():
        raise ContractError("visual source room frame invalid")
    opaque = []
    translucent = []
    attributes = {}
    unbound = []
    for j, s in enumerate(specs):
        native = s["owner"]
        if native < 0:
            unbound.append(s["name"])
            if block_unbound:
                continue
        elif native >= len(native_ids):
            raise ContractError("visual source geom owner exceeds native IDs")
        g = s["g"]
        rgba = np.asarray(effective_rgba(model, g), dtype=np.float64)
        if rgba.shape != (4,) or not np.isfinite(rgba).all():
            raise ContractError("invalid compiled MuJoCo source material")
        world = (
            np.asarray(s["vertices"], dtype=np.float64)
            @ np.asarray(data.geom_xmat[g]).reshape(3, 3).T
            + data.geom_xpos[g]
        )
        local = (world - center) @ axes.T
        record = (j, local, s["faces"])
        attributes[j] = {
            "owner": native,
            "native_id": native_ids[native] if native >= 0 else None,
            "geom_id": g,
            "geom_name": s["name"],
            "alpha": float(rgba[3]),
            "source_valid_color_sample_count": s["original_valid_samples"],
            "source_all_color_sample_count": s["original_dense_samples"],
            "material_opaque": bool(rgba[3] >= 1 - 1.0e-7),
        }
        if rgba[3] >= 1 - 1.0e-7:
            opaque.append(record)
        else:
            translucent.append(record)
    return {
        "opaque": opaque,
        "translucent": translucent,
        "attributes": attributes,
        "source_unbound_visual_geom_names": unbound,
        "source_visual_schema": "SIGNED_MUJOCO_GT_VISUAL_GEOMETRY_PER_GEOM_V1",
        "visual_geom_count": len(specs),
        "room_uid": room["uid"],
        "native_owner_ids": list(native_ids),
        "training_ready": False,
    }


def view_source_zbuffer(
    data,
    points,
    rgb,
    color_valid,
    source_owner,
    selected_native_ids,
    bounds_min,
    bounds_max,
    axis,
    *,
    meters_per_pixel=0.01,
    backend="gpu",
):
    """Project actual source visual mesh first, then source-bound RGB pixels."""
    if backend != "gpu":
        raise ContractError(
            "visual source GPU z-buffer required until CPU oracle exists"
        )
    if axis not in AXES or meters_per_pixel != 0.01:
        raise ContractError("invalid source view axis/resolution")
    if (
        data.get("source_visual_schema")
        != "SIGNED_MUJOCO_GT_VISUAL_GEOMETRY_PER_GEOM_V1"
    ):
        raise ContractError("missing exact compiled visual source proof")
    from g2.views.exact_compute import get_engine
    from g2.views.gpu_color_select import get_projector

    selected = set(selected_native_ids)
    specids = {
        idx
        for idx, row in data["attributes"].items()
        if row["owner"] in selected and row["owner"] >= 0 and row["material_opaque"]
    }
    meshes = [e for e in data["opaque"] if e[0] in specids]
    lo = np.asarray(bounds_min, dtype=np.float64)
    hi = np.asarray(bounds_max, dtype=np.float64)
    if not meshes:
        # Direction may be deliberately EMPTY (e.g. no upper objects).
        # Geometry and color must remain empty, never inferred from floors.
        right0, up0, _ = (np.asarray(x, float) for x in AXES[axis])
        corners0 = np.asarray(
            [
                [x, y, z]
                for x in (lo[0], hi[0])
                for y in (lo[1], hi[1])
                for z in (lo[2], hi[2])
            ]
        )
        uv0 = corners0 @ np.stack([right0, up0], axis=1)
        uvmin0 = np.floor(uv0.min(axis=0) / meters_per_pixel) * meters_per_pixel
        dims = (
            np.floor((uv0.max(axis=0) - uvmin0) / meters_per_pixel + 1e-8).astype(int)
            + 1
        )
        width, height = map(int, dims)
        if width < 1 or height < 1 or width * height > 4_000_000:
            raise ContractError("empty source visual View exceeds pixel budget")
        visual = np.zeros((height, width), dtype=bool)
        depth = np.full((height, width), np.nan, dtype=float)
        spec_owner = np.full((height, width), -2, dtype=np.int32)
        size = (width, height)
        ginfo = {"triangles": 0, "empty_direction": True}
    else:
        visual, depth, spec_owner, size, ginfo = get_engine().draw(
            meshes, specids, lo, hi, axis, meters_per_pixel
        )
        width, height = size
    native_owner = np.full((height, width), -2, dtype=np.int32)
    material_valid = np.zeros((height, width), dtype=bool)
    for sid in specids:
        a = data["attributes"][sid]
        m = visual & (spec_owner == sid)
        if not m.any():
            continue
        native_owner[m] = a["owner"]
        if a["source_valid_color_sample_count"] > 0:
            material_valid[m] = True
    # Nearest SOURCE RGB per pixel is an independent pipeline. No mesh-driven
    # interpolation, no collision-based fallback, no colors for missing layers.
    xyz = np.asarray(points, dtype=np.float64)
    rgb = np.asarray(rgb)
    color_valid = np.asarray(color_valid)
    owner = np.asarray(source_owner, dtype=np.int32)
    if (
        xyz.ndim != 2
        or xyz.shape[1] != 3
        or not np.isfinite(xyz).all()
        or rgb.shape != (len(xyz), 3)
        or color_valid.shape != (len(xyz),)
        or owner.shape != (len(xyz),)
        or not len(xyz)
    ):
        raise ContractError("invalid source surfel input")
    right, up, forward = (np.asarray(x, float) for x in AXES[axis])
    corners = np.asarray(
        [
            [x, y, z]
            for x in (lo[0], hi[0])
            for y in (lo[1], hi[1])
            for z in (lo[2], hi[2])
        ]
    )
    uv = corners @ np.stack([right, up], axis=1)
    uvorigin = np.floor(uv.min(axis=0) / meters_per_pixel) * meters_per_pixel
    if not specids:
        # Empty directions should not upload/render millions of color voxels.
        pix = np.empty(0, dtype=np.int64)
        rr = np.empty(0, dtype=np.int64)
        cc = np.empty(0, dtype=np.int64)
        z = np.empty(0, dtype=np.float64)
        info = {"gpu_selected_pixels": 0, "empty_source_direction": True}
    else:
        pix, rr, cc, z, info = get_projector().select(
            xyz,
            rgb,
            color_valid,
            owner,
            selected,
            lo,
            hi,
            right,
            up,
            forward,
            uvorigin,
            meters_per_pixel,
            width,
            height,
        )
    # Color must be same SOURCE native object, on a source visual mesh with at
    # least one proven color sample, and within native voxel quantization.
    depth_diff = np.abs(z - depth[rr, cc])
    strict = (
        visual[rr, cc]
        & material_valid[rr, cc]
        & (owner[pix] == native_owner[rr, cc])
        & color_valid[pix]
        & (depth_diff <= 0.0100001)
    )
    color = np.zeros((height, width, 3), dtype=np.uint8)
    observed = np.zeros((height, width), dtype=bool)
    keep_rr, keep_cc = rr[strict], cc[strict]
    observed[keep_rr, keep_cc] = True
    color[keep_rr, keep_cc] = rgb[pix[strict]]
    geo_mismatch = int((~strict & visual[rr, cc]).sum())
    meta = dict(
        source_visual_geometry="MUJOCO_GT_VISUAL_GEOM_ZBUFFER_OPAQUE_ONLY",
        source_visual_surface_color="NATIVE_10MM_COLOR_MAP_SAME_OWNER_NEAREST_PIXEL",
        source_collision_geometry_used_for_zbuffer=False,
        source_visual_per_geom_occlusion=True,
        source_visual_geom_count=len(specids),
        source_materials_unsupported_transparency=len(data["translucent"]),
        source_unbound_visual_geoms_excluded=len(
            data["source_unbound_visual_geom_names"]
        ),
        source_surfel_depth_tolerance_m=0.0100001,
        source_subgeom_rgb_identity_proof=False,
        source_material_color_coverage_independently_proven=False,
        source_transparency_composited=False,
        visual_mesh_geometry_pixels=int(visual.sum()),
        visual_mesh_color_valid_pixels=int(observed.sum()),
        visual_mesh_color_invalid_pixels=int((visual & ~observed).sum()),
        matched_source_color_voxel_pixels=int(len(pix)),
        eligible_source_projected_color_pixels=int(strict.sum()),
        source_color_rejected_visible_pixels=geo_mismatch,
        source_zbuffer_gpu_info=ginfo,
        source_surfel_gpu_info=info,
        # Standard G2 view.json geometry metadata contract for all callers.
        axis=axis,
        right_world=right.tolist(),
        up_world=up.tolist(),
        forward_world=forward.tolist(),
        uv_min_world=uvorigin.tolist(),
        world_bounds_min=lo.tolist(),
        world_bounds_max=hi.tolist(),
        width=width,
        height=height,
        meters_per_pixel=meters_per_pixel,
        pixel_centers="uv_min+(column+0.5,bottom_row+0.5)*mpp",
        depth_kind="signed_world_dot_forward",
        color_depth_tolerance_m=0.0100001,
        color_support="SOURCE_MUJOCO_NATIVE_10MM_VISUAL_SURFELS",
        training_ready=False,
    )
    return color, observed, visual, depth, native_owner, spec_owner, meta
