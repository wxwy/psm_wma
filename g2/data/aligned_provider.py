"""Read-only DATA_C candidate provider for the G2 model's existing B/C boundary.

This module never initializes a renderer, VAE, ROS, online sim or LLM.
Formal G2RunRecipe explicitly REJECTS this candidate until an independent
train/val split and initial-text production approval elevate its evidence.
"""

from __future__ import annotations

import hashlib
import os
from collections import OrderedDict
from collections.abc import Mapping
from contextlib import contextmanager
from copy import copy
from pathlib import Path

from g2.data.episode_state import (
    canonical,
    episode_path,
    file_identity,
    read_bound_json,
    read_episode_state,
)
from g2.data.joint_index import (
    TOP_VIEW_IDS as _TOP_VIEW_IDS,
)
from g2.data.joint_index import (
    DataCError,
    _assert_dual_top,
    _owner_view,
    make_joint_recipe,
    open_joint_view_source,
    read_joint_episode,
    verify_joint_view_refs,
)
from g2.latent_cache.contract import safe_relative
from g2.latent_cache.storage import ViewReader


def _sha(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def open_corpus_manifest(root):
    root = Path(root)
    source = root / "manifest.json"
    marker = root / "CORPUS_COMPLETE.json"
    receipt, _, _ = read_bound_json(marker)
    if not receipt.get("manifest_sha256"):
        raise DataCError("candidate DATA_C corpus has no sealed digest")
    content, _, _ = read_bound_json(source, expected_sha256=receipt["manifest_sha256"])
    if (
        content.get("schema") not in {"g2_data_c_corpus_v1", "g2_data_c_corpus_v2"}
        or (
            content.get("schema") == "g2_data_c_corpus_v2"
            and content.get("top_view_variant") != "both"
        )
        or receipt.get("schema") != "g2_data_c_corpus_complete_v1"
        or receipt.get("complete") is not True
        or content.get("training_ready") is not False
        or receipt.get("training_ready") is not False
        or content.get("data_identity")
        != canonical({k: v for k, v in content.items() if k != "data_identity"})
    ):
        raise DataCError("candidate DATA_C corpus manifest invalid")
    return content


def corpus_rows(corpus, root):
    rows = {}
    for row in corpus["episodes"]:
        task, ep = row["task_class"], row["episode_index"]
        episode_path(root, task, ep)
        sha = row["joint_sha256"]
        if (
            (task, ep) in rows
            or type(row["window_count"]) is not int
            or row["window_count"] <= 0
            or not isinstance(sha, str)
            or len(sha) != 64
            or any(ch not in "0123456789abcdef" for ch in sha)
        ):
            raise DataCError("invalid or duplicate DATA_C corpus episode row")
        rows[task, ep] = dict(row)
    if not rows:
        raise DataCError("empty DATA_C corpus")
    return rows


def _native_view(index, reader, metadata, state, ref, *, file_witnesses=None):
    """Only selected ViewReader rows, exact owner/content/projection and mask."""
    from cosmos_framework.model.generator.mot.g2_contracts import (
        SpatialView,
        ViewIdentity,
    )

    from .spatial_view import reader_projection, reader_raster

    result = reader.read_view(
        ref["view_id"],
        state["logical_state_id"],
        **({"file_witnesses": file_witnesses} if file_witnesses is not None else {}),
    )
    if not result["present"]:
        raise DataCError("DATA_C selected view absent at inference")
    owner = result["owner"]
    entry = index.manifest["views"][ref["view_id"]]
    if (
        result["record_index"] != ref["record_index"]
        or result["logical_frame"] != state["frame"]
        or owner["owner_frame"] != ref["physical_owner_frame"]
        or owner["owner_state_id"] != ref["physical_owner_state"]
        or owner["owner_state_ordinal"] != ref["physical_owner_ordinal"]
        or owner["png_sha256"] != ref["physical_png_sha256"]
        or entry["path"] != ref["cache_file"]
        or entry["sha256"] != ref["cache_file_sha256"]
        or entry["record_sha256"][result["record_index"]] != ref["record_sha256"]
        or index.manifest["recipe"]["recipe_id"] != ref["vae_recipe_id"]
    ):
        raise DataCError("DATA_C selected view owner/source/recipe differs")
    view = metadata["views"][ref["view_id"]]
    proj = view["image_projection"]
    if (
        proj["projection_id"] != ref["projection_id"]
        or view["membership_version"] != ref["membership_version"]
        or view["geometry_version"] != ref["geometry_version"]
        or view["image_owner"]["frame"] != owner["owner_frame"]
        or view["image_owner"]["sha256"] != owner["png_sha256"]
        or str(view.get("room_uid")) != ref["room_id"]
        or view.get("island_id") != ref["island_id"]
        or ref["view_scope"]
        != (
            "floor"
            if view.get("is_floor_top")
            else "island"
            if view.get("island_id") is not None
            else "room"
        )
        or ref["direction"] != ref["view_id"].rsplit("/", 1)[-1].removesuffix("_w_rbs")
    ):
        raise DataCError("DATA_C projection/membership/image provenance changed")
    projection = reader_projection(metadata["world_frame"], proj)
    raster, mask = reader_raster(
        result["preprocessing"], projection, tuple(result["latent"].shape[1:])
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


class _EpisodeData(Mapping):
    """Public episode lookup with a small cache of decoded episode payloads."""

    def __init__(self, rows, load, max_episodes):
        self.rows, self.load, self.max_episodes = rows, load, max_episodes
        self.cache = OrderedDict()
        self.witnesses = {}

    def __contains__(self, key):
        return key in self.rows

    def __iter__(self):
        return iter(self.rows)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, key):
        if key not in self.cache:
            value = self.load(self.rows[key])
            if len(self.cache) == self.max_episodes:
                evicted, _ = self.cache.popitem(last=False)
                self.witnesses.pop(evicted, None)
            self.cache[key] = value
        self.cache.move_to_end(key)
        return self.cache[key]


class CandidateAlignedG2Provider:
    """Read-only DATA_C provider for immutable source and selected View reads."""

    evidence_scope = "g2_real_aligned_candidate_not_formal_training"
    latent_channels = 48
    split_identity = "SCOPED_EPISODES_SPLIT_NOT_FROZEN"
    _episode_cache_size = 4

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
        cache_size = os.environ.get("PSM_G2_EPISODE_CACHE_SIZE", "4")
        if cache_size not in {"4", "16"}:
            raise DataCError("PSM_G2_EPISODE_CACHE_SIZE must be 4 or 16")
        self._episode_cache_size = int(cache_size)
        self.data_c_root = Path(data_c_root)
        self.state15_root = Path(state15_root)
        self.view_root = Path(view_root)
        self.global_memory_enabled = global_memory_enabled
        self.initial_language_root = (
            Path(initial_language_root) if initial_language_root is not None else None
        )
        self.initial_language_recipe_id = initial_language_recipe_id
        live_corpus = open_corpus_manifest(data_c_root)
        live_episodes = corpus_rows(live_corpus, data_c_root)
        if corpus_manifest_override is None:
            self.corpus = live_corpus
            rows = live_episodes
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
            rows = corpus_rows(override, data_c_root)
            if any(live_episodes.get(key) != row for key, row in rows.items()):
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
        self.data = _EpisodeData(rows, self._load_episode, self._episode_cache_size)
        self._views = OrderedDict()
        self._language = OrderedDict()
        self._language_bindings = None
        self._joint_id = canonical(
            make_joint_recipe(
                state_recipe_id=self.corpus["state15_recipe_id"],
                view_recipe_id=self.corpus["view_recipe_id"],
                top_variant=self.corpus["top_view_variant"],
            )
        )
        if self.corpus.get("recipe_id", self._joint_id) != self._joint_id:
            raise DataCError("DATA_C corpus joint recipe differs from source fields")
        self._prefetch_witnesses = None
        self.view_read_count = 0

    def fork_for_worker(self):
        """Clone mutable runtime state for one Raw Prefetch worker.

        Immutable certified index/recipe/bindings are shared read-only.
        Episode tensors, language LRUs and ViewReader handles must *never*
        be shared with the trainer thread or another worker.
        """
        worker = copy(self)
        worker.data = _EpisodeData(
            self.data.rows, worker._load_episode, self._episode_cache_size
        )
        worker._views = OrderedDict()
        worker._language = OrderedDict()
        worker._prefetch_witnesses = None
        worker.view_read_count = 0
        return worker

    @contextmanager
    def capture_prefetch_witnesses(self):
        """Capture verified file versions for one speculative CPU segment."""
        if getattr(self, "_prefetch_witnesses", None) is not None:
            raise DataCError("nested speculative witness capture")
        witnesses = {}
        self._prefetch_witnesses = witnesses
        try:
            yield witnesses
        finally:
            self._prefetch_witnesses = None

    def _record_prefetch_witnesses(self, witnesses):
        packet = getattr(self, "_prefetch_witnesses", None)
        if packet is not None:
            for path, token in witnesses.items():
                if packet.setdefault(path.absolute(), token) != token:
                    raise DataCError(
                        "source version changed within speculative segment"
                    )

    def _load_episode(self, row):
        task, ep = row["task_class"], row["episode_index"]
        witnesses = {}
        c_path = episode_path(self.data_c_root, task, ep)
        value, _ = read_joint_episode(
            c_path,
            task=task,
            episode=ep,
            recipe_id=self._joint_id,
            source_binding_digest=self.corpus["source_binding_digest"],
            expected_sha256=row["joint_sha256"],
            window_count=row["window_count"],
            file_witnesses=witnesses,
        )
        state15, meta, _ = read_episode_state(
            episode_path(self.state15_root, task, ep),
            task=task,
            episode=ep,
            frame_count=value["source_frame_count"],
            recipe_id=value["recipe"]["state15_recipe_id"],
            source_binding_digest=value["source_binding_digest"],
            expected_sha256=value["data_b_sha256"],
            file_witnesses=witnesses,
        )
        if meta["original_instruction"] != value["original_instruction"]:
            raise DataCError("DATA_B and DATA_C original instructions differ")
        self.data.witnesses[task, ep] = witnesses
        return value, state15

    def _versioned_text(self, task_class, episode_index, idx):
        from g2.language.initial_context import read_versioned_initial_language

        key = (task_class, episode_index)
        if key not in self._language:
            witnesses = {}
            binding = (
                self._language_bindings[key]
                if self._language_bindings is not None
                else None
            )
            record = read_versioned_initial_language(
                self.initial_language_root,
                recipe_id=self.initial_language_recipe_id,
                task_class=task_class,
                episode_index=episode_index,
                source_binding_digest=idx["source_binding_digest"],
                original_instruction=idx["original_instruction"],
                view_root=self.view_root if binding is None else None,
                expected_files=binding,
                file_witnesses=witnesses,
            )
            if len(self._language) == self._episode_cache_size:
                self._language.popitem(last=False)
            self._language[key] = (record, witnesses)
        self._language.move_to_end(key)
        record, witnesses = self._language[key]
        for path, (_, previous) in witnesses.items():
            if file_identity(path) != previous:
                raise DataCError(
                    "independent language or source changed during Provider lifetime"
                )
        if getattr(self, "_prefetch_witnesses", None) is not None:
            self._record_prefetch_witnesses(
                {path: token for path, (_, token) in witnesses.items()}
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
        if getattr(self, "_prefetch_witnesses", None) is not None:
            self._record_prefetch_witnesses(self.data.witnesses[key])
        if type(decision_frame) is not int or not 0 <= decision_frame < len(
            idx["windows"]
        ):
            raise DataCError("decision frame outside indexed G1 horizon")
        item = idx["windows"][decision_frame]
        ordinal = item["spatial_state_ordinal"]
        if (
            item["decision_frame"] != decision_frame
            or type(ordinal) is not int
            or not 0 <= ordinal < len(idx["spatial_states"])
            or idx["spatial_states"][ordinal]["frame"] != item["spatial_state_frame"]
            or item["spatial_state_frame"] > decision_frame
        ):
            raise DataCError("DATA_C no-future index invariant violated")
        return idx, states, item

    def read_common(self, *, task_class, episode_index, decision_frame):
        from cosmos_framework.data.generator.action.utils.static_task_text import (
            StaticTaskText,
        )
        from cosmos_framework.model.generator.mot.g2_contracts import G2SampleIdentity

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
        if (
            identity.data_version != self.identity
            or state["frame"] != identity.logical_state_frame
        ):
            raise DataCError("provider logical state differs from model identity")
        epdir = episode_path(self.view_root, task, ep)
        view_key = (task, ep)
        if view_key not in self._views:
            manifest, source, witnesses = open_joint_view_source(epdir, idx)
            verify_joint_view_refs(idx, manifest, source)
            if len(self._views) == self._episode_cache_size:
                _, (_, _, reader, _) = self._views.popitem(last=False)
                reader.close()
            self._views[view_key] = (
                manifest,
                source,
                ViewReader(source, max_views=12),
                witnesses,
            )
        self._views.move_to_end(view_key)
        manifest, reader_index, reader, witnesses = self._views[view_key]
        if any(file_identity(path) != token for path, token in witnesses.items()):
            raise DataCError("source View index changed during reader lifetime")
        refs = _select_runtime_view_refs(
            reader_index,
            reader,
            epdir,
            state,
            win["spatial_state_ordinal"],
            top_view_variant=top_view_variant,
        )
        relative = safe_relative(
            state["spatial_metadata_file"], suffix=".json"
        ).as_posix()
        metadata_path = epdir / relative
        metadata, _, metadata_token = read_bound_json(
            metadata_path, expected_sha256=manifest["files"][relative]
        )
        if (
            metadata["frame"] != state["frame"]
            or metadata["state_id"] != state["logical_state_id"]
            or metadata["geometry_version"] != state["geometry_version"]
        ):
            raise DataCError("DATA_C spatial metadata belongs to a different state")
        packet = getattr(self, "_prefetch_witnesses", None)
        if packet is None:
            views = tuple(
                _native_view(reader_index, reader, metadata, state, ref) for ref in refs
            )
        else:
            self._record_prefetch_witnesses(witnesses)
            self._record_prefetch_witnesses({metadata_path: metadata_token})
            selected_files = {}
            views = tuple(
                _native_view(
                    reader_index,
                    reader,
                    metadata,
                    state,
                    ref,
                    file_witnesses=selected_files,
                )
                for ref in refs
            )
            self._record_prefetch_witnesses(selected_files)

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
        for _, _, reader, _ in self._views.values():
            reader.close()
        self._views.clear()
        self._language.clear()
        self.data.cache.clear()
        self.data.witnesses.clear()
