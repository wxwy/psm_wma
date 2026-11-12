"""Source-bound, simulation-only geometry bootstrap and no-cloud negative gates."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from g2.io import ContractError, canonical
from g2.nav_bridge import fullmap_geometry_only as direct
from g2.offline import atomic_6views_run as runner


@pytest.fixture
def source_gt(tmp_path):
    src=tmp_path/"native_gt"
    src.mkdir()
    files={"grid.txt":b"ORIGINAL_GRID", "objects.txt":b"ORIGINAL_OBJECTS",
           "occupancy.raw":b"\x00\x01\x02"}
    for name,payload in files.items():
        (src/name).write_bytes(payload)
    identity={"schema":"nav_sg_mujoco_oracle_v1","mujoco_version":"3.3.7",
              "source_note":"geometry-only fixture"}
    gt={"schema":"nav_sg_mujoco_oracle_v1",
        "scene_id":"TEST_ONLY_scene","source_identity":identity,
        "source_sha256":hashlib.sha256(canonical(identity)).hexdigest(),
        "state":{"format":"mujoco_fullphysics","frame_id":0,
                 "timestamp":0.5},
        "entities":[{"instance_id":"fixture:box","part_id":"whole"}],
        "files":{name:{"sha256":hashlib.sha256(payload).hexdigest(),
                        "bytes":len(payload)} for name,payload in files.items()}}
    (src/"manifest.json").write_text(json.dumps(gt))
    return src,gt


def test_proof_explicitly_omits_all_color_cloud_and_rgbd_fields(source_gt,tmp_path):
    src,gt=source_gt
    result=direct.prepare(src/"manifest.json",tmp_path/"prepared")
    text=(tmp_path/"prepared/source_proof.txt").read_text()
    assert text.startswith("NAV_SG_FULL_MAP_GEOMETRY_ONLY_V1\n")
    assert 'cloud_sha256' not in text
    assert 'colored_cloud' not in text
    assert 'rgbd' not in text.lower()
    assert result["source_color_transport"]=="NONE_MUJOCO_DIRECT_VISUAL_MESH"
    assert result["source_sha256"]==gt["source_sha256"]
    assert not result["training_ready"]


def test_changed_source_native_geometry_hash_is_rejected(source_gt,tmp_path):
    src,_=source_gt
    (src/"objects.txt").write_bytes(b"CHANGED")
    with pytest.raises(ContractError,match="transport/source"):
        direct.prepare(src/"manifest.json",tmp_path/"prepared")
    assert not (tmp_path/"prepared").exists()


@pytest.mark.parametrize("field,value",[
    ("schema","PERCEPTION_SOURCE"),
    ("state_format","qpos"),
    ("frame_id",100),
    ("training_ready",True),
    ("source_sha256","0"*64),
])
def test_invalid_fullmap_source_fails_closed(source_gt,tmp_path,field,value):
    src,gt=source_gt
    if field=="state_format":gt["state"]["format"]=value
    elif field=="frame_id":gt["state"]["frame_id"]=value
    else:gt[field]=value
    (src/"manifest.json").write_text(json.dumps(gt))
    with pytest.raises(ContractError,match="original frame0"):
        direct.prepare(src/"manifest.json",tmp_path/"prepared")
    assert not (tmp_path/"prepared").exists()


def test_published_or_source_overlapping_destination_rejected(source_gt,tmp_path):
    src,_=source_gt
    with pytest.raises(ContractError):
        direct.prepare(src/"manifest.json",src/"inside")
    direct.prepare(src/"manifest.json",tmp_path/"prepared")
    with pytest.raises(ContractError):
        direct.prepare(src/"manifest.json",tmp_path/"prepared")


def test_direct_geometry_only_is_explicit_cli_opt_in():
    parser=runner.parser()
    assert parser.parse_args(["plan"]).sim_direct_geometry_only is False
    assert parser.parse_args(
        ["plan","--sim-direct-geometry-only"]).sim_direct_geometry_only is True
    assert runner.WorkerConfig.__dataclass_fields__[
        "sim_direct_geometry_only"].default is False


def test_geometry_only_native_gate_cannot_inherit_rgbd_env(monkeypatch,tmp_path):
    for name in ("G2_GT_PRESCAN_FRAME0","G2_GT_FULL_MAP_FRAME0_PROOF",
                 "G2_GT_OBSERVED_COLOR_MANIFEST"):
        monkeypatch.setenv(name,"UNTRUSTED_INHERITED_RGBD")
    configs=SimpleNamespace(
        nav_repo=tmp_path,nav_setup=tmp_path/"catkin_setup.bash",
        min_z=.15,max_z=1.8,port=29992)
    calls=[]
    def stub(argv,*,cwd,env,row,name):
        assert name=="source_gt_geometry_only_native_room_sg"
        assert env["G2_GT_FULL_MAP_GEOMETRY_ONLY_PROOF"] == str(
            tmp_path/"prepared/source_proof.txt")
        for key in ("G2_GT_PRESCAN_FRAME0","G2_GT_FULL_MAP_FRAME0_PROOF",
                    "G2_GT_OBSERVED_COLOR_MANIFEST"):
            assert key not in env
        assert env["G2_GT_EXPORT_SPATIAL"]=="true"
        assert env["G2_GT_MIN_ASSIGNED"]=="0"
        path=tmp_path/"native_root/native_run"
        (path/"frame_0/spatial_snapshot").mkdir(parents=True)
        (path/"frame_0/spatial_snapshot/SNAPSHOT_COMPLETE").write_text("ok")
        (path/"FULL_MAP_PREVIEW_COMPLETE").write_text("ok")
        calls.append(1)
    monkeypatch.setattr(runner,"subprocess_stage",stub)
    runner._native_geometry_gate(
        configs,tmp_path/"prepared",tmp_path/"gt",
        tmp_path/"native_root",{"task_class":"TEST","episode_id":1})
    assert calls==[1]
