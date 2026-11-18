"""Versioned numerical identity for true B1..32/T1 batches, not legacy B1."""

from __future__ import annotations

import copy

from .contract import (
    CacheError,
    fingerprint,
    preprocessing_recipe,
    safe_relative,
    validate_preprocessing,
)

RECIPE_SCHEMA = "g2_spatial_view_vae_batch_recipe_v2"
ENCODER_SCHEMA = "g2_spatial_wan_batch_t1_v1"
CONTEXT_SCHEMA = "g2_spatial_vae_batch_execution_v1"
NUMERICS = dict(
    cudnn_deterministic=True,
    cudnn_benchmark=False,
    allow_tf32=False,
    deterministic_algorithms=True,
    cublas_workspace_config=":4096:8",
    replay="SAME_ORDERED_BATCH_EXACT_OR_FAIL",
    oom="FAIL_RETAIN_FIXED_BATCH_NO_IMPLICIT_SPLIT",
)


def is_batch(recipe):
    return isinstance(recipe, dict) and recipe.get("schema") == RECIPE_SCHEMA


def make_batch_recipe(
    encoder, preprocessing=None, *, max_batch_size=32, storage_dtype="float32"
):
    if type(max_batch_size) is not int or not 1 <= max_batch_size <= 32:
        raise CacheError("actual per-GPU maximum batch must be in1..32")
    prep = preprocessing_recipe() if preprocessing is None else preprocessing
    validate_preprocessing(prep)
    if (prep["height"], prep["width"]) != (256, 256) or storage_dtype != "float32":
        raise CacheError("batch recipe requires256x256 and full FP32 latent storage")
    if not isinstance(encoder, dict) or encoder.get("schema") != ENCODER_SCHEMA:
        raise CacheError("batch recipe requires the explicit batch encoder identity")
    if (
        encoder.get("max_batch_size") != max_batch_size
        or encoder.get("numerics") != NUMERICS
    ):
        raise CacheError("batch numerical policy differs from the encoder")
    value = dict(
        schema=RECIPE_SCHEMA,
        encoder=copy.deepcopy(encoder),
        preprocessing=copy.deepcopy(prep),
        storage_dtype=storage_dtype,
        batch_size=max_batch_size,
        independent_frames=True,
        input_layout="BCTHW",
        input_shape=["B", 3, 1, 256, 256],
        actual_batch_range=[1, max_batch_size],
        record_layout="CHW",
        record_shape=[48, 16, 16],
        view_layout="UCHW",
        batch_context_required=True,
        numerics=copy.deepcopy(NUMERICS),
    )
    value["recipe_id"] = fingerprint(value)
    return value


def validate_batch_recipe(value):
    try:
        rebuilt = make_batch_recipe(
            value["encoder"],
            value["preprocessing"],
            max_batch_size=value["batch_size"],
            storage_dtype=value["storage_dtype"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise CacheError("invalid batch recipe") from exc
    if value != rebuilt:
        raise CacheError("batch recipe fingerprint differs")
    return value


def make_context(recipe, members):
    validate_batch_recipe(recipe)
    if not isinstance(members, list) or not 1 <= len(members) <= recipe["batch_size"]:
        raise CacheError("batch membership exceeds the declared numerical recipe")
    seen = set()
    for member in members:
        if not isinstance(member, dict) or set(member) != {"job", "event"}:
            raise CacheError(
                "batch member must preserve its actual job and final event"
            )
        _hash(member["job"])
        event_identity(member["event"])
        key = (member["job"], member["event"]["event_id"])
        if key in seen:
            raise CacheError("duplicate batch member")
        seen.add(key)
    value = dict(
        schema=CONTEXT_SCHEMA,
        recipe_id=recipe["recipe_id"],
        members=copy.deepcopy(members),
        input_shape=[len(members), 3, 1, 256, 256],
    )
    value["batch_id"] = fingerprint(value)
    return value


def _hash(value):
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise CacheError("batch source identity must be SHA256")


def event_identity(event):
    """JSON-only replay identity. Admission still uses the original pixel validator.

    Selected-View readers must not import a producer, queue, renderer or VAE.
    Here they verify the recorded event hash/phase/path and ordered pixel hashes.
    """
    fields = {
        "event_id",
        "episode_key",
        "view_id",
        "canonical_view_id",
        "variant",
        "rgb_sha256",
        "final_pixel_phase",
        "source_fingerprint",
        "profile_id",
        "pixel_record_key",
        "size_wh",
    }
    if not isinstance(event, dict) or set(event) != fields:
        raise CacheError("unknown batch event identity fields")
    for key in (
        "event_id",
        "rgb_sha256",
        "source_fingerprint",
        "profile_id",
        "pixel_record_key",
    ):
        _hash(event[key])
    for key in ("episode_key", "view_id", "canonical_view_id"):
        safe_relative(event[key])
    identity = {
        k: event[k]
        for k in (
            "episode_key",
            "view_id",
            "rgb_sha256",
            "source_fingerprint",
            "profile_id",
        )
    }
    marked = event["view_id"].endswith("_w_rbs")
    if (
        event["event_id"] != fingerprint(identity)
        or event["pixel_record_key"]
        != fingerprint(dict(view_id=event["view_id"], rgb_sha256=event["rgb_sha256"]))
        or event["canonical_view_id"]
        != (event["view_id"][:-6] if marked else event["view_id"])
        or event["variant"] != ("w_rbs" if marked else "clean")
        or event["final_pixel_phase"]
        != ("FINAL_MARKER_PIXELS" if marked else "FINAL_CLEAN_PIXELS")
    ):
        raise CacheError("batch event source/variant/final-pixel hash differs")
    if (
        not isinstance(event["size_wh"], list)
        or len(event["size_wh"]) != 2
        or any(type(v) is not int or v < 1 for v in event["size_wh"])
    ):
        raise CacheError("invalid batch pixel dimensions")


def validate_context(context, recipe):
    try:
        rebuilt = make_context(recipe, context["members"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CacheError("invalid numerical batch context") from exc
    if rebuilt != context:
        raise CacheError("batch member/order/context fingerprint differs")
    return context


def record_path(context, position):
    if type(position) is not int or not 0 <= position < len(context["members"]):
        raise CacheError("batch record position outside immutable membership")
    return f"records/{context['batch_id']}/{position:02d}.pt"


def pack_metadata(base, preprocessing, recipe):
    """Deduplicate full batch membership once per View; each record holds a ref."""
    if not is_batch(recipe):
        return dict(base, preprocessing=preprocessing)
    catalog, rows = {}, []
    for original in preprocessing:
        prep = copy.deepcopy(original)
        context = prep.pop("_batch_context")
        validate_context(context, recipe)
        key = context["batch_id"]
        if key in catalog and catalog[key] != context:
            raise CacheError("conflicting numerical execution contexts")
        catalog[key] = context
        rows.append(prep)
    metadata = dict(base, preprocessing=rows, batch_executions=catalog)
    validate_metadata(metadata, recipe)
    return metadata


def unpack_prep(metadata, position):
    prep = copy.deepcopy(metadata["preprocessing"][position])
    prep["_batch_context"] = copy.deepcopy(
        metadata["batch_executions"][prep["numerical_execution"]["batch_id"]]
    )
    return prep


def validate_metadata(metadata, recipe):
    if not is_batch(recipe):
        return
    catalog = metadata.get("batch_executions")
    if not isinstance(catalog, dict) or not catalog:
        raise CacheError("batch payload is missing its numerical membership catalog")
    for key, context in catalog.items():
        validate_context(context, recipe)
        if key != context["batch_id"]:
            raise CacheError("batch catalog key differs")
    used = set()
    for record, prep in zip(
        metadata["view_plan"]["records"], metadata["preprocessing"], strict=True
    ):
        execution = prep.get("numerical_execution", {})
        context = catalog.get(execution.get("batch_id"))
        position = execution.get("position")
        if (
            context is None
            or type(position) is not int
            or not 0 <= position < len(context["members"])
        ):
            raise CacheError("record has no valid numerical batch position")
        event = context["members"][position]["event"]
        origin = execution.get("origin", {})
        if (
            not isinstance(origin, dict)
            or not origin.get("worker")
            or not origin.get("attempt")
            or not origin.get("physical_gpu")
            or not isinstance(origin.get("device"), dict)
            or origin.get("encoder_descriptor_sha256") != fingerprint(recipe["encoder"])
        ):
            raise CacheError("batch record is missing its actual numerical origin")
        kind = origin["device"].get("kind")
        if kind != ("TEST_ONLY_CPU" if recipe["encoder"].get("test_only") else "cuda"):
            raise CacheError("numerical origin cannot relabel CPU fixture as real GPU")
        if (
            event["view_id"] != metadata["view_id"]
            or event["rgb_sha256"] != record["png_sha256"]
            or prep.get("vae_input_shape") != context["input_shape"]
            or prep.get("latent_shape") != [48, 16, 16]
            or prep.get("latent_dtype") != "float32"
            or execution.get("actual_batch_size") != len(context["members"])
        ):
            raise CacheError("batch input/owner/full latent layout differs")
        if not metadata["episode_key"].startswith("pixel/") and (
            event["episode_key"] != metadata["episode_key"]
            or event["event_id"] != record.get("event_id")
        ):
            raise CacheError(
                "batch member belongs to another episode or physical owner"
            )
        used.add(context["batch_id"])
    if used != set(catalog):
        raise CacheError("unreferenced batch history in selected View payload")
