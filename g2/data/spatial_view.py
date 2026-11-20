"""Convert renderer geometry and preprocessing receipts to the shared Reader ABI."""

from __future__ import annotations

from cosmos_framework.model.generator.mot.g2_contracts import (
    RasterMapping,
    SpatialProjection,
)
from cosmos_framework.model.generator.mot.global_spatial import (
    patch_layout,
    projection_vector,
)


def reader_projection(world_frame, image_projection):
    proj = image_projection
    basis = proj["reference_frame"]
    projection = SpatialProjection(
        projection_id=proj["projection_id"],
        world_frame=world_frame,
        origin_world=tuple(map(float, basis["origin_world"])),
        axes_world=tuple(tuple(map(float, x)) for x in basis["axes_world"]),
        right_world=tuple(map(float, proj["right_world"])),
        up_world=tuple(map(float, proj["up_world"])),
        forward_world=tuple(map(float, proj["forward_world"])),
        uv_min_room=tuple(map(float, proj["uv_min_room"])),
        width_px=proj["width_px"],
        height_px=proj["height_px"],
        meters_per_pixel=proj["meters_per_pixel"],
        physical_width_m=proj["physical_width_m"],
        physical_height_m=proj["physical_height_m"],
        rows_flipped=proj["rows_flipped"],
        pixel_center_offset=proj["pixel_center_offset"],
    )
    projection_vector(projection)
    return projection


def reader_raster(preprocessing, projection, grid_hw):
    raster = RasterMapping(
        original_hw=tuple(preprocessing["original_hw"]),
        resized_hw=tuple(preprocessing["resized_hw"]),
        canvas_hw=tuple(preprocessing["canvas_hw"]),
        content_box=tuple(preprocessing["content_box"]),
    )
    _, mask = patch_layout(raster, grid_hw, rows_flipped=projection.rows_flipped)
    return raster, mask
