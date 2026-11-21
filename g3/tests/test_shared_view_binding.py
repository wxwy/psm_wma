"""Synthetic tests: B1K adapters bind to original G2, never reimplement it."""
from unittest.mock import patch
import unittest

from g2.io import ContractError
from g3.behavior1k.shared_view_binding import bind_b1k_visual_parts

SHA="a"*64
SCENE="synthetic_room_source_for_b1k"

def snapshot():
 return {
  "scene_id":SCENE,"source_sha256":SHA,
  "source_mode":"oracle_diagnostic","geometry_source_mode":"ORACLE_GRID",
  "structure_mode":"ORACLE_DIAGNOSTIC",
  "surface_transport_mode":"ORACLE_DIAGNOSTIC_GEOMETRY_ONLY_NO_PRESCAN",
  "surface_color_source":"ORACLE_DIAGNOSTIC_NO_COLOR",
  "rooms":[{"uid":0}],
  "entities":[
   {"id":"entity_0","kind":"object","source_instance_id":"drawer",
    "source_part_id":"link_0","source_category_id":"bottom_cabinet"},
   {"id":"entity_1","kind":"floor","source_instance_id":"floor",
    "source_part_id":"base_link","source_category_id":"floors"},
  ],
 }

def plan():
 return {"rooms/0/floor_top":{
  "axis":"floor_top","room_uid":0,"island_id":None,
  "native_entity_ids":["entity_0","entity_1"]},
  "rooms/0/upper_up":{
  "axis":"upper_up","room_uid":0,"island_id":None,"native_entity_ids":[]}}

def catalog():
 return {
  "drawer":{"category":"bottom_cabinet","links":{"link_0":{}, "link_1":{}}},
  "floor":{"category":"floors","links":{"base_link":{}}}
 }

def bind(s=None,c=None,p=None):
 with patch("g3.behavior1k.shared_view_binding.validate_snapshot",return_value=s or snapshot()), \
      patch("g3.behavior1k.shared_view_binding.renderer_member_sets",return_value=p or plan()):
  return bind_b1k_visual_parts(s or snapshot(),c or catalog(),
                              scene_id=SCENE,source_sha256=SHA)

class B1KSharedViewBindingTests(unittest.TestCase):
 def test_exact_link_names_not_parent_object_or_extra_link(self):
  result=bind()
  a=result["view_plan"]["rooms/0/floor_top"]
  self.assertEqual(a["native_entity_ids"],["entity_0","entity_1"])
  self.assertEqual([(x["source_instance_id"],x["source_part_id"]) for x in a["source_parts"]],
                   [("drawer","link_0"),("floor","base_link")])
  self.assertNotIn("link_1",[x["source_part_id"] for x in a["source_parts"]])
  self.assertFalse(result["connections_recomputed_in_B1K_adapter"])
  self.assertFalse(result["visual_pixels_generated"])
  self.assertFalse(result["full_map_ready"])
  self.assertEqual(result["view_count"],2)
 def test_rejects_category_mismatch(self):
  c=catalog();c["drawer"]["category"]="floor"
  with self.assertRaises(ContractError):bind(c=c)
 def test_rejects_missing_actual_link(self):
  c=catalog();del c["drawer"]["links"]["link_0"]
  with self.assertRaises(ContractError):bind(c=c)
 def test_rejects_missing_object(self):
  c=catalog();del c["drawer"]
  with self.assertRaises(ContractError):bind(c=c)
 def test_rejects_duplicate_source_part(self):
  s=snapshot();s["entities"].append({**s["entities"][0],"id":"entity_99"})
  with self.assertRaises(ContractError):bind(s=s)
 def test_rejects_mismatched_source_hash(self):
  with self.assertRaises(ContractError):
   with patch("g3.behavior1k.shared_view_binding.validate_snapshot",return_value=snapshot()):
    bind_b1k_visual_parts(snapshot(),catalog(),scene_id=SCENE,source_sha256="b"*64)
 def test_rejects_color_claimed_as_native_oracle(self):
  s=snapshot();s["surface_color_source"]="NATIVE_COLOR_MAP_AND_OBJECT_GEOMETRY"
  with self.assertRaises(ContractError):bind(s=s)
 def test_rejects_muJoCo_fullmap_as_b1k_diagnostic(self):
  s=snapshot();s["source_mode"]="full_map_mujoco_source"
  with self.assertRaises(ContractError):bind(s=s)
 def test_rejects_view_member_not_in_snapshot(self):
  p=plan();p["rooms/0/floor_top"]["native_entity_ids"].append("entity_999")
  with self.assertRaises(ContractError):bind(p=p)
 def test_rejects_view_for_unknown_room(self):
  p=plan();p["rooms/0/floor_top"]["room_uid"]=5
  with self.assertRaises(ContractError):bind(p=p)

if __name__=="__main__":
 unittest.main()
