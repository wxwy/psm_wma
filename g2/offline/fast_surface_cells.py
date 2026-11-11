"""F21 C++ triangle->sparse-surface-cell rasterization bridge.

No MuJoCo in C++, so simulator identity and source albedo remain original
read-only Python G2 logic.  C++ only computes barycentric projections.
"""
from pathlib import Path
import ctypes
import numpy as np

LIB=Path(__file__).resolve().parents[1]/"bin/libfast_surface_cells.so"

class _RasterResult(ctypes.Structure):
    _fields_=[("face_ids",ctypes.POINTER(ctypes.c_uint32)),
              ("barycentric",ctypes.POINTER(ctypes.c_double)),
              ("count",ctypes.c_uint64),
              ("status",ctypes.c_int)]

lib=ctypes.CDLL(str(LIB))
lib.f21_raster_cells.argtypes=[
    ctypes.POINTER(ctypes.c_double),ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_uint32,ctypes.c_double,ctypes.c_uint64]
lib.f21_raster_cells.restype=_RasterResult
lib.f21_free_result.argtypes=[ctypes.POINTER(_RasterResult)]
lib.f21_free_result.restype=None

def raster_world_triangles(triangles,keep,leaf=.01,max_points=8_000_000):
    tri=np.ascontiguousarray(triangles,dtype=np.float64)
    mask=np.ascontiguousarray(keep,dtype=np.uint8)
    if (tri.ndim!=3 or tri.shape[1:]!=(3,3) or
        mask.shape!=(len(tri),) or not np.isfinite(tri).all()):
        raise ValueError("invalid world triangles / explicit face keep mask")
    result=lib.f21_raster_cells(tri.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                mask.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                len(tri),leaf,max_points)
    try:
        if result.status:
            raise RuntimeError(f"F21 native 1cm surface raster error {result.status}")
        if not result.count:
            return np.empty(0,dtype=np.int64),np.empty((0,3),dtype=np.float64)
        ids=np.ctypeslib.as_array(result.face_ids,shape=(result.count,)).copy().astype(np.int64)
        bary=np.ctypeslib.as_array(result.barycentric,shape=(result.count*3,)).copy().reshape(-1,3)
        if len(ids)!=len(bary) or np.any(ids>=len(tri)) or not np.isfinite(bary).all():
            raise RuntimeError("native raster returned invalid barycentric samples")
        return ids,bary
    finally:
        lib.f21_free_result(ctypes.byref(result))
