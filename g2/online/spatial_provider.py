"""Bind the current Actor's F27 publication to the native R2 Reader."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from pathlib import Path

from cosmos_framework.inference.g2_policy_conditions import (
    OnlineSpatialSnapshot,
    mask_content_identity,
)
from cosmos_framework.model.generator.mot.g2_contracts import SpatialView, ViewIdentity
from cosmos_framework.model.generator.mot.global_spatial import patch_layout

from g2.data.episode_state import file_identity, read_bound_bytes, read_bound_json
from g2.data.spatial_view import reader_projection, reader_raster
from g2.io import ContractError, sha
from g2.latent_cache.contract import contained, fingerprint, safe_relative
from g2.latent_cache.encoding import preprocess_rgb
from g2.offline.spatial_metadata import asset_identity, select_views

from .spatial_source import LIVE_VIEWS, PERIOD_FRAMES, task_binding_identity
from .view_encoder import MAX_PNG_BYTES, OnlineViewEncoder, decode_rgb, read_view_recipe


def create_live_provider(
    *, scratch_root, recipe_path, recipe_id, weights, timeout_s, max_views
):
    scratch_root = Path(scratch_root).resolve(strict=True)
    recipe = read_view_recipe(recipe_path, recipe_id)
    encoder = OnlineViewEncoder(
        weights=weights,
        recipe_path=recipe_path,
        recipe_id=recipe_id,
        timeout_s=timeout_s,
    )
    return LiveSpatialProvider(scratch_root, recipe, encoder, max_views=max_views)


class LiveSpatialProvider:
    def __init__(self, scratch_root, recipe, encoder, *, max_views):
        self.root = Path(scratch_root).resolve(strict=True)
        self.recipe = recipe
        self.encoder = encoder
        self.max_views = max_views
        # Cache only the small raster receipt. The Session cache owns latents.
        self._preprocessing = lru_cache(maxsize=256)(self._preprocess)

    @staticmethod
    def _png(path, png_sha):
        raw, _, _ = read_bound_bytes(path, limit=MAX_PNG_BYTES, expected_sha256=png_sha)
        return raw

    def _preprocess(self, path, png_sha, _generation):
        rgb = decode_rgb(self._png(path, png_sha))
        return preprocess_rgb(rgb, self.recipe["preprocessing"])[1]

    def snapshot(self, identity, base, *, spatial_source=None, static_text=None):
        if spatial_source is None or static_text is None:
            raise ContractError(
                "native R2 requires the Actor's current spatial publication"
            )
        rel = safe_relative(spatial_source["path"], ".json")
        if (
            len(rel.parts) != 3
            or not rel.parts[0].startswith("g2-online-")
            or rel.parts[1:] != Path(LIVE_VIEWS).parts
        ):
            raise ContractError("R2 source must belong to an EvalV2 Actor publication")
        path = contained(self.root, rel)
        live, _, _ = read_bound_json(
            path, expected_sha256=sha(spatial_source["sha256"])
        )
        metadata = live["spatial_metadata"]
        frame = identity.logical_state_frame
        source = sha(live["source_sha256"])
        if (
            live.get("schema") != "g2_online_f27_views_v1"
            or live.get("episode_id") != identity.episode_id
            or metadata.get("schema") != "g2_state_spatial_metadata_v1"
            or metadata.get("frame") != frame
            or metadata.get("scene_id") != identity.scene_id
            or metadata.get("world_frame") != "world"
            or metadata["geometry_provenance"].get("source_sha256") != source
            or frame != identity.decision_frame // PERIOD_FRAMES * PERIOD_FRAMES
            or static_text["source_identity"] != source
            or metadata["spatial_metadata_id"]
            != fingerprint(
                {k: v for k, v in metadata.items() if k != "spatial_metadata_id"}
            )
        ):
            raise ContractError(
                "R2 source does not match the current Episode and spatial frontier"
            )
        init, _, _ = read_bound_json(path.parents[1] / "initial_condition.json")
        task = init["task_set"]
        text_id = init["text"]["text_id"]
        if (
            static_text["initial_context_identity"] != text_id
            or init["text"]["augmented_instruction"]
            != static_text["enhanced_instruction"]
            or init["text"]["original_instruction"]
            != static_text["original_instruction"]
            or task_binding_identity(identity.episode_id, source, task, text_id)
            != identity.task_binding_id
        ):
            raise ContractError(
                "R2 spatial task entities do not match the initialized binding"
            )
        variant = "w_rbs" if base.top_variant == "with_robot" else "clean"
        selection = select_views(metadata, task, top_variant=variant)
        # DATA_C's formal ABI has exactly one canonical floor image.
        if selection["mandatory_view_ids"] != [
            "sixview/floor_top_w_rbs" if variant == "w_rbs" else "sixview/floor_top"
        ]:
            raise ContractError("R2 requires the canonical DATA_C top View")
        ids = selection["selected_view_ids"]
        if len(ids) > self.max_views:
            raise MemoryError("R2 selected views exceed the Session entry budget")

        views, projections, rasters, masks, types = [], [], [], [], []
        for vid in ids:
            view = metadata["views"][vid]
            owner = view["image_owner"]
            owner_frame = owner["frame"]
            view_png = f"{vid}.png"
            fields = asset_identity(view_png)
            if (
                type(owner_frame) is not int
                or not 0 <= owner_frame <= frame
                or owner_frame % PERIOD_FRAMES != 0
                or owner["path"] != f"frame_{owner_frame}/{view_png}"
                or any(view.get(k) != v for k, v in fields.items())
                or view["geometry_version"] != metadata["geometry_version"]
                or view["membership_version"] != fingerprint(view["membership"])
            ):
                raise ContractError("R2 view owner or renderer membership differs")
            filename = contained(path.parent, owner["path"])
            png_sha = sha(owner["sha256"])
            proj = view["image_projection"]
            if proj["projection_id"] != fingerprint(
                {k: v for k, v in proj.items() if k != "projection_id"}
            ):
                raise ContractError("R2 projection identity differs")
            projection = reader_projection(metadata["world_frame"], proj)
            prep = self._preprocessing(filename, png_sha, file_identity(filename))
            raster, mask = reader_raster(
                prep, projection, tuple(self.recipe["record_shape"][1:])
            )
            if raster.original_hw != (
                projection.height_px,
                projection.width_px,
            ) or not bool(mask.any()):
                raise ContractError("R2 projection and actual PNG dimensions differ")
            top = fields["is_floor_top"]
            island = view["island_id"]
            views.append(
                ViewIdentity(
                    view_id=vid,
                    content_version=png_sha,
                    image_owner=filename.relative_to(self.root).as_posix(),
                    image_owner_frame=owner_frame,
                    geometry_version=view["geometry_version"],
                    membership_version=view["membership_version"],
                    recipe_id=self.recipe["recipe_id"],
                )
            )
            projections.append(projection)
            rasters.append(raster)
            masks.append(mask_content_identity(mask))
            types.append(
                (
                    "floor" if top else "room" if island is None else "island",
                    vid.rsplit("/", 1)[-1].removesuffix("_w_rbs"),
                    str(view["room_uid"]),
                    island,
                    base.top_variant if top else None,
                )
            )
        return OnlineSpatialSnapshot(
            identity=identity,
            source="online_rollout",
            signature=replace(
                base,
                views=tuple(views),
                projections=tuple(projections),
                rasters=tuple(rasters),
                view_types=tuple(types),
            ),
            mask_content_ids=tuple(masks),
        )

    def load_view(self, snapshot, index):
        signature = snapshot.signature
        identity = signature.views[index]
        path = contained(self.root, identity.image_owner)
        latent = self.encoder.encode(self._png(path, identity.content_version))
        projection, raster = signature.projections[index], signature.rasters[index]
        scope, direction, room, island, variant = signature.view_types[index]
        # Recreate the exact support mask from the validated preprocessing receipt.
        _, mask = patch_layout(
            raster, tuple(latent.shape[1:]), rows_flipped=projection.rows_flipped
        )
        return SpatialView(
            identity=identity,
            latent=latent,
            valid_mask=mask,
            projection=projection,
            raster=raster,
            scope=scope,
            direction=direction,
            room_id=room,
            island_id=island,
            top_variant=variant,
        )

    def close(self):
        self.encoder.close()
