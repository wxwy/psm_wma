"""P1 scene-level view reuse gate (experimental; original G2 pipeline untouched).

One comparison at each sampled view state:
- non-robot visual-geom pose changed? rerender scene
- only robot chassis x/y/yaw changed? reuse raw scene and redraw floor arrow
- neither changed? reference existing view images

There are deliberately NO per-view input fingerprints, no view-specific
dependency graph, and no PNG hashes in the *runtime* change decision.
Use separate byte/pixel parity tests as a non-production audit oracle.
"""
from dataclasses import dataclass
import math
from pathlib import Path
import numpy as np


@dataclass(frozen=True)
class ViewEvent:
    state_id: int
    frame: int
    mode: str
    scene_source_state: int
    raw_floor_source_state: int
    final_floor_source_state: int
    object_translation_max_m: float
    object_rotation_max_deg: float
    robot_xy_delta_m: float
    robot_yaw_delta_rad: float

    @property
    def scene_rerender(self):
        return self.mode == "FULL"

    @property
    def redraw_robot_arrow(self):
        return self.mode in ("FULL", "ARROW_ONLY")


class SceneViewCursor:
    """Scene event cursor: <1 mm and <1 degree ignored (experimental only).

    Measurements are compared with the LAST ACTUAL SCENE RENDER, not the
    previous sample. Robot chassis x/y/yaw is tracked independently per
    sampled state. SG and exact MuJoCo GT are never modified.
    """

    def __init__(self, visual_geom_ids, *, translation_tol_m=0.001,
                 rotation_tol_deg=1.0, robot_xy_tol_m=1e-10,
                 robot_yaw_tol_rad=1e-10):
        ids=np.asarray(visual_geom_ids)
        if (ids.ndim!=1 or not len(ids) or ids.dtype.kind not in "iu"
                or np.any(ids<0) or len(np.unique(ids))!=len(ids)):
            raise ValueError("non-robot GT geom IDs must be unique and non-empty")
        for name,value in (
            ("translation_tol_m",translation_tol_m),
            ("rotation_tol_deg",rotation_tol_deg),
            ("robot_xy_tol_m",robot_xy_tol_m),
            ("robot_yaw_tol_rad",robot_yaw_tol_rad),
        ):
            if (type(value) not in (float,int) or not math.isfinite(value)
                    or value < 0):
                raise ValueError("invalid numeric tolerance "+name)
        self.ids=ids.astype(np.int64,copy=True)
        self.tpos=float(translation_tol_m)
        self.trot=float(rotation_tol_deg)
        self.trobot=float(robot_xy_tol_m)
        self.tyaw=float(robot_yaw_tol_rad)
        self._last_robot=None
        self._last_rendered_scene=None
        self._previous_id=-1
        self._previous_frame=-1
        self._scene_keyframe=None
        self._last_floor_png_state=None

    @staticmethod
    def _max_rotation_degrees(current, reference):
        """SO(3) geodesic rotation angle; no matrix-entry/angular-unit confusion.

        atan2(sin(angle), cos(angle)) is stable near zero and pi, unlike
        arccos(trace) without a small-angle guard.
        """
        relative=np.matmul(current,np.swapaxes(reference,-1,-2))
        cosine=np.clip((np.trace(relative,axis1=-2,axis2=-1)-1.0)*0.5,-1.0,1.0)
        skew=np.stack([
            relative[:,2,1]-relative[:,1,2],
            relative[:,0,2]-relative[:,2,0],
            relative[:,1,0]-relative[:,0,1],
        ],axis=1)
        sine=0.5*np.linalg.norm(skew,axis=1)
        return float(np.degrees(np.max(np.arctan2(sine,cosine))))

    def observe(self, state_id, frame, positions, rotations, robot_xy_yaw):
        if (type(state_id) is not int or state_id!=self._previous_id+1
                or type(frame) is not int or frame<=self._previous_frame):
            raise ValueError("scene frame order must be strictly increasing")
        pos=np.asarray(positions,dtype=np.float64)
        mat=np.asarray(rotations,dtype=np.float64)
        bot=np.asarray(robot_xy_yaw,dtype=np.float64)
        if pos.shape!=(len(self.ids),3):
            raise ValueError("wrong number of visual-geom positions")
        if mat.shape not in ((len(self.ids),3,3),(len(self.ids),9)):
            raise ValueError("wrong number of visual-geom rotations")
        mat=mat.reshape(len(self.ids),3,3)
        if (bot.shape!=(3,) or not np.isfinite(pos).all()
                or not np.isfinite(mat).all() or not np.isfinite(bot).all()):
            raise ValueError("non-finite or invalid pose")
        if self._last_rendered_scene is None:
            dp=dm=dr=dy=0.0
            mode="FULL"
        else:
            # Compare the scene with its ACTUALLY RENDERED keyframe. If the
            # previous sampled frame was also skipped, measuring only the
            # adjacent delta would let sub-threshold movement accumulate
            # indefinitely without triggering any scene refresh.
            keypos,keymat=self._last_rendered_scene
            dp=float(np.max(np.linalg.norm(pos-keypos,axis=1)))
            dm=self._max_rotation_degrees(mat,keymat)
            oldbot=self._last_robot
            dr=float(np.linalg.norm(bot[:2]-oldbot[:2]))
            dy=float(abs(math.atan2(math.sin(bot[2]-oldbot[2]),
                                    math.cos(bot[2]-oldbot[2]))))
            # Owner-specified strict below threshold rule: >= 1mm or >= 1deg
            # is a scene event, even when other geoms remain stationary.
            if dp>=self.tpos or dm>=self.trot:
                mode="FULL"
            elif dr>self.trobot or dy>self.tyaw:
                mode="ARROW_ONLY"
            else:
                mode="REUSE_ALL"
        if mode=="FULL":
            self._scene_keyframe=state_id
            self._last_rendered_scene=(pos.copy(),mat.copy())
            self._last_floor_png_state=state_id
        elif mode=="ARROW_ONLY":
            self._last_floor_png_state=state_id
        out=ViewEvent(
            state_id,frame,mode,self._scene_keyframe,self._scene_keyframe,
            self._last_floor_png_state,dp,dm,dr,dy)
        self._last_robot=bot.copy()
        self._previous_id=state_id
        self._previous_frame=frame
        return out


def validate_view_path(path):
    p=Path(path)
    if (not isinstance(path,str) or not path or p.is_absolute()
            or ".." in p.parts or p.suffix.lower()!=".png"
            or p.parts[0] not in ("sixview","islands")
            or len(p.parts)<2):
        raise ValueError("unsafe view path")
    return str(p)


def index_state(event, views, *, top="sixview/floor_top.png"):
    """Simple direct ref_state mapping; NEVER chain or symlink across Episodes.

    Every state retains its own SG file. All image paths are optional physical
    files plus direct indexes to a prior state with a real PNG.
    """
    if event.mode not in ("FULL","ARROW_ONLY","REUSE_ALL"):
        raise ValueError("bad event mode")
    # The owner-approved approximate scene-change policy is explicit and
    # cannot be disabled accidentally when materializing v2 references.
    values=(event.object_translation_max_m,event.object_rotation_max_deg)
    if any(not math.isfinite(x) or x<0 for x in values):
        raise ValueError("invalid scene movement evidence")
    if (event.mode != "FULL" and
            (event.object_translation_max_m>=0.001 or event.object_rotation_max_deg>=1.0)):
        raise ValueError("cannot index a state exceeding 1 mm or 1 degree")
    paths=[validate_view_path(s) for s in views]
    if len(paths)!=len(set(paths)) or top not in paths:
        raise ValueError("duplicate or missing floor-top view")
    files={}
    refs={}
    for path in paths:
        if event.mode=="FULL" or (event.mode=="ARROW_ONLY" and path==top):
            files[path]=True
        else:
            source=event.final_floor_source_state if path==top else event.scene_source_state
            if source>=event.state_id or source<0:
                raise ValueError("reuse must refer to a previous physical view")
            refs[path]={"ref_state":source,"path":path}
    return dict(state_id=event.state_id,frame=event.frame,
                update_mode=event.mode,view_pngs=sorted(files),
                view_refs=refs,
                floor_background_ref_state=event.raw_floor_source_state)


def resolve_indexed_png(states, state_id, path, episode_root):
    """Non-negotiable safe consumer: direct older refs, no broken/remote paths."""
    path=validate_view_path(path)
    if state_id not in range(len(states)):
        raise ValueError("unknown state id")
    row=states[state_id]
    if path in row["view_pngs"]:
        owner=state_id
    else:
        ref=row["view_refs"].get(path)
        if not isinstance(ref,dict) or ref.get("path")!=path:
            raise ValueError("missing view-ref")
        owner=ref.get("ref_state")
        if type(owner) is not int or not 0<=owner<state_id:
            raise ValueError("invalid direct reference")
        if path not in states[owner]["view_pngs"]:
            raise ValueError("reference is not a physical owner")
    frame=states[owner]["frame"]
    root=Path(episode_root)
    result=root/f"state_{owner:06d}_frame_{frame:06d}"/path
    if result.is_symlink() or not result.is_file():
        raise ValueError("referenced materialized PNG missing")
    if root.resolve(strict=True) not in result.resolve(strict=True).parents:
        raise ValueError("referenced PNG escapes Episode")
    return result


def robot_pose_xy_yaw(chassis_pose):
    """Existing chassis_pose() is the source of robot base heading."""
    p=np.asarray(chassis_pose["position_world"],float)
    f=np.asarray(chassis_pose["forward_world"],float)
    if p.shape!=(3,) or f.shape!=(3,) or not np.isfinite(p).all() or not np.isfinite(f).all():
        raise ValueError("invalid robot pose")
    return np.asarray([p[0],p[1],math.atan2(f[1],f[0])],dtype=np.float64)
