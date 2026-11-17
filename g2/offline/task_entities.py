"""Initialization-GT Atomic roles, never perception or success-state inference."""

from __future__ import annotations

from g2.io import ContractError
from g2.latent_cache.contract import fingerprint

RULE_VERSION = "robocasa_atomic_initialization_roles_v1_candidate"
SOURCE_REVISION = "425684d332f135f5b30a40b321f52d15a0fe9250"
# (role, official fixture_refs key, unique-class fallback). None forbids guessing.
FIXTURE_RULES = {
    "CloseBlenderLid": (("target", "blender", ("Blender",)),),
    "CloseFridge": (
        (
            "target",
            "fxtr",
            ("FridgeFrenchDoor", "FridgeSideBySide", "FridgeBottomFreezer", "Fridge"),
        ),
    ),
    "CloseToasterOvenDoor": (("target", "toaster_oven", ("ToasterOven",)),),
    "CoffeeSetupMug": (("destination", "coffee_machine", ("CoffeeMachine",)),),
    "NavigateKitchen": (("target", "target_fixture", None),),
    "OpenCabinet": (
        (
            "target",
            "fxtr",
            ("SingleCabinet", "HingeCabinet", "DoubleCabinet", "Cabinet"),
        ),
    ),
    "OpenDrawer": (("target", "drawer", ("Drawer",)),),
    "OpenStandMixerHead": (("target", "stand_mixer", ("StandMixer",)),),
    "PickPlaceCounterToCabinet": (
        ("destination", "cab", None),
        ("source_reference", "counter", None),
    ),
    "PickPlaceCounterToStove": (("destination_reference", "stove", None),),
    "PickPlaceDrawerToCounter": (
        ("source_reference", "drawer", None),
        ("related_reference", "counter", None),
    ),
    "PickPlaceSinkToCounter": (("source_reference", "sink", None),),
    "PickPlaceToasterToCounter": (("source_reference", "toaster", ("Toaster",)),),
    "SlideDishwasherRack": (("target", "dishwasher", ("Dishwasher",)),),
    "TurnOffStove": (("target", "stove", ("Stove", "Stovetop")),),
    "TurnOnElectricKettle": (("target", "electric_kettle", ("ElectricKettle",)),),
    "TurnOnMicrowave": (("target", "microwave", ("Microwave",)),),
    "TurnOnSinkFaucet": (("target", "sink", ("Sink",)),),
}
OBJECT_RULES = {
    "CoffeeSetupMug": (("target", "obj"),),
    "PickPlaceCounterToCabinet": (("target", "obj"),),
    "PickPlaceCounterToStove": (("target", "obj"), ("destination_object", "container")),
    "PickPlaceDrawerToCounter": (("target", "obj"),),
    "PickPlaceSinkToCounter": (("target", "obj"), ("destination_object", "container")),
    "PickPlaceToasterToCounter": (("target", "obj"), ("destination_object", "plate")),
}


def source_entity_index(graph):
    """Preserve every SG ID for every exact (source instance, source part)."""
    result, seen = {}, set()
    for entity in graph["entities"]:
        eid = entity["id"]
        if not isinstance(eid, str) or not eid:
            raise ContractError("SG entity identity must be a nonempty string")
        if eid in seen:
            raise ContractError("duplicate SG entity ID")
        seen.add(eid)
        instance = entity.get("source_instance_id")
        part = entity.get("source_part_id")
        if (
            not isinstance(instance, str)
            or not instance
            or not isinstance(part, str)
            or not part
        ):
            raise ContractError("SG exact source instance/part identity missing")
        result.setdefault(instance, {}).setdefault(part, []).append(eid)
    return {
        i: {p: sorted(ids) for p, ids in sorted(parts.items())}
        for i, parts in sorted(result.items())
    }


def bind_task_entities(task_class, ep_meta, graph):
    if task_class not in FIXTURE_RULES:
        raise ContractError(
            "unsupported Atomic initialization semantics: " + task_class
        )
    fixtures = ep_meta.get("fixtures")
    refs = ep_meta.get("fixture_refs", {})
    objects = ep_meta.get("object_cfgs", [])
    if (
        not isinstance(fixtures, dict)
        or not isinstance(refs, dict)
        or not isinstance(objects, list)
    ):
        raise ContractError("invalid official initialization metadata")
    index = source_entity_index(graph)
    roles, failures = [], []

    def add(role, instance, evidence, status="BOUND"):
        parts = index.get(instance, {}) if instance else {}
        ids = sorted({eid for values in parts.values() for eid in values})
        if status == "BOUND" and not ids:
            status = "SOURCE_NOT_IN_SG"
        record = dict(
            role=role,
            source_instance_id=instance,
            source_part_ids=sorted(parts),
            entity_ids=ids,
            source_part_to_entity_ids=parts,
            binding_status=status,
            evidence=evidence,
        )
        roles.append(record)
        if status != "BOUND":
            failures.append(dict(role=role, status=status, evidence=evidence))

    for role, key, classes in FIXTURE_RULES[task_class]:
        name = refs.get(key)
        if isinstance(name, dict):
            name = name.get("name")
        evidence = dict(kind="OFFICIAL_FIXTURE_REF", pointer="/fixture_refs/" + key)
        if name is None and classes is not None:
            candidates = sorted(
                name
                for name, value in fixtures.items()
                if isinstance(value, dict) and value.get("cls") in classes
            )
            if len(candidates) != 1:
                add(
                    role,
                    None,
                    dict(kind="UNIQUE_OFFICIAL_CLASS", candidates=candidates),
                    "AMBIGUOUS" if candidates else "MISSING_INITIALIZATION_REFERENCE",
                )
                continue
            name = candidates[0]
            evidence = dict(
                kind="UNIQUE_OFFICIAL_CLASS",
                pointer="/fixtures/" + name,
                class_name=fixtures[name]["cls"],
            )
        if not isinstance(name, str) or name not in fixtures:
            add(role, None, evidence, "MISSING_INITIALIZATION_REFERENCE")
            continue
        add(role, "fixture:" + name, evidence)
    for role, name in OBJECT_RULES.get(task_class, ()):
        candidates = [
            i
            for i, value in enumerate(objects)
            if isinstance(value, dict) and value.get("name") == name
        ]
        if len(candidates) != 1:
            add(
                role,
                None,
                dict(kind="OFFICIAL_OBJECT_CFG", name=name),
                "AMBIGUOUS" if candidates else "MISSING_INITIALIZATION_REFERENCE",
            )
            continue
        add(
            role,
            "object:" + name,
            dict(
                kind="OFFICIAL_OBJECT_CFG",
                pointer=f"/object_cfgs/{candidates[0]}",
                name=name,
            ),
        )
    result = dict(
        schema="g2_gt_task_entity_set_v1",
        task_class=task_class,
        grounding="SIMULATION_INITIALIZATION_GT",
        rule_version=RULE_VERSION,
        rule_source_revision=SOURCE_REVISION,
        historical_generator_identity="NOT_CERTIFIED_BY_PUBLIC_REFERENCE",
        roles=roles,
        source_instance_part_to_entity_ids=index,
        entity_ids=sorted({eid for r in roles for eid in r["entity_ids"]}),
        binding_status="BOUND" if not failures else "UNRESOLVED",
        failures=failures,
        initialization_metadata_sha256=fingerprint(ep_meta),
        excluded_initialization_keys=(
            ["src_fixture"] if task_class == "NavigateKitchen" else []
        ),
        destination_policy=(
            "ANY_COUNTER_NOT_REGISTERED_COUNTER_ONLY"
            if task_class == "PickPlaceDrawerToCounter"
            else "TASK_INITIALIZATION_ROLES"
        ),
        current_on_inside_or_success="NOT_INFERRED",
    )
    # Knob identity is initialization semantics, not the knob's current state.
    if task_class == "TurnOffStove":
        task_refs = ep_meta.get("task_refs", {})
        if not isinstance(task_refs, dict):
            raise ContractError("invalid official task_refs")
        knob = task_refs.get("knob")
        if not isinstance(knob, str) or not knob:
            result["binding_status"] = "UNRESOLVED"
            result["failures"].append(
                dict(role="knob", status="MISSING_INITIALIZATION_REFERENCE")
            )
        result["semantic_subtarget"] = dict(
            knob=knob, part_binding="NOT_ASSUMED_FROM_INSTANCE_BINDING"
        )
    result["task_entity_set_id"] = fingerprint(result)
    return result
