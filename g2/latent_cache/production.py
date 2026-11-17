"""Stage-A shared-core finalization, independent of renderers and VAE loading."""

from __future__ import annotations

from pathlib import Path

from g2.io import digest, read_json

from .contract import CacheError, contained
from .storage import atomic_json, build_lock


def target_lock(root):
    root = Path(root).absolute()
    return root.parent / (".stage-a-vae-lock-" + root.name)


def cache_receipt(root):
    from .builder import verify_episode
    from .sealed_source import scan_source
    from .storage import open_episode_index

    # Full tensor audit and sealed-source/owner check, without loading VAE.
    audit = verify_episode(root, check_source=False)
    plan = scan_source(root)
    index = open_episode_index(root)
    from .builder import _source_binding

    if (
        index.manifest["source"] != _source_binding(plan)
        or index.manifest["states"] != plan["states"]
        or set(index.manifest["views"]) != set(plan["views"])
    ):
        raise CacheError("final cache coverage/source differs")
    from .builder import _base_metadata, _check_metadata
    from .storage import inspect_view_payload

    for vid, view in plan["views"].items():
        info = inspect_view_payload(contained(index.cache_root, view["path"]))
        _check_metadata(
            info["metadata"],
            _base_metadata(plan, index.manifest["recipe"], vid, view),
            index.manifest["recipe"],
        )
    from . import final_source as final

    source = final.load_source(root)
    is_final = source["schema"] == final.SOURCE_SCHEMA
    return dict(
        schema="g2_verified_profile_vae_v2"
        if is_final
        else "g2_verified_profile_vae_v1",
        verified=True,
        source_id=source["source_id"],
        profile_id=source["profile_id"],
        cache_manifest_sha256=digest(index.cache_root / "manifest.json"),
        cache_complete_sha256=digest(index.cache_root / "COMPLETE.json"),
        recipe_id=index.recipe_id,
        views=audit["payloads_checked"],
        records=audit["records_checked"],
        **(
            dict(source_index_sha256=digest(contained(root, final.CAPSULE)))
            if is_final
            else {}
        ),
    )


def publish_profile(root):
    """Cache first, final profile second; no circular hash and no fake COMPLETE."""
    from g2.offline.output_profile import SCHEMA, OutputProfile, completion
    from g2.offline.stage_a import validate_profile_episode

    root = Path(root)
    manifest = validate_profile_episode(root, require_complete=False)
    from .final_source import PROFILE_SCHEMA

    if manifest["schema"] == PROFILE_SCHEMA:
        return manifest
    profile = OutputProfile.from_dict(manifest["output_profile"])
    if not profile.view_vae:
        raise CacheError("profile does not declare VAE")
    receipt = cache_receipt(root)
    manifest["products"]["view_vae"] = "ready"
    manifest["vae_receipt"] = receipt
    manifest.update(
        completion(
            profile,
            manifest["products"],
            source_sealed=manifest["source_id"],
            vae_receipt=receipt,
        )
    )
    if not manifest["profile_complete"]:
        raise CacheError("other required profile artifacts are pending")
    if (root / "COMPLETE.json").exists():
        validate_profile_episode(root)
        (root / "VAE_PROFILE_PUBLISH_PENDING.json").unlink(missing_ok=True)
        return manifest
    import hashlib
    import json

    next_sha = hashlib.sha256(
        (
            json.dumps(
                manifest, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
            )
            + "\n"
        ).encode("utf-8")
    ).hexdigest()
    prepared = dict(
        schema="g2_vae_profile_publish_pending_v1",
        source_id=manifest["source_id"],
        next_manifest_sha256=next_sha,
        cache_receipt=receipt,
    )
    journal = root / "VAE_PROFILE_PUBLISH_PENDING.json"
    if journal.exists():
        if read_json(contained(root, journal.name)) != prepared:
            raise CacheError("profile publication transaction differs")
    else:
        atomic_json(journal, prepared)
    atomic_json(root / "episode_manifest.json", manifest, replace=True)
    atomic_json(
        root / "COMPLETE.json",
        dict(
            schema=SCHEMA,
            episode_id=manifest["episode_id"],
            state_count=manifest["state_count"],
            source_id=manifest["source_id"],
            episode_manifest_sha256=digest(root / "episode_manifest.json"),
            complete=True,
        ),
    )
    validate_profile_episode(root)
    journal.unlink()
    from .storage import _fsync_directory

    _fsync_directory(root)
    return manifest


def cleanup_inputs(root):
    """Only own PNG-disabled input namespace; release durable before unlink."""
    from g2.offline.stage_a import validate_profile_episode

    from .sealed_source import released_inputs
    from .storage import _fsync_directory

    root = Path(root)
    validate_profile_episode(root)
    from .final_source import PROFILE_SCHEMA

    if read_json(contained(root, "episode_manifest.json"))["schema"] == PROFILE_SCHEMA:
        return dict(
            released_inputs=0,
            source_id=read_json(contained(root, "episode_manifest.json"))["source_id"],
        )
    receipt = cache_receipt(root)
    source = read_json(contained(root, "spatial_source.json"))
    files = {
        o["path"]: o["sha256"]
        for v in source["views"].values()
        for o in v["owners"]
        if o["path"] and o["path"].startswith("_spatial_inputs/")
    }
    release = dict(
        schema="g2_released_vae_inputs_v1",
        source_id=source["source_id"],
        cache_manifest_sha256=receipt["cache_manifest_sha256"],
        files=files,
    )
    path = root / "VAE_INPUT_RELEASE.json"
    if path.exists():
        if read_json(contained(root, path.name)) != release:
            raise CacheError("release identity differs; refuse cleanup")
    else:
        atomic_json(path, release)
    released_inputs(root, source)
    for rel, sha in sorted(files.items()):
        path = contained(root, rel, allow_missing=True)
        if path.exists():
            if digest(path) != sha:
                raise CacheError("input changed before cleanup; retain it")
            path.unlink()
            _fsync_directory(path.parent)
    validate_profile_episode(root)
    return dict(released_inputs=len(files), source_id=source["source_id"])


def build_profile(
    root,
    encoder,
    *,
    preprocessing=None,
    storage_dtype="float32",
    batch_size=1,
    resume=False,
    record_provider=None,
    cleanup=False,
):
    from .builder import build_episode

    with build_lock(target_lock(root)):
        from g2.offline.output_profile import OutputProfile

        profile = OutputProfile.from_dict(
            read_json(contained(root, "episode_manifest.json"))["output_profile"]
        )
        if not profile.view_vae:
            raise CacheError(
                "profile does not declare VAE; never rewrite its output configuration"
            )
        result = build_episode(
            root,
            encoder,
            preprocessing=preprocessing,
            storage_dtype=storage_dtype,
            batch_size=batch_size,
            resume=resume,
            _record_provider=record_provider,
        )
        publish_profile(root)
        if cleanup:
            cleanup_inputs(root)
        return dict(result, profile_complete=True)
