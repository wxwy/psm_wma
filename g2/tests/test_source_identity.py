"""Public-schema reproductions only; no server ep_meta or private assets."""
import pytest
from g2.io import ContractError
from g2.sim.prescan import pointer, source_binding


def spec(collection="fixtures", instance="outlet_room", path=None, **kwargs):
    return {"role":"visual", "source_kind":"ep_meta", "source_instance_name":instance,
            "ep_meta_pointer":path or "/fixtures/outlet_room", **kwargs}


@pytest.mark.parametrize("fixture_class",["WallAccessory","HingeCabinet"])
def test_official_fixture_identity_lives_in_dict_key(fixture_class):
    ep={"fixtures":{"outlet_room":{"cls":fixture_class}}}
    result=source_binding(spec(),"TEST_ONLY_geom",ep)
    assert result["instance_name"]=="outlet_room"
    assert result["collection"]=="fixtures"
    assert result["category"]=={"field":"cls","value":fixture_class}
    assert result["record"]==ep["fixtures"]["outlet_room"]


def test_object_cfg_list_binds_name_and_original_group_provenance():
    ep={"object_cfgs":[{"name":"obj","obj_groups":["cup","mug"]}]}
    result=source_binding(spec(instance="obj",path="/object_cfgs/0"),"g",ep)
    assert result["category"]=={"field":"obj_groups","value":["cup","mug"]}


def test_escaped_fixture_key_is_exact_identity():
    ep={"fixtures":{"a/b~c":{"cls":"WallAccessory"}}}
    result=source_binding(spec(instance="a/b~c",path="/fixtures/a~1b~0c"),"g",ep)
    assert result["instance_name"]=="a/b~c"


@pytest.mark.parametrize("change",[
    {"source_instance_name":"wrong"}, {"ep_meta_pointer":"/fixtures/missing"},
    {"ep_meta_pointer":"/fixtures/outlet_room/cls"}, {"source_category":"Cabinet"},
    {"source_category_field":"obj_groups"}, {"source_collection":"object_cfgs"},
    {"role":"robot"}, {"role":"not_a_role"}])
def test_wrong_fixture_identity_category_pointer_or_role_rejected(change):
    ep={"fixtures":{"outlet_room":{"cls":"WallAccessory"}}}
    with pytest.raises(ContractError):source_binding(spec(**change),"g",ep)


@pytest.mark.parametrize("record",[{}, {"cls":""}, {"cls":" "}, {"cls":7},
    {"cls":"WallAccessory","name":"conflicting_name"}])
def test_missing_or_conflicting_official_fixture_category_rejected(record):
    with pytest.raises(ContractError):
        source_binding(spec(),"g",{"fixtures":{"outlet_room":record}})


def test_fixtures_list_is_not_silently_treated_as_official_dict():
    with pytest.raises(ContractError):
        source_binding(spec(instance="f",path="/fixtures/0"),"g",{"fixtures":[{"name":"f","cls":"WallAccessory"}]})


@pytest.mark.parametrize("fault",["wrong_category","duplicate_name","robot_role","missing_category"])
def test_object_cfgs_fail_closed(fault):
    ep={"object_cfgs":[{"name":"obj","obj_groups":"cup"}]}
    s=spec(instance="obj",path="/object_cfgs/0")
    if fault=="wrong_category":s["source_category"]="plate"
    elif fault=="duplicate_name":ep["object_cfgs"].append(dict(ep["object_cfgs"][0]))
    elif fault=="robot_role":s["role"]="robot"
    else:ep["object_cfgs"][0].pop("obj_groups")
    with pytest.raises(ContractError):source_binding(s,"g",ep)


@pytest.mark.parametrize("path",["/a~2b","/list/-1","/list/00","/list/+0","/list/ 0","/list/-"])
def test_json_pointer_rejects_invalid_escapes_and_array_tokens(path):
    with pytest.raises(ContractError):pointer({"a~2b":1,"list":[1]},path)


def test_json_pointer_root_and_escaped_tokens():
    document={"a/b":{"~key":[42]}}
    assert pointer(document,"") is document
    assert pointer(document,"/a~1b/~0key/0")==42


def test_mjcf_cannot_silently_keep_official_identity_assertions():
    with pytest.raises(ContractError):
        source_binding({**spec(),"source_kind":"mjcf","geom_name":"g"},"g",{})
