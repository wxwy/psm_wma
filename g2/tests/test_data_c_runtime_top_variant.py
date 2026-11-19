"""One DATA_C index serves either pre-encoded floor top without rewriting labels."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from g2.data.aligned_provider import DataCError, _select_runtime_view_refs


IDS = {
    "with_robot": "sixview/floor_top_w_rbs",
    "without_robot": "sixview/floor_top",
}


def sample(variant="with_robot"):
    base = {
        "view_id": IDS[variant],
        "top_variant": variant,
        "view_scope": "floor",
        "membership_version": "members-fixed",
        "geometry_version": "geometry-fixed",
        "projection_id": "projection-fixed",
        "vae_recipe_id": "vae-fixed",
        "physical_owner_frame": 10,
        "physical_png_sha256": "original",
        "cache_file": "one-file",
        "record_index": 0,
    }
    side = {"view_id": "sixview/plus_X", "view_scope": "room"}
    state = {
        "logical_state_id": 5,
        "frame": 20,
        "spatial_metadata_file": "state_5/spatial_metadata.json",
        "selected_views": [base, side],
    }
    return state, base, side


@pytest.mark.parametrize("variant", ("with_robot", "without_robot"))
def test_same_top_variant_keeps_exact_immutable_refs(monkeypatch, variant):
    state, base, side = sample(variant)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("existing top must not be resolved again")

    monkeypatch.setattr("g2.data.aligned_provider._owner_view", forbidden)
    refs = _select_runtime_view_refs(
        None, None, None, state, 5, top_view_variant=variant
    )
    assert refs[0] is base
    assert refs[1] is side


@pytest.mark.parametrize(
    ("saved", "requested"),
    (("with_robot", "without_robot"), ("without_robot", "with_robot")),
)
def test_both_top_variants_resolve_from_same_state(monkeypatch, saved, requested):
    state, base, side = sample(saved)
    calls = []

    def resolve(index, reader, epdir, source, ordinal, view_id, *, recipe_id):
        calls.append((source, ordinal, view_id, recipe_id))
        return {
            **base,
            "view_id": view_id,
            "top_variant": requested,
            "physical_owner_frame": 15,
            "physical_png_sha256": "alternate-real-content",
            "cache_file": "alternate-file",
            "record_index": 3,
        }

    monkeypatch.setattr("g2.data.aligned_provider._owner_view", resolve)
    refs = _select_runtime_view_refs(
        SimpleNamespace(), SimpleNamespace(), "/episode", state, 5,
        top_view_variant=requested,
    )
    assert refs[0]["view_id"] == IDS[requested]
    assert refs[0]["physical_png_sha256"] != base["physical_png_sha256"]
    assert refs[0]["record_index"] != base["record_index"]
    assert refs[1] is side
    assert state["selected_views"][0] is base
    source, ordinal, view_id, recipe_id = calls[0]
    assert source["frame"] == 20
    assert source["state_id"] == 5
    assert source["spatial_metadata"] == state["spatial_metadata_file"]
    assert source["selection"]["membership_ids"]["sixview/floor_top"] == "members-fixed"
    assert ordinal == 5
    assert view_id == IDS[requested]
    assert recipe_id == "vae-fixed"


@pytest.mark.parametrize("kind", ("geometry", "projection", "membership", "future"))
def test_variant_change_fails_closed_on_invalid_source(monkeypatch, kind):
    state, base, _ = sample()

    def invalid(*_args, **_kwargs):
        ref = {
            **base,
            "view_id": IDS["without_robot"],
            "top_variant": "without_robot",
        }
        if kind == "geometry":
            ref["geometry_version"] = "other"
        elif kind == "projection":
            ref["projection_id"] = "other"
        elif kind == "membership":
            ref["membership_version"] = "other"
        else:
            ref["physical_owner_frame"] = 21
        return ref

    monkeypatch.setattr("g2.data.aligned_provider._owner_view", invalid)
    with pytest.raises(DataCError, match="disagree|future"):
        _select_runtime_view_refs(
            None, None, None, state, 5, top_view_variant="without_robot"
        )


def test_unknown_or_ambiguous_top_is_rejected():
    state, base, _ = sample()
    with pytest.raises(DataCError, match="unknown"):
        _select_runtime_view_refs(
            None, None, None, state, 5, top_view_variant="both"
        )
    state["selected_views"].append({**base})
    with pytest.raises(DataCError, match="exactly one"):
        _select_runtime_view_refs(
            None, None, None, state, 5, top_view_variant="with_robot"
        )


def test_unavailable_alternate_is_not_silently_replaced(monkeypatch):
    state, _, _ = sample()

    def absent(*_args, **_kwargs):
        raise KeyError("clean top absent")

    monkeypatch.setattr("g2.data.aligned_provider._owner_view", absent)
    with pytest.raises(DataCError, match="absent"):
        _select_runtime_view_refs(
            None, None, None, state, 5, top_view_variant="without_robot"
        )
