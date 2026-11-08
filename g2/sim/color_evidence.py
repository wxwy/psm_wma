"""Revalidate the point-color evidence advertised by a source manifest."""
from pathlib import Path
import zipfile
import numpy as np

from g2.io import ContractError, verified_file
from .texture_projection import REASONS


def verify_color_evidence(root, manifest, cloud):
    record=manifest.get("color_audit_file")
    protocol=manifest.get("source_identity",{}).get("color_evidence_protocol")
    if protocol not in (None,"g2_sample_color_audit_v1"):
        raise ContractError("unknown hashed point color evidence protocol")
    if record is None:
        if protocol is not None or any("color_coverage" in row for row in manifest.get("geom_audit",[])):
            raise ContractError("sampled coverage lacks point color evidence")
        return None  # legacy pre-F1-B2 manifest
    if not isinstance(record,dict) or record.get("path")!="color_audit.npz":
        raise ContractError("unexpected point color evidence path")
    path=verified_file(root,record)
    n=manifest.get("point_count")
    if type(n) is not int or not 0<n<=5_000_000:raise ContractError("invalid color evidence point count")
    expected={"geom_id","local_face_id","reason_code","input_triangle_area_weight_m2"}
    try:
        with zipfile.ZipFile(path) as archive:
            entries=archive.infolist()
            if {entry.filename for entry in entries}!={key+".npy" for key in expected} or len(entries)!=4:
                raise ContractError("unexpected point color evidence arrays")
            if any(entry.file_size>n*8+4096 for entry in entries):
                raise ContractError("point color evidence exceeds bounded array size")
        with np.load(path,allow_pickle=False) as archive:
            values={key:archive[key] for key in expected}
        if any(value.shape!=(n,) for value in values.values()):raise ContractError("point color evidence row count mismatch")
        ids,faces,codes,weights=[values[key] for key in ("geom_id","local_face_id","reason_code","input_triangle_area_weight_m2")]
        if (any(value.dtype.kind not in "iu" or value.dtype.itemsize>8 for value in (ids,faces,codes))
            or weights.dtype.kind!="f" or not np.isfinite(weights).all() or np.any(weights<=0)
            or np.any(ids<0) or np.any(faces<0) or not set(np.unique(codes)).issubset(REASONS)):
            raise ContractError("invalid point color evidence values")
        if manifest.get("color_reason_codes")!={str(key):value for key,value in REASONS.items()}:
            raise ContractError("point color reason dictionary differs from code")
        cloud_flags=np.empty(n,bool)
        with Path(cloud).open(encoding="utf-8") as stream:
            for _ in range(7):next(stream)
            for index in range(n):
                fields=next(stream).split()
                if len(fields)!=7 or fields[-1] not in ("0","1"):raise ContractError("invalid source color row")
                cloud_flags[index]=fields[-1]=="1"
            if stream.read().strip():raise ContractError("extra source color rows")
        if not np.array_equal(codes==0,cloud_flags):raise ContractError("point color mask differs from original cloud")
        rows={row["geom_id"]:row for row in manifest["geom_audit"] if row.get("surface_points",0)>0}
        if np.any(ids[1:]<ids[:-1]):raise ContractError("point color geom row order differs from exporter")
        unique,starts,counts=np.unique(ids,return_index=True,return_counts=True)
        if set(unique)!=set(rows):raise ContractError("point color geom IDs differ from sampled inventory")
        spans={int(g):slice(int(start),int(start+count)) for g,start,count in zip(unique,starts,counts)}
        for g,row in rows.items():
            selected=spans[g];face_ids=faces[selected];reason=codes[selected];coverage=row.get("color_coverage",{})
            valid=int(np.count_nonzero(reason==0));sampling=row.get("sampling",{})
            evaluated=len(np.unique(face_ids));retained=sampling.get("retained_face_count",0)
            if (len(face_ids)!=row["surface_points"] or np.any(face_ids>=sampling.get("input_face_count",0))
                or np.any(np.isin(face_ids,sampling.get("discarded_zero_area_face_ids",[])))
                or coverage.get("color_valid_points")!=valid
                or coverage.get("sampled_points")!=len(face_ids)
                or coverage.get("color_invalid_points")!=len(face_ids)-valid
                or not np.isclose(coverage.get("color_valid_fraction",-1),valid/len(face_ids),rtol=1e-12,atol=1e-15)
                or evaluated!=retained or coverage.get("retained_input_face_count")!=retained
                or coverage.get("evaluated_retained_face_count")!=evaluated
                or coverage.get("evaluated_retained_face_fraction")!=1
                or coverage.get("continuous_surface_color_coverage_certified") is not False):
                raise ContractError("point color face/coverage inventory mismatch")
            invalid={REASONS[int(code)]:int(np.count_nonzero(reason==code)) for code in np.unique(reason) if code!=0}
            area=float(weights[selected].sum())
            fraction=float(weights[selected][cloud_flags[selected]].sum()/area) if area else None
            if (coverage.get("invalid_point_reason_counts")!=invalid
                or not np.isclose(area,coverage.get("sampled_input_triangle_area_m2",-1),rtol=1e-12,atol=1e-15)
                or (fraction is None)!=(coverage.get("area_weighted_valid_sample_fraction") is None)
                or (fraction is not None and not np.isclose(fraction,coverage["area_weighted_valid_sample_fraction"],rtol=1e-12,atol=1e-15))):
                raise ContractError("point color weighted coverage mismatch")
    except (OSError,ValueError,KeyError,TypeError,StopIteration,zipfile.BadZipFile) as error:
        raise ContractError("invalid point color evidence: "+str(error)) from error
    return record["sha256"]
