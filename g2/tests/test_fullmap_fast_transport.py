"""Simulation-only native transport regression; RGB-D is not involved."""
from pathlib import Path

import pytest

from g2.io import ContractError
from g2.nav_bridge.fullmap_transport import verify_native_color_transport


@pytest.fixture
def rows(tmp_path):
    pytest.importorskip("pandas")
    source=tmp_path/"precolored.txt"
    output=tmp_path/"surfaces.csv"
    source.write_text(
        "NAV_SG_PRECOLORED_CLOUD_V1\n"
        "scene_id \"TEST\"\nsource_sha256 x\nframe_id 0\n"
        "world_frame \"world\"\npoints 3\ndata\n"
        "0.125 0.5 0.25 7 8 9 1\n"
        "0.375 0.5 0.25 25 50 125 1\n"
        "0.625 0.5 0.25 0 0 0 0\n"
    )
    output.write_text(
        "x,y,z,red,green,blue,color_valid,entity_id\n"
        "0.125,0.5,0.25,7,8,9,1,entity_7\n"
        "0.375,0.5,0.25,25,50,125,1,unknown\n"
        "0.625,0.5,0.25,0,0,0,0,entity_7\n"
    )
    return source,output


def test_source_xyz_color_mask_count_and_unknown_are_preserved(rows):
    assert verify_native_color_transport(*rows,{"entity_7"},3)==3


@pytest.mark.parametrize("from_text,to_text,message",[
    ("0.125,0.5", "0.625,0.5", "XYZ"),
    ("0.125,0.5,0.25,7,8,9,1", "0.125,0.5,0.25,9,8,9,1", "RGB"),
    (",unknown\n", ",entity_9\n", "entity label"),
    ("0.625,0.5,0.25,0,0,0,0,entity_7\n", "", "count"),
    ("0.625,0.5,0.25,0,0,0,0,entity_7", "0.625,0.5,0.25,0,0,0,2,entity_7", "RGB"),
])
def test_tampered_transport_fails_closed(rows,from_text,to_text,message):
    source,target=rows
    original=target.read_text()
    assert from_text in original
    target.write_text(original.replace(from_text,to_text,1))
    with pytest.raises(ContractError,match=message):
        verify_native_color_transport(source,target,{"entity_7"},3)


@pytest.mark.parametrize("bad", [0,-1,True,5_000_001])
def test_invalid_count_fails_closed(rows,bad):
    with pytest.raises(ContractError):
        verify_native_color_transport(*rows,{"entity_7"},bad)


def test_source_file_tamper_fails_closed(rows):
    source,target=rows
    source.write_text(source.read_text().replace("0.125 0.5 0.25 7 8 9 1",
                                                 "0.125 0.5 0.25 13 8 9 1"))
    with pytest.raises(ContractError,match="RGB"):
        verify_native_color_transport(source,target,{"entity_7"},3)


def test_legacy_profile_never_enables_fast_source_transport(tmp_path):
    from g2.nav_bridge.full_map import _verify_snapshot
    from g2.tests.test_full_map_contract import full_case
    snapshot=full_case()
    snapshot["source_mode"]="perception"
    with pytest.raises(ContractError):
        _verify_snapshot(tmp_path,snapshot,{} ,tmp_path/"proof",
                         trust_native_owner=True)


def test_full_map_capture_default_is_deep():
    import inspect
    from g2.nav_bridge.full_map import capture,_verify_snapshot
    assert inspect.signature(capture).parameters["trust_native_owner"].default is False
    assert inspect.signature(_verify_snapshot).parameters["trust_native_owner"].default is False
