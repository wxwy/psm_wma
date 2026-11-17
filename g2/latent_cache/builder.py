"""Offline orchestration; source discovery, encoding and numerical reads stay separate."""

from __future__ import annotations

import math
from io import BytesIO
from pathlib import Path

from g2.io import digest, read_json

from .contract import (
    COMPLETE_SCHEMA,
    INDEX_SCHEMA,
    PAYLOAD_SCHEMA,
    CacheError,
    contained,
    fingerprint,
    make_recipe,
    safe_relative,
    validate_recipe,
)


def _real_directory(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_dir():
        raise CacheError("source root must be a real directory without symlinks")
    return path


def discover_episodes(dataset_root, tasks=None, episodes=None):
    """Discover completed G2 packages, not a second raw-RoboCasa membership list.

    Existing catalogue naming and each package's actual manifest identity are
    authoritative. This never loads original models, states, SG or VAE.
    """
    from g2.offline.atomic_6views_catalog import EPISODE_NAME

    root = _real_directory(dataset_root)
    if tasks is not None:
        if isinstance(tasks, str) or not isinstance(tasks, (list, tuple, set)):
            raise CacheError("tasks must be an explicit collection")
        tasks = set(tasks)
        if not tasks or any(len(safe_relative(t).parts) != 1 for t in tasks):
            raise CacheError("invalid task selection")
    if episodes is not None:
        if isinstance(episodes, (str, int)) or not isinstance(
            episodes, (list, tuple, set)
        ):
            raise CacheError("episodes must be an explicit collection of global IDs")
        episodes = set(episodes)
        if not episodes or any(type(e) is not int or e < 0 for e in episodes):
            raise CacheError("invalid global episode selection")
    if (root / "episode_manifest.json").exists():
        candidates = [root]
    else:
        task_root = contained(root, "tasks")
        available = {
            p.name for p in task_root.iterdir() if p.is_dir() or p.is_symlink()
        }
        selected = available if tasks is None else tasks
        if selected - available:
            raise CacheError("unknown selected task")
        candidates = []
        for name in sorted(selected):
            path = contained(root, "tasks/" + name + "/episodes")
            for ep in sorted(path.iterdir()):
                match = EPISODE_NAME.fullmatch(ep.name)
                if match and (episodes is None or int(match.group(1)) in episodes):
                    candidates.append(_real_directory(ep))
    found, seen_tasks, seen_episodes = [], set(), set()
    for path in candidates:
        manifest = read_json(contained(path, "episode_manifest.json"))
        task, eid = manifest.get("task_class"), manifest.get("episode_id")
        if tasks is not None and task not in tasks:
            continue
        if episodes is not None and eid not in episodes:
            continue
        if not isinstance(task, str) or type(eid) is not int or eid < 0:
            raise CacheError("invalid completed episode identity")
        contained(path, "COMPLETE.json")
        if path != root and (
            path.parent.parent.name != task or path.name != f"episode_{eid:06d}"
        ):
            raise CacheError("package manifest does not match its catalogue location")
        if (task, eid) in {(t, e) for t, e, _ in found}:
            raise CacheError("duplicate package identity")
        found.append((task, eid, path))
        seen_tasks.add(task)
        seen_episodes.add(eid)
    if (
        not found
        or (tasks is not None and tasks - seen_tasks)
        or (episodes is not None and episodes - seen_episodes)
    ):
        raise CacheError("selected completed episode is missing")
    return [p for _, _, p in sorted(found)]


def _source_binding(plan):
    # Upstream manifests need not contain PNG hashes. Bind the actual owner
    # inventory too, so a changed PNG cannot mix with a partial old cache.
    return dict(
        plan["source"],
        view_index_sha256=fingerprint(
            {"states": plan["states"], "views": plan["views"]}
        ),
    )


def plan_episode(episode_root, recipe):
    from .encoding import validate_wan_canvas
    from .source import scan_episode

    validate_recipe(recipe)
    validate_wan_canvas(
        recipe["preprocessing"]["height"], recipe["preprocessing"]["width"]
    )
    plan = scan_episode(episode_root)
    physical = sum(len(v["records"]) for v in plan["views"].values())
    present = sum(
        sum(i is not None for i in v["state_records"]) for v in plan["views"].values()
    )
    return dict(
        schema="g2_spatial_view_vae_plan_v1",
        dry_run=True,
        episode_root=plan["episode_root"],
        episode_key=plan["episode_key"],
        episode=plan["episode"],
        source=_source_binding(plan),
        recipe=recipe,
        states=plan["states"],
        views=plan["views"],
        logical_view_count=len(plan["views"]),
        physical_image_count=physical,
        logical_present_count=present,
        reference_count=present - physical,
        output_files=[
            str(Path(plan["episode_root"]) / "vae_cache" / v["path"])
            for v in plan["views"].values()
        ],
        actual_latent_shape=None,
        real_vae_gate="NOT_RUN",
        cache_written=False,
    )


def _base_index(plan, recipe):
    return dict(
        schema=INDEX_SCHEMA,
        episode_key=plan["episode_key"],
        episode=plan["episode"],
        source=_source_binding(plan),
        recipe=recipe,
        states=plan["states"],
        views={},
        complete=False,
        training_ready=False,
        acceptance="CACHE_COMPLETION_IS_NOT_MODEL_OR_PRODUCTION_ACCEPTANCE",
    )


def _base_metadata(plan, recipe, view_id, view):
    return dict(
        schema=PAYLOAD_SCHEMA,
        episode_key=plan["episode_key"],
        episode=plan["episode"],
        source=_source_binding(plan),
        recipe_id=recipe["recipe_id"],
        view_id=view_id,
        view_plan=view,
        states=plan["states"],
        record_layout="CHW",
        view_layout="UCHW",
    )


def _check_metadata(metadata, base, recipe):
    if any(metadata.get(k) != value for k, value in base.items()):
        raise CacheError("existing View source/owner/recipe metadata differs")
    for record, prep in zip(
        base["view_plan"]["records"], metadata["preprocessing"], strict=True
    ):
        if prep.get("original_hw") != record["original_hw"] or prep.get(
            "canvas_hw"
        ) != [recipe["preprocessing"]["height"], recipe["preprocessing"]["width"]]:
            raise CacheError("existing View preprocessing differs from source/recipe")


def _read_rgb(plan, record):
    import hashlib

    import numpy as np
    from PIL import Image

    path = contained(plan["episode_root"], record["png_path"])
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != record["png_sha256"]:
        raise CacheError("source PNG changed before encoding")
    with Image.open(BytesIO(raw)) as image:
        image.load()
        if image.format != "PNG" or image.mode != "RGB":
            raise CacheError("source must remain a uint8 RGB PNG")
        rgb = np.array(image, copy=True)
    if list(rgb.shape[:2]) != record["original_hw"]:
        raise CacheError("source PNG dimensions changed")
    return rgb


def _index_entry(info, view):
    return {
        **{k: v for k, v in info.items() if k != "metadata"},
        "path": view["path"],
        "state_records": view["state_records"],
    }


def build_episode(
    episode_root,
    encoder,
    *,
    preprocessing=None,
    storage_dtype="float32",
    batch_size=1,
    resume=False,
):
    """One locked episode, one atomic numeric file per View, no source writes."""
    from .encoding import validate_wan_canvas
    from .source import scan_episode, verify_source
    from .storage import (
        atomic_json,
        build_lock,
        inspect_view_payload,
        write_view_payload,
    )

    recipe = make_recipe(
        encoder.descriptor(),
        preprocessing,
        storage_dtype=storage_dtype,
        batch_size=batch_size,
    )
    validate_wan_canvas(
        recipe["preprocessing"]["height"], recipe["preprocessing"]["width"]
    )
    plan = scan_episode(episode_root)
    root = Path(plan["episode_root"])
    cache = contained(root, "vae_cache", allow_missing=True)
    if cache.exists() and not resume:
        raise CacheError("cache target exists; explicit resume is required")
    index = _base_index(plan, recipe)
    encoded, reused = 0, 0
    with build_lock(cache):
        marker = contained(cache, "COMPLETE.json", allow_missing=True)
        manifest = contained(cache, "manifest.json", allow_missing=True)
        if marker.exists():
            verify_episode(root, expected_recipe_id=recipe["recipe_id"])
            return dict(
                episode_key=plan["episode_key"],
                recipe_id=recipe["recipe_id"],
                cache_root=str(cache),
                view_count=len(plan["views"]),
                encoded_records=0,
                reused_views=len(plan["views"]),
                already_complete=True,
            )
        existing = read_json(manifest) if manifest.exists() else None
        if existing is not None:
            if (
                not isinstance(existing, dict)
                or any(
                    existing.get(k) != index[k]
                    for k in (
                        "schema",
                        "episode_key",
                        "episode",
                        "source",
                        "recipe",
                        "states",
                    )
                )
                or not isinstance(existing.get("views"), dict)
                or set(existing["views"]) - set(plan["views"])
            ):
                raise CacheError(
                    "partial cache source or recipe differs; never overwrite"
                )
        else:
            atomic_json(manifest, index)
        import torch

        for view_id, view in plan["views"].items():
            if encoder.descriptor() != recipe["encoder"]:
                raise CacheError("encoder computational identity changed")
            path = contained(cache, view["path"], allow_missing=True)
            base = _base_metadata(plan, recipe, view_id, view)
            if path.exists():
                info = inspect_view_payload(path)
                _check_metadata(info["metadata"], base, recipe)
                if info["dtype"] != storage_dtype:
                    raise CacheError("existing View storage dtype differs")
                if existing is not None and view_id in existing["views"]:
                    if _index_entry(info, view) != existing["views"][view_id]:
                        raise CacheError(
                            "existing View does not match partial cache index"
                        )
                reused += 1
            else:
                if existing is not None and view_id in existing["views"]:
                    raise CacheError("previously completed View payload is missing")
                values, metadata = [], []
                for record in view["records"]:
                    latent, prep = encoder.encode(
                        _read_rgb(plan, record), recipe["preprocessing"]
                    )
                    if (
                        type(latent) is not torch.Tensor
                        or latent.device.type != "cpu"
                        or latent.dtype != torch.float32
                        or latent.ndim != 3
                        or any(n <= 0 for n in latent.shape)
                        or not torch.isfinite(latent).all()
                        or not isinstance(prep, dict)
                        or prep.get("original_hw") != record["original_hw"]
                        or prep.get("canvas_hw")
                        != [
                            recipe["preprocessing"]["height"],
                            recipe["preprocessing"]["width"],
                        ]
                    ):
                        raise CacheError(
                            "encoder did not return a finite full FP32 CHW grid and provenance"
                        )
                    if values and latent.shape != values[0].shape:
                        raise CacheError("View versions have different latent shapes")
                    stored = (
                        latent.detach()
                        .to(dtype=getattr(torch, storage_dtype), copy=True)
                        .contiguous()
                    )
                    if not torch.isfinite(stored).all():
                        raise CacheError(
                            "storage conversion produced non-finite values"
                        )
                    # Quantization error is explicit; BF16 compute does not make
                    # reduced-precision storage lossless.
                    prep = dict(
                        prep,
                        latent_shape=list(latent.shape),
                        latent_mask_basis="CONTENT_RECT_ONLY_RECEPTIVE_FIELD_NOT_CERTIFIED",
                        storage_conversion=dict(
                            from_dtype="float32",
                            to_dtype=storage_dtype,
                            exact=bool(torch.equal(latent, stored.float())),
                            max_abs_error=float((latent - stored.float()).abs().max()),
                        ),
                    )
                    values.append(stored)
                    metadata.append(prep)
                    encoded += 1
                info = write_view_payload(
                    path, dict(base, preprocessing=metadata), torch.stack(values)
                )
            index["views"][view_id] = _index_entry(info, view)
            atomic_json(manifest, index, replace=True)
        if encoder.descriptor() != recipe["encoder"]:
            raise CacheError("encoder computational identity changed")
        # Full numeric audit belongs to the writer/explicit verifier, never to
        # every training read. Detect a changed earlier payload before COMPLETE.
        for view_id, entry in index["views"].items():
            info = inspect_view_payload(contained(cache, entry["path"]))
            _check_metadata(
                info["metadata"],
                _base_metadata(plan, recipe, view_id, plan["views"][view_id]),
                recipe,
            )
            if _index_entry(info, plan["views"][view_id]) != entry:
                raise CacheError("payload changed during cache construction")
        verify_source(plan)
        index["complete"] = True
        atomic_json(manifest, index, replace=True)
        atomic_json(
            marker,
            dict(
                schema=COMPLETE_SCHEMA,
                complete=True,
                manifest_sha256=digest(manifest),
                recipe_id=recipe["recipe_id"],
                episode_key=plan["episode_key"],
                training_ready=False,
            ),
        )
    return dict(
        episode_key=plan["episode_key"],
        recipe_id=recipe["recipe_id"],
        cache_root=str(cache),
        view_count=len(plan["views"]),
        encoded_records=encoded,
        reused_views=reused,
        already_complete=False,
    )


def verify_episode(
    episode_root,
    *,
    expected_recipe_id=None,
    check_source=True,
    reencoder=None,
    atol=0.0,
    rtol=0.0,
):
    """Read-only full cache audit; actual VAE re-encoding is separately opt-in."""
    from .storage import (
        ViewReader,
        inspect_view_payload,
        open_episode_index,
        validate_payload_binding,
    )

    if any(
        type(x) not in (int, float) or not math.isfinite(x) or x < 0
        for x in (atol, rtol)
    ):
        raise CacheError("invalid explicit re-encoding tolerance")
    if reencoder is None and (atol or rtol):
        raise CacheError("tolerances apply only to explicit re-encoding")
    index = open_episode_index(episode_root, expected_recipe_id=expected_recipe_id)
    recipe = validate_recipe(index.manifest["recipe"])
    plan = None
    if check_source or reencoder is not None:
        from .source import scan_episode

        plan = scan_episode(episode_root)
        if (
            index.episode_key != plan["episode_key"]
            or index.manifest["source"] != _source_binding(plan)
            or index.manifest["states"] != plan["states"]
            or set(index.manifest["views"]) != set(plan["views"])
        ):
            raise CacheError("cache coverage/source does not match original episode")
    payloads, records = 0, 0
    max_error = 0.0
    if reencoder is not None and reencoder.descriptor() != recipe["encoder"]:
        raise CacheError("re-encoder identity differs from sealed recipe")
    for view_id, entry in index.manifest["views"].items():
        path = contained(index.cache_root, entry["path"])
        info = inspect_view_payload(path)
        validate_payload_binding(index, view_id, entry, info)
        view = (
            plan["views"][view_id]
            if plan is not None
            else info["metadata"]["view_plan"]
        )
        if _index_entry(info, view) != entry:
            raise CacheError("payload does not match sealed cache index")
        if plan is not None:
            _check_metadata(
                info["metadata"], _base_metadata(plan, recipe, view_id, view), recipe
            )
        payloads += 1
        records += info["shape"][0]
        if reencoder is not None:
            import torch

            # Budget each explicitly selected file, rather than silently raising
            # the training reader's configured limits or opening other Views.
            with ViewReader(
                index, max_views=1, max_bytes=max(1, entry["bytes"])
            ) as reader:
                for record in view["records"]:
                    actual, _ = reencoder.encode(
                        _read_rgb(plan, record), recipe["preprocessing"]
                    )
                    stored = reader.read_view(view_id, record["owner_state_id"])[
                        "latent"
                    ]
                    if (
                        not isinstance(actual, torch.Tensor)
                        or actual.device.type != "cpu"
                        or actual.dtype != torch.float32
                        or actual.shape != stored.shape
                        or not torch.isfinite(actual).all()
                    ):
                        raise CacheError(
                            "re-encoder output layout/shape/finite differs"
                        )
                    error = float((actual - stored.float()).abs().max())
                    max_error = max(max_error, error)
                    if not torch.allclose(actual, stored.float(), atol=atol, rtol=rtol):
                        raise CacheError(
                            "re-encoded latent differs from cache at explicit tolerance"
                        )
    if plan is not None:
        from .source import verify_source

        verify_source(plan)
    if reencoder is not None and reencoder.descriptor() != recipe["encoder"]:
        raise CacheError("re-encoder identity changed during comparison")
    return dict(
        episode_key=index.episode_key,
        recipe_id=index.recipe_id,
        payloads_checked=payloads,
        records_checked=records,
        source_checked=check_source or reencoder is not None,
        reencoding_checked=reencoder is not None,
        max_abs_error=max_error if reencoder is not None else None,
        atol=atol,
        rtol=rtol,
        training_ready=False,
    )
