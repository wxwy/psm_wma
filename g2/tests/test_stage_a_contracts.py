"""Stage-A contracts: explicit profiles, current facts and exact task identities."""

import copy
from dataclasses import replace

import pytest

from g2.io import ContractError
from g2.offline.language_context import (
    LanguageRecipe,
    TextBank,
    enhance_caption,
    resolve_caption_rows,
)
from g2.offline.output_profile import PRODUCTS, OutputProfile, completion
from g2.offline.spatial_metadata import (
    projection_from_renderer,
    select_views,
    state_metadata,
    validate_raw_pose,
)
from g2.offline.task_entities import FIXTURE_RULES, OBJECT_RULES, bind_task_entities
from g2.tests.test_stage_a_package import stage_case
from g2.views.render_connections import renderer_member_sets
from g2.views.robot_pose_marker import project


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"selection_top_variant": "other"},
        {"selection_top_variant": "clean", "scene_graph": False},
        {"selection_top_variant": "w_rbs", "marker_variants": False},
        {"selection": False, "language": True, "task_entities": False},
        {"selection": False, "view_vae": True, "spatial_metadata": False},
        {"selection": False, "sixview_png": 1},
    ],
)
def test_profiles_reject_implicit_or_inconsistent_dependencies(changes):
    with pytest.raises(ContractError):
        OutputProfile(**changes)


def test_source_projection_matches_marker_with_translated_rotated_room():
    from g2.tests.test_robot_pose_marker import _meta, _pose

    meta = _meta()
    meta.update(forward_world=[0, 0, -1], native_entity_ids=["entity_0"])
    serialized = projection_from_renderer(meta)
    col, row, _, _ = project(meta, _pose())
    u = serialized["uv_min_room"][0] + (col + 0.5) * serialized["meters_per_pixel"]
    v = (
        serialized["uv_min_room"][1]
        + (serialized["height_px"] - row - 0.5) * serialized["meters_per_pixel"]
    )
    assert (u, v) == pytest.approx((1.0, -0.5))
    assert serialized["reference_frame"]["origin_world"] == [10, 20, 0]
    assert serialized["physical_width_m"] == pytest.approx(4.2)
    pose = dict(_pose(), frame=200, source_frame=200, coordinate_frame="world")
    assert validate_raw_pose(pose, frame=200, world_frame="world") == pose
    with pytest.raises(ContractError, match="provenance"):
        validate_raw_pose(pose, frame=201, world_frame="world")
    with pytest.raises(ContractError, match="invalid"):
        validate_raw_pose(
            dict(pose, forward_world=[0, 0, 0]), frame=200, world_frame="world"
        )


def test_profile_identity_states_and_no_queue_as_complete():
    profile = OutputProfile(selection_top_variant="both", view_vae=True)
    assert OutputProfile.from_dict(profile.to_dict()) == profile
    statuses = {p: "ready" for p in PRODUCTS}
    statuses["view_vae"] = "pending"
    result = completion(profile, statuses, source_sealed="a" * 64)
    assert result["source_ready"] and not result["profile_complete"]
    statuses["language"] = "absent"
    with pytest.raises(ContractError, match="structured"):
        completion(profile, statuses, source_sealed="a" * 64)
    statuses["language"] = "ready"
    with pytest.raises(ContractError, match="SHA256"):
        completion(profile, statuses, source_sealed=True)
    changed = profile.to_dict()
    changed["robot_pose"] = False
    with pytest.raises(ContractError, match="identity"):
        OutputProfile.from_dict(changed)


@pytest.mark.parametrize("task", sorted(FIXTURE_RULES))
def test_all_18_tasks_bind_all_parts_and_exclude_distractors(task):
    fixtures, refs, objects, entities = {}, {}, [], []
    expected = set()
    for i, (role, key, classes) in enumerate(FIXTURE_RULES[task]):
        name = "fixture_" + str(i)
        fixtures[name] = dict(cls=classes[0] if classes else "Counter")
        refs[key] = name
        for part in ("body", "handle"):
            eid = name + "_" + part
            entities.append(
                dict(id=eid, source_instance_id="fixture:" + name, source_part_id=part)
            )
            expected.add(eid)
    for role, name in OBJECT_RULES.get(task, ()):
        objects.append(dict(name=name))
        for i in range(2):
            eid = name + "_" + str(i)
            entities.append(
                dict(
                    id=eid, source_instance_id="object:" + name, source_part_id="whole"
                )
            )
            expected.add(eid)
    # Both missing fine category and distr prefixes are legitimate *distractors*.
    objects.extend(
        [
            dict(name="distr", type="object", info={"cat": "soap_dispenser"}),
            dict(name="distr_counter"),
        ]
    )
    entities.append(
        dict(id="distr_id", source_instance_id="object:distr", source_part_id="whole")
    )
    refs["src_fixture"] = "unrelated_start"
    fixtures["unrelated_start"] = dict(cls="Counter")
    entities.append(
        dict(
            id="start_id",
            source_instance_id="fixture:unrelated_start",
            source_part_id="whole",
        )
    )
    metadata = dict(
        fixtures=fixtures,
        fixture_refs=refs,
        object_cfgs=objects,
        task_refs={"knob": "front_left"},
    )
    result = bind_task_entities(task, metadata, dict(entities=entities))
    assert result["binding_status"] == "BOUND"
    assert set(result["entity_ids"]) == expected
    assert (
        "distr_id" not in result["entity_ids"]
        and "start_id" not in result["entity_ids"]
    )
    assert result["source_instance_part_to_entity_ids"]["object:distr"]["whole"] == [
        "distr_id"
    ]
    assert all(r["source_part_to_entity_ids"] for r in result["roles"])
    if task == "PickPlaceDrawerToCounter":
        assert result["destination_policy"] == "ANY_COUNTER_NOT_REGISTERED_COUNTER_ONLY"
        assert "destination" not in [r["role"] for r in result["roles"]]
    if task == "TurnOffStove":
        assert (
            result["semantic_subtarget"]["part_binding"]
            == "NOT_ASSUMED_FROM_INSTANCE_BINDING"
        )


def test_empty_fixture_refs_unique_fallback_and_ambiguity():
    graph = dict(
        entities=[
            dict(
                id="body_1",
                source_instance_id="fixture:blender_0",
                source_part_id="body",
            ),
            dict(
                id="body_2",
                source_instance_id="fixture:blender_0",
                source_part_id="body",
            ),
            dict(
                id="lid_1",
                source_instance_id="fixture:loose_lid_0",
                source_part_id="whole",
            ),
        ]
    )
    meta = dict(
        fixtures={
            "blender_0": {"cls": "Blender"},
            "loose_lid_0": {"cls": "BlenderLid"},
        },
        fixture_refs={},
        object_cfgs=[],
    )
    result = bind_task_entities("CloseBlenderLid", meta, graph)
    assert result["entity_ids"] == ["body_1", "body_2", "lid_1"]
    assert result["roles"][0]["evidence"]["kind"] == "UNIQUE_OFFICIAL_CLASS"
    meta["fixtures"]["blender_1"] = {"cls": "Blender"}
    result = bind_task_entities("CloseBlenderLid", meta, graph)
    assert result["binding_status"] == "UNRESOLVED"
    assert result["failures"][0]["status"] == "AMBIGUOUS"
    nav = bind_task_entities(
        "NavigateKitchen",
        dict(
            fixtures=meta["fixtures"],
            object_cfgs=[],
            fixture_refs={"src_fixture": "blender_0"},
        ),
        graph,
    )
    assert not nav["entity_ids"] and nav["binding_status"] == "UNRESOLVED"


def test_current_membership_version_can_change_without_image_owner(tmp_path):
    kwargs, snapshots = stage_case(
        tmp_path, OutputProfile(selection_top_variant="clean")
    )
    snapshot = snapshots[0]
    member_plan = renderer_member_sets(snapshot)
    native = "rooms/0/floor_top"
    from g2.io import read_json

    raw = kwargs["rendered"] / "state_000000_frame_000000"
    meta = read_json(raw / "g2_original_gpu" / native / "view.json")
    owner = dict(state_id=0, frame=0, path="old.png", projection=meta)
    assets = [dict(rgb_file="sixview/floor_top.png", native_view=native)]
    a = state_metadata(
        snapshot,
        assets,
        member_plan,
        state_id=0,
        owner_rows={"sixview/floor_top": owner},
    )
    current = copy.deepcopy(member_plan)
    current[native]["native_entity_ids"].remove("entity_3")
    b = state_metadata(
        snapshots[2],
        assets,
        current,
        state_id=2,
        owner_rows={"sixview/floor_top": owner},
    )
    av, bv = a["views"]["sixview/floor_top"], b["views"]["sixview/floor_top"]
    assert av["image_owner"] == bv["image_owner"]
    assert av["image_projection"] == bv["image_projection"]
    assert av["membership_version"] != bv["membership_version"]
    assert "entity_3" not in b["object_to_view_ids"]
    assert projection_from_renderer(meta)["physical_width_m"] == 4
    assert projection_from_renderer(meta)["pixel_center_span_m"] == [3.9375, 3.9375]
    task = bind_task_entities("NavigateKitchen", kwargs["ep_meta"], snapshot)
    b["views"]["sixview/floor_top"]["availability"] = "disabled"
    with pytest.raises(ContractError, match="mandatory"):
        select_views(b, task, top_variant="clean")


def test_caption_authority_determinism_budget_and_no_private_or_future_facts(tmp_path):
    kwargs, snapshots = stage_case(
        tmp_path, OutputProfile(selection_top_variant="clean")
    )
    graph = snapshots[0]
    graph["target_pos"] = [999, 888, 777]
    graph["expert_actions"] = ["move_to_future"]
    graph["success"] = True
    graph["entities"][2]["inside"] = "UNPROVEN_CONTACT"
    task = bind_task_entities("NavigateKitchen", kwargs["ep_meta"], graph)
    original = "  Navigate to the target counter.\n原任务保持原样  "
    recipe = LanguageRecipe(include_aabb=True, decimal_places=2)
    a = enhance_caption(original, graph, task, recipe)
    assert a == enhance_caption(original, graph, task, recipe)
    assert a["enhanced_text"].startswith(original)
    for forbidden in (
        "999",
        "888",
        "777",
        "move_to_future",
        "UNPROVEN_CONTACT",
        "source_file",
        "ep_meta_pointer",
        "expert_actions",
        "success",
    ):
        assert forbidden not in a["enhanced_text"]
    assert a["recipe"]["production_template_frozen"] is False
    short = enhance_caption(original, graph, task, replace(recipe, max_characters=10))
    assert short["enhanced_text"] == original and short["original_exceeds_budget"]
    bank = TextBank()
    bank.add(0, 0, dict(original_text=original), graph, task, recipe)
    bank.add(1, 10, dict(original_text=original), graph, task, recipe)
    assert len(bank.texts) == 1
    changed = copy.deepcopy(graph)
    changed["entities"][2]["bbox_max"][0] += 0.1
    bank.add(2, 20, dict(original_text=original), changed, task, recipe)
    assert len(bank.texts) == 2
    omitted = TextBank()
    tiny = replace(recipe, max_characters=10)
    omitted.add(0, 0, dict(original_text=original), graph, task, tiny)
    omitted.add(1, 10, dict(original_text=original), changed, task, tiny)
    assert len(omitted.texts) == 1
    assert omitted.states[0]["fact_context"] != omitted.states[1]["fact_context"]
    with pytest.raises(ContractError, match="causal"):
        bank.add(3, 19, dict(original_text=original), graph, task, recipe)
    rows = [dict(episode_index=0, frame_index=f, task_index=7) for f in (0, 10)]
    captions = resolve_caption_rows(
        rows,
        [dict(task_index=7, task=original)],
        frames=[0, 10],
        episode_id=0,
        ep_meta_lang=original,
    )
    assert captions[10]["original_text"] == original
    with pytest.raises(ContractError, match="disagree"):
        resolve_caption_rows(
            rows,
            [dict(task_index=7, task=original)],
            frames=[0],
            episode_id=0,
            ep_meta_lang=original.strip(),
        )
    with pytest.raises(ContractError, match="no authoritative"):
        resolve_caption_rows(
            rows,
            [dict(task_index=7, task=original)],
            frames=[20],
            episode_id=0,
            ep_meta_lang=original,
        )
