"""Source identity/affiliation regressions, with independent small geometries."""

import copy
from types import SimpleNamespace

import numpy as np
import pytest

from g2.io import ContractError
from g2.views.surface_registry import (
    compile_surface_registry,
    select_shell_faces,
    select_surface_ids,
)


FACES = np.array([
    [0, 2, 1], [1, 2, 3], [4, 5, 6], [5, 7, 6],
    [0, 1, 4], [1, 5, 4], [2, 6, 3], [3, 6, 7],
    [0, 4, 2], [2, 4, 6], [1, 3, 5], [3, 7, 5],
])


def vertices(lo, hi):
    return np.array([[hi[a] if j & (1 << a) else lo[a] for a in range(3)] for j in range(8)], float)


def fixture():
    def entity(i, kind, lo, hi, roots=(), floor="UNKNOWN", island=None):
        return {
            "id": f"entity_{i}", "kind": kind, "bbox_min": lo, "bbox_max": hi,
            "vertices": vertices(lo, hi).tolist(), "triangles": FACES.tolist(),
            "room_uid": 0 if kind == "object" else -1, "adjacent_room_uids": [0],
            "root_affiliations": list(roots), "connection_relay_allowed": kind == "object",
            "island_id": island, "floor_state": floor,
        }
    entities = [
        entity(0, "floor", [-2, -2, -0.1], [2, 2, 0]),
        entity(1, "wall", [-2, -2.1, 0], [2, -2, 3]),
        entity(2, "object", [-0.5, -0.5, 0], [0.5, 0.5, 0.7], ["entity_0"], "YES", "island_0_entity_2"),
        entity(3, "object", [-0.5, -1.9, 1.4], [0.5, -1.8, 2], ["entity_1"], "NO"),
    ]
    snapshot = {
        "scene_id": "TEST_ONLY_SURFACE_REGISTRY", "source_sha256": "a" * 64,
        "frame_id": 0, "entities": entities, "connection_distance": 0.3,
        "affiliations_complete": True,
        "connections": {"threshold_m": 0.3, "roots_are_endpoints_only": True,
                        "objects": [{"entity_id": e["id"], "floor_state": e["floor_state"]}
                                    for e in entities if e["kind"] == "object"]},
        "rooms": [{"uid": 0, "center": [0, 0, 1.5], "reference_frame": {
            "origin_world": [0, 0, 0], "axes_world": np.eye(3).tolist()}}],
    }
    model = SimpleNamespace(ngeom=8, geom_matid=np.arange(8, dtype=np.int32))
    data = SimpleNamespace(geom_xpos=np.zeros((8, 3)), geom_xmat=np.tile(np.eye(3).reshape(1, 9), (8, 1)))
    return model, data, snapshot


def spec(gid, lo, hi, owner=-1, instance=None, source_kind="ep_meta", **extra):
    return {"g": gid, "owner": owner, "kind": "box", "vertices": vertices(lo, hi),
            "faces": FACES.copy(), "name": f"arbitrary_{gid}",
            "source_instance": [source_kind, instance or f"instance_{gid}"], **extra}


def selected(registry, axis, members, island=False):
    return select_surface_ids(registry, 0, axis, set(members), [-3, -3, -1], [3, 3, 4], island=island)


def test_ownerless_wall_attachment_visible_without_creating_semantic_entity():
    model, data, snapshot = fixture()
    original = copy.deepcopy(snapshot)
    registry = compile_surface_registry(model, data, [spec(7, [1, -1.99, 1], [1.1, -1.95, 1.1])], snapshot)
    row = registry["surfaces"][7]
    assert row["semantic_owner_index"] is None and row["surface_id"] == 7
    assert row["material_id"] == 7 and row["spec_index"] == 0
    assert selected(registry, "-Y", [1, 3]) == {7}
    assert selected(registry, "upper_up", [3]) == {7}
    assert selected(registry, "floor_top", [0, 2]) == set()
    assert row["room_affiliations"][0]["native_scene_graph_modified"] is False
    assert snapshot == original


def test_owner_label_does_not_control_fixed_view_geometry():
    model, data, snapshot = fixture()
    geometry = spec(4, [-0.5, -1.9, 1.4], [0.5, -1.8, 2], owner=3)
    bound = compile_surface_registry(model, data, [geometry], snapshot)
    unbound = compile_surface_registry(model, data, [dict(geometry, owner=-1)], snapshot)
    assert selected(bound, "-Y", [1, 3]) == selected(unbound, "-Y", [1, 3]) == {4}
    np.testing.assert_array_equal(bound["surfaces"][4]["world_vertices"], unbound["surfaces"][4]["world_vertices"])


def test_direct_and_indirect_attachment_inherit_existing_island_only():
    model, data, snapshot = fixture()
    source = [spec(5, [0, 0, 0.85], [0.1, 0.1, 0.95]),
              spec(6, [0, 0, 1.20], [0.1, 0.1, 1.25])]
    registry = compile_surface_registry(model, data, source, snapshot)
    assert selected(registry, "floor_top", [0, 2]) == {5, 6}
    assert selected(registry, "+X", [2], island=True) == {5, 6}
    assert selected(registry, "-Y", [1, 3]) == set()


def test_floor_is_terminal_and_does_not_relay_to_wall():
    model, data, snapshot = fixture()
    registry = compile_surface_registry(model, data, [spec(5, [1.4, 1.4, 0], [1.5, 1.5, 0.1])], snapshot)
    assert selected(registry, "floor_top", [0, 2]) == {5}
    assert selected(registry, "-Y", [1, 3]) == set()
    assert registry["surfaces"][5]["room_affiliations"][0]["root_entity_ids"] == ["entity_0"]


@pytest.mark.parametrize("gap,visible", [(0.29, True), (0.3, False), (0.31, False)])
def test_connection_threshold_is_strict(gap, visible):
    model, data, snapshot = fixture()
    # Use the exact zero floor boundary to avoid cancellation at the threshold.
    source = spec(5, [1.4, 1.4, gap], [1.5, 1.5, gap + 0.05])
    registry = compile_surface_registry(model, data, [source], snapshot)
    assert (5 in selected(registry, "floor_top", [0])) is visible


def test_full_three_dimensional_gap_cannot_be_replaced_by_axis_gap():
    model, data, snapshot = fixture()
    snapshot["entities"] = [snapshot["entities"][2]]
    snapshot["entities"][0]["root_affiliations"] = []
    registry = compile_surface_registry(model, data, [spec(6, [0.7, 0.7, 0.9], [0.8, 0.8, 1])], snapshot)
    assert registry["surfaces"][6]["room_affiliations"] == {}
    assert 6 in registry["uncertain_surface_ids"]


def test_unclassified_source_is_retained_without_becoming_a_relay():
    model, data, snapshot = fixture()
    source = [spec(4, [-2, -2, 0], [2, 2, 3], source_kind="mjcf"),
              spec(5, [1.4, 1.4, 2.4], [1.5, 1.5, 2.5])]
    registry = compile_surface_registry(model, data, source, snapshot)
    assert set(registry["surfaces"]) == {4, 5}
    assert set(registry["uncertain_surface_ids"]) == {4, 5}
    assert selected(registry, "-Y", [1, 3]) == set()


def test_incomplete_connection_coverage_does_not_assume_upper_membership():
    model, data, snapshot = fixture()
    snapshot["affiliations_complete"] = False
    registry = compile_surface_registry(model, data, [spec(7, [1, -1.99, 1], [1.1, -1.95, 1.1])], snapshot)
    assert selected(registry, "-Y", [1, 3]) == {7}
    assert selected(registry, "upper_up", [3]) == set()


def test_ownerless_explicit_wall_uses_parallel_geometry_not_perpendicular_root():
    model, data, snapshot = fixture()
    source = spec(4, [-2, -2.1, 0], [2, -2, 3], structural_role="wall")
    registry = compile_surface_registry(model, data, [source], snapshot)
    assert selected(registry, "-Y", [1, 3]) == {4}
    assert registry["surfaces"][4]["structural_role"] == "wall"


def test_view_bounds_are_in_native_room_frame():
    model, data, snapshot = fixture()
    source = spec(3, [-0.5, -1.9, 1.4], [0.5, -1.8, 2], owner=3)
    registry = compile_surface_registry(model, data, [source], snapshot)
    assert select_surface_ids(registry, 0, "-Y", {1, 3}, [1, 1, 1], [2, 2, 2]) == set()


def test_slab_selection_has_no_name_or_backing_special_case():
    points = vertices([-2, -0.05, 0], [2, 0.05, 3])
    keep, receipt = select_shell_faces(points, FACES, "wall", np.zeros(3), np.eye(3), [0, 2, 1.5])
    assert keep.sum() == 2
    assert np.all(points[FACES[keep], 1] == 0.05)
    assert receipt["name_based_selection"] is False
    assert receipt["duplicate_layer_removed"] is False


def test_geom_and_instance_renaming_preserves_wall_faces_and_membership():
    model, data, snapshot = fixture()
    source = spec(4, [-2, -2.1, 0], [2, -2, 3], structural_role="wall")
    renamed = dict(source, name="arbitrary_backing_surface", source_instance=["ep_meta", "different_instance"])
    registries = [compile_surface_registry(model, data, [item], snapshot) for item in (source, renamed)]
    assert selected(registries[0], "-Y", [1, 3]) == selected(registries[1], "-Y", [1, 3]) == {4}
    masks = []
    for registry in registries:
        row = registry["surfaces"][4]
        mask, _ = select_shell_faces(row["local_vertices"], row["faces"], row["structural_role"], row["position"], row["rotation"], snapshot["rooms"][0]["center"])
        masks.append(mask)
    np.testing.assert_array_equal(*masks)
    assert masks[0].sum() == 2


def test_coincident_distinct_geoms_and_materials_are_not_fused():
    model, data, snapshot = fixture()
    source = [spec(gid, [1, -1.99, 1], [1.1, -1.95, 1.1]) for gid in (4, 5)]
    registry = compile_surface_registry(model, data, source, snapshot)
    assert selected(registry, "-Y", [1, 3]) == {4, 5}
    assert registry["surfaces"][4]["material_id"] != registry["surfaces"][5]["material_id"]


def test_rotated_slab_selects_same_original_face_indices():
    points = vertices([-2, -0.05, 0], [2, 0.05, 3])
    angle = 0.71
    rotation = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    expected, _ = select_shell_faces(points, FACES, "wall", [0, 0, 0], np.eye(3), [0, 2, 1.5])
    actual, _ = select_shell_faces(points, FACES, "wall", [4, 5, 0], rotation, np.array([0, 2, 1.5]) @ rotation.T + [4, 5, 0])
    np.testing.assert_array_equal(expected, actual)


@pytest.mark.parametrize("role", [None, "wall"])
def test_uncertain_open_thin_sheet_is_not_erased(role):
    points = np.array([[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]], float)
    keep, receipt = select_shell_faces(points, [[0, 1, 2], [0, 2, 3]], role, [0, 0, 0], np.eye(3), [0, 2, 1])
    assert keep.all() and receipt["policy"].startswith("PRESERVED")


def test_incomplete_slab_and_ambiguous_interior_keep_all_faces():
    points = vertices([-2, -0.05, 0], [2, 0.05, 3])
    keep, _ = select_shell_faces(points, FACES[:-1], "wall", [0, 0, 0], np.eye(3), [0, 2, 1.5])
    assert keep.all()
    keep, _ = select_shell_faces(points, FACES, "wall", [0, 0, 0], np.eye(3), [0, 0, 1.5])
    assert keep.all()


def test_duplicate_geom_id_is_rejected_not_silently_replaced():
    model, data, snapshot = fixture()
    source = spec(1, [0, 0, 0], [1, 1, 1])
    with pytest.raises(ContractError, match="duplicate"):
        compile_surface_registry(model, data, [source, source], snapshot)
