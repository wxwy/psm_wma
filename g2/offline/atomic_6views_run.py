"""One-command RoboCasa G2 Full-Map F27 production from ORIGINAL open-source data.

The entrypoint itself discovers source episode IDs, generates every missing
intermediate, and reuses completed source-bound artifacts. It NEVER depends on
acceptance-folder snapshots or prebuilt flat/depth caches. GPU work is launched
ONLY by explicit 'run --manual-start --allow-experimental' in the foreground.

Pipeline per episode:
source -> factual metadata -> 10cm GT grid -> nav_sg GT -> 5cm first-frame
preview color -> native Room/SG bootstrap -> sealed native bundle -> lean F27
VisualGeom roster -> all 2Hz original GT states -> native Room-bound dynamic
snapshots/Islands -> native 10mm visual deltas -> native 10cm/10mm dualmap ->
F27 -> compact PNG/SG in user-selected output tree.

Official nav_sg is kept in a distinct process from PSM-WMA (both use package g2).
No guessed semantic on/inside relations or human certification is asserted.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import time
import traceback

from g2.io import ContractError, read_json, write_json
from g2.views.robot_pose_marker import (MARKER_RECIPE_VERSION, DEFAULT_MARKER_STYLE,
    MarkerAppearance, marker_cache_key, add_appearance_args,
    appearance_from_args, appearance_cli_args)
from . import atomic_6views_plan as plan
from .atomic_6views_compact import package
from .atomic_6views_geometry import build as build_geometry
from .atomic_6views_metadata import build as build_metadata
from .atomic_6views_source import prepare_model
from .atomic_6views_visual_inventory import build as build_visual_roster
from .atomic_6views_snapshots import generate as generate_snapshots

STAGES=("source","metadata","grid","native_gt","prescan",
        "native_prepare","native_run","bundle","visual_roster",
        "nav_states","snapshots","color","native_dualmap","f27")
RECEIPT="G2_STAGE_COMPLETE.json"


@dataclass(frozen=True)
class WorkerConfig:
    nav_repo: Path
    nav_setup: Path
    native_binary: Path
    python: Path
    output_root: Path
    work_root: Path
    keep_work: bool
    min_z: float
    max_z: float
    port: int
    gpu: int
    robocasa_repo: Path
    robosuite_repo: Path
    # Explicit Full Map GT-only initialization; default legacy remains intact.
    sim_direct_geometry_only: bool=False
    # Only RoboCasa/MuJoCo offline F27: skip per-frame 10cm nav_states and
    # run the native long-lived 10mm direct-color worker separately.
    sim_color_only: bool=False
    # MuJoCo GT+VisualMesh/material direct; no native 10mm RGB/voxel stages.
    sim_direct_material: bool=False
    # Experiment only. The legacy worker remains the default.
    scene_event_index: bool=False
    lazy_texel_decode: bool=False
    robot_pose_marker: bool=True
    robot_pose_marker_style: str="game_arrow"
    marker_appearance: MarkerAppearance=field(default_factory=MarkerAppearance)


def event(kind, *, row=None, **values):
    prefix=" ".join(f"{key}={value}" for key,value in values.items())
    who = ("task="+row["task_class"]+" episode="+str(row["episode_id"])+" ") if row else ""
    print("G2_"+kind+" "+who+prefix,flush=True)


def subprocess_stage(command, *, cwd=None, env=None, row=None, name=None):
    if row:
        event("SUBPROCESS_START",row=row,stage=name,argv0=command[0])
    begin=time.monotonic()
    # Inherit stdout/stderr so native per-state logs and F27 progress are LIVE.
    subprocess.run([str(v) for v in command],cwd=cwd,env=env,check=True)
    if row:
        event("SUBPROCESS_DONE",row=row,stage=name,seconds=round(time.monotonic()-begin,2))


def _stage_mark(path, name, row, *, robot_pose_marker=None,
                robot_pose_marker_style=None, marker_appearance=None,
                scene_event_index=None, lazy_texel_decode=None,
                sim_direct_material=None):
    marker=Path(path)/RECEIPT
    if not marker.is_file() or marker.is_symlink():
        return False
    data=read_json(marker)
    return (data.get("schema")=="g2_atomic_production_stage_v1"
            and data.get("complete") is True
            and data.get("stage")==name
            and data.get("source_fingerprint")==row["source_fingerprint"]
            and data.get("renderer")=="f27"
            and (scene_event_index is None or data.get("scene_event_index") is scene_event_index)
            and (lazy_texel_decode is None or data.get("lazy_texel_decode") is lazy_texel_decode)
            and (sim_direct_material is None or data.get("sim_direct_material") is sim_direct_material)
            and (robot_pose_marker is None or
                 data.get("robot_pose_marker") is robot_pose_marker)
            and (robot_pose_marker_style is None or
                 data.get("robot_pose_marker_style")==robot_pose_marker_style)
            and (robot_pose_marker is not True or
                 (data.get("robot_pose_marker_recipe_version")==MARKER_RECIPE_VERSION and
                  data.get("robot_pose_marker_appearance_sha256")==marker_cache_key(
                      robot_pose_marker_style or DEFAULT_MARKER_STYLE,
                      marker_appearance if marker_appearance is not None else MarkerAppearance()))))


def stage(work, name, row, builder, *, required=(), robot_pose_marker=None,
          robot_pose_marker_style=None, marker_appearance=None,
          scene_event_index=None, lazy_texel_decode=None,
          sim_direct_material=None):
    target=Path(work)/name
    if target.is_symlink():
        raise ContractError("stage must not be a symlink: "+str(target))
    if target.exists():
        if (_stage_mark(target,name,row,robot_pose_marker=robot_pose_marker,
                        robot_pose_marker_style=robot_pose_marker_style,
                        marker_appearance=marker_appearance,
                        scene_event_index=scene_event_index,
                        lazy_texel_decode=lazy_texel_decode,
                        sim_direct_material=sim_direct_material)
                and all((target/p).is_file() for p in required)):
            event("STAGE_REUSE",row=row,stage=name)
            return target
        # Only our own scratch root, never original source or finished output.
        if target.parent!=work or not target.is_dir():
            raise ContractError("stage output is not a managed scratch directory")
        event("STAGE_REBUILD",row=row,stage=name)
        shutil.rmtree(target)
    started=time.monotonic()
    event("STAGE_START",row=row,stage=name)
    builder(target)
    if not target.is_dir() or any(not (target/p).is_file() for p in required):
        raise ContractError("stage did not create required files: "+name)
    write_json(target/RECEIPT,{
        "schema":"g2_atomic_production_stage_v1","stage":name,
        "source_fingerprint":row["source_fingerprint"],
        "complete":True,"renderer":"f27","training_ready":False,
        **({"scene_event_index":scene_event_index} if scene_event_index is not None else {}),
        **({"lazy_texel_decode":lazy_texel_decode} if lazy_texel_decode is not None else {}),
        **({"sim_direct_material":sim_direct_material} if sim_direct_material is not None else {}),
        **({"robot_pose_marker":robot_pose_marker} if robot_pose_marker is not None else {}),
        **({"robot_pose_marker_style":robot_pose_marker_style}
           if robot_pose_marker_style is not None else {}),
        **({"robot_pose_marker_recipe_version":MARKER_RECIPE_VERSION,
            "robot_pose_marker_appearance_sha256":marker_cache_key(
                robot_pose_marker_style or DEFAULT_MARKER_STYLE,
                marker_appearance if marker_appearance is not None else MarkerAppearance())}
           if robot_pose_marker is True else {}),
    })
    event("STAGE_DONE",row=row,stage=name,
          seconds=round(time.monotonic()-started,2))
    return target


def _nav_env(config):
    env=os.environ.copy()
    # nav_sg source owns g2 in its own subprocess. Preserve optional Python
    # wheel overlay, but never import the two repositories as one g2 package.
    env["PYTHONPATH"]=str(config.nav_repo)+os.pathsep+env.get("PYTHONPATH","")
    env["PYTHONDONTWRITEBYTECODE"]="1"
    return env


def _native_gate(config, prepared, native_manifest, prescan, root, row):
    # The outer stage is managed by the Python runner; nav_sg's CLI creates
    # only its 'native_run' child, with an independent nonexisting output.
    root.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy()
    env.pop("PYTHONPATH",None)  # ROS1 Noetic uses a different Python ABI.
    env.update(
        G2_GT_PROJECTION_MIN_Z=str(config.min_z),
        G2_GT_PROJECTION_MAX_Z=str(config.max_z),
        G2_GT_EXPORT_SPATIAL="true",
        G2_GT_MIN_ASSIGNED="0",
        G2_GT_FULL_MAP_FRAME0_PROOF=str(prepared/"source_proof.txt"),
        G2_GT_PRESCAN_FRAME0=str(prescan/"precolored.txt"),
        G2_GT_ROS_PORT=str(config.port),
        G2_GT_ROS_HOME=str(root.parent/"native_ros_home"),
        PYTHONDONTWRITEBYTECODE="1",
    )
    # Native gate is shipped by nav_sg. Avoid assuming a system-wide ROS1.
    script=(f"source {shlex_quote(config.nav_setup)}; "
            f"bash {shlex_quote(config.nav_repo/'g2/gt/native_gate.sh')} "
            f"{shlex_quote(native_manifest/'grid.txt')} "
            f"{shlex_quote(native_manifest/'objects.txt')} "
            f"{shlex_quote(root/'native_run')} esdf_grid")
    subprocess_stage(["bash","-lc",script],cwd=config.nav_repo,env=env,
                     row=row,name="native_room_sg")
    if not (root/"native_run"/"FULL_MAP_PREVIEW_COMPLETE").is_file():
        raise ContractError("native Room/SG did not complete frame0")
    return root


def _native_geometry_gate(config, prepared, native_manifest, root, row):
    """Simulation-only nav_sg native Room/SG from 10cm Oracle geometry.

    No precolored cloud, RGB-D, or color worker is supplied to the initializer.
    The original _native_gate remains the unmodified legacy entry point.
    """
    root.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy()
    env.pop("PYTHONPATH",None)
    # Never inherit a cloud/perception source into the geometry-only worker.
    for name in ("G2_GT_PRESCAN_FRAME0","G2_GT_PRESCAN_FRAME200",
                 "G2_GT_FULL_MAP_FRAME0_PROOF","G2_GT_FULL_MAP_FRAME200_PROOF",
                 "G2_GT_OBSERVED_COLOR_MANIFEST",
                 "G2_GT_NEXT_OBSERVED_COLOR_MANIFEST"):
        env.pop(name,None)
    env.update(
        G2_GT_PROJECTION_MIN_Z=str(config.min_z),
        G2_GT_PROJECTION_MAX_Z=str(config.max_z),
        G2_GT_EXPORT_SPATIAL="true",G2_GT_MIN_ASSIGNED="0",
        G2_GT_FULL_MAP_GEOMETRY_ONLY_PROOF=str(prepared/"source_proof.txt"),
        G2_GT_ROS_PORT=str(config.port),
        G2_GT_ROS_HOME=str(root.parent/"direct_native_ros_home"),
        PYTHONDONTWRITEBYTECODE="1",
    )
    script=(f"source {shlex_quote(config.nav_setup)}; "
            f"bash {shlex_quote(config.nav_repo/'g2/gt/native_gate.sh')} "
            f"{shlex_quote(native_manifest/'grid.txt')} "
            f"{shlex_quote(native_manifest/'objects.txt')} "
            f"{shlex_quote(root/'native_run')} esdf_grid")
    subprocess_stage(["bash","-lc",script],cwd=config.nav_repo,env=env,
                     row=row,name="source_gt_geometry_only_native_room_sg")
    if not (root/"native_run/frame_0/spatial_snapshot/SNAPSHOT_COMPLETE").is_file() or not (
            root/"native_run/FULL_MAP_PREVIEW_COMPLETE").is_file():
        raise ContractError("geometry-only native Full Map Room/SG was not produced")
    return root


def shlex_quote(value):
    import shlex
    return shlex.quote(str(value))


def produce_one(row,config):
    from g2.nav_bridge.full_map import capture as capture_native
    from g2.nav_bridge.full_map import prepare as prepare_native
    from g2.sim.prescan import export as prescan
    from .episode import prepare as prepare_color
    # Rendering is a separate process with physical EGL pinning, not a shared
    # MuJoCo/GL context inside the CPU orchestrator.
    start=time.monotonic()
    work=config.work_root/row["task_class"]/f"episode_{row['episode_id']:06d}"
    # Separate source-mode namespace is required: no legacy snapshot/color/F27
    # stage receipt may be silently reused by the new direct GT recipe.
    if config.sim_color_only and not config.sim_direct_geometry_only:
        raise ContractError("simulation color-only requires native Full Map GT Room/SG")
    if config.sim_direct_geometry_only:
        work=work/("direct_gt_geometry_only_color_only_v1" if config.sim_color_only
                   else "direct_gt_geometry_only_v1")
    work.mkdir(parents=True,exist_ok=True)
    original=row["original"]
    scene=f"robocasa365_atomic_{row['episode_id']:06d}"
    nav_env=_nav_env(config)
    asset_roots=(config.robocasa_repo,config.robosuite_repo)
    rules=(("/opt/conda/envs/robocasa/lib/python3.10/site-packages/robosuite",
            str(config.robosuite_repo/"robosuite")),
           ("/root/robocasa/robocasa",str(config.robocasa_repo/"robocasa")))
    root=stage(work,"source",row,lambda p:prepare_model(
        original["model.xml.gz"],original["ep_meta.json"],
        original["states.npz"],p,length=row["source_frames"],
        layout=row["layout_id"],rules=rules,asset_roots=asset_roots),
        required=("source_receipt.json","scene_rebased.xml"))
    metadata=stage(work,"metadata",row,lambda p:build_metadata(
        root/"scene_rebased.xml",original["ep_meta.json"],original["states.npz"],
        p,scene_id=scene,asset_roots=asset_roots),
        required=("role_map.json","native_metadata.json"))
    grid=stage(work,"grid",row,lambda p:build_geometry(
        root/"scene_rebased.xml",original["states.npz"],
        metadata/"native_metadata.json",p,asset_roots=asset_roots),
        required=("grid_plan.json","known_region.json"))
    grid_plan=read_json(grid/"grid_plan.json")["grid"]
    def nav_gt(p):
        cmd=[config.python,"-m","g2.gt.mujoco_scene",
            "--mjcf",root/"scene_rebased.xml",
            "--metadata",metadata/"native_metadata.json",
            "--ep-meta",original["ep_meta.json"],
            "--states",original["states.npz"],"--state-format","mujoco_fullphysics",
            "--known-region",grid/"known_region.json",
            "--geometry","collision","--frame","0",
            "--resolution",str(grid_plan["resolution"]),
            "--dims",*[str(x) for x in grid_plan["dims"]],
            "--origin",*[str(x) for x in grid_plan["origin"]]]
        for asset in asset_roots:
            cmd.extend(("--asset-root",asset))
        cmd.extend(("--output",p))
        subprocess_stage(cmd,cwd=config.nav_repo,env=nav_env,row=row,name="native_source_gt")
    native_gt=stage(work,"native_gt",row,nav_gt,required=("manifest.json","grid.txt","objects.txt"))
    if config.sim_direct_geometry_only:
        from g2.nav_bridge.fullmap_geometry_only import (
            prepare as prepare_geometry_only,
            capture as capture_geometry_only,
        )
        direct_prepared=stage(work,"direct_prepare",row,lambda p:
            prepare_geometry_only(native_gt/"manifest.json",p),
            required=("source_proof.txt","plan.json"))
        direct_native=stage(work,"direct_native",row,lambda p:
            _native_geometry_gate(config,direct_prepared,native_gt,p,row),
            required=("native_run/frame_0/spatial_snapshot/snapshot.json",
                      "native_run/frame_0/spatial_snapshot/SNAPSHOT_COMPLETE"))
        bundle=stage(work,"direct_bundle",row,lambda p:
            capture_geometry_only(
                direct_native/"native_run/frame_0/spatial_snapshot",
                direct_prepared,p),
            required=("bundle.json","snapshot.json"))
    else:
        def prescan_builder(p):
            prescan(root/"scene_rebased.xml",metadata/"role_map.json",p,
                states=original["states.npz"],frame=0,spacing=.05,
                asset_roots=asset_roots,ep_meta=original["ep_meta.json"],
                state_format="mujoco_fullphysics",world_frame="world",
                native_manifest=native_gt/"manifest.json",
                allow_partial_color=True)
        color_prescan=stage(work,"prescan",row,prescan_builder,
                            required=("manifest.json","precolored.txt"))
        natprep=stage(work,"native_prepare",row,lambda p:prepare_native(
            native_gt/"manifest.json",color_prescan/"manifest.json",
            nav_repo=config.nav_repo,output=p,room_source="esdf_grid",
            min_z=config.min_z,max_z=config.max_z),
            required=("source_proof.txt","source_inputs.json"))
        native_initial=stage(work,"native_run",row,
            lambda p:_native_gate(config,natprep,native_gt,color_prescan,p,row),
            required=("native_run/frame_0/spatial_snapshot/snapshot.json",
                      "native_run/frame_0/spatial_snapshot/SNAPSHOT_COMPLETE"))
        # The legacy full-map source retains its original complete RGB,
        # validity and native ownership evidence. Native RGB-D stays unchanged.
        bundle=stage(work,"bundle",row,lambda p:capture_native(
            native_initial/"native_run/frame_0/spatial_snapshot",natprep,p,
            trust_native_owner=True),
            required=("bundle.json","snapshot.json"))
    roster=stage(work,"visual_roster",row,lambda p:build_visual_roster(
        native_gt/"manifest.json",metadata/"role_map.json",p),
        required=("dense_manifest.json",))
    if config.sim_color_only:
        # Dynamic SG already comes from the original MuJoCo state. The initial
        # Room comes from source-bound native GT; no 10cm navigation timeline is
        # consumed by the offline F27 color-only renderer.
        navstates=None
    else:
        def nav_frames(p):
            subprocess_stage([config.python,"-m","g2.gt.episode_nav_states",
                "--source-manifest",native_gt/"manifest.json",
                "--frames",json.dumps(row["spatial_frames"]),
                "--output",p],cwd=config.nav_repo,env=nav_env,
                row=row,name="native_navigation_states")
        navstates=stage(work,"nav_states",row,nav_frames,
                        required=("nav_manifest.json",))
    snapshots=stage(work,"snapshots",row,lambda p:generate_snapshots(
        bundle/"snapshot.json",native_gt/"manifest.json",
        row["spatial_frames"],nav_repo=config.nav_repo,
        role_map=metadata/"role_map.json",
        visual_inventory=roster/"dense_manifest.json",
        bundle_manifest=bundle/"bundle.json",
        layout_id=row["layout_id"],output=p),
        required=("episode_inputs.json","COMPLETE.json"))
    if config.sim_direct_material:
        # Simulation-only direct material path: source/GT/Scene Graph are
        # present, but NO 10mm colored voxelization or native-color stage.
        prepared=None
        dualmap=None
    else:
        prepared=stage(work,"color",row,lambda p:prepare_color(
            snapshots/"episode_inputs.json",
            None if config.sim_color_only else navstates/"nav_manifest.json",p,
            color_only=config.sim_color_only),
            required=("color_manifest.json","native_sequence.txt"))
    if config.sim_color_only and not config.sim_direct_material:
        def native_color_only(p):
            native_bin=config.native_binary.with_name("gt_direct_color_only")
            if not native_bin.is_file():
                raise ContractError("native 10mm color-only executable not built from nav_sg")
            env=os.environ.copy()
            env.pop("PYTHONPATH",None)
            command=("set -e; source "+shlex_quote(config.nav_setup)+"; "+
                     shlex_quote(native_bin)+" --plan "+
                     shlex_quote(prepared/"native_sequence.txt")+" --output "+
                     shlex_quote(p))
            subprocess_stage(["bash","-lc",command],cwd=config.nav_repo,
                             env=env,row=row,name="native_10mm_color_only")
        dualmap=stage(work,"native_color_only",row,native_color_only,
                      required=("G2_NATIVE_COLOR_ONLY_COMPLETE.json",))
    elif not config.sim_direct_material:
        def native_episode(p):
            env=os.environ.copy()
            env.pop("PYTHONPATH",None)  # Restore Noetic-owned packages via catkin setup.
            subprocess_stage(["bash",
                Path(__file__).with_name("native_sequence_gate.sh"),
                config.nav_setup,config.native_binary,
                prepared/"native_sequence.txt",p,str(config.port),
                str(config.min_z),str(config.max_z)],cwd=config.nav_repo,
                env=env,row=row,name="native_dualmap")
        dualmap=stage(work,"native_dualmap",row,native_episode,
                       required=("F24_NATIVE_FULL_EPISODE_COMPLETE.json",))
    def render(p):
        env=os.environ.copy()
        env.update(MUJOCO_GL="egl",PYOPENGL_PLATFORM="egl",
                   MUJOCO_EGL_DEVICE_ID=str(config.gpu),
                   CUDA_VISIBLE_DEVICES=str(config.gpu),
                   PYTHONDONTWRITEBYTECODE="1")
        command=[config.python,"-m","g2.offline.episode","render",
            "--inputs",snapshots/"episode_inputs.json",
            "--output",p,"--backend","gpu","--renderer","f27"]
        if not config.sim_direct_material:
            command+=["--prepared",prepared,"--native-output",dualmap]
        command+=(
            (["--color-only"] if config.sim_color_only else [])+
            (["--sim-direct-material"] if config.sim_direct_material else [])+
            (["--no-robot-pose-marker"] if not config.robot_pose_marker else [])+
            ["--robot-pose-marker-style",config.robot_pose_marker_style]+
            (["--scene-event-index"] if config.scene_event_index else [])+
            (["--lazy-texel-decode"] if config.lazy_texel_decode else [])+
            appearance_cli_args(config.marker_appearance))
        subprocess_stage(command,cwd=Path(__file__).resolve().parents[2],
                         env=env,row=row,name="f27")
    f27=stage(work,"f27",row,render,required=("episode_receipt.json",),
              robot_pose_marker=config.robot_pose_marker,
              robot_pose_marker_style=(config.robot_pose_marker_style
                                       if config.robot_pose_marker else None),
              marker_appearance=config.marker_appearance,
              scene_event_index=True if config.scene_event_index else None,
              lazy_texel_decode=True if config.lazy_texel_decode else None,
              sim_direct_material=True if config.sim_direct_material else None)
    final=config.output_root/row["expected_relative_output"]
    if config.scene_event_index:
        from .atomic_6views_compact_v2 import package_indexed
        result=package_indexed(f27,final,episode_id=row["episode_id"],
                               task_class=row["task_class"],selection=row)
    else:
        result=package(f27,final,episode_id=row["episode_id"],
                       task_class=row["task_class"],selection=row)
    event("EPISODE_DONE",row=row,states=result["state_count"],
          output=final,elapsed_s=round(time.monotonic()-start,2))
    if not config.keep_work:
        shutil.rmtree(work)
    return result


def _load_selection(plan_root):
    plans=[]
    for file in sorted(Path(plan_root).glob("batch_*.json")):
        data=read_json(file)
        if data.get("renderer")!="f27":
            raise ContractError("non-F27 planning manifest")
        plans.extend(data["episodes"])
    ids=[x["episode_id"] for x in plans]
    if len(ids)!=len(set(ids)):
        raise ContractError("duplicate episode in pinned plan")
    return plans


def _ports(gpus,workers,base):
    if not gpus or len(set(gpus))!=len(gpus) or any(x<0 for x in gpus):
        raise ContractError("invalid physical GPU list")
    if not 1<=workers<=8 or base<=1024 or base+len(gpus)*workers>=65535:
        raise ContractError("invalid worker count/ROS port range")
    return [(gpu,slot,base+index*workers+slot)
            for index,gpu in enumerate(gpus) for slot in range(workers)]


def ensure_repository_builds(repo, nav_repo, nav_setup, native_binary, *,
                             sim_direct_geometry_only=False, sim_color_only=False):
    """Compile missing/stale native modules exclusively from both source trees."""
    repo=Path(repo).resolve(strict=True)
    nav_repo=Path(nav_repo).resolve(strict=True)
    raster_src=repo/"g2/offline/fast_surface_cells.cpp"
    raster_bin=repo/"g2/bin/libfast_surface_cells.so"
    if not raster_src.is_file():
        raise ContractError("missing V3 native triangle raster source")
    if (not raster_bin.is_file()
            or raster_src.stat().st_mtime_ns>raster_bin.stat().st_mtime_ns):
        event("BUILD",repo="psm_wma_v3",target="libfast_surface_cells")
        subprocess_stage(["bash",repo/"g2/offline/build_native_raster.sh"],cwd=repo)
    cpp=nav_repo/"mapping_8_3/mapping/src/gt/gt_direct_color_episode.cpp"
    if not cpp.is_file():
        raise ContractError("missing nav_sg committed native worker source")
    if not nav_setup.is_file():
        raise ContractError("nav_sg ROS Noetic setup.bash is not installed")
    build_root=nav_repo/".g2_catkin_ws/build"
    if not build_root.is_dir():
        raise ContractError("nav_sg catkin workspace is not configured")
    geometry_source=nav_repo/"mapping_8_3/mapping/src/gt/gt_oracle_native.cpp"
    geometry_binary=native_binary.parent/"gt_oracle_native"
    direct_deps=(geometry_source,
                 nav_repo/"mapping_8_3/mapping/src/map_input/spatial_snapshot.cpp",
                 nav_repo/"mapping_8_3/mapping/include/mapping/map_input/spatial_snapshot.h")
    need_direct=(sim_direct_geometry_only and
                 (not geometry_binary.is_file() or any(
                     p.stat().st_mtime_ns>geometry_binary.stat().st_mtime_ns
                     for p in direct_deps)))
    if (not native_binary.is_file()
            or cpp.stat().st_mtime_ns>native_binary.stat().st_mtime_ns
            or need_direct):
        event("BUILD",repo="nav_sg",target="gt_direct_color_episode")
        script=("set -e; source "+shlex_quote(nav_setup)+"; "
                "cmake --build "+shlex_quote(build_root)
                +" --target gt_direct_color_episode gt_oracle_native -j4")
        subprocess_stage(["bash","-lc",script],cwd=nav_repo)
    if (not native_binary.is_file()
            or cpp.stat().st_mtime_ns>native_binary.stat().st_mtime_ns):
        raise ContractError("nav_sg worker did not build from current source")
    if sim_color_only:
        if not sim_direct_geometry_only:
            raise ContractError("color-only native worker requires explicit direct Full Map")
        source=nav_repo/"g2/gt/gt_direct_color_only.cpp"
        binary=native_binary.with_name("gt_direct_color_only")
        if not source.is_file():
            raise ContractError("simulation color-only nav_sg executable source is absent")
        if not binary.is_file() or source.stat().st_mtime_ns>binary.stat().st_mtime_ns:
            event("BUILD",repo="nav_sg",target="gt_direct_color_only")
            shell=("set -e; source "+shlex_quote(nav_setup)+"; cmake --build "+
                   shlex_quote(build_root)+" --target gt_direct_color_only -j4")
            subprocess_stage(["bash","-lc",shell],cwd=nav_repo)
        if not binary.is_file() or source.stat().st_mtime_ns>binary.stat().st_mtime_ns:
            raise ContractError("native 10mm source-color worker missing or stale")


def schedule(args):
    rows,_=plan.discover(args.mapping,args.raw_root,args.depth_root,
                         require_depth=args.require_depth)
    selected,counts=plan.select(rows,tasks=args.task,
                                 episodes_per_task=args.episodes_per_task)
    pending=[r for r in selected if not plan.completed_output(r,args.output_root,allow_index_v2=args.scene_event_index)]
    event("SELECTION",total=len(selected),pending=len(pending),
          selected_tasks=len(counts),per_task=args.episodes_per_task or "ALL",
          renderer="f27")
    for task,count in counts.items():
        event("TASK",name=task,selected=count)
    if args.action=="scan":
        return 0
    if args.action=="run" and not (args.manual_start and args.allow_experimental):
        raise ContractError("only the owner may manually start: run --manual-start --allow-experimental")
    index=plan.build(args.mapping,args.raw_root,args.depth_root,
        args.plan_root,args.output_root,expected=args.expected,
        tasks=args.task,episodes_per_task=args.episodes_per_task,
        batch_size=args.batch_size,resume=args.resume,
        require_depth=args.require_depth,
        allow_index_v2=args.scene_event_index)
    if args.action=="plan":
        event("PLAN",path=args.plan_root,episodes=index["episodes_total"],
              batches=index["batches_total"],production_started=False)
        return 0
    # A previous reusable immutable plan can contain already DONE rows;
    # actual dispatch only enqueues current pending source identities.
    if not args.plan_root.is_dir():
        raise ContractError("pinned plan is missing")
    all_rows=_load_selection(args.plan_root)
    saved={r["episode_id"]:r for r in selected}
    if any(saved.get(r["episode_id"],{}).get("source_fingerprint")!=r["source_fingerprint"]
           for r in all_rows):
        raise ContractError("pinned plan differs from current original source")
    jobs=[r for r in all_rows if not plan.completed_output(r,args.output_root,allow_index_v2=args.scene_event_index)]
    if not jobs:
        event("ALL_DONE",total=len(selected),skipped_completed=len(selected))
        return 0
    nav_repo=args.nav_repo.resolve(strict=True)
    nav_setup=args.nav_setup or nav_repo/".g2_catkin_ws/devel/setup.bash"
    native_binary=args.native_binary or nav_repo/".g2_catkin_ws/devel/lib/mapping/gt_direct_color_episode"
    for p in (nav_setup,native_binary):
        if not p.is_file():
            raise ContractError("native ROS/catkin runtime missing: "+str(p))
    # Only the explicit owner-triggered run reaches compilation or GPU stages.
    root=args.work_root or args.output_root/"_work"
    raw=args.raw_root.resolve(strict=True)
    root=root.absolute()
    if (root==raw or raw in root.parents or root in raw.parents
            or root==args.output_root or root in args.output_root.parents):
        raise ContractError("work-root overlaps original input/parent or output parent")
    slots=_ports(args.gpus,args.workers_per_gpu,args.ros_port_base)
    ensure_repository_builds(Path(__file__).resolve().parents[2],nav_repo,nav_setup,native_binary,
                             sim_direct_geometry_only=args.sim_direct_geometry_only,
                             sim_color_only=args.sim_color_only and not args.sim_direct_material)
    args.output_root.mkdir(parents=True,exist_ok=True)
    root.mkdir(parents=True,exist_ok=True)
    q=queue.Queue()
    for row in jobs:q.put(row)
    failures=[]
    finished=[]
    started=time.monotonic()
    for r in all_rows:
        if plan.completed_output(r,args.output_root,allow_index_v2=args.scene_event_index):
            finished.append(r["episode_id"])
    def worker(slot):
        gpu,subslot,port=slot
        while True:
            try:row=q.get_nowait()
            except queue.Empty:return
            status="FAILED"
            for attempt in range(1,args.max_attempts+1):
                event("START",row=row,gpu=gpu,slot=subslot,
                      attempt=attempt,max_attempts=args.max_attempts)
                cmd=[sys.executable,"-m","g2.offline.atomic_6views_run","work",
                     "--episode-id",str(row["episode_id"]),
                     "--plan-root",str(args.plan_root),
                     "--output-root",str(args.output_root),
                     "--work-root",str(root),
                     "--nav-repo",str(nav_repo),
                     "--robocasa-repo",str(args.robocasa_repo),
                     "--robosuite-repo",str(args.robosuite_repo),
                     "--nav-setup",str(nav_setup),
                     "--native-binary",str(native_binary),
                     "--ros-port",str(port),"--gpu",str(gpu),
                     "--min-z",str(args.min_z),"--max-z",str(args.max_z),
                     "--manual-start","--allow-experimental"]
                if args.keep_work:cmd.append("--keep-work")
                if args.sim_direct_geometry_only:cmd.append("--sim-direct-geometry-only")
                if args.sim_color_only:cmd.append("--sim-color-only")
                if args.sim_direct_material:cmd.append("--sim-direct-material")
                if args.scene_event_index:cmd.append("--scene-event-index")
                if args.lazy_texel_decode:cmd.append("--lazy-texel-decode")
                if not args.robot_pose_marker:cmd.append("--no-robot-pose-marker")
                cmd.extend(["--robot-pose-marker-style",args.robot_pose_marker_style])
                cmd.extend(appearance_cli_args(appearance_from_args(args)))
                try:
                    subprocess.run(cmd,check=True)
                    if not plan.completed_output(row,args.output_root,allow_index_v2=args.scene_event_index):
                        raise ContractError("worker returned without matching final output")
                    status="DONE"
                    break
                except (subprocess.CalledProcessError,ContractError) as error:
                    event("ATTEMPT_FAILED",row=row,gpu=gpu,slot=subslot,
                          attempt=attempt,error=str(error).replace(" ","_")[:180])
            with lock:
                if status=="DONE":
                    finished.append(row["episode_id"])
                else:
                    failures.append(row["episode_id"])
                n=len(finished)
                overall=len(selected)
                elapsed=max(0.001,time.monotonic()-started)
                bytask=sum(saved[eid]["task_class"]==row["task_class"] for eid in finished)
                current=counts[row["task_class"]]
                event("PROGRESS",row=row,status=status,finished=n,
                      total=overall,percent=f"{n/overall*100:.1f}",
                      task_finished=bytask,task_total=current,
                      failed=len(failures),elapsed_s=round(elapsed,1))
    import threading
    lock=threading.Lock()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(slots)) as ex:
        list(ex.map(worker,slots))
    event("SUMMARY",selected=len(selected),finished=len(finished),
          failed=len(failures),failed_ids=sorted(failures),
          seconds=round(time.monotonic()-started,1))
    return 0 if not failures else 2


def run_one_cli(args):
    if not args.manual_start or not args.allow_experimental:
        raise ContractError("work action is manual-only")
    for batch in Path(args.plan_root).glob("batch_*.json"):
        rows=read_json(batch)["episodes"]
        selected=next((x for x in rows if x["episode_id"]==args.episode_id),None)
        if selected is not None:break
    else:raise ContractError("episode is absent from immutable source plan")
    if plan.completed_output(selected,args.output_root,allow_index_v2=args.scene_event_index):
        event("EPISODE_REUSE",row=selected)
        return 0
    config=WorkerConfig(
        nav_repo=args.nav_repo.resolve(strict=True),nav_setup=args.nav_setup,
        native_binary=args.native_binary,python=Path(sys.executable),
        output_root=args.output_root,work_root=args.work_root,
        keep_work=args.keep_work,min_z=args.min_z,max_z=args.max_z,
        port=args.ros_port,gpu=args.gpu,
        robocasa_repo=args.robocasa_repo,robosuite_repo=args.robosuite_repo,
        sim_direct_geometry_only=args.sim_direct_geometry_only,
            sim_color_only=args.sim_color_only,
            sim_direct_material=args.sim_direct_material,
            scene_event_index=args.scene_event_index,
            lazy_texel_decode=args.lazy_texel_decode,
            robot_pose_marker=args.robot_pose_marker,
            robot_pose_marker_style=args.robot_pose_marker_style,
            marker_appearance=appearance_from_args(args))
    produce_one(selected,config)
    return 0


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("scan","plan","run","work"))
    p.add_argument("--raw-root",type=Path,default=plan.RAW)
    p.add_argument("--mapping",type=Path,default=plan.FLAT/"flat_v3_mapping.parquet")
    p.add_argument("--depth-root",type=Path,default=plan.DEPTH)
    p.add_argument("--require-depth",action="store_true")
    p.add_argument("--output-root",type=Path,default=plan.OUTPUT)
    p.add_argument("--plan-root",type=Path)
    p.add_argument("--work-root",type=Path)
    p.add_argument("--task",action="append",default=[])
    p.add_argument("--episodes-per-task",type=int,default=None,
                   help="default ALL episodes per selected task")
    p.add_argument("--batch-size",type=int,default=100)
    p.add_argument("--expected",type=int,default=None)
    p.add_argument("--resume",action="store_true")
    p.add_argument("--gpus",default="4,5,6,7")
    p.add_argument("--workers-per-gpu",type=int,default=2)
    p.add_argument("--max-attempts",type=int,default=2)
    p.add_argument("--ros-port-base",type=int,default=21500)
    p.add_argument("--nav-repo",type=Path,default=Path(__file__).resolve().parents[3]/"nav_sg")
    p.add_argument("--robocasa-repo",type=Path,
                   default=Path("/mnt/data1/data_v2_0617/robocasa_repo"))
    p.add_argument("--robosuite-repo",type=Path,
                   default=Path("/mnt/data1/data_v2_0617/robosuite_repo"))
    p.add_argument("--nav-setup",type=Path)
    p.add_argument("--native-binary",type=Path)
    p.add_argument("--min-z",type=float,default=.15)
    p.add_argument("--max-z",type=float,default=1.8)
    p.add_argument("--manual-start",action="store_true")
    p.add_argument("--allow-experimental",action="store_true")
    p.add_argument("--robot-pose-marker",action=argparse.BooleanOptionalAction,
                   default=True, help="include chassis marker on final floor-top PNGs (default: on)")
    p.add_argument("--robot-pose-marker-style",choices=("classic","game_arrow"),
                   default="game_arrow",help="final floor-top marker style (default: game_arrow)")
    add_appearance_args(p)
    p.add_argument("--sim-color-only",action="store_true",
                   help="experimental RoboCasa GT: F27 direct 10mm color, no nav_states")
    p.add_argument("--scene-event-index",action="store_true",
                   help="EXPERIMENT ONLY: 1mm/1deg scene event rendering + compact v2 indexed Views")
    p.add_argument("--sim-direct-material",action="store_true",
                   help="EXPERIMENT ONLY: eliminate 10mm color voxel and native_color_only stages")
    p.add_argument("--lazy-texel-decode",action="store_true",
                   help="EXPERIMENT ONLY: on-demand source texel decoding in F27")
    p.add_argument("--sim-direct-geometry-only",action="store_true",
                   help="experimental RoboCasa Full Map 10cm GT native Room/SG; never RGB-D")
    p.add_argument("--keep-work",action="store_true",
                   help="retain large temporary artifacts (default: clean on success)")
    p.add_argument("--episode-id",type=int)
    p.add_argument("--ros-port",type=int)
    p.add_argument("--gpu",type=int)
    return p


def main(argv=None):
    args=parser().parse_args(argv)
    if args.max_attempts<1 or args.max_attempts>5:
        raise ContractError("invalid retry count")
    if args.action in ("run","work") and not (
            args.manual_start and args.allow_experimental):
        raise ContractError("production is manual-only: explicitly pass "
                            "--manual-start --allow-experimental")
    if args.sim_color_only and not args.sim_direct_geometry_only:
        raise ContractError("color-only Full Map requires --sim-direct-geometry-only")
    if args.scene_event_index and not (args.sim_color_only and args.sim_direct_geometry_only
                                       and args.robot_pose_marker):
        raise ContractError("P1 View event indexing requires explicit direct GT + color-only + marker")
    if args.sim_direct_material and not (args.scene_event_index and args.sim_color_only
                                         and args.sim_direct_geometry_only):
        raise ContractError("P2 direct material requires approved P1/F27 direct GT mode")
    args.gpus=[int(x) for x in args.gpus.split(",")]
    args.output_root=args.output_root.resolve()
    if args.action=="work":
        if (args.plan_root is None or args.episode_id is None
                or args.work_root is None or args.ros_port is None
                or args.gpu is None or args.nav_setup is None
                or args.native_binary is None):
            raise ContractError("incomplete pinned manual worker launch")
        return run_one_cli(args)
    if args.plan_root is None:
        # Stable selection-specific plan is established only by the new plan
        # action, never by guessed filenames elsewhere in the repository.
        raise ContractError("--plan-root required for reproducible selection/resume")
    return schedule(args)


if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as error:
        traceback.print_exc()
        print("G2_WORKFLOW_REFUSED "+str(error),file=sys.stderr,flush=True)
        raise SystemExit(2)
