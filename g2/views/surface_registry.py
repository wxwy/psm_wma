"""Source surface identities and view-only geometric affiliations.

Semantic identity is optional.  These supplementary affiliations do not amend
the native Scene Graph or claim to be native connection certificates.  Unknown
surfaces remain in the registry even when a view affiliation cannot be proved.
"""

import math

import numpy as np

from g2.io import ContractError
from g2.nav_bridge.connections import bbox_gap


SCHEMA = "g2_surface_registry_v1"
STRUCTURAL_ROLES = frozenset(("floor", "wall", "ceiling"))
AXES = frozenset(("floor_top", "upper_up", "+X", "-X", "+Y", "-Y"))


def _mesh(vertices, faces):
    vertices = np.asarray(vertices, dtype=np.float64)
    faces = np.asarray(faces)
    if (
        vertices.ndim != 2
        or vertices.shape[1:] != (3,)
        or not len(vertices)
        or not np.isfinite(vertices).all()
        or faces.ndim != 2
        or faces.shape[1:] != (3,)
        or faces.dtype.kind not in "iu"
        or np.any(faces < 0)
        or np.any(faces >= len(vertices))
    ):
        raise ContractError("invalid registered surface mesh")
    return vertices, np.asarray(faces, dtype=np.int32)


def _frame(position, rotation):
    position = np.asarray(position, dtype=np.float64)
    rotation = np.asarray(rotation, dtype=np.float64).reshape(3, 3)
    if (
        position.shape != (3,)
        or not np.isfinite(position).all()
        or not np.isfinite(rotation).all()
        or not np.allclose(rotation @ rotation.T, np.eye(3), atol=1e-6, rtol=0)
        or not np.isclose(np.linalg.det(rotation), 1, atol=1e-6, rtol=0)
    ):
        raise ContractError("invalid registered surface transform")
    return position, rotation


def _structural_role(spec, entity):
    if entity is not None and entity.get("kind") in STRUCTURAL_ROLES:
        return entity["kind"], {"basis": "NATIVE_ENTITY_KIND", "entity_id": entity["id"]}
    explicit = spec.get("structural_role")
    if explicit is not None:
        if explicit not in STRUCTURAL_ROLES:
            raise ContractError("unsupported explicit structural role")
        return explicit, {
            "basis": "SOURCE_ADAPTER_DECLARED_STRUCTURAL_ROLE",
            "source_evidence": spec.get("structural_role_evidence"),
        }
    # Exact source classes are metadata, not geom or instance name heuristics.
    category = spec.get("source_category")
    declared = {"Wall": "wall", "Floor": "floor", "Ceiling": "ceiling",
                "wall": "wall", "floor": "floor", "ceiling": "ceiling"}
    if isinstance(category, str) and category in declared:
        return declared[category], {"basis": "SOURCE_CATEGORY", "source_category": category}
    return None, {"basis": "STRUCTURAL_ROLE_UNKNOWN"}


def _entity_rooms(entity):
    if entity.get("kind") == "object":
        uid = entity.get("room_uid", -1)
        return {uid} if type(uid) is int and uid >= 0 else set()
    return set(entity.get("adjacent_room_uids", ()))


def _source_identity(spec):
    identity = spec.get("source_instance")
    if isinstance(identity, (list, tuple)) and len(identity) == 2:
        return identity[0], identity[1]
    return spec.get("source_kind"), spec.get("instance")


def _parallel_structure(surface, entity):
    """Avoid matching a source wall to a perpendicular wall at a room corner."""
    vertices = np.asarray(entity.get("vertices", []), float)
    if vertices.ndim != 2 or vertices.shape[1:] != (3,) or len(vertices) < 3:
        return False
    centered = vertices - vertices.mean(axis=0)
    eigenvalues, eigenvectors = np.linalg.eigh(centered.T @ centered)
    if eigenvalues[1] <= 0:
        return False
    widths = np.ptp(surface["local_vertices"], axis=0)
    if np.sort(widths)[1] <= 0:
        return False
    normal = surface["rotation"][:, int(np.argmin(widths))]
    return abs(float(normal @ eigenvectors[:, 0])) > 0.99


def compile_surface_registry(model, data, specs, snapshot):
    """Compile stable geom identities and optional native/geometry affiliations.

    Only explicitly source-bound object/fixture instances can supplement the
    native object connection graph.  Unclassified MJCF surfaces are retained
    without becoming accidental structural or object relays.
    """
    entities = {entity["id"]: entity for entity in snapshot["entities"]}
    if len(entities) != len(snapshot["entities"]):
        raise ContractError("duplicate native entity identity")
    native_ids = sorted(entities)
    rooms = {room["uid"]: room for room in snapshot["rooms"]}
    if len(rooms) != len(snapshot["rooms"]):
        raise ContractError("duplicate room identity")
    threshold = snapshot.get("connections", {}).get(
        "threshold_m", snapshot.get("connection_distance", 0.3)
    )
    if type(threshold) not in (int, float) or not math.isfinite(threshold) or threshold <= 0:
        raise ContractError("invalid surface affiliation distance")
    connection_rows = {
        row["entity_id"]: row for row in snapshot.get("connections", {}).get("objects", [])
    }
    surfaces = {}
    groups = {}
    for index, spec in enumerate(specs):
        gid = spec["g"]
        owner = spec.get("owner", -1)
        if type(gid) is not int or gid < 0 or gid >= model.ngeom or gid in surfaces:
            raise ContractError("invalid or duplicate surface geom ID")
        if owner is None:
            owner = -1
        if type(owner) is not int or owner < -1 or owner >= len(native_ids):
            raise ContractError("invalid optional semantic owner")
        entity = entities[native_ids[owner]] if owner >= 0 else None
        local, faces = _mesh(spec["vertices"], spec["faces"])
        position, rotation = _frame(data.geom_xpos[gid], data.geom_xmat[gid])
        world = local @ rotation.T + position
        role, role_evidence = _structural_role(spec, entity)
        source_kind, instance = _source_identity(spec)
        material = int(model.geom_matid[gid])
        surface = {
            "surface_id": gid,
            "geom_id": gid,
            "spec_index": index,
            "kind": spec["kind"],
            "semantic_owner_index": owner if owner >= 0 else None,
            "semantic_owner_id": native_ids[owner] if owner >= 0 else None,
            "material_id": material,
            "local_vertices": local,
            "world_vertices": world,
            "faces": faces,
            "position": position,
            "rotation": rotation,
            "bbox_min": world.min(axis=0),
            "bbox_max": world.max(axis=0),
            "structural_role": role,
            "structural_role_evidence": role_evidence,
            "source_evidence": {
                "scene_id": snapshot.get("scene_id"),
                "source_sha256": snapshot.get("source_sha256"),
                "source_kind": source_kind,
                "source_instance": instance,
                "source_geom_id": gid,
                "semantic_identity_required_for_geometry": False,
            },
            "room_affiliations": {},
            "affiliation_status": "UNKNOWN_RETAINED",
        }
        surfaces[gid] = surface
        if entity is not None:
            row = connection_rows.get(entity["id"], {})
            for uid in _entity_rooms(entity) & rooms.keys():
                surface["room_affiliations"][uid] = {
                    "basis": "NATIVE_ENTITY_VIEW_MEMBERSHIP",
                    "anchor_entity_ids": [entity["id"]],
                    "root_entity_ids": list(entity.get("root_affiliations", [])),
                    "floor_state": "YES" if role == "floor" else row.get("floor_state", "UNKNOWN"),
                    "island_ids": [entity["island_id"]] if entity.get("island_id") else [],
                    "view_only": True,
                }
            surface["affiliation_status"] = "NATIVE_BINDING" if surface["room_affiliations"] else "UNKNOWN_RETAINED"
        elif role is None and source_kind == "ep_meta" and isinstance(instance, str) and instance:
            group = groups.setdefault((source_kind, instance), {"surface_ids": []})
            group["surface_ids"].append(gid)
        elif role is not None:
            anchors = [
                e for e in entities.values()
                if e.get("kind") == role and bbox_gap(surface, e) < threshold
                and _parallel_structure(surface, e)
            ]
            possible_rooms = set().union(*(_entity_rooms(e) for e in anchors)) if anchors else set()
            if len(possible_rooms) == 1 and possible_rooms <= rooms.keys():
                uid = next(iter(possible_rooms))
                surface["room_affiliations"][uid] = {
                    "basis": "SOURCE_STRUCTURE_GEOMETRY_VIEW_AFFILIATION_ONLY",
                    "anchor_entity_ids": sorted(e["id"] for e in anchors),
                    "root_entity_ids": sorted(e["id"] for e in anchors),
                    "floor_state": "YES" if role == "floor" else "UNKNOWN",
                    "island_ids": [],
                    "view_only": True,
                    "native_scene_graph_modified": False,
                }
                surface["affiliation_status"] = "GEOMETRIC_VIEW_AFFILIATION"

    # Supplementary source instances may relay to other such instances or to
    # existing eligible objects. Structural roots are terminals, never relays.
    keys = sorted(groups)
    for group in groups.values():
        members = [surfaces[gid] for gid in group["surface_ids"]]
        group["bbox_min"] = np.min([s["bbox_min"] for s in members], axis=0)
        group["bbox_max"] = np.max([s["bbox_max"] for s in members], axis=0)
        group["anchors"] = []
        for entity in entities.values():
            eligible = entity.get("kind") in STRUCTURAL_ROLES or (
                entity.get("kind") == "object" and entity.get("connection_relay_allowed") is True
            )
            if eligible:
                gap = bbox_gap(group, entity)
                if gap < threshold:
                    group["anchors"].append((entity["id"], gap))
    neighbors = {key: set() for key in keys}
    for i, left in enumerate(keys):
        for right in keys[i + 1 :]:
            if bbox_gap(groups[left], groups[right]) < threshold:
                neighbors[left].add(right)
                neighbors[right].add(left)
    remaining = set(keys)
    complete = snapshot.get("affiliations_complete") is True
    while remaining:
        component = set()
        pending = [min(remaining)]
        while pending:
            key = pending.pop()
            if key in component:
                continue
            component.add(key)
            pending.extend(neighbors[key] - component)
        remaining -= component
        anchors = sorted({eid for key in component for eid, _ in groups[key]["anchors"]})
        candidate_rooms = set().union(*(_entity_rooms(entities[eid]) for eid in anchors)) if anchors else set()
        # A component straddling multiple native rooms is unresolved, never
        # assigned to whichever room happens to be processed first.
        if len(candidate_rooms) != 1 or not candidate_rooms <= rooms.keys():
            continue
        uid = next(iter(candidate_rooms))
        roots = set()
        islands = set()
        for eid in anchors:
            entity = entities[eid]
            if entity.get("kind") in STRUCTURAL_ROLES:
                roots.add(eid)
            else:
                roots.update(entity.get("root_affiliations", []))
                if entity.get("island_id"):
                    islands.add(entity["island_id"])
        if any(eid not in entities or entities[eid].get("kind") not in STRUCTURAL_ROLES for eid in roots):
            raise ContractError("invalid native structural affiliation endpoint")
        floor = any(entities[eid].get("kind") == "floor" for eid in roots)
        wall = any(entities[eid].get("kind") == "wall" for eid in roots)
        affiliation = {
            "basis": "SOURCE_SURFACE_BBOX_VIEW_AFFILIATION_ONLY",
            "anchor_entity_ids": anchors,
            "root_entity_ids": sorted(roots),
            "floor_state": "YES" if floor else "NO" if complete else "UNKNOWN",
            "island_ids": sorted(islands) if floor and not wall else [],
            "threshold_m": float(threshold),
            "metric": "WORLD_AABB_3D_EUCLIDEAN",
            "comparison": "STRICT_LESS_THAN",
            "roots_are_endpoints_only": True,
            "native_scene_graph_modified": False,
            "view_only": True,
            "direct_anchor_edges": [
                {"source_instance": key[1], "entity_id": eid, "distance_m": gap}
                for key in sorted(component)
                for eid, gap in groups[key]["anchors"]
            ],
            "source_component_instances": [key[1] for key in sorted(component)],
        }
        for key in component:
            for gid in groups[key]["surface_ids"]:
                surfaces[gid]["room_affiliations"][uid] = dict(affiliation)
                surfaces[gid]["affiliation_status"] = "GEOMETRIC_VIEW_AFFILIATION"
    return {
        "schema": SCHEMA,
        "surfaces": surfaces,
        "rooms": rooms,
        "native_entity_ids": native_ids,
        "native_entities": entities,
        "connection_distance_m": float(threshold),
        "semantic_graph_modified": False,
        "uncertain_surface_ids": [gid for gid, s in surfaces.items() if s["affiliation_status"] == "UNKNOWN_RETAINED"],
    }


def select_surface_ids(registry, room_uid, axis, members, low, high, island=False):
    """Return source Geom IDs, independently of optional semantic IDs."""
    if registry.get("schema") != SCHEMA or axis not in AXES or room_uid not in registry["rooms"]:
        raise ContractError("invalid surface view selection")
    identities = registry["native_entity_ids"]
    members = set(members)
    if any(type(i) is not int or i < 0 or i >= len(identities) for i in members):
        raise ContractError("invalid native member index")
    member_ids = {identities[i] for i in members}
    selected_islands = {registry["native_entities"][eid].get("island_id") for eid in member_ids} - {None}
    room = registry["rooms"][room_uid]
    origin, axes = _frame(room["reference_frame"]["origin_world"], room["reference_frame"]["axes_world"])
    low, high = np.asarray(low, float), np.asarray(high, float)
    if low.shape != (3,) or high.shape != (3,) or not np.isfinite([low, high]).all() or np.any(high < low):
        raise ContractError("invalid surface view bounds")
    result = set()
    for gid, surface in registry["surfaces"].items():
        affiliation = surface["room_affiliations"].get(room_uid)
        if affiliation is None:
            continue
        local = (surface["world_vertices"] - origin) @ axes.T
        if np.any(local.max(axis=0) < low) or np.any(local.min(axis=0) > high):
            continue
        owner = surface["semantic_owner_index"]
        if owner is not None:
            include = owner in members
        elif island:
            include = bool(selected_islands.intersection(affiliation["island_ids"]))
        elif axis == "floor_top":
            include = affiliation["floor_state"] == "YES"
        elif axis == "upper_up":
            include = affiliation["floor_state"] == "NO"
        else:
            include = bool(member_ids.intersection(affiliation["root_entity_ids"]))
        if include:
            result.add(gid)
    return result


def select_shell_faces(vertices, faces, structural_role, position, rotation, room_center):
    """Select a proven regular slab's room-facing plane; preserve other meshes.

    No geom/instance name is inspected. This does not remove duplicate geoms or
    backing layers. The returned mask always indexes the original face array.
    """
    vertices, faces = _mesh(vertices, faces)
    position, rotation = _frame(position, rotation)
    center = np.asarray(room_center, float)
    if center.shape != (3,) or not np.isfinite(center).all():
        raise ContractError("invalid room interior reference")
    keep = np.ones(len(faces), dtype=bool)
    receipt = {"policy": "PRESERVED_UNCERTAIN_OR_NONSTRUCTURAL_SURFACE", "selected_faces": len(faces), "original_faces": len(faces), "structural_role": structural_role, "name_based_selection": False, "duplicate_layer_removed": False}
    if structural_role is None:
        return keep, receipt
    if structural_role not in STRUCTURAL_ROLES:
        raise ContractError("invalid explicit shell structural role")
    widths = np.ptp(vertices, axis=0)
    thin_axis = int(np.argmin(widths))
    thin = rotation[:, thin_axis]
    scale = max(float(np.max(widths)), 1.0)
    tolerance = scale * 1e-8
    if widths[thin_axis] <= tolerance or np.sort(widths)[1] < 3 * widths[thin_axis]:
        return keep, receipt
    if structural_role == "wall" and abs(float(thin[2])) >= 0.15:
        return keep, receipt
    if structural_role in ("floor", "ceiling") and abs(float(thin[2])) <= 0.99:
        return keep, receipt
    tri = vertices[faces]
    cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    areas = np.linalg.norm(cross, axis=1) * 0.5
    extremities = (float(vertices[:, thin_axis].min()), float(vertices[:, thin_axis].max()))
    masks = []
    certified_faces = np.zeros(len(faces), dtype=bool)
    # Both broad planes alone are insufficient: an open box or an internal
    # extra surface is not a proven regular closed slab.
    for axis in range(3):
        expected_area = float(np.prod(np.delete(widths, axis)))
        for value in (vertices[:, axis].min(), vertices[:, axis].max()):
            mask = (np.ptp(tri[:, :, axis], axis=1) <= tolerance) & (np.abs(tri[:, :, axis].mean(axis=1) - value) <= tolerance) & (areas > 0)
            if not np.isclose(areas[mask].sum(), expected_area, rtol=1e-6, atol=tolerance * tolerance):
                return keep, receipt
            certified_faces |= mask
            if axis == thin_axis:
                masks.append(mask)
    if np.any((areas > 0) & ~certified_faces):
        return keep, receipt
    room_coordinate = float((center - position) @ thin)
    if extremities[0] - tolerance <= room_coordinate <= extremities[1] + tolerance:
        return keep, receipt
    side = 0 if room_coordinate < extremities[0] else 1
    keep = masks[side]
    receipt.update(policy="CERTIFIED_REGULAR_SLAB_ROOM_SIDE", selected_faces=int(keep.sum()), thin_axis_local=thin_axis, plane_local=extremities[side], room_interior_point_world=center.tolist())
    return keep, receipt
