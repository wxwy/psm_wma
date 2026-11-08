"""Own source-declaration evidence; no automatic semantic role certification."""
import numpy as np
import pytest

from g2.io import ContractError, digest, read_json, write_json
from g2.sim.asset_inventory import inventory
from g2.sim.prescan import export
from g2.sim.source_geometry import load_model, model_source_hash
from g2.sim.source_scope import verify_full_scene_review


@pytest.fixture
def roles_scene(tmp_path):
    root=tmp_path/"own_roles";root.mkdir();xml=root/"model.xml";meta=root/"roles.json"
    xml.write_text('''<mujoco><default><geom rgba=".2 .3 .4 1"/></default><worldbody>
      <body name="fixture_body"><joint type="slide" axis="1 0 0"/>
        <geom name="visible" type="box" size=".2 .3 .4"/>
        <geom name="collision" type="box" size=".2 .3 .4" group="1"/></body>
      <body name="robot_source_body"><geom name="robot" type="sphere" size=".1"/></body>
      <geom name="auxiliary" type="sphere" size=".1" rgba="1 0 0 0"/>
      </worldbody></mujoco>''')
    values={name:{"role":role,"source_kind":"mjcf","geom_name":name,
        "classification_reason":"Own explicitly authored "+role+" source"}
        for name,role in (("visible","visual"),("collision","collision"),("robot","robot"),("auxiliary","auxiliary"))}
    values["robot"]["source_body_name"]="robot_source_body"
    write_json(meta,{"schema":"g2_sim_prescan_v1","scene_id":"TEST_ONLY_SOURCE_ROLES","geoms":values})
    return root,xml,meta


def bound_metadata(scene,out):
    _,xml,meta=scene
    audited=inventory(xml,out,metadata=meta)
    template=read_json(out/"roles_template.json")
    write_json(meta,template)
    return audited,template


def test_inventory_source_nodes_do_not_assign_roles_or_certify_them(roles_scene,tmp_path):
    _,xml,_=roles_scene
    result=inventory(xml,tmp_path/"inv",scene_id="TEST_ONLY_SOURCE_ROLES")
    assert result["summary"]["role_counts"]=={"UNCLASSIFIED":4}
    assert result["source_role_documents"][0]["source_defaults"]
    for row in result["geom_audit"]:
        evidence=row["role_evidence"]
        assert evidence["status"]=="SOURCE_BOUND" and evidence["role_certified"] is False
        node=evidence["source_geom_nodes"][0]
        assert node["attributes"]["name"]==row["geom_name"]
        assert node["source_sha256"]==digest(xml)
        assert node["xml_path"].startswith("/mujoco/worldbody[0]/")
        assert evidence["asserted_role"] is None
    template=read_json(tmp_path/"inv/roles_template.json")
    assert all(spec["role"] is None and spec["role_evidence"]["asserted_role"] is None for spec in template["geoms"].values())


def test_explicit_bound_roles_export_and_robot_exclusion_has_original_body_proof(roles_scene,tmp_path):
    _,xml,meta=roles_scene
    _,template=bound_metadata(roles_scene,tmp_path/"inv")
    result=export(xml,meta,tmp_path/"out",require_role_evidence=True,spacing=.3)
    rows={row["geom_name"]:row for row in result["geom_audit"]}
    assert rows["robot"]["source"]["body_binding"]["status"]=="VERIFIED"
    assert rows["robot"]["role_evidence"]["source_geom_nodes"][0]["body_ancestors"]==["robot_source_body"]
    assert all(row["role_evidence"]["assertion_checked"] for row in rows.values())
    assert set(row["geom_name"] for row in result["visual_geoms"])=={"visible"}
    assert result["unclassified_geom_count"]==0 and result["training_ready"] is False
    assert result["gates"]["full_scene_source_certified"] is False


@pytest.mark.parametrize("fault",["signature","node","asserted_role","missing_proof","robot_root","reason","source_edit"])
def test_strict_role_evidence_rejects_unbound_assertions(roles_scene,tmp_path,fault):
    _,xml,meta=roles_scene
    _,values=bound_metadata(roles_scene,tmp_path/"inv")
    spec=values["geoms"]["visible"]
    if fault=="signature":spec["role_evidence"]["compiled_signature_sha256"]="0"*64
    elif fault=="node":spec["role_evidence"]["source_geom_node_sha256"]="0"*64
    elif fault=="asserted_role":spec["role_evidence"]["asserted_role"]="auxiliary"
    elif fault=="missing_proof":del spec["role_evidence"]
    elif fault=="robot_root":values["geoms"]["robot"].pop("source_body_name")
    elif fault=="reason":spec["classification_reason"]=""
    else:xml.write_text(xml.read_text().replace('size=".2 .3 .4"','size=".21 .3 .4"',1))
    write_json(meta,values)
    with pytest.raises(ContractError):export(xml,meta,tmp_path/"out",require_role_evidence=True)
    assert not (tmp_path/"out/COMPLETE").exists()


def test_unknown_role_is_partial_source_and_never_changed_to_auxiliary(roles_scene,tmp_path):
    _,xml,meta=roles_scene
    _,values=bound_metadata(roles_scene,tmp_path/"inv")
    del values["geoms"]["collision"]
    write_json(meta,values)
    result=export(xml,meta,tmp_path/"out",require_role_evidence=True,allow_unclassified=True,spacing=.3)
    row=next(row for row in result["geom_audit"] if row["geom_name"]=="collision")
    assert row["role"]=="UNCLASSIFIED" and row["color_status"]=="EXCLUDED_UNCLASSIFIED"
    assert row["source"]["kind"]=="unclassified" and row["surface_points"]==0
    assert result["status"]=="PARTIAL_SOURCE" and result["unclassified_geom_count"]==1
    assert result["source_audit"]["full_scene_review_eligible"] is False
    assert result["training_ready"] is False and not (tmp_path/"out/COMPLETE").exists()
    with pytest.raises(ContractError):verify_full_scene_review(tmp_path/"out/manifest.json",tmp_path/"out/manifest.json")


def test_untrusted_robot_exclusion_becomes_explicit_gap_in_partial_mode(roles_scene,tmp_path):
    _,xml,meta=roles_scene
    _,values=bound_metadata(roles_scene,tmp_path/"inv")
    del values["geoms"]["robot"]["source_body_name"]
    write_json(meta,values)
    result=export(xml,meta,tmp_path/"out",require_role_evidence=True,allow_unclassified=True)
    row=next(row for row in result["geom_audit"] if row["geom_name"]=="robot")
    assert row["role"]=="UNCLASSIFIED" and "robot exclusion" in row["declaration_error"]
    assert result["status"]=="PARTIAL_SOURCE"


def test_role_signature_and_original_node_identity_survive_frame_motion(roles_scene,tmp_path):
    root,xml,meta=roles_scene
    _,values=bound_metadata(roles_scene,tmp_path/"inv")
    _,sources=load_model(xml)
    qpos=np.zeros((201,1));qpos[200]=.12
    states=root/"states.npz";np.savez(states,qpos=qpos,time=np.arange(201)*.02)
    values["state_source"]={"model_source_sha256":model_source_hash(sources),"states_sha256":digest(states)}
    write_json(meta,values)
    first=export(xml,meta,tmp_path/"f0",states=states,require_role_evidence=True,spacing=.3)
    later=export(xml,meta,tmp_path/"f200",states=states,frame=200,require_role_evidence=True,spacing=.3)
    a=next(row for row in first["geom_audit"] if row["geom_name"]=="visible")
    b=next(row for row in later["geom_audit"] if row["geom_name"]=="visible")
    assert a["role_evidence"]==b["role_evidence"]
    assert a["world_position"]!=b["world_position"]
    assert first["source_sha256"]==later["source_sha256"]


@pytest.mark.parametrize("extension",[".inc",".mjcf",".xml"])
def test_include_extension_and_enclosing_robot_body_are_source_evidence(roles_scene,tmp_path,extension):
    root,xml,meta=roles_scene
    fragment=root/("robot_part"+extension)
    fragment.write_text('<mujocoinclude><geom name="robot" type="sphere" size=".1"/></mujocoinclude>')
    xml.write_text(xml.read_text().replace('<geom name="robot" type="sphere" size=".1"/>',
                                         '<include file="'+fragment.name+'"/>'))
    result,template=bound_metadata(roles_scene,tmp_path/"inv")
    row=next(row for row in result["geom_audit"] if row["geom_name"]=="robot")
    node=row["role_evidence"]["source_geom_nodes"][0]
    assert node["body_ancestors"]==["robot_source_body"]
    assert node["source_sha256"]==digest(fragment)
    assert node["inclusion_chain"][0]["reference"]==fragment.name
    assert node["inclusion_chain"][0]["source_sha256"]==digest(xml)
    assert node["source_logical_id"].endswith(extension)
    candidate=export(xml,meta,tmp_path/"out",require_role_evidence=True,spacing=.3)
    assert candidate["unclassified_geom_count"]==0


def test_excluded_plane_uses_same_compiled_signature_in_inventory_and_export(roles_scene,tmp_path):
    _,xml,meta=roles_scene
    xml.write_text(xml.read_text().replace('</worldbody>',
        '<geom name="plane" type="plane" size="0 0 .1"/></worldbody>'))
    values=read_json(meta)
    values["geoms"]["plane"]={"role":"auxiliary","source_kind":"mjcf","geom_name":"plane",
        "classification_reason":"Own explicit test diagnostic plane, source decision requires external review"}
    write_json(meta,values)
    audit,_=bound_metadata(roles_scene,tmp_path/"inv")
    result=export(xml,meta,tmp_path/"out",require_role_evidence=True,spacing=.3)
    a=next(row for row in audit["geom_audit"] if row["geom_name"]=="plane")
    b=next(row for row in result["geom_audit"] if row["geom_name"]=="plane")
    assert a["geometry_type"]==b["geometry_type"]=="plane"
    assert a["role_evidence"]["compiled_signature_sha256"]==b["role_evidence"]["compiled_signature_sha256"]
    assert b["surface_points"]==0
