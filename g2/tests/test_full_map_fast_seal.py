"""Full Map production sealing and white-only upper view regression gates.

Checks that an already fully source-audited bundle is sealed by byte identity
rather than a second expensive point-by-point reparse. The public bundle load
still requires the original deep validator.
"""
import hashlib
import json
from pathlib import Path

import pytest

from g2.io import ContractError, canonical
from g2.nav_bridge import full_map


def _bundle_fixture(tmp_path):
    p=tmp_path/"bundle"
    p.mkdir()
    originals={}
    snapshot={
        "scene_id":"test_source", "source_sha256":"a"*64,
        "frame_id":0,"timestamp_ns":123,"world_frame":"world",
        "source_mode":"full_map_mujoco_source",
        "native_build_source_sha256":"b"*64,
        "geometry_source_mode":"FULL_MAP_MUJOCO_SOURCE",
    }
    for name in full_map.NATIVE_FILES | full_map.EVIDENCE_FILES:
        file=p/name
        if name=="snapshot.json":
            file.write_text(json.dumps(snapshot))
        else:
            file.write_bytes(("sealed:"+name).encode())
        originals[name]=file
    files={name:{
        "path":name, "bytes":f.stat().st_size,
        "sha256":hashlib.sha256(f.read_bytes()).hexdigest()
    } for name,f in originals.items()}
    manifest={key:snapshot[key] for key in (
        "scene_id","source_sha256","frame_id","timestamp_ns","world_frame",
        "source_mode","native_build_source_sha256","geometry_source_mode"
    )}
    manifest.update({
        "schema":"g2_native_bundle_v1",
        "source_scope":{"status":full_map.STATUS,"full_scene_source_certified":False},
        "semantic_stage":"MUJOCO_GT_SOURCE_NOT_MODEL_PREDICTIONS",
        "structural_stage":"SOURCE_GT_NATIVE_ROOM_GRAPH",
        "native_structure_proof":None,
        "observation_witness":None,
        "surface_points":1,"files":files,"training_ready":False,
    })
    manifest["version_sha256"]=hashlib.sha256(canonical(manifest)).hexdigest()
    (p/"bundle.json").write_text(json.dumps(manifest))
    return p,manifest,originals


def test_preverified_bundle_copy_sealed_against_each_source_byte(tmp_path):
    root,manifest,originals=_bundle_fixture(tmp_path)
    assert full_map._verify_sealed_copy(root,manifest,originals) is True
    (root/"surfaces.csv").write_bytes(b"tamper")
    with pytest.raises(ContractError, match="source attachment identity"):
        full_map._verify_sealed_copy(root,manifest,originals)


def test_bundle_copy_rejects_unsealed_manifest_or_source_provenance(tmp_path):
    root,manifest,originals=_bundle_fixture(tmp_path)
    import copy
    bad=copy.deepcopy(manifest)
    bad["training_ready"]=True
    with pytest.raises(ContractError, match="invalid source-bound"):
        full_map._verify_sealed_copy(root,bad,originals)
    bad=copy.deepcopy(manifest)
    bad["surface_points"]=3
    with pytest.raises(ContractError, match="version digest"):
        full_map._verify_sealed_copy(root,bad,originals)
    original=originals.pop("source_proof.txt")
    with pytest.raises(ContractError,match="invalid source-bound"):
        full_map._verify_sealed_copy(root,manifest,originals)
    originals["source_proof.txt"]=original
    with pytest.raises(Exception):
        full_map.verify_bundle(root,manifest)  # public API still deep, not shallow
