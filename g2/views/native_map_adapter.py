"""Native 10 mm surface map -> the same source-independent View composer.

Full Map source: a separately verified C++ opaque color-cell stream. Each
surface-cell ID is a reversible world-voxel Morton code; it is NOT a MuJoCo
Geom ID. No object-name/semantic filter, nearest-Geom color patch, unknown
opacity promotion, or pretend source material ID is allowed.

RGB from this historical producer is a legacy encoded display byte, not a
certified physical linear material albedo. This adapter decodes it for
linear-light compositing and records that distinction explicitly.

Transparent Full Map assets require separate source material layers;
the existing native cell producer intentionally omits alpha<1 surfaces.
Sensor RGB-D requires its own measured opacity evidence, never this GT flag.
"""
import numpy as np

from g2.io import ContractError
from g2.sim.texture_projection import srgb_to_linear
from g2.views.surface_renderer import project_surface_samples


def _spread20(value):
    x=np.asarray(value,dtype=np.uint64)&np.uint64(0xfffff)
    x=(x | x << np.uint64(32)) & np.uint64(0x001f00000000ffff)
    x=(x | x << np.uint64(16)) & np.uint64(0x001f0000ff0000ff)
    x=(x | x << np.uint64(8)) & np.uint64(0x100f00f00f00f00f)
    x=(x | x << np.uint64(4)) & np.uint64(0x10c30c30c30c30c3)
    x=(x | x << np.uint64(2)) & np.uint64(0x1249249249249249)
    return x


def voxel_cell_identity(xyz,leaf_m=.01):
    """Stable nonnegative <=60-bit identity, independent of native Owner."""
    xyz=np.asarray(xyz,dtype=np.float64)
    if xyz.ndim!=2 or xyz.shape[1]!=3 or not np.isfinite(xyz).all():
        raise ContractError('invalid native surface points')
    if type(leaf_m) not in (float,int) or leaf_m!=.01:
        raise ContractError('native surfel ID requires the verified 10mm leaf')
    cells=np.floor(xyz/leaf_m).astype(np.int64)
    if np.any((cells<-524288)|(cells>524287)):
        raise ContractError('native cell coordinate exceeds reversible Morton range')
    u=np.asarray(cells+524288,dtype=np.uint64)
    packed=_spread20(u[:,0]) | (_spread20(u[:,1])<<np.uint64(1)) | (_spread20(u[:,2])<<np.uint64(2))
    # Explicit namespace bit: native cells can never be confused with the
    # small positive MuJoCo Visual Geom IDs in the same compositor.
    return (packed | np.uint64(1<<62)).astype(np.int64)


def native_map_samples(surface, snapshot, *, certified_opaque=False):
    """Adapt exact source-bound native cells without inventing original Geom."""
    if not certified_opaque:
        raise ContractError('native source map alpha requires explicit opaque producer proof')
    if not isinstance(surface,(tuple,list)) or len(surface)!=5:
        raise ContractError('invalid native map input')
    xyz,rgb,valid,owners,evidence=surface
    if (evidence.get('source_mode')!='NATIVE_LONG_LIVED_DIRECT_COLOR_WORKER_10MM_FULL_SOURCE'
            or any(evidence.get(k)!=snapshot.get(k) for k in ('scene_id','source_sha256','frame_id','world_frame'))):
        raise ContractError('native opaque cell proof/scene identity mismatch')
    xyz=np.asarray(xyz,dtype=np.float64)
    rgb=np.asarray(rgb)
    valid=np.asarray(valid)
    owners=np.asarray(owners)
    n=len(xyz)
    if (rgb.shape!=(n,3) or rgb.dtype!=np.uint8
        or valid.shape!=(n,) or valid.dtype!=np.bool_
        or owners.shape!=(n,) or owners.dtype.kind not in 'iu'
        or np.any(owners<-1) or np.any(owners>=len(snapshot['entities']))):
        raise ContractError('invalid native cell color/owner arrays')
    ids=voxel_cell_identity(xyz)
    if np.unique(ids).size!=n:
        raise ContractError('duplicate native voxel cell identity')
    return dict(points=xyz,geom_id=ids,
        material_id=np.full(n,-1,dtype=np.int32),
        rgb_linear=srgb_to_linear(rgb.astype(np.float64)/255.),
        color_valid=valid,alpha=np.ones(n,dtype=np.float64),
        alpha_valid=np.ones(n,dtype=bool),semantic_owner=np.asarray(owners,dtype=np.int32),
        provenance=dict(kind='NATIVE_10MM_OPAQUE_SURFACE_CELLS',
            scene_id=evidence['scene_id'],frame_id=evidence['frame_id'],
            source_sha256=evidence['source_sha256'],cell_id='SIGNED_GRID_MORTON_20X3',
            source_geom_id_known=False, source_material_id_known=False,
            opaque_evidence_from='VERIFIED_SOURCE_NATIVE_ALPHA255_PRODUCER',
            color_encoding='LEGACY_DISPLAY_SRGB_DECODE_FOR_LINEAR_COMPOSITION',
            numeric_material_albedo_certified=False,training_ready=False))




def native_room_samples(surface, snapshot, room):
    """Decode map once per state and bind it to one native Room reference."""
    samples=native_map_samples(surface,snapshot,certified_opaque=True)
    axes=np.asarray(room['reference_frame']['axes_world'],dtype=np.float64)
    origin=np.asarray(room['reference_frame']['origin_world'],dtype=np.float64)
    if axes.shape!=(3,3) or origin.shape!=(3,) or not np.isfinite(axes).all():
        raise ContractError('invalid native room reference frame')
    samples['points']=(samples['points']-origin)@axes.T
    samples['provenance']=dict(samples['provenance'],
        room_uid=room['uid'],source_coordinates='NATIVE_ROOM_REFERENCE')
    return samples


def project_native_map_view(surface, snapshot, room, low, high, axis, mpp=.01):
    """Project the existing high-resolution map through the common composer."""
    samples=native_map_samples(surface,snapshot,certified_opaque=True)
    origin=np.asarray(room['reference_frame']['origin_world'],dtype=np.float64)
    axes=np.asarray(room['reference_frame']['axes_world'],dtype=np.float64)
    if origin.shape!=(3,) or axes.shape!=(3,3):
        raise ContractError('invalid native room reference frame')
    samples['points']=(samples['points']-origin)@axes.T
    result=project_surface_samples(samples,low,high,axis,mpp,background_rgb_linear=np.ones(3))
    return result,samples['provenance']
