"""DATA_C v2 indexes both independent top-View owners in one episode file."""

from __future__ import annotations

import pytest

from g2.data.aligned_provider import _select_runtime_view_refs
from g2.data.joint_index import (
    DataCError,
    _assert_dual_top,
    _state_views,
    make_joint_recipe,
)


def _top(name, *, frame=10):
    return {
        "view_id": (
            "sixview/floor_top_w_rbs" if name == "with_robot" else "sixview/floor_top"
        ),
        "top_variant": name,
        "view_scope": "floor",
        "physical_owner_frame": frame,
        "projection_id": "same_projection",
        "geometry_version": "same_geometry",
        "membership_version": "same_membership",
        "vae_recipe_id": "same_vae",
        "physical_png_sha256": "distinct_" + name,
        "record_index": 3 if name == "with_robot" else 1,
    }


def _state():
    return {
        "frame": 20,
        "selected_views": [
            {"view_id": "sixview/plus_X", "top_variant": None},
            {"view_id": "sixview/minus_Y", "top_variant": None},
        ],
        "top_views": {
            "with_robot": _top("with_robot"),
            "without_robot": _top("without_robot"),
        },
    }


def test_dual_top_recipe_is_versioned_and_variant_independent():
    old = make_joint_recipe(
        state_recipe_id="s", view_recipe_id="v", top_variant="with_robot"
    )
    new = make_joint_recipe(state_recipe_id="s", view_recipe_id="v", top_variant="both")
    assert old["schema"] == "g2_data_c_joint_recipe_v1"
    assert new["schema"] == "g2_data_c_joint_recipe_v2"
    assert new["top_variants"] == ["with_robot", "without_robot"]
    assert new["top_variant"] == "both"
    assert new != old


def test_one_index_selects_both_and_keeps_nontop_unchanged():
    state = _state()
    _assert_dual_top(state)
    all_views = _state_views(state)
    assert len(all_views) == 4
    assert len({v["view_id"] for v in all_views}) == 4
    with_robot = _select_runtime_view_refs(
        None, None, None, state, 0, top_view_variant="with_robot"
    )
    clean = _select_runtime_view_refs(
        None, None, None, state, 0, top_view_variant="without_robot"
    )
    assert len(with_robot) == len(clean) == 3
    assert with_robot[0]["view_id"] == "sixview/floor_top_w_rbs"
    assert clean[0]["view_id"] == "sixview/floor_top"
    assert with_robot[1:] == clean[1:] == tuple(state["selected_views"])
    assert with_robot[0]["physical_png_sha256"] != clean[0]["physical_png_sha256"]


@pytest.mark.parametrize(
    "fault", ("missing", "future", "projection", "membership", "duplicate")
)
def test_corrupt_dual_top_is_rejected(fault):
    state = _state()
    if fault == "missing":
        del state["top_views"]["without_robot"]
    elif fault == "future":
        state["top_views"]["without_robot"]["physical_owner_frame"] = 21
    elif fault == "projection":
        state["top_views"]["with_robot"]["projection_id"] = "different"
    elif fault == "membership":
        state["top_views"]["with_robot"]["membership_version"] = "different"
    else:
        state["selected_views"].append(_top("with_robot"))
    with pytest.raises(DataCError, match="dual top"):
        _assert_dual_top(state)


def test_v2_rejects_undefined_runtime_variant():
    with pytest.raises(DataCError, match="unknown"):
        _select_runtime_view_refs(
            None, None, None, _state(), 0, top_view_variant="both"
        )
