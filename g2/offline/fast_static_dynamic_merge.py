"""F21 optimized exact G2 color-layer compositor.

Aggregate every STATIC geom once. After true object movement, aggregate the
DYNAMIC submap only; merge it into the read-only static sorted key table using
binary search. No full ~3 million-key np.unique per spatial state.

Compare output exact to F21 slow assemble(layers, all_specs) for any source
frame; both use mean RGB per geom and conservative owner conflict -1.
"""
import time
from dataclasses import dataclass
import numpy as np

KEYDT=np.dtype([("x","<i4"),("y","<i4"),("z","<i4")])

@dataclass
class Accum:
    keys: np.ndarray
    rgb_sum: np.ndarray
    count: np.ndarray
    owner_min: np.ndarray
    owner_max: np.ndarray
    owner: np.ndarray
    rgb: np.ndarray
    count_input: int

def aggregate(layers, specs, gids=None):
    start=time.perf_counter()
    keys=[];rgb=[];owners=[]
    for spec in specs:
        if gids is not None and spec["g"] not in gids:
            continue
        component=layers.get(spec["g"])
        if component is None:continue
        k,c=component
        keys.append(k);rgb.append(c)
        owners.append(np.full(len(k),spec["owner"],np.int32))
    if not keys:
        return (None,round(time.perf_counter()-start,5))
    key=np.concatenate(keys);colors=np.concatenate(rgb);own=np.concatenate(owners)
    u,inv=np.unique(key,axis=0,return_inverse=True)
    n=np.bincount(inv,minlength=len(u))
    sums=np.column_stack([np.bincount(inv,weights=colors[:,i],minlength=len(u)) for i in range(3)])
    lo=np.full(len(u),np.iinfo(np.int32).max,np.int32)
    hi=np.full(len(u),-2,np.int32)
    np.minimum.at(lo,inv,own);np.maximum.at(hi,inv,own)
    o=np.where(lo==hi,lo,-1).astype(np.int32)
    out=np.rint(sums/n[:,None]).astype(np.uint8)
    return Accum(u,sums,n,lo,hi,o,out,len(key)),round(time.perf_counter()-start,5)

def combine(static,dynamic,leaf=.01):
    start=time.perf_counter()
    if static is None and dynamic is None:
        raise ValueError("both maps empty")
    if static is None:
        keys=dynamic.keys;rgb=dynamic.rgb;owner=dynamic.owner
        overlap=0
    elif dynamic is None:
        keys=static.keys;rgb=static.rgb;owner=static.owner
        overlap=0
    else:
        static_u=np.ascontiguousarray(static.keys).view(KEYDT).reshape(-1)
        dynamic_u=np.ascontiguousarray(dynamic.keys).view(KEYDT).reshape(-1)
        positions=np.searchsorted(static_u,dynamic_u)
        valid=positions<len(static_u)
        matched=np.zeros(len(positions),bool)
        matched[valid]=static_u[positions[valid]]==dynamic_u[valid]
        overlap=int(matched.sum())
        # Static backing arrays remain immutable; do not modify cached values.
        rgb=static.rgb.copy()
        owner=static.owner.copy()
        if overlap:
            pos=positions[matched];idx=np.flatnonzero(matched)
            n=static.count[pos]+dynamic.count[idx]
            s=static.rgb_sum[pos]+dynamic.rgb_sum[idx]
            rgb[pos]=np.rint(s/n[:,None]).astype(np.uint8)
            minimum=np.minimum(static.owner_min[pos],dynamic.owner_min[idx])
            maximum=np.maximum(static.owner_max[pos],dynamic.owner_max[idx])
            owner[pos]=np.where(minimum==maximum,minimum,-1).astype(np.int32)
        # Maintain lexicographically sorted grid keys as in the original
        # all-source np.unique. This prevents nearest-neighbor tie behavior
        # from changing solely due to different source array order.
        remaining=~matched
        newkeys=dynamic.keys[remaining]
        m=len(newkeys);nstatic=len(static.keys)
        if m:
            positions=positions[remaining]  # already monotone for sorted dynamic keys
            static_dst=np.arange(nstatic,dtype=np.int64)+np.searchsorted(
                positions,np.arange(nstatic,dtype=np.int64),side="right")
            dynamic_dst=positions+np.arange(m,dtype=np.int64)
            target_n=nstatic+m
            merged_keys=np.empty((target_n,3),dtype=np.int32)
            merged_rgb=np.empty((target_n,3),dtype=np.uint8)
            merged_owner=np.empty(target_n,dtype=np.int32)
            merged_keys[static_dst]=static.keys
            merged_keys[dynamic_dst]=newkeys
            merged_rgb[static_dst]=rgb
            merged_rgb[dynamic_dst]=dynamic.rgb[remaining]
            merged_owner[static_dst]=owner
            merged_owner[dynamic_dst]=dynamic.owner[remaining]
            keys,rgb,owner=merged_keys,merged_rgb,merged_owner
        else:
            keys=static.keys
        assert len(keys)==len(rgb)==len(owner)
        if len(keys)>1:
            a,b=keys[:-1],keys[1:]
            increasing=(b[:,0]>a[:,0]) | (
                (b[:,0]==a[:,0]) & ((b[:,1]>a[:,1]) | (
                    (b[:,1]==a[:,1]) & (b[:,2]>a[:,2]))))
            assert np.all(increasing), "source voxel keys must be unique and lexsorted"
    xyz=(keys.astype(np.float64)+.5)*leaf
    meta=dict(voxel_leaf_m=leaf,
        dense_sample_spacing_m=leaf,dense_small_sample_spacing_m=leaf,
        dense_source_points=(static.count_input if static else 0)+(dynamic.count_input if dynamic else 0),
        dense_valid_color_points=len(xyz),
        unassigned_source_instance_points=int(np.count_nonzero(owner==-1)),
        direct_voxel_source="MUJOCO_VISUAL_ASSET_UV_COLOR_CPP_TRI_RASTER_NO_TXT",
        source_mode="MUJOCO_FULL_SCENE",
        native_G2_scene_graph_unchanged=True,
        nav_original_10cm_grid_unchanged=True)
    scene=(xyz,rgb,np.ones(len(rgb),bool),owner,meta)
    timings=dict(source_candidates=meta["dense_source_points"],
       unique_voxels=len(keys),
       owner_conflict_or_unknown_voxels=meta["unassigned_source_instance_points"],
       dynamic_overlaps_static_voxel_keys=overlap,
       merge_s=round(time.perf_counter()-start,5),
       static_color_map_reused=True)
    return scene,timings

def check_equivalence(a,b):
    x,y=a[0],b[0]
    # Both maps can have different sorted key order after overlay.
    ai=np.lexsort((x[:,2],x[:,1],x[:,0]))
    bi=np.lexsort((y[:,2],y[:,1],y[:,0]))
    for k in range(4):
        if k==2:continue
        xx=a[k][ai];yy=b[k][bi]
        if not np.array_equal(xx,yy):
            raise AssertionError(f"F21 static/dynamic cached merge does not match full rebuild key {k}")
    return True
