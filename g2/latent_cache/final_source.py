"""Small, explicit final source v2 contract. JSON-only lazy-reader verification.

The working seal's hashes are historical provenance, never recomputed for a
retired file. Numeric payloads retain their original immutable source header.
"""

from __future__ import annotations

import copy
from pathlib import Path

from g2.io import digest, read_json

from .contract import CacheError, contained, fingerprint

SOURCE_SCHEMA = "g2_final_spatial_source_v2"
CAPSULE_SCHEMA = "g2_spatial_source_index_v2"
PROFILE_SCHEMA = "g2_spatial_profile_episode_v2"
INDEX_SCHEMA = "g2_spatial_view_vae_index_v2"
COMPLETE_SCHEMA = "g2_spatial_view_vae_complete_v2"
RECEIPT_SCHEMA = "g2_spatial_source_retirement_v2"
CAPSULE = "spatial_source_index.json"
READY = "SPATIAL_SOURCE_FINAL_READY.json"
RECEIPT = "SOURCE_RETIREMENT.json"
JOURNAL = ".source_retirement/transaction.json"
FULL = "spatial_source.json"


def payload_source(source):
    return source["working_source"] if source.get("schema") == SOURCE_SCHEMA else source


def product_identity(manifest):
    return fingerprint(
        {
            k: manifest[k]
            for k in (
                "episode_id",
                "task_class",
                "source_fingerprint",
                "source_id",
                "output_profile",
                "states",
                "files",
            )
        }
    )


def minimum_projection(raw):
    from g2.offline.spatial_metadata import projection_from_renderer

    keys = (
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
        "coordinate_frame",
        "room_bounds_min",
        "room_bounds_max",
        "depth_kind",
    )
    result = {k: copy.deepcopy(raw[k]) for k in keys if k in raw}
    if projection_from_renderer(result) != projection_from_renderer(raw):
        raise CacheError("projection information would be lost during retirement")
    return result


def compact_views(source):
    projections = {}
    views = {}
    for vid, view in source["views"].items():
        owners = []
        for owner in view["owners"]:
            projection = minimum_projection(owner["projection"])
            pid = fingerprint(projection)
            projections[pid] = projection
            owners.append(
                dict(
                    {k: v for k, v in owner.items() if k != "projection"},
                    projection_ref=pid,
                )
            )
        views[vid] = dict(view, owners=owners)
    return views, projections


def load_capsule(root):
    capsule = read_json(contained(root, CAPSULE), limit=1024 * 1024)
    if (
        not isinstance(capsule, dict)
        or not isinstance(capsule.get("attestation"), dict)
        or type(capsule.get("episode_id")) is not int
        or capsule["episode_id"] < 0
    ):
        raise CacheError("invalid final source capsule fields")
    if (
        capsule.get("schema") != CAPSULE_SCHEMA
        or capsule.get("capsule_id")
        != fingerprint({k: v for k, v in capsule.items() if k != "capsule_id"})
        or capsule.get("attestation_id") != fingerprint(capsule.get("attestation"))
    ):
        raise CacheError("invalid final source capsule identity")
    working = capsule.get("working_source", {})
    scope = capsule.get("attestation", {}).get("scope", {})
    if (
        working.get("schema") != "g2_sealed_spatial_source_v1"
        or working.get("source_id") != capsule.get("source_id")
        or capsule.get("episode_key")
        != f"{capsule.get('task_class')}/episode_{capsule.get('episode_id', -1):06d}"
        or any(
            scope.get(k) != capsule.get(k)
            for k in ("episode_key", "source_fingerprint", "profile_id", "recipe_id")
        )
        or capsule.get("attestation", {}).get("job_id") != fingerprint(scope)
        or capsule.get("working_readiness", {}).get("source_id")
        != capsule.get("source_id")
        or capsule.get("working_readiness", {}).get("source_manifest_sha256")
        != working.get("manifest_sha256")
    ):
        raise CacheError("final capsule working provenance/scope differs")
    return capsule


def source_binding(capsule, root):
    return dict(
        schema=SOURCE_SCHEMA,
        source_id=capsule["source_id"],
        capsule_id=capsule["capsule_id"],
        manifest_sha256=digest(contained(root, CAPSULE)),
        complete_sha256=digest(contained(root, READY)),
        identity_manifest=CAPSULE,
        readiness_marker=READY,
        validation_scope="VERIFIED_FINAL_CAPSULE_RETIRED_WORKING_AUDIT",
        working_source=capsule["working_source"],
    )


def verify_reader_binding(root, source, cache_manifest, cache_complete):
    """Hash only small indices/receipts; no PNG, SG, PT or renderer read."""
    capsule = load_capsule(root)
    ready = read_json(contained(root, READY))
    receipt = read_json(contained(root, RECEIPT))
    complete = read_json(contained(root, "COMPLETE.json"))
    if not isinstance(receipt, dict) or set(receipt) != {
        "schema",
        "source_id",
        "episode_key",
        "recipe_id",
        "attestation_id",
        "capsule_sha256",
        "working_proof",
        "work_cleanup",
        "final_files",
        "retired_files",
        "full_audit_archive",
        "source_disposition",
    }:
        raise CacheError("unknown final retirement receipt fields")
    if (
        fingerprint(receipt["working_proof"])
        != capsule["attestation"]["working_proof_sha256"]
        or fingerprint(receipt["work_cleanup"])
        != capsule["attestation"]["work_cleanup_sha256"]
        or receipt["retired_files"]
        != {
            FULL: capsule["working_source"]["manifest_sha256"],
            "SPATIAL_SOURCE_READY.json": capsule["working_source"]["complete_sha256"],
        }
        or receipt["full_audit_archive"] != capsule["full_audit_archive"]
        or receipt["source_disposition"]
        != "REMOVED_ONLY_AFTER_VERIFIED_FINAL_SOURCE_PUBLICATION"
    ):
        raise CacheError("retirement provenance differs from final capsule")
    if set(complete) != {
        "schema",
        "episode_id",
        "state_count",
        "source_id",
        "episode_manifest_sha256",
        "complete",
        "source_index_sha256",
        "source_retirement_sha256",
    }:
        raise CacheError("unknown final source completion fields")
    expected = source_binding(capsule, root)
    expected["view_index_sha256"] = capsule["working_source"]["view_index_sha256"]
    if source != expected:
        raise CacheError("cache final source binding differs from capsule")
    if (
        ready
        != dict(
            schema=SOURCE_SCHEMA,
            source_id=capsule["source_id"],
            capsule_id=capsule["capsule_id"],
            source_manifest_sha256=source["manifest_sha256"],
            attestation_id=capsule["attestation_id"],
            complete_source_index=True,
        )
        or receipt.get("schema") != RECEIPT_SCHEMA
        or receipt.get("attestation_id") != capsule["attestation_id"]
        or receipt.get("capsule_sha256") != source["manifest_sha256"]
        or receipt.get("source_id") != capsule["source_id"]
        or receipt.get("episode_key") != cache_manifest["episode_key"]
        or receipt.get("recipe_id") != cache_manifest["recipe"]["recipe_id"]
        or complete.get("schema") != PROFILE_SCHEMA
        or complete.get("complete") is not True
        or complete.get("source_retirement_sha256") != digest(contained(root, RECEIPT))
        or complete.get("source_index_sha256") != source["manifest_sha256"]
        or complete.get("source_id") != capsule["source_id"]
        or complete.get("episode_id") != capsule["episode_id"]
        or complete.get("state_count") != len(cache_manifest["states"])
        or cache_complete.get("source_index_sha256") != source["manifest_sha256"]
        or cache_complete.get("attestation_id") != capsule["attestation_id"]
    ):
        raise CacheError("final source/cache/profile receipt chain differs")
    files = receipt.get("final_files", {})
    for rel in (CAPSULE, READY, "vae_cache/manifest.json", "vae_cache/COMPLETE.json"):
        if files.get(rel) != digest(contained(root, rel)):
            raise CacheError("final source receipt file hash differs: " + rel)
    if (
        complete.get("episode_manifest_sha256") != files.get("episode_manifest.json")
        or capsule["recipe_id"] != cache_manifest["recipe"]["recipe_id"]
        or capsule["numeric_inventory_sha256"]
        != fingerprint(
            dict(states=cache_manifest["states"], views=cache_manifest["views"])
        )
        or capsule["episode_key"] != cache_manifest["episode_key"]
    ):
        raise CacheError("final source numeric inventory/scope differs")
    if (Path(root) / FULL).exists() or (Path(root) / FULL).is_symlink():
        raise CacheError("final capsule still has an unretired full source")
    return capsule


def materialize_source(root, manifest):
    """Restore only verifier-required fields; large audit payload is never read."""
    capsule = load_capsule(root)
    if (
        manifest.get("schema") != PROFILE_SCHEMA
        or manifest.get("source_format") != SOURCE_SCHEMA
        or manifest.get("source_index_sha256") != digest(contained(root, CAPSULE))
        or capsule["product_inventory_sha256"] != product_identity(manifest)
        or any(
            capsule[k] != manifest[k]
            for k in ("source_id", "episode_id", "task_class", "source_fingerprint")
        )
        or capsule["profile_id"]
        != fingerprint(
            {k: v for k, v in manifest["output_profile"].items() if k != "profile_id"}
        )
    ):
        raise CacheError("final source/product manifest identity differs")
    views = {}
    for vid, view in capsule["views"].items():
        owners = []
        for owner in view["owners"]:
            pid = owner["projection_ref"]
            projection = capsule["projections"].get(pid)
            if (
                projection is None
                or fingerprint(projection) != pid
                or minimum_projection(projection) != projection
            ):
                raise CacheError("final projection table differs")
            owners.append(
                dict(
                    {k: v for k, v in owner.items() if k != "projection_ref"},
                    projection=projection,
                )
            )
        views[vid] = dict(view, owners=owners)
    return dict(
        schema=SOURCE_SCHEMA,
        source_id=capsule["source_id"],
        episode_id=capsule["episode_id"],
        task_class=capsule["task_class"],
        source_fingerprint=capsule["source_fingerprint"],
        profile_id=capsule["profile_id"],
        world_frame=capsule["world_frame"],
        states=manifest["states"],
        files=manifest["files"],
        views=views,
        source_inputs_sha256=capsule["source_inputs_sha256"],
        final_pixel_events=capsule["final_pixel_events"],
    )


def validate_profile_header(root, manifest):
    cache = read_json(contained(root, "vae_cache/manifest.json"))
    complete = read_json(contained(root, "vae_cache/COMPLETE.json"))
    if cache.get("schema") != INDEX_SCHEMA or complete.get("schema") != COMPLETE_SCHEMA:
        raise CacheError("final profile requires v2 cache indices")
    capsule = verify_reader_binding(root, cache["source"], cache, complete)
    receipt = read_json(contained(root, RECEIPT))
    if receipt["final_files"].get("episode_manifest.json") != digest(
        contained(root, "episode_manifest.json")
    ):
        raise CacheError("final profile manifest changed after retirement")
    return materialize_source(root, manifest), capsule


def load_source(root):
    manifest = read_json(contained(root, "episode_manifest.json"))
    if manifest.get("schema") == PROFILE_SCHEMA:
        return materialize_source(root, manifest)
    from g2.offline.view_only_source import load_working_source

    return load_working_source(root)[0]


def working_source_sha(root):
    manifest = read_json(contained(root, "episode_manifest.json"))
    if manifest.get("schema") == PROFILE_SCHEMA:
        working = load_capsule(root)["working_source"]
        return working.get("raw_source_sha256", working["manifest_sha256"])
    from g2.offline.view_only_source import load_working_source

    return load_working_source(root)[1]
