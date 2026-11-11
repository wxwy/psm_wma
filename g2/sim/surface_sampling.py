"""Bounded surface sampling with exact-zero rejection evidence.

Face IDs always index the input triangle table (the compiled local mesh for
MuJoCo), including skipped faces. This is independent of room segmentation.
"""
from fractions import Fraction
import hashlib
import math
from numbers import Real

import numpy as np

from g2.io import ContractError


class SamplingFailure(ContractError):
    def __init__(self, message, audit):
        super().__init__(message)
        self.audit = dict(audit, status="REJECTED", rejection_reason=message)


def geometry_sha256(vertices, faces):
    """Hash every original vertex/face; discarded faces remain source evidence."""
    return hashlib.sha256(vertices.astype("<f8").tobytes() + faces.astype("<i8").tobytes()).hexdigest()


def _exact_cross(triangle):
    # float32 -> Python float is exact too. Fractions preserve the represented
    # input coordinates; neither an epsilon nor a rounded cross proves zero.
    xyz = [[Fraction(float(v)) for v in point] for point in triangle]
    a = [xyz[1][i] - xyz[0][i] for i in range(3)]
    b = [xyz[2][i] - xyz[0][i] for i in range(3)]
    return tuple(a[i] * b[j] - a[j] * b[i] for i, j in ((1, 2), (2, 0), (0, 1)))


def audit_surface(vertices, faces):
    """Inspect all triangles without allocating a cloud; never hide bad faces."""
    if (not isinstance(vertices, np.ndarray) or vertices.ndim != 2 or vertices.shape[1] != 3
            or vertices.dtype.kind != "f" or vertices.dtype.itemsize not in (4, 8)
            or not np.isfinite(vertices).all() or not isinstance(faces, np.ndarray)
            or faces.ndim != 2 or faces.shape[1] != 3 or not len(faces)
            or faces.dtype.kind not in "iu" or np.any(faces < 0) or np.any(faces >= len(vertices))):
        raise ContractError("invalid visual mesh")
    discarded, near, underflow, nonfinite, areas = [], [], [], [], []
    for index, triangle in enumerate(vertices[faces]):
        with np.errstate(over="ignore", invalid="ignore", under="ignore"):
            tri64 = triangle.astype(np.float64)
            cross = np.cross(tri64[1] - tri64[0], tri64[2] - tri64[0])
            norm64 = float(np.hypot.reduce(cross))
            # A conservative forward-error bound for differences/products of
            # finite coordinates. Only candidates pay for exact rational math.
            magnitude = np.max(np.abs(tri64))
            bound = max(1e-14, float(64 * np.finfo(np.float64).eps * magnitude * magnitude))
            candidate = not np.isfinite(norm64) or float(np.max(np.abs(cross))) <= bound
        exact_near = False
        if candidate:
            exact = _exact_cross(triangle)
            if not any(exact):
                discarded.append(index)
                continue
            # This is diagnostic only: a small strictly positive cross never
            # rejects or removes a face. Exact squares survive float underflow.
            exact_near = sum(component * component for component in exact) <= Fraction(1e-14) ** 2
            try:
                norm64 = math.hypot(*(float(component) for component in exact))
            except OverflowError:
                norm64 = math.inf
        # Preserve nonfinite/overflow protection and normal sampling arithmetic;
        # the former positive-area minimum is explicitly retired by F1-C.
        with np.errstate(over="ignore", invalid="ignore", under="ignore"):
            legacy_norm = float(np.linalg.norm(np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])))
        if not math.isfinite(norm64) or not math.isfinite(legacy_norm):
            nonfinite.append(index)
        elif exact_near or legacy_norm <= 1e-14:
            near.append(index)
        area64 = norm64 / 2 if math.isfinite(norm64) else 0.
        if math.isfinite(norm64) and area64 == 0:
            underflow.append(index)  # exact-positive input, not a zero face
        areas.append(area64)
    try:
        area = math.fsum(areas)
    except OverflowError:
        area = None
    audit = {
        "schema": "g2_surface_sampling_audit_v1", "status": "GEOMETRY_VALID",
        "policy": "EXACT_ZERO_ONLY_RETAIN_ALL_POSITIVE", "coordinate_dtype": vertices.dtype.str,
        "zero_predicate": "EXACT_RATIONAL_CROSS_OF_REPRESENTED_INPUT_COORDINATES",
        "retained_near_positive_face_ids": near,
        "retained_area_underflow_face_ids": underflow,
        "face_id_basis": "INPUT_LOCAL_TRIANGLE_INDEX", "input_face_count": len(faces),
        "retained_face_count": len(faces) - len(discarded),
        "discarded_zero_area_face_ids": discarded, "discarded_zero_area_face_count": len(discarded),
        "discarded_face_fraction": len(discarded) / len(faces),
        "discarded_area_m2": 0., "discarded_area_fraction": 0. if len(discarded) < len(faces) else None,
        "retained_area_m2": area, "area_measurement": "FLOAT64_APPROXIMATION_OF_INPUT_LOCAL_COORDINATES",
        "rejected_nonfinite_face_ids": nonfinite,
        "local_geometry_sha256": geometry_sha256(vertices, faces), "sampled_point_count": 0,
    }
    reason = ("nonfinite visual triangle geometry" if nonfinite or area is None else
              "visual mesh has no nonzero-area triangles" if len(discarded) == len(faces) else None)
    if reason:
        audit.update(status="REJECTED", rejection_reason=reason)
    return audit


def sample_surface(vertices, faces, spacing, remaining, *, with_audit=False):
    """Sample every retained face in original order, within a hard point budget."""
    audit = audit_surface(vertices, faces)
    if audit["status"] == "REJECTED":
        raise SamplingFailure(audit["rejection_reason"], audit)
    if (not isinstance(spacing, Real) or isinstance(spacing, bool)
            or not math.isfinite(spacing) or spacing <= 0):
        raise SamplingFailure("invalid surface spacing", audit)
    if type(remaining) is not int or remaining < 0:
        raise SamplingFailure("invalid pre-scan point budget", audit)
    audit.update(spacing_m=float(spacing), point_budget=remaining)
    points, face_ids, weights = [], [], []
    discarded = set(audit["discarded_zero_area_face_ids"])
    total = 0
    for index, tri in enumerate(vertices[faces]):
        if index in discarded:
            continue
        with np.errstate(over="ignore", invalid="ignore", under="ignore"):
            edge = max(np.linalg.norm(tri[i] - tri[j]) for i, j in ((0, 1), (1, 2), (2, 0)))
            if edge < math.sqrt(np.finfo(tri.dtype).tiny):
                # Squared norms can underflow to zero OR a smaller nonzero
                # subnormal value. Keep the true length/spacing budget while
                # leaving ordinary original-dtype arithmetic unchanged.
                tri64 = tri.astype(np.float64)
                edge = max(math.hypot(*(tri64[i] - tri64[j])) for i, j in ((0, 1), (1, 2), (2, 0)))
            ratio = edge / spacing
        if not np.isfinite(edge) or not np.isfinite(ratio):
            audit.update(rejection_face_id=index, allocated_point_count_before_rejection=total)
            raise SamplingFailure("nonfinite surface subdivision", audit)
        steps = max(1, int(np.ceil(ratio)))
        count = (steps + 1) * (steps + 2) // 2
        if total + count > remaining:
            audit.update(rejection_face_id=index, allocated_point_count_before_rejection=total,
                         required_points_at_rejection=total + count)
            raise SamplingFailure("pre-scan point budget exceeded; choose coarser spacing", audit)
        bary = np.asarray([[i / steps, j / steps, 1 - (i + j) / steps]
                           for i in range(steps + 1) for j in range(steps + 1 - i)])
        points.append(bary @ tri)
        face_ids.extend([index] * count)
        weights.append(bary)
        total += count
    audit.update(status="SAMPLED", sampled_point_count=total)
    result = np.concatenate(points), np.asarray(face_ids), np.concatenate(weights)
    return (*result, audit) if with_audit else result
