"""Read-only DATA_C candidate provider for the G2 model's existing B/C boundary.

This module never initializes a renderer, VAE, ROS, online sim or LLM.
Formal G2RunRecipe explicitly REJECTS this candidate until an independent
train/val split and initial-text production approval elevate its evidence.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from pathlib import Path

import torch

from g2.data.episode_state import (
    canonical,
    digest,
    episode_path,
    json_load,
    require_regular,
)
from g2.data.joint_index import (
    DataCError,
    _assert_dual_top,
    _owner_view,
    make_joint_recipe,
)
from g2.latent_cache.storage import ViewReader, open_episode_index


def _sha(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def open_corpus_manifest(root):
    root = Path(root)
    source = root / "manifest.json"
    marker = root / "CORPUS_COMPLETE.json"
    require_regular(source)
    require_regular(marker)
    content = json_load(source)
    receipt = json_load(marker)
    if (
        content.get("schema") not in {"g2_data_c_corpus_v1", "g2_data_c_corpus_v2"}
        or (
            content.get("schema") == "g2_data_c_corpus_v2"
            and content.get("top_view_variant") != "both"
        )
        or receipt.get("schema") != "g2_data_c_corpus_complete_v1"
        or receipt.get("manifest_sha256") != digest(source)
        or receipt.get("complete") is not True
        or content.get("training_ready") is not False
        or receipt.get("training_ready") is not False
    ):
        raise DataCError("candidate DATA_C corpus manifest invalid")
    return content


def _native_view(index, reader, episode_dir, state, ref):
    """Only selected ViewReader rows, exact owner/content/projection and mask."""
    from cosmos_framework.model.generator.mot.g2_contracts import (
        RasterMapping,
        SpatialProjection,
        SpatialView,
        ViewIdentity,
    )
    from cosmos_framework.model.generator.mot.global_spatial import (
        patch_layout,
        projection_vector,
    )

    result = reader.read_view(ref["view_id"], state["logical_state_id"])
    if not result["present"]:
        raise DataCError("DATA_C selected view absent at inference")
    owner = result["owner"]
    if (
        result["record_index"] != ref["record_index"]
        or owner["owner_frame"] != ref["physical_owner_frame"]
        or owner["png_sha256"] != ref["physical_png_sha256"]
        or index.manifest["views"][ref["view_id"]]["sha256"] != ref["cache_file_sha256"]
        or index.manifest["recipe"]["recipe_id"] != ref["vae_recipe_id"]
    ):
        raise DataCError("DATA_C selected view owner/source/recipe differs")
    source = json_load(episode_dir / state["spatial_metadata_file"])
    view = source["views"][ref["view_id"]]
    proj = view["image_projection"]
    basis = proj["reference_frame"]
    if (
        proj["projection_id"] != ref["projection_id"]
        or view["membership_version"] != ref["membership_version"]
        or view["geometry_version"] != ref["geometry_version"]
        or view["image_owner"]["sha256"] != owner["png_sha256"]
    ):
        raise DataCError("DATA_C projection/membership/image provenance changed")
    projection = SpatialProjection(
        projection_id=proj["projection_id"],
        world_frame=source["world_frame"],
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
    projection_vector(projection)  # native metrical/orthonormal acceptance gate
    pp = result["preprocessing"]
    raster = RasterMapping(
        original_hw=tuple(pp["original_hw"]),
        resized_hw=tuple(pp["resized_hw"]),
        canvas_hw=tuple(pp["canvas_hw"]),
        content_box=tuple(pp["content_box"]),
    )
    _, mask = patch_layout(
        raster, tuple(result["latent"].shape[1:]), rows_flipped=projection.rows_flipped
    )
    if not bool(mask.any()) or result["latent"].shape[0] != 48:
        raise DataCError("invalid geometry or latent channels")
    vi = ViewIdentity(
        view_id=ref["view_id"],
        content_version=owner["png_sha256"],
        image_owner=owner["png_path"],
        image_owner_frame=owner["owner_frame"],
        geometry_version=view["geometry_version"],
        membership_version=view["membership_version"],
        recipe_id=ref["vae_recipe_id"],
    )
    return SpatialView(
        identity=vi,
        latent=result["latent"],
        valid_mask=mask,
        projection=projection,
        raster=raster,
        scope=ref["view_scope"],
        direction=ref["direction"],
        room_id=ref["room_id"],
        island_id=ref["island_id"] if ref["view_scope"] == "island" else None,
        top_variant=ref["top_variant"],
    )


_TOP_VIEW_IDS = {
    "with_robot": "sixview/floor_top_w_rbs",
    "without_robot": "sixview/floor_top",
}


def _select_runtime_view_refs(
    index, reader, episode_dir, state, ordinal, *, top_view_variant
):
    """Resolve either published top image from one immutable DATA_C joint index.

    DATA_C stores a source-bound reference to its original selected top.
    The other already-encoded top is resolved against the *same* logical
    spatial state, real spatial metadata and View VAE physical owner. No
    DATA_C rewrite, VAE encode or zero-token substitute is permitted.
    """
    if top_view_variant not in _TOP_VIEW_IDS:
        raise DataCError("unknown requested top variant")
    if "top_views" in state:
        _assert_dual_top(state)
        # V2 materializes both true VAE references in DATA_C once. The
        # requested variant is resolved without recomputing its provenance.
        # _native_view still verifies actual cache/owner/geometry on read.
        return (
            state["top_views"][top_view_variant],
            *state["selected_views"],
        )
    refs = tuple(state["selected_views"])
    top = [
        (i, ref)
        for i, ref in enumerate(refs)
        if ref["view_id"] in _TOP_VIEW_IDS.values()
    ]
    if len(top) != 1:
        raise DataCError("DATA_C requires exactly one stored top view")
    pos, base = top[0]
    if (
        base["view_id"] != _TOP_VIEW_IDS.get(base.get("top_variant"))
        or base.get("view_scope") != "floor"
        or sum(ref.get("view_scope") == "floor" for ref in refs) != 1
    ):
        raise DataCError("stored top View ID/variant/scope inconsistent")
    if base["top_variant"] == top_view_variant:
        return refs

    # The selected clean top's membership is the shared selection policy.
    # Both images must have identical projection, geometry and membership,
    # but content hash, owner frame, VAE record and cache file may differ.
    raw_state = {
        "state_id": state["logical_state_id"],
        "frame": state["frame"],
        "spatial_metadata": state["spatial_metadata_file"],
        "selection": {
            "membership_ids": {"sixview/floor_top": base["membership_version"]}
        },
    }
    try:
        alternate = _owner_view(
            index,
            reader,
            episode_dir,
            raw_state,
            ordinal,
            _TOP_VIEW_IDS[top_view_variant],
            recipe_id=base["vae_recipe_id"],
        )
    except (KeyError, ValueError, OSError) as exc:
        raise DataCError("requested top variant absent or source-invalid") from exc
    if any(
        alternate[field] != base[field]
        for field in (
            "projection_id",
            "geometry_version",
            "membership_version",
            "vae_recipe_id",
        )
    ):
        raise DataCError("top variants disagree in spatial source geometry/recipe")
    if alternate["physical_owner_frame"] > state["frame"]:
        raise DataCError("requested top would leak future physical owner")
    resolved = list(refs)
    resolved[pos] = alternate
    return tuple(resolved)


class CandidateAlignedG2Provider:
    """Read-only 3ep DATA_C provider, deliberately not yet 'verified_data_c'."""

    evidence_scope = "g2_real_aligned_candidate_not_formal_training"
    latent_channels = 48
    split_identity = "SCOPED_EPISODES_SPLIT_NOT_FROZEN"

    def __init__(
        self,
        *,
        data_c_root,
        state15_root,
        view_root,
        global_memory_enabled=True,
        initial_language_root=None,
        initial_language_recipe_id=None,
        corpus_manifest_override=None,
    ):
        if (initial_language_root is None) != (initial_language_recipe_id is None):
            raise DataCError(
                "external language requires both explicit root and recipe ID"
            )
        self.data_c_root = Path(data_c_root)
        self.state15_root = Path(state15_root)
        self.view_root = Path(view_root)
        self.global_memory_enabled = global_memory_enabled
        self.initial_language_root = (
            Path(initial_language_root) if initial_language_root is not None else None
        )
        self.initial_language_recipe_id = initial_language_recipe_id
        live_corpus = open_corpus_manifest(data_c_root)
        if corpus_manifest_override is None:
            self.corpus = live_corpus
        else:
            override = corpus_manifest_override
            if (
                not isinstance(override, dict)
                or override.get("data_identity")
                != canonical(
                    {k: v for k, v in override.items() if k != "data_identity"}
                )
                or any(
                    override.get(k) != live_corpus.get(k)
                    for k in (
                        "schema",
                        "source_binding_digest",
                        "state15_recipe_id",
                        "view_recipe_id",
                        "recipe_id",
                        "top_view_variant",
                        "alignment_version",
                        "split_identity",
                        "evidence_scope",
                        "training_ready",
                    )
                )
            ):
                raise DataCError(
                    "certified DATA_C manifest override differs in source/recipe"
                )
            live_episodes = {
                (row["task_class"], row["episode_index"]): row
                for row in live_corpus["episodes"]
            }
            if not override.get("episodes") or any(
                live_episodes.get((row["task_class"], row["episode_index"])) != row
                for row in override["episodes"]
            ):
                raise DataCError(
                    "certified DATA_C override contains missing/modified episode"
                )
            self.corpus = override
        self.identity = (
            self.corpus["data_identity"]
            if self.initial_language_root is None
            else canonical(
                {
                    "data_c_identity": self.corpus["data_identity"],
                    "initial_language_recipe_id": self.initial_language_recipe_id,
                    "language_scope": "review_episode_static_frame0_external",
                }
            )
        )
        self.data = {}
        self._views = {}
        self._top_variant_refs = OrderedDict()
        self._language = {}
        self._manifest_stat = {}
        expected_joint_id = canonical(
            make_joint_recipe(
                state_recipe_id=self.corpus["state15_recipe_id"],
                view_recipe_id=self.corpus["view_recipe_id"],
                top_variant=self.corpus["top_view_variant"],
            )
        )
        if self.corpus.get("recipe_id", expected_joint_id) != expected_joint_id:
            raise DataCError("DATA_C corpus joint recipe differs from source fields")
        for row in self.corpus["episodes"]:
            task, ep = row["task_class"], row["episode_index"]
            c_path = episode_path(self.data_c_root, task, ep)
            value = json_load(c_path / "joint_index.json")
            marker = json_load(c_path / "COMPLETE.json")
            b_path = episode_path(self.state15_root, task, ep)
            b_marker = json_load(b_path / "COMPLETE.json")
            if (
                marker["joint_sha256"] != digest(c_path / "joint_index.json")
                or marker["joint_sha256"] != row["joint_sha256"]
                or value["recipe_id"] != expected_joint_id
                or value["recipe_id"] != canonical(value["recipe"])
                or b_marker["state15_sha256"] != value["data_b_sha256"]
                or digest(b_path / "state15.pt") != value["data_b_sha256"]
                or value["source_binding_digest"]
                != self.corpus["source_binding_digest"]
            ):
                raise DataCError("DATA_C Provider source/episode/data_b bind mismatch")
            obj = torch.load(
                b_path / "state15.pt", map_location="cpu", weights_only=True, mmap=True
            )
            if (
                obj["metadata"]["recipe_id"] != value["recipe"]["state15_recipe_id"]
                or obj["metadata"]["source_binding_digest"]
                != value["source_binding_digest"]
                or obj["state15"].shape != (value["source_frame_count"], 15)
            ):
                raise DataCError("DATA_B Provider state15 shape/recipe mismatch")
            if not bool(torch.isfinite(obj["state15"]).all()):
                raise DataCError("nonfinite persisted DATA_B")
            self.data[(task, ep)] = (value, obj["state15"])
        self.view_read_count = 0

    def _versioned_text(self, task_class, episode_index, idx):
        from g2.language.initial_context import read_versioned_initial_language

        key = (task_class, episode_index)
        if key not in self._language:
            record = read_versioned_initial_language(
                self.initial_language_root,
                recipe_id=self.initial_language_recipe_id,
                task_class=task_class,
                episode_index=episode_index,
                source_binding_digest=idx["source_binding_digest"],
                original_instruction=idx["original_instruction"],
                view_root=self.view_root,
            )
            version = self.initial_language_recipe_id
            lang_ep = (
                self.initial_language_root
                / "recipes"
                / version
                / "tasks"
                / task_class
                / "episodes"
                / f"episode_{episode_index:06d}"
            )
            view_ep = episode_path(self.view_root, task_class, episode_index)
            paths = (
                self.initial_language_root / "OUTPUT_IDENTITY.json",
                self.initial_language_root / "recipes" / version / "RECIPE.json",
                lang_ep / "initial_context.json",
                lang_ep / "COMPLETE.json",
                view_ep / "episode_manifest.json",
                view_ep / "task_entities.json",
                view_ep / "language.json",
                view_ep / record["provenance"]["initial_scene_graph_relative_path"],
            )
            watches = []
            for path in paths:
                require_regular(path)
                st = path.stat()
                watches.append(
                    (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
                )
            self._language[key] = (record, paths, tuple(watches))
        record, paths, watches = self._language[key]
        for path, previous in zip(paths, watches, strict=True):
            require_regular(path)
            st = path.stat()
            token = (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
            if token != previous:
                raise DataCError(
                    "independent language or source changed during Provider lifetime"
                )
        return {
            "original_instruction": record["original_instruction"],
            "enhanced_instruction": record["augmented_instruction"],
            "text_template_recipe_id": record["recipe"]["recipe_id"],
            "text_id": record["text_id"],
        }

    def _item(self, task_class, episode_index, decision_frame):
        key = (task_class, episode_index)
        if key not in self.data:
            raise DataCError("episode absent from DATA_C index/split")
        idx, states = self.data[key]
        if type(decision_frame) is not int or not 0 <= decision_frame < len(
            idx["windows"]
        ):
            raise DataCError("decision frame outside indexed G1 horizon")
        item = idx["windows"][decision_frame]
        if (
            item["decision_frame"] != decision_frame
            or item["spatial_state_frame"] > decision_frame
        ):
            raise DataCError("DATA_C no-future index invariant violated")
        return idx, states, item

    def read_common(self, *, task_class, episode_index, decision_frame):
        from cosmos_framework.model.generator.mot.g2_contracts import G2SampleIdentity
        from cosmos_framework.data.generator.action.utils.static_task_text import (
            StaticTaskText,
        )

        idx, states, window = self._item(task_class, episode_index, decision_frame)
        text = (
            idx["static_text"]
            if self.initial_language_root is None
            else self._versioned_text(task_class, episode_index, idx)
        )
        episode_id = f"{task_class}/episode_{episode_index:06d}"
        identity = G2SampleIdentity(
            episode_id=episode_id,
            scene_id=f"robocasa365_atomic_{episode_index:06d}",
            subtask_id=f"atomic_{episode_index:06d}",
            decision_frame=decision_frame,
            logical_state_frame=window["spatial_state_frame"],
            data_version=self.identity,
            alignment_version=self.corpus["alignment_version"],
            state15_recipe_id=idx["recipe"]["state15_recipe_id"],
            task_binding_id=canonical(
                {
                    "episode": episode_id,
                    "raw_source": idx["source_binding_digest"],
                    "static_text_id": text["text_id"],
                }
            ),
        )
        static = StaticTaskText(
            original_instruction=text["original_instruction"],
            enhanced_instruction=text["enhanced_instruction"],
            episode_id=episode_id,
            subtask_id=f"atomic_{episode_index:06d}",
            template_identity=text["text_template_recipe_id"],
            source_identity=_sha(idx["source_binding_digest"]),
            initial_context_identity=text["text_id"],
        )
        return {
            "identity": identity,
            "static_task_text": static,
            "state15": states[decision_frame].clone(),
            "task_class": task_class,
            "episode_index": episode_index,
            "source_binding_digest": idx["source_binding_digest"],
            "state15_space": "data_b_model_input",
        }

    def read_selected_views(self, identity, *, top_view_variant):
        if not self.global_memory_enabled:
            raise DataCError("R1 must not read spatial views")
        if top_view_variant not in _TOP_VIEW_IDS:
            raise DataCError("unknown requested top variant")
        task, tail = identity.episode_id.rsplit("/episode_", 1)
        ep = int(tail)
        idx, _, win = self._item(task, ep, identity.decision_frame)
        state = idx["spatial_states"][win["spatial_state_ordinal"]]
        if state["frame"] != identity.logical_state_frame:
            raise DataCError("provider logical state differs from model identity")
        epdir = episode_path(self.view_root, task, ep)
        snapshots = (
            (epdir / "vae_cache/manifest.json", idx["view_vae_manifest_sha256"]),
            (epdir / "episode_manifest.json", idx["view_episode_manifest_sha256"]),
        )
        # First use hashes the small immutable manifests; subsequent per-window
        # reads compare file-stat identities in O(1), not rehash 150KB each
        # time. Unexpected rotation or replacement fails closed.
        for path, sha in snapshots:
            require_regular(path)
            stat = path.stat()
            token = (
                stat.st_dev,
                stat.st_ino,
                stat.st_size,
                stat.st_mtime_ns,
                stat.st_ctime_ns,
            )
            old = self._manifest_stat.get(path)
            if old is None:
                if sha != digest(path):
                    raise DataCError(
                        "source view manifest modified after DATA_C publication"
                    )
                self._manifest_stat[path] = token
            elif old != token:
                raise DataCError("source view manifest changed during reader lifetime")
        if (task, ep) not in self._views:
            source = open_episode_index(
                epdir, expected_recipe_id=idx["view_vae_recipe_id"]
            )
            self._views[task, ep] = (
                source,
                ViewReader(source, max_views=12, max_bytes=256 * 1024 * 1024),
            )
        reader_index, reader = self._views[task, ep]
        key = (task, ep, win["spatial_state_ordinal"], top_view_variant)
        refs = self._top_variant_refs.get(key)
        if refs is None:
            refs = _select_runtime_view_refs(
                reader_index,
                reader,
                epdir,
                state,
                win["spatial_state_ordinal"],
                top_view_variant=top_view_variant,
            )
            self._top_variant_refs[key] = refs
            if len(self._top_variant_refs) > 4096:
                self._top_variant_refs.popitem(last=False)
        else:
            self._top_variant_refs.move_to_end(key)
        views = tuple(
            _native_view(reader_index, reader, epdir, state, ref) for ref in refs
        )
        tops = [v for v in views if v.top_variant is not None]
        if len(tops) != 1 or tops[0].top_variant != top_view_variant:
            raise DataCError("expected exactly one top view matching G2 configuration")
        if any(
            v.identity.image_owner_frame > identity.logical_state_frame for v in views
        ):
            raise DataCError("future physical owner")
        self.view_read_count += 1
        return views

    def close(self):
        for _, reader in self._views.values():
            reader.close()
        self._views.clear()
        self._top_variant_refs.clear()