"""Fail-closed, opt-in 10mm native source-only transport for RoboCasa F27."""
import copy
import hashlib
from pathlib import Path

import pytest

from g2.io import ContractError
from g2.offline.native_transport import sha_file,write_color_only_sequence
from g2.offline import atomic_6views_run as runner


@pytest.fixture
def prepared(tmp_path):
    sources=[]
    for index,frame in enumerate((0,10)):
        path=tmp_path/f"frame_{frame}.g2layer10.bin"
        path.write_bytes(f"native source visual layer {frame}".encode())
        sources.append(dict(
            frame=frame,source_scene_id="robocasa_source_scene",
            source_sha256="a"*64,
            source_state_sha256=str(index+1)*64,
            source_state_file_sha256="e"*64,
            data_file=str(path),binary_sha256=sha_file(path),
            expected_full_color_sha256=str(index+3)*64,
            expected_full_color_voxels=40+index,
            expected_unknown_owner_cells=5+index,
            initial_all_static_and_dynamic=(index==0)))
    return dict(schema="g2_direct_color_episode_prepared_v1",
                native_color_only_without_10cm_nav=True,
                navigation_manifest_sha256=None,training_ready=False,
                source_sha256="a"*64,layout=9,complete_episode_states=2,
                frames=[0,10],states=sources,
                original_states_file_sha256="e"*64)


def test_no_navigation_or_rgbd_is_declared(prepared,tmp_path):
    path=tmp_path/"native_source_only.txt"
    result=write_color_only_sequence(path,prepared)
    text=path.read_text()
    assert result==sha_file(path)
    assert text.startswith("F24_G2_NATIVE_COLOR_ONLY_SEQUENCE_V1\n")
    assert "nav_states" not in text
    assert "known_free_region" not in text
    assert all("RGBD" not in line for line in text.splitlines()[:5])
    assert text.splitlines()[4]=="rows 2"


@pytest.mark.parametrize("tamper",(
    lambda x:x.update(native_color_only_without_10cm_nav=False),
    lambda x:x.update(navigation_manifest_sha256="0"*64),
    lambda x:x.update(training_ready=True),
    lambda x:x.update(complete_episode_states=3),
    lambda x:x["states"][1].update(source_sha256="f"*64),
    lambda x:x["states"][1].update(frame=0),
    lambda x:x["states"][1].update(source_state_file_sha256="9"*64),
    lambda x:x["states"][1].update(initial_all_static_and_dynamic=True),
    lambda x:x["states"][1].update(expected_unknown_owner_cells=100),
    lambda x:x["states"][1].update(binary_sha256="a"*64),
))
def test_color_only_manifest_tampering_rejected(prepared,tmp_path,tamper):
    mutated=copy.deepcopy(prepared)
    tamper(mutated)
    with pytest.raises((ContractError,ValueError,KeyError,TypeError)):
        write_color_only_sequence(tmp_path/"not_published.txt",mutated)
    assert not (tmp_path/"not_published.txt").exists()


def test_original_binary_tampering_rejected(prepared,tmp_path):
    Path(prepared["states"][0]["data_file"]).write_bytes(b"payload was replaced")
    with pytest.raises(ContractError,match="mutated"):
        write_color_only_sequence(tmp_path/"not_published.txt",prepared)


def test_never_overwrites_existing_transport(prepared,tmp_path):
    path=tmp_path/"existing.txt"
    path.write_text("PRESERVE THIS")
    with pytest.raises(FileExistsError):
        write_color_only_sequence(path,prepared)
    assert path.read_text()=="PRESERVE THIS"


def test_explicit_cli_optin_and_default_legacy_unchanged(tmp_path):
    assert runner.parser().parse_args(["plan"]).sim_color_only is False
    assert runner.parser().parse_args(["plan","--sim-color-only"]).sim_color_only is True
    assert runner.WorkerConfig.__dataclass_fields__["sim_color_only"].default is False
    with pytest.raises(ContractError,match="requires --sim-direct-geometry-only"):
        runner.main(["plan","--sim-color-only",
                     "--plan-root",str(tmp_path/"never_scan_sources")])
