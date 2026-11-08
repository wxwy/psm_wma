"""Point evidence integrity and legacy sealing compatibility, own fixtures."""
import hashlib
import numpy as np
import pytest

from g2.io import ContractError, canonical, digest, read_json, write_json
from g2.sim.source_scope import verify_full_scene_review
from g2.tests.test_source_scope import exported, review_for, recorded_fixture


@pytest.mark.parametrize("fault",["missing_file","missing_record","stripped_coverage","row_count","mask","geom","face","weights","reason","coverage_count","coverage_fraction","face_fraction","continuous_claim"])
def test_new_color_evidence_cannot_be_missing_or_internally_contradictory(exported,fault):
    _,_,_,_,out,m=exported
    path=out/"color_audit.npz"
    with np.load(path,allow_pickle=False) as archive:values={key:archive[key].copy() for key in archive.files}
    coverage=next(row["color_coverage"] for row in m["geom_audit"] if row.get("surface_points",0)>0)
    if fault=="missing_file":path.unlink()
    elif fault=="missing_record":del m["color_audit_file"]
    elif fault=="stripped_coverage":
        del m["color_audit_file"]
        for row in m["geom_audit"]:row.pop("color_coverage",None)
    elif fault=="coverage_count":coverage["color_valid_points"]-=1
    elif fault=="coverage_fraction":coverage["color_valid_fraction"]=.2
    elif fault=="face_fraction":coverage["evaluated_retained_face_fraction"]=.2
    elif fault=="continuous_claim":coverage["continuous_surface_color_coverage_certified"]=True
    else:
        if fault=="row_count":values["geom_id"]=values["geom_id"][:-1]
        elif fault=="mask":values["reason_code"][0]=1
        elif fault=="geom":values["geom_id"][0]=999
        elif fault=="face":values["local_face_id"][0]=999
        elif fault=="weights":values["input_triangle_area_weight_m2"][0]*=2
        else:values["reason_code"][0]=255
        np.savez_compressed(path,**values)
        m["color_audit_file"].update(bytes=path.stat().st_size,sha256=digest(path))
    m["geom_audit_sha256"]=hashlib.sha256(canonical(m["geom_audit"])).hexdigest()
    write_json(out/"manifest.json",m)
    with pytest.raises((ContractError,FileNotFoundError)):
        verify_full_scene_review(out/"manifest.json",review_for(out,m))


def test_sealed_bundle_contains_and_rechecks_point_evidence(native_factory,exported,tmp_path):
    from g2.nav_bridge.snapshot import capture,load_bundle
    native,run,out,m=recorded_fixture(native_factory,exported)
    packet=capture(native,tmp_path/"sealed",native_run=run/"native_run.json",prescan_manifest=out/"manifest.json",
                   full_scene_review=review_for(out,m))
    name="source_evidence/color_audit.npz"
    assert name in packet["files"]
    assert (tmp_path/"sealed"/name).read_bytes()==(out/"color_audit.npz").read_bytes()
    load_bundle(tmp_path/"sealed")
    (tmp_path/"sealed"/name).write_bytes(b"corrupt")
    with pytest.raises(ContractError):load_bundle(tmp_path/"sealed")


def test_legacy_source_manifest_without_point_coverage_still_seals(native_factory,exported,tmp_path):
    from g2.nav_bridge.snapshot import capture,load_bundle
    _,_,_,_,out,m=exported
    del m["color_audit_file"];del m["color_reason_codes"]
    # Simulate the actual pre-B2 producer identity. Removing evidence from the
    # current producer while retaining its source SHA is a separate rejection.
    identity=m["source_identity"]
    for key in ("color_evidence_protocol","require_role_evidence","allow_unclassified"):identity.pop(key,None)
    identity["adapter_source_sha256"]="a2ea096fbc53c60c2a385b4fbb931041d39edf3432423e90ff1d3c14662955db"
    old=m["source_sha256"]
    m["source_sha256"]=m["visual_source_sha256"]=hashlib.sha256(canonical(identity)).hexdigest()
    cloud=out/"precolored.txt";cloud.write_text(cloud.read_text().replace(old,m["source_sha256"],1))
    m["file"].update(bytes=cloud.stat().st_size,sha256=digest(cloud))
    for row in m["geom_audit"]:
        for key in ("color_coverage","role_evidence","geometry_type_id"):row.pop(key,None)
    m["geom_audit_sha256"]=hashlib.sha256(canonical(m["geom_audit"])).hexdigest()
    write_json(out/"manifest.json",m)
    native,run,out,m=recorded_fixture(native_factory,exported)
    packet=capture(native,tmp_path/"sealed",native_run=run/"native_run.json",prescan_manifest=out/"manifest.json",
                   full_scene_review=review_for(out,m))
    assert len(packet["files"])==7
    assert "color_audit_sha256" not in packet["source_scope"]
    load_bundle(tmp_path/"sealed")
