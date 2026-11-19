"""BEHAVIOR-1K source Object/Link adapter to the ONE G2 native view planner.

This module NEVER assigns Room / Floor / Wall / Island membership, does not
produce pixels, and does not change G2 renderer algorithms. It only maps
source-native OmniGibson Object+Part names to the exact already-certified
G2 nav_sg entity IDs in the shared renderer_member_sets() output.

The current Oracle/no-color mode is explicitly diagnostic. Future certified
Full Map modes require a separate source-proof gate; never auto-promote.
"""
from __future__ import annotations

from collections import Counter

from g2.io import ContractError
from g2.nav_bridge.snapshot import validate_snapshot
from g2.views.render_connections import renderer_member_sets

SCHEMA="g3_b1k_native_source_bound_g2_view_membership_v1"
ORACLE_TRANSPORT="ORACLE_DIAGNOSTIC_GEOMETRY_ONLY_NO_PRESCAN"


def _sha64(value):
    return (isinstance(value,str) and len(value)==64 and
            all(c in "0123456789abcdef" for c in value))


def bind_b1k_visual_parts(snapshot,live_objects,*,source_sha256,scene_id):
    """Validate the original shared G2 Snapshot and bind its *native* parts.

    live_objects are PersistentB1KWorldState.objects, not fabricated category
    guesses or a 1m OmniGibson Room map. Part keys must match the original
    OmniGibson Link names. Inputs are in-process on the licensed simulator.
    """
    if not _sha64(source_sha256) or not isinstance(scene_id,str) or not scene_id:
        raise ContractError("missing source-bound B1K scene/geometry identity")
    snap=validate_snapshot(snapshot)
    if (snap["source_mode"]!="oracle_diagnostic" or
        snap.get("surface_transport_mode")!=ORACLE_TRANSPORT or
        snap.get("surface_color_source")!="ORACLE_DIAGNOSTIC_NO_COLOR" or
        snap.get("geometry_source_mode")!="ORACLE_GRID" or
        snap.get("structure_mode")!="ORACLE_DIAGNOSTIC" or
        snap.get("scene_id")!=scene_id or
        snap.get("source_sha256")!=source_sha256):
        raise ContractError("B1K diagnostic and native SpatialSnapshot proof differ")
    if not isinstance(live_objects,dict) or not live_objects:
        raise ContractError("native B1K live Object/Link catalog required")
    entities={}
    parts={}
    for entity in snap["entities"]:
        eid=entity["id"]
        src=entity.get("source_instance_id")
        part=entity.get("source_part_id")
        category=entity.get("source_category_id")
        role=entity.get("kind")
        if (not isinstance(src,str) or not src or
            not isinstance(part,str) or not part or
            not isinstance(category,str) or not category or
            role not in ("object","floor","wall")):
            raise ContractError("incomplete B1K native Object/Link semantic binding")
        record=live_objects.get(src)
        if not isinstance(record,dict) or record.get("category")!=category:
            raise ContractError("native Snapshot Object category does not match OG runtime")
        links=record.get("links")
        if not isinstance(links,dict) or part not in links:
            raise ContractError("native Snapshot Part missing in OmniGibson source Link catalog")
        key=(src,part)
        if key in parts:
            raise ContractError("duplicate native source Object+Part identity")
        parts[key]=eid
        entities[eid]=(src,part,role)
    shared_plan=renderer_member_sets(snap)
    room_uids={r["uid"] for r in snap["rooms"]}
    plan={}
    for name,view in sorted(shared_plan.items()):
        if view.get("room_uid") not in room_uids or view.get("axis") not in (
            "floor_top","upper_up","+X","-X","+Y","-Y"):
            raise ContractError("unknown G2 native Room/axis selector")
        members=view.get("native_entity_ids")
        if not isinstance(members,list) or len(set(members))!=len(members):
            raise ContractError("G2 renderer returned malformed view member IDs")
        if any(eid not in entities for eid in members):
            raise ContractError("G2 renderer selected absent source Object/Part")
        # IMPORTANT: do NOT add e.g. a full parent object when only one of
        # its articulated parts belongs in this Room/Wall view. Preserve the
        # exact part list, and let the original F27 rendering stage decide
        # projectability and whether an empty direction needs a PNG.
        bound=[
            {"native_entity_id":eid,
             "source_instance_id":entities[eid][0],
             "source_part_id":entities[eid][1],
             "native_kind":entities[eid][2]}
            for eid in members
        ]
        plan[name]={
            "axis":view["axis"],"room_uid":view["room_uid"],
            "island_id":view.get("island_id"),
            "native_entity_ids":list(members),
            "source_parts":bound,
            "selection_origin":"ORIGINAL_G2_renderer_member_sets",
            "render_status":"NOT_RENDERED_DIAGNOSTIC_ONLY",
        }
    receipt={
        "schema":SCHEMA,
        "source_mode":"oracle_diagnostic",
        "scene_id":scene_id,
        "source_sha256":source_sha256,
        "source_validation":"ORIGINAL_G2_validate_snapshot_AND_renderer_member_sets",
        "role_counts":dict(Counter(e["kind"] for e in snap["entities"])),
        "room_uids":sorted(room_uids),
        "view_count":len(plan),
        "view_plan":plan,
        "semantic_room_labels_used_as_authority":False,
        "source_parts_are_original_links":True,
        "connections_recomputed_in_B1K_adapter":False,
        "visual_pixels_generated":False,
        "full_map_ready":False,
        "training_ready":False,
    }
    return receipt
