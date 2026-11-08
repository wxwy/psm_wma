"""Public review schema and self-created MJCF only; no private server files."""
import copy
import pytest
from g2.io import ContractError,write_json
from g2.sim.prescan import export,source_binding


@pytest.fixture
def ep_meta():
    return {"object_cfgs":[
        {"name":"obj","type":"object","obj_groups":["tool","utensil"],"info":{"cat":"whisk"}},
        {"name":"distr","type":"object","info":{"cat":"soap_dispenser"}}]}


def spec(index,**kwargs):
    return {"role":"visual","source_kind":"ep_meta","source_instance_name":"obj" if index==0 else "distr",
            "ep_meta_pointer":"/object_cfgs/"+str(index),**kwargs}


@pytest.mark.parametrize("index,category",[(0,"whisk"),(1,"soap_dispenser")])
def test_default_retains_groups_fine_category_and_coarse_type(ep_meta,index,category):
    before=copy.deepcopy(ep_meta)
    b=source_binding(spec(index),"TEST_ONLY_geom",ep_meta)
    assert b["fine_category"]=={"field":"info.cat","value":category}
    assert b["coarse_type"]=={"field":"type","value":"object"}
    assert b["category"]==({"field":"obj_groups","value":["tool","utensil"]} if index==0 else
                          {"field":"info.cat","value":"soap_dispenser"})
    assert b["record"]==before["object_cfgs"][index] and ep_meta==before


@pytest.mark.parametrize("index,category",[(0,"whisk"),(1,"soap_dispenser")])
def test_explicit_nested_category_matches_exact_original_value(ep_meta,index,category):
    b=source_binding(spec(index,source_category_field="info.cat",source_category=category),"g",ep_meta)
    assert b["category"]=={"field":"info.cat","value":category}


@pytest.mark.parametrize("field",["obj_groups","obj_type","cls"])
def test_legacy_fields_without_info_keep_existing_binding(field):
    value=["cup"] if field=="obj_groups" else "cup"
    ep={"object_cfgs":[{"name":"obj",field:value}]}
    b=source_binding(spec(0),"g",ep)
    assert b["category"]=={"field":field,"value":value}
    assert "fine_category" not in b and "coarse_type" not in b


@pytest.mark.parametrize("field",["type","info/cat","info.cat.extra"])
def test_coarse_type_and_arbitrary_paths_are_not_fine_categories(ep_meta,field):
    with pytest.raises(ContractError):source_binding(spec(1,source_category_field=field),"g",ep_meta)


@pytest.mark.parametrize("fault",["missing_info","missing_cat","null_info","list_info","text_info",
                                  "null_cat","empty_cat","blank_cat","list_cat","int_cat","bool_cat"])
def test_missing_or_malformed_nested_category_fails_closed(ep_meta,fault):
    record=ep_meta["object_cfgs"][1]
    if fault=="missing_info":record.pop("info")
    elif fault=="missing_cat":record["info"]={}
    elif fault in ("null_info","list_info","text_info"):
        record["info"]={"null_info":None,"list_info":[],"text_info":"soap_dispenser"}[fault]
    else:record["info"]["cat"]={"null_cat":None,"empty_cat":"","blank_cat":" ",
                                "list_cat":["soap_dispenser"],"int_cat":1,"bool_cat":True}[fault]
    with pytest.raises(ContractError):source_binding(spec(1),"g",ep_meta)


@pytest.mark.parametrize("index",[0,1])
def test_bad_expected_fine_category_cannot_use_group_or_type(ep_meta,index):
    with pytest.raises(ContractError):
        source_binding(spec(index,source_category_field="info.cat",source_category="object"),"g",ep_meta)


def test_legacy_groups_cannot_hide_malformed_fine_category(ep_meta):
    ep_meta["object_cfgs"][0]["info"]["cat"]=None
    with pytest.raises(ContractError):source_binding(spec(0),"g",ep_meta)


def test_duplicate_object_name_remains_ambiguous(ep_meta):
    ep_meta["object_cfgs"].append(copy.deepcopy(ep_meta["object_cfgs"][1]))
    with pytest.raises(ContractError):source_binding(spec(1),"g",ep_meta)


@pytest.mark.parametrize("path",["/object_cfgs/0","/object_cfgs/01","/object_cfgs/1/info"])
def test_wrong_or_noncanonical_source_pointer_is_rejected(ep_meta,path):
    with pytest.raises(ContractError):source_binding(spec(1,ep_meta_pointer=path),"g",ep_meta)


def test_flat_dotted_key_cannot_replace_nested_info(ep_meta):
    record=ep_meta["object_cfgs"][1];record.pop("info");record["info.cat"]="soap_dispenser"
    with pytest.raises(ContractError):source_binding(spec(1,source_category_field="info.cat"),"g",ep_meta)


def test_official_object_cannot_be_silently_switched_to_mjcf(ep_meta):
    with pytest.raises(ContractError):source_binding(spec(1,source_kind="mjcf",geom_name="g"),"g",ep_meta)


def test_nested_categories_survive_full_geom_audit_without_promoting_scope(ep_meta,tmp_path):
    from g2.sim.source_scope import verify_full_scene_review
    from g2.tests.test_source_scope import review_for
    source=tmp_path/"source";source.mkdir()
    model=source/"model.xml";metadata=source/"roles.json";ep=source/"ep_meta.json"
    model.write_text('''<mujoco><worldbody>
      <body name="obj_body"><geom name="obj_visual" type="box" size=".1 .1 .1" rgba=".1 .2 .3 1"/></body>
      <body name="distr_body" pos="1 0 0"><geom name="distr_visual" type="box" size=".1 .1 .1" rgba=".3 .4 .5 1"/></body>
      </worldbody></mujoco>''')
    geoms={name+"_visual":spec(index,source_category_field="info.cat",source_body_name=name+"_body",
        classification_reason="TEST_ONLY explicit source-authored visual") for index,name in enumerate(("obj","distr"))}
    write_json(metadata,{"schema":"g2_sim_prescan_v1","scene_id":"TEST_ONLY_nested_category","geoms":geoms})
    write_json(ep,ep_meta);out=tmp_path/"out"
    m=export(model,metadata,out,ep_meta=ep,spacing=.2)
    rows={row["geom_name"]:row for row in m["geom_audit"]}
    assert len(rows)==m["compiled_geom_count"]==2
    assert rows["distr_visual"]["source"]["category"]=={"field":"info.cat","value":"soap_dispenser"}
    assert rows["obj_visual"]["source"]["fine_category"]["value"]=="whisk"
    assert "soap_dispenser" not in (out/"precolored.txt").read_text()
    assert m["completion_scope"]=="DECLARED_VISUAL_GEOMS_ONLY" and m["training_ready"] is False
    assert m["gates"]["full_scene_source_certified"] is False
    with pytest.raises(ContractError):verify_full_scene_review(out/"manifest.json",None)
    # TEST_ONLY external-review protocol fixture; no real human acceptance.
    assert verify_full_scene_review(out/"manifest.json",review_for(out,m))["status"]=="REVIEWED_FULL_SCENE_SOURCE"
