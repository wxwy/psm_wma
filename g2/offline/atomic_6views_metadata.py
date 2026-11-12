"""Derive factual geom visibility and GT instance metadata from RoboCasa source.

No scene-specific names, material colors, or learned semantics are invented.
Official ep_meta fixture/object identities are used for category provenance.
Unmatched geometry stays explicit UNKNOWN, never deleted. Robot exclusion
follows the recorded PandaOmron root prefixes, with review status retained.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from g2.io import ContractError
from g2.sim.source_geometry import effective_rgba, load_model, model_source_hash
from g2.offline.atomic_6views_source import DEFAULT_ASSET_ROOTS, _hash

ROBOT_PREFIXES = ("robot0_", "mobilebase0_", "gripper0_")
SCHEMA = "g2_atomic_official_semantic_candidate_v1"


def _classify(name, group, collidable, rgba_alpha, robot_prefixes=ROBOT_PREFIXES):
    if any(name.startswith(prefix) for prefix in robot_prefixes):
        return "robot"
    if group == 0 and collidable:
        return "collision"
    if group == 1 and not collidable and rgba_alpha > 0:
        return "visual"
    if group in (0, 1, 2) and not collidable:
        return "auxiliary"
    raise ContractError("unsupported compiled geom visibility/physics flags: " + name)


def _match(name, fixture_keys, object_keys):
    # Original official instance identifiers, longest exact prefix with a
    # separator, not a per-layout category guess.
    fixture = next((k for k in fixture_keys if name == k or name.startswith(k + "_")), None)
    obj = next((k for k in object_keys if name == k or name.startswith(k + "_")), None)
    if fixture is not None and obj is not None:
        raise ContractError("fixture and object source identity overlap: " + name)
    return ("fixture", fixture) if fixture is not None else (
        ("object", obj) if obj is not None else ("unmatched", None))


def derive(model, ep_meta, *, scene_id, state_sha256, model_source_sha256):
    import mujoco
    if not isinstance(ep_meta, dict) or not isinstance(ep_meta.get("fixtures"), dict):
        raise ContractError("official ep_meta fixture identities missing")
    fixture_names = sorted(ep_meta["fixtures"], key=len, reverse=True)
    object_records = ep_meta.get("object_cfgs", [])
    if not isinstance(object_records, list):
        raise ContractError("official object_cfgs is not a list")
    object_sources = {entry["name"]: (i, entry) for i, entry in enumerate(object_records)
                      if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    if len(object_sources) != len(object_records):
        raise ContractError("duplicated/invalid source object names")
    object_names = sorted(object_sources, key=len, reverse=True)
    roles, gt_geoms, counts, unmatched = {}, {}, Counter(), []
    for g in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g) or f"geom_{g}"
        if name in roles:
            raise ContractError("duplicate geom name")
        group = int(model.geom_group[g])
        collidable = bool(model.geom_contype[g] or model.geom_conaffinity[g])
        alpha = float(effective_rgba(model, g)[3])
        role = _classify(name, group, collidable, alpha)
        source_type, official_name = _match(name, fixture_names, object_names)
        # Preserve the exact provenance ABI consumed by g2.sim.prescan:
        # original fixture/object JSON Pointer, or exact source geom name.
        source_record = {
            "role": role, "classification_reason":
                "OFFICIAL_EP_META_INSTANCE_AND_COMPILED_GROUP_COLLISION_ALPHA",
        }
        if role != "robot" and source_type == "fixture":
            category = ep_meta["fixtures"][official_name].get("cls")
            if not isinstance(category, str) or not category:
                raise ContractError("official fixture class missing")
            escaped = official_name.replace("~", "~0").replace("/", "~1")
            source_record.update(
                source_kind="ep_meta", ep_meta_pointer="/fixtures/" + escaped,
                source_instance_name=official_name,
                source_collection="fixtures", source_category_field="cls",
                source_category=category)
        elif role != "robot" and source_type == "object":
            index, original_record = object_sources[official_name]
            info = original_record.get("info", {})
            if isinstance(info, dict) and isinstance(info.get("cat"), str) and info["cat"]:
                source_record.update(
                    source_kind="ep_meta", ep_meta_pointer=f"/object_cfgs/{index}",
                    source_instance_name=official_name,
                    source_collection="object_cfgs", source_category_field="info.cat",
                    source_category=info["cat"])
            else:
                source_record.update(source_kind="mjcf", geom_name=name,
                    classification_reason="SOURCE_GEOM_WITHOUT_OFFICIAL_OBJECT_FINE_CATEGORY")
        else:
            source_record.update(source_kind="mjcf", geom_name=name)
        roles[name] = source_record
        counts[role] += 1
        if role == "robot":
            gt_geoms[name] = {"include": False,
                              "exclusion_reason": "SOURCE_PANDAOMRON_ROBOT_GEOM"}
            continue
        if not collidable or group != 0:
            continue  # Occupancy is collision-sourced, not visual appearance.
        if source_type == "fixture":
            fixture_cls = ep_meta["fixtures"][official_name].get("cls")
            if not isinstance(fixture_cls, str) or not fixture_cls:
                raise ContractError("official fixture class missing")
            kind = ("wall" if fixture_cls == "Wall"
                    else "floor" if fixture_cls == "Floor" else "object")
            instance = "fixture:" + official_name
            category = fixture_cls.lower()
            label = fixture_cls
        elif source_type == "object":
            _, record = object_sources[official_name]
            raw_cat = record.get("info", {}).get("cat", "unknown")
            category = raw_cat if isinstance(raw_cat, str) and raw_cat else "unknown"
            label = category
            kind = "object"
            instance = "object:" + official_name
        else:
            bodyid = int(model.geom_bodyid[g])
            body = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, bodyid) or "world"
            # Model-generated structural roots that are absent from ep_meta
            # keep their original explicit structural prefix, with provenance
            # marked SOURCE-NAME-ONLY (not a human-certified wall detector).
            if name.startswith("wall_"):
                kind, category, label = "wall", "wall", "wall"
                instance = "mjcf_wall:" + body
            elif name.startswith("floor_"):
                kind, category, label = "floor", "floor", "floor"
                instance = "mjcf_floor:" + body
            else:
                kind, category, label = "object", "unknown", "unknown"
                instance = "unclassified:" + body
                unmatched.append(name)
        gt_geoms[name] = {
            "instance_id": instance, "part_id": "whole",
            "category_id": category, "category_label": label, "kind": kind,
        }
    # A single native entity groups multiple visual/collision geom parts.
    # Each contributing body may contain a distinct door/drawer joint.
    # Preserve ONE actual union-of-source-joints per entity so nav_sg's
    # owner key (instance,part) remains unique and its joint consistency
    # contract does not fail merely because a fixture has moving parts.
    actual_joints = {}
    for geom_id in range(model.ngeom):
        geom_name = mujoco.mj_id2name(
            model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or f"geom_{geom_id}"
        spec = gt_geoms.get(geom_name, {})
        if "instance_id" not in spec:
            continue
        key = spec["instance_id"]
        joint_set = actual_joints.setdefault(key, set())
        body = int(model.geom_bodyid[geom_id])
        while body > 0:
            first, count = int(model.body_jntadr[body]), int(model.body_jntnum[body])
            for j in range(first, first+count):
                name = mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_JOINT,j)
                if name:
                    joint_set.add(name)
            body = int(model.body_parentid[body])
    for geom_spec in gt_geoms.values():
        if "instance_id" in geom_spec:
            names = sorted(actual_joints[geom_spec["instance_id"]])
            geom_spec["joint_id"] = ",".join(names) if names else "none"
    if not any(x.get("kind") == "floor" for x in gt_geoms.values()):
        raise ContractError("no official floor fixture was classified")
    if not any(x.get("kind") == "wall" for x in gt_geoms.values()):
        raise ContractError("no official wall fixture was classified")
    return (
        {"schema": "g2_sim_prescan_v1", "scene_id": scene_id,
         "state_source": {"model_source_sha256": model_source_sha256,
                          "states_sha256": state_sha256},
         "geoms": roles, "training_ready": False,
         "classification_policy": "COMPILED_FLAGS_NOT_HUMAN_SEMANTIC_REVIEW"},
        {"schema": "nav_sg_gt_metadata_v1", "scene_id": scene_id,
         "state_source": {"model_source_sha256": model_source_sha256,
                          "states_sha256": state_sha256},
         "geoms": gt_geoms,
         "training_ready": False,
         "unmatched_source_count": len(unmatched)},
        {"schema": SCHEMA, "scene_id": scene_id,
         "role_counts": dict(counts), "native_collision_geoms": len(gt_geoms),
         "unmatched_collision_geom_names": unmatched,
         "official_fixture_count": len(fixture_names),
         "official_dynamic_object_count": len(object_names),
         "not_human_semantic_approved": True, "training_ready": False})


def build(rebased_xml, ep_meta, states, output, *, scene_id, asset_roots=DEFAULT_ASSET_ROOTS):
    source = Path(rebased_xml).resolve(strict=True)
    ep_meta = Path(ep_meta).resolve(strict=True)
    states = Path(states).resolve(strict=True)
    dest = Path(output).absolute()
    if dest.exists() or dest.is_symlink():
        raise ContractError("metadata output already exists")
    meta = json.loads(ep_meta.read_text())
    model, sources = load_model(source, asset_roots)
    role, native, audit = derive(
        model, meta, scene_id=scene_id, state_sha256=_hash(states),
        model_source_sha256=model_source_hash(sources))
    dest.mkdir(parents=True)
    for filename, body in (("role_map.json", role), ("native_metadata.json", native),
                           ("source_classification_audit.json", audit)):
        with (dest / filename).open("x", encoding="utf-8") as f:
            json.dump(body, f, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            f.write("\n")
    return audit


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rebased-xml", required=True)
    p.add_argument("--ep-meta", required=True)
    p.add_argument("--states", required=True)
    p.add_argument("--scene-id", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args(argv)
    print(json.dumps(build(args.rebased_xml, args.ep_meta, args.states,
                           args.output, scene_id=args.scene_id), ensure_ascii=False))


if __name__ == "__main__":
    main()
