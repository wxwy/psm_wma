"""Independent task-definition expectations, not generated from product rules.

Invented source identities exercise each task among unrelated available items.
This is a semantic CPU contract, not historical real-episode certification.
"""

import copy

import pytest

from g2.io import ContractError, digest, read_json, write_json
from g2.latent_cache.contract import fingerprint
from g2.offline.language_context import LanguageRecipe, enhance_caption
from g2.offline.spatial_metadata import select_views
from g2.offline.task_entities import bind_task_entities

# Expectations are manually specified from the pinned initialization/task
# definitions and the GPT F1/F2 source review, independently of both rule tables.
CASES = [
    (
        "CloseBlenderLid",
        {},
        {"target": "fixture:blender", "manipulated_lid": "fixture:loose_lid"},
    ),
    ("CloseFridge", {"fxtr": "fridge"}, {"target": "fixture:fridge"}),
    (
        "CloseToasterOvenDoor",
        {"toaster_oven": "toaster_oven"},
        {"target": "fixture:toaster_oven"},
    ),
    (
        "CoffeeSetupMug",
        {},
        {"destination": "fixture:coffee_machine", "target": "object:obj"},
    ),
    ("NavigateKitchen", {"target_fixture": "cabinet"}, {"target": "fixture:cabinet"}),
    ("OpenCabinet", {"fxtr": "cabinet"}, {"target": "fixture:cabinet"}),
    ("OpenDrawer", {"drawer": "drawer"}, {"target": "fixture:drawer"}),
    ("OpenStandMixerHead", {}, {"target": "fixture:stand_mixer"}),
    (
        "PickPlaceCounterToCabinet",
        {"cab": "cabinet", "counter": "counter"},
        {
            "destination": "fixture:cabinet",
            "source_reference": "fixture:counter",
            "target": "object:obj",
        },
    ),
    (
        "PickPlaceCounterToStove",
        {"stove": "stove", "counter": "counter"},
        {
            "destination_reference": "fixture:stove",
            "target": "object:obj",
            "source_container": "object:obj_container",
            "destination_object": "object:container",
        },
    ),
    (
        "PickPlaceDrawerToCounter",
        {"drawer": "drawer", "counter": "counter"},
        {
            "source_reference": "fixture:drawer",
            "related_reference": "fixture:counter",
            "target": "object:obj",
        },
    ),
    (
        "PickPlaceSinkToCounter",
        {"sink": "sink", "counter": "counter"},
        {
            "source_reference": "fixture:sink",
            "target": "object:obj",
            "destination_object": "object:container",
        },
    ),
    (
        "PickPlaceToasterToCounter",
        {"counter": "counter"},
        {
            "source_reference": "fixture:toaster",
            "target": "object:obj",
            "destination_object": "object:plate",
        },
    ),
    (
        "SlideDishwasherRack",
        {"dishwasher": "dishwasher"},
        {"target": "fixture:dishwasher"},
    ),
    ("TurnOffStove", {}, {"target": "fixture:stove"}),
    (
        "TurnOnElectricKettle",
        {"electric_kettle": "kettle"},
        {"target": "fixture:kettle"},
    ),
    ("TurnOnMicrowave", {}, {"target": "fixture:microwave"}),
    ("TurnOnSinkFaucet", {}, {"target": "fixture:sink"}),
]
FIXTURES = dict(
    blender="Blender",
    loose_lid="BlenderLid",
    fridge="Fridge",
    toaster_oven="ToasterOven",
    coffee_machine="CoffeeMachine",
    cabinet="SingleCabinet",
    drawer="Drawer",
    stand_mixer="StandMixer",
    counter="Counter",
    init_counter="Counter",
    other_counter="Counter",
    stove="Stove",
    sink="Sink",
    toaster="Toaster",
    dishwasher="Dishwasher",
    kettle="ElectricKettle",
    microwave="Microwave",
    unrelated="WallAccessory",
)
OBJECTS = (
    "obj",
    "obj_container",
    "container",
    "plate",
    "distr",
    "drawer_obj",
    "distr_counter",
    "distr_cab",
    "cookware",
)


def test_resume_rejects_self_consistent_stale_role_rule_version(tmp_path):
    from g2.offline.output_profile import OutputProfile
    from g2.offline.stage_a import package_stage_a, validate_profile_episode
    from g2.tests.test_stage_a_package import stage_case

    kwargs, _ = stage_case(tmp_path, OutputProfile(selection_top_variant="clean"))
    root = tmp_path / "published"
    package_stage_a(destination=root, **kwargs)
    # Represent an old candidate whose own hashes/IDs are coherent. Re-signing
    # file checksums must not grant the older incomplete semantic rules trust.
    tasks = read_json(root / "task_entities.json")
    old_id, task = next(iter(tasks["sets"].items()))
    task["rule_version"] = "robocasa_atomic_initialization_roles_v1_candidate"
    task["task_entity_set_id"] = fingerprint(
        {k: v for k, v in task.items() if k != "task_entity_set_id"}
    )
    new_id = task["task_entity_set_id"]
    tasks["sets"] = {new_id: task}
    write_json(root / "task_entities.json", tasks)
    manifest = read_json(root / "episode_manifest.json")
    source = read_json(root / "spatial_source.json")
    for obj in (manifest, source):
        obj["files"]["task_entities.json"] = digest(root / "task_entities.json")
        for state in obj["states"]:
            assert state["task_entity_set_id"] == old_id
            state["task_entity_set_id"] = new_id
    source["source_id"] = fingerprint(
        {k: v for k, v in source.items() if k != "source_id"}
    )
    write_json(root / "spatial_source.json", source)
    ready = read_json(root / "SPATIAL_SOURCE_READY.json")
    ready.update(
        source_id=source["source_id"],
        source_manifest_sha256=digest(root / "spatial_source.json"),
    )
    write_json(root / "SPATIAL_SOURCE_READY.json", ready)
    manifest["source_id"] = source["source_id"]
    write_json(root / "episode_manifest.json", manifest)
    complete = read_json(root / "COMPLETE.json")
    complete.update(
        source_id=source["source_id"],
        episode_manifest_sha256=digest(root / "episode_manifest.json"),
    )
    write_json(root / "COMPLETE.json", complete)
    with pytest.raises(ContractError, match="stale role metadata"):
        validate_profile_episode(root, require_complete=False)


def semantic_case(task):
    _, refs, expected = next(row for row in CASES if row[0] == task)
    metadata = dict(
        fixtures={name: dict(cls=kind) for name, kind in FIXTURES.items()},
        fixture_refs=dict(refs, src_fixture="init_counter"),
        object_cfgs=[dict(name=name) for name in OBJECTS],
        task_refs={"knob": "front_left", "cookware_burner": "back_right"},
    )
    entities = []
    for source in [
        *("fixture:" + n for n in FIXTURES),
        *("object:" + n for n in OBJECTS),
    ]:
        for part in ("base", "handle"):
            for fragment in range(2):
                entities.append(
                    dict(
                        id=source.replace(":", "_") + "_" + part + "_" + str(fragment),
                        source_instance_id=source,
                        source_part_id=part,
                        label=source,
                        room_uid=0,
                        island_id=None,
                    )
                )
    return metadata, dict(entities=entities), expected


@pytest.mark.parametrize("task", [row[0] for row in CASES])
def test_independent_initialization_semantics_for_all_18_tasks(task):
    metadata, graph, expected = semantic_case(task)
    result = bind_task_entities(task, metadata, graph)
    assert result["binding_status"] == "BOUND"
    assert len(result["roles"]) == len(expected)
    assert {r["role"]: r["source_instance_id"] for r in result["roles"]} == expected
    expected_ids = {
        e["id"]
        for e in graph["entities"]
        if e["source_instance_id"] in expected.values()
    }
    assert set(result["entity_ids"]) == expected_ids
    assert "fixture:init_counter" not in {
        r["source_instance_id"] for r in result["roles"]
    }
    for role in result["roles"]:
        assert len(role["entity_ids"]) == 4
        assert set(role["source_part_to_entity_ids"]) == {"base", "handle"}
    if task == "PickPlaceDrawerToCounter":
        assert result["destination_policy"] == "ANY_COUNTER_NOT_REGISTERED_COUNTER_ONLY"


@pytest.mark.parametrize(
    "task,missing_source",
    [
        ("CloseBlenderLid", "fixture:loose_lid"),
        ("PickPlaceCounterToStove", "object:obj_container"),
    ],
)
def test_required_independent_role_is_not_bound_when_source_or_sg_missing(
    task, missing_source
):
    metadata, graph, _ = semantic_case(task)
    missing_graph = dict(
        entities=[
            e for e in graph["entities"] if e["source_instance_id"] != missing_source
        ]
    )
    result = bind_task_entities(task, metadata, missing_graph)
    assert result["binding_status"] == "UNRESOLVED"
    assert any(f["status"] == "SOURCE_NOT_IN_SG" for f in result["failures"])
    kind, name = missing_source.split(":")
    if kind == "fixture":
        del metadata["fixtures"][name]
    else:
        metadata["object_cfgs"] = [
            r for r in metadata["object_cfgs"] if r["name"] != name
        ]
    result = bind_task_entities(task, metadata, graph)
    assert result["binding_status"] == "UNRESOLVED"
    assert any(
        f["status"] == "MISSING_INITIALIZATION_REFERENCE" for f in result["failures"]
    )


def test_ambiguous_lid_and_duplicate_source_plate_never_choose_first():
    metadata, graph, _ = semantic_case("CloseBlenderLid")
    metadata["fixtures"]["other_lid"] = {"cls": "BlenderLid"}
    assert (
        bind_task_entities("CloseBlenderLid", metadata, graph)["binding_status"]
        == "UNRESOLVED"
    )
    metadata, graph, _ = semantic_case("PickPlaceCounterToStove")
    metadata["object_cfgs"].append({"name": "obj_container"})
    result = bind_task_entities("PickPlaceCounterToStove", metadata, graph)
    assert result["binding_status"] == "UNRESOLVED"
    assert any(f["status"] == "AMBIGUOUS" for f in result["failures"])


@pytest.mark.parametrize(
    "task,extra_source",
    [
        ("CloseBlenderLid", "fixture:loose_lid"),
        ("PickPlaceCounterToStove", "object:obj_container"),
    ],
)
def test_required_auxiliary_entities_reach_text_and_their_associated_views(
    task, extra_source
):
    metadata, graph, _ = semantic_case(task)
    task_set = bind_task_entities(task, metadata, graph)
    extra_ids = [
        e["id"] for e in graph["entities"] if e["source_instance_id"] == extra_source
    ]
    # Explicit synthetic renderer-member inputs, not a claim about which real
    # episode direction was missing. Exercise the existing selector unchanged.
    spatial = dict(
        views={
            "sixview/floor_top": dict(
                availability="ready",
                is_floor_top=True,
                variant="clean",
                membership_version="top",
                membership={"native_entity_ids": []},
            ),
            "sixview/plus_X": dict(
                availability="reference",
                is_floor_top=False,
                variant="clean",
                membership_version="side",
                membership={"native_entity_ids": extra_ids},
            ),
        },
        entity_to_view_ids={eid: ["sixview/plus_X"] for eid in extra_ids},
    )
    selection = select_views(spatial, task_set, top_variant="clean")
    assert selection["selected_view_ids"] == ["sixview/floor_top", "sixview/plus_X"]
    text = enhance_caption(
        "Synthetic task instruction.", graph, task_set, LanguageRecipe()
    )
    assert extra_source in text["enhanced_text"]
    assert "object:distr" not in text["enhanced_text"]
    altered = copy.deepcopy(metadata)
    altered["fixture_refs"]["src_fixture"] = "other_counter"
    assert (
        bind_task_entities(task, altered, graph)["entity_ids"] == task_set["entity_ids"]
    )
