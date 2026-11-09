"""Full sampled-point evidence, with explicitly approximate area weights."""
import math
import numpy as np
from .texture_projection import REASONS
from .surface_sampling import _exact_cross


def color_coverage(vertices, faces, face_ids, valid, reasons):
    triangles = vertices.astype(float)[faces]
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    areas = .5 * np.hypot.reduce(cross, axis=1)
    with np.errstate(over="ignore",invalid="ignore"):
        magnitude=np.max(np.abs(triangles),axis=(1,2))
        bound=np.maximum(1e-14,64*np.finfo(np.float64).eps*magnitude*magnitude)
    candidates=np.flatnonzero((np.max(np.abs(cross),axis=1)<=bound)|~np.isfinite(areas))
    positive=areas>0
    for index in candidates:
        exact=_exact_cross(triangles[index])
        positive[index]=any(exact)
        areas[index]=.5*math.hypot(*(float(component) for component in exact))
    counts = np.bincount(face_ids, minlength=len(faces))
    weights = areas[face_ids] / counts[face_ids]
    sampled = counts > 0
    total_area = float(areas[sampled].sum())
    kept = int(np.count_nonzero(sampled)); retained=int(np.count_nonzero(positive))
    underflow=weights==0
    underflow_faces=np.unique(face_ids[underflow]).tolist()
    invalid = {REASONS[int(code)]: int(np.count_nonzero(reasons == code)) for code in np.unique(reasons) if code != 0}
    return weights, {
        "sampled_points": len(valid), "color_valid_points": int(np.count_nonzero(valid)),
        "color_invalid_points": int(np.count_nonzero(~valid)),
        "color_valid_fraction": float(np.mean(valid)), "invalid_point_reason_counts": invalid,
        "evaluated_retained_face_count": kept, "retained_input_face_count":retained,
        "evaluated_retained_face_fraction": kept/retained if retained else None,
        "sampled_input_triangle_area_m2": total_area,
        "area_weight_underflow_face_ids":underflow_faces,
        "area_weight_underflow_point_count":int(np.count_nonzero(underflow)),
        "area_weight_status":"FLOAT64_UNDERFLOW" if underflow_faces else "FLOAT64_APPROXIMATION",
        "area_weighted_valid_sample_fraction": float(weights[valid].sum() / total_area) if total_area and not underflow_faces else None,
        "area_basis": "FLOAT64_INPUT_TRIANGLE_APPROXIMATION_WEIGHTED_SAMPLES_NOT_CONTINUOUS_COVERAGE",
        "continuous_surface_color_coverage_certified": False,
        "scope": "DECLARED_SAMPLED_SURFACES_ONLY_NOT_WHOLE_HOUSE",
    }
