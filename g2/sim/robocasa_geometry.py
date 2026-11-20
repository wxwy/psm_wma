"""Official RoboCasa GT geometry used by archived frames and live MuJoCo.

The caller owns the MuJoCo model and MjData. Scene classification and a
finite, source-derived native raster plan use the same simulator geometry
and official initialization metadata in both entry points. The plan keeps
the existing TEST_ONLY free-region provenance.
"""

from collections import Counter

import numpy as np

from g2.io import ContractError
from g2.sim.prescan import geom_surface_mesh, geometry_type_names
from g2.sim.source_geometry import effective_rgba

ROBOT_PREFIXES = ("robot0_", "mobilebase0_", "gripper0_")
METADATA_SCHEMA = "g2_atomic_official_semantic_candidate_v1"


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
    fixture = next(
        (k for k in fixture_keys if name == k or name.startswith(k + "_")), None
    )
    obj = next((k for k in object_keys if name == k or name.startswith(k + "_")), None)
    if fixture is not None and obj is not None:
        raise ContractError("fixture and object source identity overlap: " + name)
    return (
        ("fixture", fixture)
        if fixture is not None
        else (("object", obj) if obj is not None else ("unmatched", None))
    )


def derive_scene_metadata(
    model, ep_meta, *, scene_id, state_sha256, model_source_sha256, state_data=None
):
    import mujoco

    if not isinstance(ep_meta, dict) or not isinstance(ep_meta.get("fixtures"), dict):
        raise ContractError("official ep_meta fixture identities missing")
    fixture_names = sorted(ep_meta["fixtures"], key=len, reverse=True)
    object_records = ep_meta.get("object_cfgs", [])
    if not isinstance(object_records, list):
        raise ContractError("official object_cfgs is not a list")
    object_sources = {
        entry["name"]: (i, entry)
        for i, entry in enumerate(object_records)
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    if len(object_sources) != len(object_records):
        raise ContractError("duplicated/invalid source object names")
    object_names = sorted(object_sources, key=len, reverse=True)
    state_data = state_data if state_data is not None else mujoco.MjData(model)
    mujoco.mj_forward(model, state_data)
    geom_kinds = geometry_type_names()
    # Official physical wall geometry defines the room's vertical envelope.
    # Invisible collision primitives above this envelope are legacy placement
    # placeholders, not navigable or visible kitchen geometry. This is a
    # MATERIAL+GEOMETRY policy, never a task/Layout/name-specific exclusion.
    wall_tops = []
    for geom_id in range(model.ngeom):
        name = (
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)
            or f"geom_{geom_id}"
        )
        origin, fixture = _match(name, fixture_names, object_names)
        if (
            origin != "fixture"
            or ep_meta["fixtures"][fixture].get("cls") != "Wall"
            or not (model.geom_contype[geom_id] or model.geom_conaffinity[geom_id])
        ):
            continue
        kind = geom_kinds.get(int(model.geom_type[geom_id]))
        if kind not in ("box", "sphere", "ellipsoid", "capsule", "cylinder", "mesh"):
            continue
        vertices, _ = geom_surface_mesh(model, geom_id, kind)
        world = (
            vertices @ state_data.geom_xmat[geom_id].reshape(3, 3).T
            + state_data.geom_xpos[geom_id]
        )
        wall_tops.append(float(world[:, 2].max()))
    wall_top = max(wall_tops) if wall_tops else None
    roles, gt_geoms, counts, unmatched, excluded_placeholders = (
        {},
        {},
        Counter(),
        [],
        [],
    )
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
            "role": role,
            "classification_reason": "OFFICIAL_EP_META_INSTANCE_AND_COMPILED_GROUP_COLLISION_ALPHA",
        }
        if role != "robot" and source_type == "fixture":
            category = ep_meta["fixtures"][official_name].get("cls")
            if not isinstance(category, str) or not category:
                raise ContractError("official fixture class missing")
            escaped = official_name.replace("~", "~0").replace("/", "~1")
            source_record.update(
                source_kind="ep_meta",
                ep_meta_pointer="/fixtures/" + escaped,
                source_instance_name=official_name,
                source_collection="fixtures",
                source_category_field="cls",
                source_category=category,
            )
        elif role != "robot" and source_type == "object":
            index, original_record = object_sources[official_name]
            info = original_record.get("info", {})
            if (
                isinstance(info, dict)
                and isinstance(info.get("cat"), str)
                and info["cat"]
            ):
                source_record.update(
                    source_kind="ep_meta",
                    ep_meta_pointer=f"/object_cfgs/{index}",
                    source_instance_name=official_name,
                    source_collection="object_cfgs",
                    source_category_field="info.cat",
                    source_category=info["cat"],
                )
            else:
                source_record.update(
                    source_kind="mjcf",
                    geom_name=name,
                    classification_reason="SOURCE_GEOM_WITHOUT_OFFICIAL_OBJECT_FINE_CATEGORY",
                )
        else:
            source_record.update(source_kind="mjcf", geom_name=name)
        roles[name] = source_record
        counts[role] += 1
        if role == "robot":
            gt_geoms[name] = {
                "include": False,
                "exclusion_reason": "SOURCE_PANDAOMRON_ROBOT_GEOM",
            }
            continue
        if (
            role == "collision"
            and alpha == 0
            and wall_top is not None
            and float(state_data.geom_xpos[g, 2]) > wall_top + 0.5
        ):
            kind = geom_kinds.get(int(model.geom_type[g]))
            if kind in ("box", "sphere", "ellipsoid", "capsule", "cylinder", "mesh"):
                vertices, _ = geom_surface_mesh(model, g, kind)
                zmin = float(
                    (
                        vertices @ state_data.geom_xmat[g].reshape(3, 3).T
                        + state_data.geom_xpos[g]
                    )[:, 2].min()
                )
                if zmin > wall_top + 0.5:
                    gt_geoms[name] = {
                        "include": False,
                        "exclusion_reason": "INVISIBLE_COLLIDABLE_OUTSIDE_OFFICIAL_WALL_VERTICAL_ENVELOPE",
                    }
                    excluded_placeholders.append(name)
                    continue
        if not collidable or group != 0:
            continue  # Occupancy is collision-sourced, not visual appearance.
        if source_type == "fixture":
            fixture_cls = ep_meta["fixtures"][official_name].get("cls")
            if not isinstance(fixture_cls, str) or not fixture_cls:
                raise ContractError("official fixture class missing")
            kind = (
                "wall"
                if fixture_cls == "Wall"
                else "floor"
                if fixture_cls == "Floor"
                else "object"
            )
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
            "instance_id": instance,
            "part_id": "whole",
            "category_id": category,
            "category_label": label,
            "kind": kind,
        }
    # A single native entity groups multiple visual/collision geom parts.
    # Each contributing body may contain a distinct door/drawer joint.
    # Preserve ONE actual union-of-source-joints per entity so nav_sg's
    # owner key (instance,part) remains unique and its joint consistency
    # contract does not fail merely because a fixture has moving parts.
    actual_joints = {}
    for geom_id in range(model.ngeom):
        geom_name = (
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)
            or f"geom_{geom_id}"
        )
        spec = gt_geoms.get(geom_name, {})
        if "instance_id" not in spec:
            continue
        key = spec["instance_id"]
        joint_set = actual_joints.setdefault(key, set())
        body = int(model.geom_bodyid[geom_id])
        while body > 0:
            first, count = int(model.body_jntadr[body]), int(model.body_jntnum[body])
            for j in range(first, first + count):
                name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, j)
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
        {
            "schema": "g2_sim_prescan_v1",
            "scene_id": scene_id,
            "state_source": {
                "model_source_sha256": model_source_sha256,
                "states_sha256": state_sha256,
            },
            "geoms": roles,
            "training_ready": False,
            "classification_policy": "COMPILED_FLAGS_NOT_HUMAN_SEMANTIC_REVIEW",
        },
        {
            "schema": "nav_sg_gt_metadata_v1",
            "scene_id": scene_id,
            "state_source": {
                "model_source_sha256": model_source_sha256,
                "states_sha256": state_sha256,
            },
            "geoms": gt_geoms,
            "training_ready": False,
            "unmatched_source_count": len(unmatched),
        },
        {
            "schema": METADATA_SCHEMA,
            "scene_id": scene_id,
            "role_counts": dict(counts),
            "native_collision_geoms": len(gt_geoms),
            "unmatched_collision_geom_names": unmatched,
            "excluded_invisible_out_of_room_collision_geom_count": len(
                excluded_placeholders
            ),
            "excluded_invisible_out_of_room_collision_geoms": excluded_placeholders,
            "physical_wall_top_m": wall_top,
            "official_fixture_count": len(fixture_names),
            "official_dynamic_object_count": len(object_names),
            "not_human_semantic_approved": True,
            "training_ready": False,
        },
    )


GRID_SCHEMA = "g2_atomic_geometry_bound_navigation_v1"


def grid_from_source(
    model, state, metadata, *, resolution=0.1, margin_m=0.25, max_voxels=10_000_000
):
    import mujoco

    if not 0 < resolution <= 1 or margin_m < 0:
        raise ContractError("invalid full-map geometry raster configuration")
    if (
        not isinstance(metadata, dict)
        or metadata.get("schema") != "nav_sg_gt_metadata_v1"
    ):
        raise ContractError("actual official scene classification is required")
    kinds = geometry_type_names()
    bboxes = []
    floors = []
    walls = []
    for i in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i) or f"geom_{i}"
        role = metadata.get("geoms", {}).get(name)
        if (
            not isinstance(role, dict)
            or role.get("include") is False
            or not (model.geom_contype[i] or model.geom_conaffinity[i])
        ):
            continue
        kind = kinds.get(int(model.geom_type[i]))
        if kind not in ("box", "sphere", "ellipsoid", "capsule", "cylinder", "mesh"):
            raise ContractError("nonfinite selected geom: " + name)
        vertices, _ = geom_surface_mesh(model, i, kind)
        world = vertices @ state.geom_xmat[i].reshape(3, 3).T + state.geom_xpos[i]
        if world.size == 0 or not np.isfinite(world).all():
            raise ContractError("invalid GT world geometry " + name)
        lo, hi = world.min(axis=0), world.max(axis=0)
        bboxes.append((lo, hi))
        if role.get("kind") == "floor":
            floors.append((lo, hi))
        if role.get("kind") == "wall":
            walls.append((lo, hi))
    if not bboxes or not floors or not walls:
        raise ContractError("official finite floor/wall/objects must exist in full map")
    all_lo = np.minimum.reduce([p[0] for p in bboxes])
    all_hi = np.maximum.reduce([p[1] for p in bboxes])
    extent_lo = np.floor((all_lo - margin_m) / resolution) * resolution
    extent_hi = np.ceil((all_hi + margin_m) / resolution) * resolution
    dims = np.maximum(1, np.rint((extent_hi - extent_lo) / resolution).astype(int))
    if int(np.prod(dims, dtype=object)) > max_voxels:
        raise ContractError("actual full scene exceeds nav 10cm voxel resource budget")
    # At least one source floor must contribute finite, nondegenerate XY area.
    # This is a declared oracle free-region approximation, never sensor evidence.
    floor_top = min(p[1][2] for p in floors)
    wall_top = max(p[1][2] for p in walls)
    if not np.isfinite([floor_top, wall_top]).all() or wall_top <= floor_top + 0.25:
        raise ContractError("floor/wall source geometry has no usable room height")
    regions = []
    for lo, hi in floors:
        lower = [float(lo[0]), float(lo[1]), float(floor_top + 0.1)]
        upper = [float(hi[0]), float(hi[1]), float(wall_top)]
        if all(b > a for a, b in zip(lower, upper)):
            regions.append({"type": "box", "min": lower, "max": upper})
    if not regions:
        raise ContractError("no finite official floor projected free-space support")
    known = {
        "schema": "nav_sg_known_region_v1",
        "provenance": "NOT CERTIFIED: TEST_ONLY per-episode source floor XY "
        "extrusion to source wall height; may include enclosed solids",
        "regions": regions,
    }
    report = {
        "schema": GRID_SCHEMA,
        "grid": {
            "dims": dims.tolist(),
            "origin": extent_lo.tolist(),
            "resolution": float(resolution),
        },
        "known_region": known,
        "bounding_geometry_count": len(bboxes),
        "original_floor_geom_count": len(floors),
        "original_wall_geom_count": len(walls),
        "voxel_count": int(np.prod(dims)),
        "known_free_space_is_test_only": True,
        "training_ready": False,
    }
    return report
