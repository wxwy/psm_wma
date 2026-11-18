"""Isolated G2 initial-spatial-language unit, anti-oracle and safety tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

from g2.language.initial_context import (
    InitialLanguageError,
    InitialLanguageRecipe,
    build_initial_language,
    verify_persisted_initial_language,
    write_initial_language,
)


def _entity(eid, name, pos, room=0):
    x, y, z = pos
    return {
        "id": eid,
        "label": name,
        "source_category_id": name.casefold(),
        "room_uid": room,
        "island_id": None,
        "source_instance_id": "fixture:" + eid,
        "source_part_id": "whole",
        "bbox_min": [x - 0.1, y - 0.1, z - 0.1],
        "bbox_max": [x + 0.1, y + 0.1, z + 0.1],
    }


@pytest.fixture
def fixture():
    # The target is at x=2; GT task set happens to bind the *last* drawer,
    # which must not control candidate order or silently eliminate ambiguity.
    sg = {
        "frame_id": 0,
        "world_frame": "world",
        "semantic_on_inside": "NOT_OBSERVABLE_FROM_SOURCE_BBOX",
        "entities": [
            _entity("entity_0", "pizza_cutter", (2, 0, 1)),
            _entity("entity_7", "Drawer", (100, 0, 1)),
            _entity("entity_8", "Drawer", (1, 0, 1)),
            _entity("entity_9", "Drawer", (2.1, 0, 1)),
            _entity("entity_10", "Drawer", (2, 0, 1), room=1),
        ],
        "relations": [
            {
                "type": "contains",
                "source": "room_0",
                "target": "entity_0",
                "evidence": "native_room_query",
            }
        ],
    }
    task = {
        "schema": "g2_gt_task_entity_set_v1",
        "binding_status": "BOUND",
        "grounding": "SIMULATION_INITIALIZATION_GT",
        "roles": [
            {"role": "target", "entity_ids": ["entity_0"]},
            {"role": "source_reference", "entity_ids": ["entity_9"]},
        ],
    }
    return sg, task


def build(data, **kw):
    sg, task = data
    return build_initial_language(
        original_instruction="Pick the pizza cutter from the drawer.",
        scene_graph=sg,
        task_set=task,
        task_class="PickPlaceDrawer",
        episode_index=9,
        **kw,
    )


def test_initial_semantics_uses_real_bbox_and_retains_original(fixture):
    x = build(fixture)
    msg = x["augmented_instruction"]
    assert msg.startswith("Task: Pick the pizza cutter from the drawer.\n")
    assert "Initial spatial context (world frame; metres; episode frame 0):" in msg
    assert "pizza_cutter [entity_0]: role=target; room=R0;" in msg
    assert "bbox_center=(2.000, 0.000, 1.000); bbox_size=(0.200, 0.200, 0.200)" in msg
    assert "on top" not in msg and "inside the drawer" not in msg
    assert "contact" not in msg and "source_instance_id" not in msg
    assert len(msg) <= 4096
    assert x["training_ready"] is False
    assert x["recipe"]["production_template_frozen"] is False
    assert (
        x["scene_context"]["geometry"] == "world_axis_aligned_bbox_not_center_of_mass"
    )
    assert x == build(fixture)


def test_multi_candidate_order_geometric_not_gt_target_leak(fixture):
    x = build(fixture)
    msg = x["augmented_instruction"]
    assert (
        "Ambiguity: role=source_reference; label=Drawer; room=R0; 3 same-label" in msg
    )
    assert "Drawer [entity_10]" not in msg  # different room
    # Sorted by actual distance to unique known target, never by GT-selected
    # fixture ID; excludes arbitrary incorrect 'Drawer contains cutter' facts.
    assert msg.index("Drawer [entity_9]") < msg.index("Drawer [entity_8]")
    assert msg.index("Drawer [entity_8]") < msg.index("Drawer [entity_7]")
    assert "gt_bound_entity_ids_for_audit_only" not in msg
    assert x["scene_context"]["ambiguity"][0]["gt_bound_entity_ids_for_audit_only"] == [
        "entity_9"
    ]


def test_budget_cap_explicit_omission_with_no_truncated_fact(fixture):
    small = InitialLanguageRecipe(max_characters=500, max_candidates_per_group=2)
    x = build(fixture, recipe=small)
    assert x["scene_context"]["number_of_omitted_facts"] >= 1
    assert "omitted by candidate cap/budget" in x["augmented_instruction"]
    assert x["augmented_instruction"].endswith(".")
    with pytest.raises(InitialLanguageError, match="budget"):
        build(fixture, recipe=InitialLanguageRecipe(max_characters=128))


def test_refuse_future_sg_unknown_roles_and_bad_geometry(fixture):
    sg, task = fixture
    modified = deepcopy(sg)
    modified["frame_id"] = 10
    with pytest.raises(InitialLanguageError, match="frame-0"):
        build((modified, task))
    modified = deepcopy(sg)
    modified["world_frame"] = "room"
    with pytest.raises(InitialLanguageError, match="world"):
        build((modified, task))
    modified = deepcopy(sg)
    modified["entities"][0]["bbox_max"][0] = float("nan")
    with pytest.raises(InitialLanguageError, match="bbox"):
        build((modified, task))
    modified = deepcopy(task)
    modified["binding_status"] = "UNBOUND"
    with pytest.raises(InitialLanguageError, match="unbound"):
        build((sg, modified))
    modified = deepcopy(task)
    modified["roles"][0]["entity_ids"] = ["entity_99"]
    with pytest.raises(InitialLanguageError, match="absent"):
        build((sg, modified))


def test_recipe_changes_text_id_and_unknown_freeze_rejected(fixture):
    x = build(fixture)
    y = build(fixture, recipe=InitialLanguageRecipe(decimal_places=2))
    assert x["text_id"] != y["text_id"]
    assert x["recipe"]["recipe_id"] != y["recipe"]["recipe_id"]
    with pytest.raises(InitialLanguageError, match="recipe"):
        InitialLanguageRecipe(production_template_frozen=True)


def test_independent_atomic_writer_and_verified_resume(fixture, tmp_path):
    x = build(fixture)
    root = tmp_path / "language"
    a = write_initial_language(root, x)
    b = write_initial_language(root, x)
    assert a == b
    assert a["training_ready"] is False
    assert "/recipes/" in a["path"]
    assert "initial_context.json" in a["path"]
    with pytest.raises(FileExistsError):
        write_initial_language(root, x, resume=False)
    changed = deepcopy(x)
    changed["augmented_instruction"] += " Tamper."
    with pytest.raises(InitialLanguageError, match="does not match"):
        verify_persisted_initial_language(root, changed)
    from pathlib import Path

    with Path(a["path"]).open("ab") as f:
        f.write(b"unauthorized")
    with pytest.raises(InitialLanguageError, match="match"):
        verify_persisted_initial_language(root, x)


def test_no_silent_unknown_schema_or_bad_source_role(fixture):
    sg, task = fixture
    bad = deepcopy(task)
    bad["schema"] = "future-task"
    with pytest.raises(InitialLanguageError, match="schema"):
        build((sg, bad))
    bad = deepcopy(task)
    bad["roles"][1]["role"] = ""
    with pytest.raises(InitialLanguageError, match="role"):
        build((sg, bad))
    bad = deepcopy(sg)
    bad["entities"][2]["id"] = bad["entities"][1]["id"]
    with pytest.raises(InitialLanguageError, match="duplicate"):
        build((bad, task))


def test_island_string_and_unknown_room_are_explicit(fixture):
    sg, task = deepcopy(fixture)
    sg["entities"][0]["island_id"] = "island_0_entity_0"
    sg["entities"][0]["room_uid"] = -1
    # Source role still links the same SG entity, now Room is unknown.
    x = build((sg, task))
    assert "room=unknown; island=island_0_entity_0" in x["augmented_instruction"]
    assert "room=R-1" not in x["augmented_instruction"]


def test_two_recipes_coexist_without_overwriting_same_episode(fixture, tmp_path):
    from g2.language.initial_context import (
        read_versioned_initial_language,
        InitialLanguageRecipe,
    )
    from g2.data.episode_state import atomic_write_json, digest, canonical

    root = tmp_path / "language"
    src = "a" * 64
    for cap in (2, 3):
        recipe = InitialLanguageRecipe(max_candidates_per_group=cap)
        entry = build(fixture, recipe=recipe)
        entry["provenance"] = {"g1_source_binding_digest": src}
        if cap == 2:
            old = entry
        else:
            new = entry
        atomic_write_json(
            root / "OUTPUT_IDENTITY.json",
            {
                "schema": "g2_independent_language_root_v2",
                "source_binding_digest": src,
                "training_ready": False,
            },
        )
        atomic_write_json(
            root / "recipes" / recipe.recipe_id / "RECIPE.json",
            {
                "schema": "g2_initial_language_recipe_declaration_v1",
                "source_binding_digest": src,
                "recipe": recipe.to_dict(),
                "training_ready": False,
            },
        )
        write_initial_language(root, entry)
    oldpath = (
        root
        / "recipes"
        / old["recipe"]["recipe_id"]
        / "tasks"
        / "PickPlaceDrawer"
        / "episodes"
        / "episode_000009"
        / "initial_context.json"
    )
    old_hash = digest(oldpath)
    for entry in (old, new):
        found = read_versioned_initial_language(
            root,
            recipe_id=entry["recipe"]["recipe_id"],
            task_class="PickPlaceDrawer",
            episode_index=9,
            source_binding_digest=src,
            original_instruction=entry["original_instruction"],
        )
        assert found == entry
        assert found["training_ready"] is False
    assert digest(oldpath) == old_hash
    with pytest.raises(InitialLanguageError, match="source binding"):
        read_versioned_initial_language(
            root,
            recipe_id=old["recipe"]["recipe_id"],
            task_class="PickPlaceDrawer",
            episode_index=9,
            source_binding_digest="b" * 64,
            original_instruction=old["original_instruction"],
        )
    with pytest.raises(InitialLanguageError, match="recipe ID"):
        read_versioned_initial_language(
            root,
            recipe_id="../",
            task_class="PickPlaceDrawer",
            episode_index=9,
            source_binding_digest=src,
            original_instruction=old["original_instruction"],
        )
    assert canonical({"a": 1}) != "b" * 64
