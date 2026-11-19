"""Optional, display-only visual clarity for the SHARED G2 F27 source renderer.

No change to nav_sg Scene Graph, Room, Island, source color, depth, geometry
or member selection. The original RGB remains retained and untouched; this
produces an explicitly labeled derivative for human review.

- Depth jumps expose true stairs, sofa cushions and table/shelf edges.
- Authenticated source Door outlines stay visible in floor-top even behind
  Walls (a *source-derived display overlay*, NOT physical transparency).
- Window footprints in their selected wall views receive a different mark.
- No scene/instance ID, B1K name or simulator-specific rule is hardcoded.
"""
from __future__ import annotations
import math

import numpy as np
from PIL import Image, ImageDraw


class SourceVisibilityError(ValueError):
    pass


def _validate_rgb_and_evidence(rgb,depth,geometry):
    image=np.asarray(rgb)
    z=np.asarray(depth)
    g=np.asarray(geometry)
    if (image.ndim!=3 or image.shape[2]!=3 or image.dtype!=np.uint8 or
        z.shape!=image.shape[:2] or g.shape!=image.shape[:2] or
        g.dtype!=np.bool_):
        raise SourceVisibilityError("RGB/depth/geometry arrays disagree")
    if g.any() and not np.isfinite(z[g]).all():
        raise SourceVisibilityError("source geometry has nonfinite front depth")
    return image,z,g


def source_depth_outline(rgb,depth,geometry,*,threshold_m=.015,
                         darkness=.46):
    """One-pixel source depth/silhouette edge; never edits Z/semantics/mesh.

    Disabled by default at the shared F27 call site. B1K and RoboCasa can
    enable it identically; threshold is expressed in actual source metres.
    """
    if (type(threshold_m) not in (float,int) or
        not math.isfinite(threshold_m) or not .001<=threshold_m<=.15
        or type(darkness) not in (float,int) or
        not math.isfinite(darkness) or not 0<=darkness<=1):
        raise SourceVisibilityError("invalid shared source-edge settings")
    image,z,g=_validate_rgb_and_evidence(rgb,depth,geometry)
    edges=np.zeros(g.shape,dtype=bool)
    pair=g[:,1:]&g[:,:-1]
    depth_gap=pair&(np.abs(np.where(pair,z[:,1:],0.)-
                           np.where(pair,z[:,:-1],0.))>=threshold_m)
    edges[:,1:] |= depth_gap
    edges[:,:-1] |= depth_gap
    pair=g[1:,:]&g[:-1,:]
    depth_gap=pair&(np.abs(np.where(pair,z[1:,:],0.)-
                           np.where(pair,z[:-1,:],0.))>=threshold_m)
    edges[1:,:] |= depth_gap
    edges[:-1,:] |= depth_gap
    # Draw a one-pixel genuine silhouette on selected known geometry only.
    edges[:,1:] |= g[:,1:]&~g[:,:-1]
    edges[:,:-1] |= g[:,:-1]&~g[:,1:]
    edges[1:,:] |= g[1:,:]&~g[:-1,:]
    edges[:-1,:] |= g[:-1,:]&~g[1:,:]
    out=image.copy()
    if edges.any() and darkness>0:
        out[edges]=np.clip(np.rint(out[edges].astype(float)*(1-darkness)),0,255).astype(np.uint8)
    return out,{"source_depth_or_silhouette_edge_pixels":int(edges.sum()),
                "depth_threshold_m":float(threshold_m),
                "display_only":True,
                "geometry_semantics_modified":False}


def _convex_hull(points):
    """Deterministic pixel silhouette of original source mesh vertices."""
    p=sorted({(int(x),int(y)) for x,y in points})
    if len(p)<=2:return p
    def cross(o,a,b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for x in p:
        while len(lower)>=2 and cross(lower[-2],lower[-1],x)<=0:lower.pop()
        lower.append(x)
    upper=[]
    for x in reversed(p):
        while len(upper)>=2 and cross(upper[-2],upper[-1],x)<=0:upper.pop()
        upper.append(x)
    return lower[:-1]+upper[:-1]


def source_part_silhouettes(rgb,parts,*,axis,frame_origin_world,
                            frame_axes_world,low_room,high_room,mpp,
                            visible_categories=("door","window","step")):
    """Outline actual selected source mesh parts *after* normal F27 Z-buffer.

    The client passes ONLY native G2-selected source parts. A hidden Door
    silhouette is displayed in floor_top from its original world vertices,
    never inferred from a recognition model or 1m room label.
    """
    from g2.views.surface_renderer import projection_grid
    img=np.asarray(rgb)
    if img.ndim!=3 or img.shape[2]!=3 or img.dtype!=np.uint8:
        raise SourceVisibilityError("invalid RGB")
    origin=np.asarray(frame_origin_world,float)
    axes=np.asarray(frame_axes_world,float)
    if (origin.shape!=(3,) or axes.shape!=(3,3) or
        not np.isfinite(origin).all() or not np.isfinite(axes).all()
        or not np.allclose(axes@axes.T,np.eye(3),atol=1e-7,rtol=0) or
        not np.isclose(np.linalg.det(axes),1,atol=1e-7,rtol=0)):
        raise SourceVisibilityError("invalid original Room reference frame")
    if type(mpp) not in (int,float) or mpp<=0 or not math.isfinite(mpp):
        raise SourceVisibilityError("invalid source view resolution")
    right,up,_,uv_min,w,h,_,_=projection_grid(low_room,high_room,axis,mpp)
    if img.shape[:2]!=(h,w):
        raise SourceVisibilityError("source projection pixels and RGB mismatch")
    if not isinstance(parts,(list,tuple)) or len(parts)>50000:
        raise SourceVisibilityError("source part inventory exceeds budget")
    allowed=frozenset(visible_categories)
    counts={"door":0,"window":0,"step":0}
    display=Image.fromarray(img)
    pen=ImageDraw.Draw(display)
    for item in parts:
        if not isinstance(item,dict) or item.get("kind") not in allowed:
            continue
        kind=item["kind"]
        if kind not in counts:raise SourceVisibilityError("unsupported source silhouette kind")
        vertices=np.asarray(item.get("vertices_world"),dtype=float)
        if (vertices.ndim!=2 or vertices.shape[1]!=3 or len(vertices)<2 or
            len(vertices)>5_000_000 or not np.isfinite(vertices).all()):
            raise SourceVisibilityError("invalid source-authentic part mesh")
        local=(vertices-origin)@axes.T
        uv=np.column_stack((local@right,local@up))
        screen=np.rint(np.column_stack(((uv[:,0]-uv_min[0])/mpp,
                                       h-1-(uv[:,1]-uv_min[1])/mpp))).astype(int)
        if (screen[:,0].max() <0 or screen[:,0].min()>w or
            screen[:,1].max()<0 or screen[:,1].min()>h):
            continue
        hull=_convex_hull(screen)
        if len(hull)<2:continue
        if kind=="door":
            color=(8,84,124);halo=(242,251,252)
        elif kind=="window":
            color=(167,91,5);halo=(255,249,232)
        else:
            color=(65,65,70);halo=(245,244,240)
        if len(hull)==2:
            pen.line(hull,fill=halo,width=6)
            pen.line(hull,fill=color,width=3)
        else:
            path=hull+[hull[0]]
            pen.line(path,fill=halo,width=5,joint="curve")
            pen.line(path,fill=color,width=2,joint="curve")
        counts[kind]+=1
    return np.asarray(display),{
        "source_part_silhouettes_drawn":counts,
        "source_part_silhouettes_origin":"ORIGINAL_SOURCE_VISUAL_MESH_VERTICES_G2_SELECTED_NATIVE_PART_IDS",
        "display_only":True,
        "source_depth_and_occupancy_unchanged":True,
    }



def source_structural_view_surface_filter(registry,axis):
    """Shared G2 F27 source-structure occluder policy, presentation only.

    Floor Top: omit genuine Ceilings, otherwise they hide all furniture.
    Upper Up: omit the Floor itself, otherwise the ceiling and overhead
    fixtures are hidden. Four Wall directions keep native G2-selected
    wall-associated VisualMesh as-is. Original full G2 registry is untouched.
    This does not add any connection or change nav_sg Room / Island IDs.
    """
    if axis not in ("floor_top","upper_up","+X","-X","+Y","-Y"):
        raise SourceVisibilityError("unsupported G2 F27 view axis")
    if not isinstance(registry,dict) or not isinstance(registry.get("surfaces"),dict):
        raise SourceVisibilityError("invalid shared source surface registry")
    excluded_role=(
        "ceiling" if axis=="floor_top" else
        "floor" if axis=="upper_up" else None
    )
    if excluded_role is None:
        return registry,{"source_structural_visuals_hidden":0,
                         "hidden_role":None,"shared_view_policy":True}
    selected={
        k:v for k,v in registry["surfaces"].items()
        if v.get("structural_role")!=excluded_role
    }
    out=dict(registry)
    out["surfaces"]=selected
    return out,{
        "source_structural_visuals_hidden":len(registry["surfaces"])-len(selected),
        "hidden_role":excluded_role,
        "shared_view_policy":True,
        "native_entities_and_connections_unchanged":True,
    }
