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
from dataclasses import dataclass
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


def _stage_mark(path, name, row):
    marker=Path(path)/RECEIPT
    if not marker.is_file() or marker.is_symlink():
        return False
    data=read_json(marker)
    return (data.get("schema")=="g2_atomic_production_stage_v1"
            and data.get("complete") is True
            and data.get("stage")==name
            and data.get("source_fingerprint")==row["source_fingerprint"]
            and data.get("renderer")=="f27")


def stage(work, name, row, builder, *, required=()):
    target=Path(work)/name
    if target.is_symlink():
        raise ContractError("stage must not be a symlink: "+str(target))
    if target.exists():
        if _stage_mark(target,name,row) and all((target/p).is_file() for p in required):
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
    bundle=stage(work,"bundle",row,lambda p:capture_native(
        native_initial/"native_run/frame_0/spatial_snapshot",natprep,p),
        required=("bundle.json","snapshot.json"))
    roster=stage(work,"visual_roster",row,lambda p:build_visual_roster(
        native_gt/"manifest.json",metadata/"role_map.json",p),
        required=("dense_manifest.json",))
    def nav_frames(p):
        subprocess_stage([config.python,"-m","g2.gt.episode_nav_states",
            "--source-manifest",native_gt/"manifest.json",
            "--frames",json.dumps(row["spatial_frames"]),
            "--output",p],cwd=config.nav_repo,env=nav_env,
            row=row,name="native_navigation_states")
    navstates=stage(work,"nav_states",row,nav_frames,required=("nav_manifest.json",))
    snapshots=stage(work,"snapshots",row,lambda p:generate_snapshots(
        bundle/"snapshot.json",native_gt/"manifest.json",
        row["spatial_frames"],nav_repo=config.nav_repo,
        role_map=metadata/"role_map.json",
        visual_inventory=roster/"dense_manifest.json",
        bundle_manifest=bundle/"bundle.json",
        layout_id=row["layout_id"],output=p),
        required=("episode_inputs.json","COMPLETE.json"))
    prepared=stage(work,"color",row,lambda p:prepare_color(
        snapshots/"episode_inputs.json",navstates/"nav_manifest.json",p),
        required=("color_manifest.json","native_sequence.txt"))
    def native_episode(p):
        subprocess_stage(["bash",
            Path(__file__).with_name("native_sequence_gate.sh"),
            config.nav_setup,config.native_binary,
            prepared/"native_sequence.txt",p,str(config.port),
            str(config.min_z),str(config.max_z)],cwd=config.nav_repo,
            env=os.environ.copy(),row=row,name="native_dualmap")
    dualmap=stage(work,"native_dualmap",row,native_episode,
                   required=("F24_NATIVE_FULL_EPISODE_COMPLETE.json",))
    def render(p):
        env=os.environ.copy()
        env.update(MUJOCO_GL="egl",PYOPENGL_PLATFORM="egl",
                   MUJOCO_EGL_DEVICE_ID=str(config.gpu),
                   CUDA_VISIBLE_DEVICES=str(config.gpu),
                   PYTHONDONTWRITEBYTECODE="1")
        subprocess_stage([config.python,"-m","g2.offline.episode","render",
            "--inputs",snapshots/"episode_inputs.json",
            "--prepared",prepared,"--native-output",dualmap,
            "--output",p,"--backend","gpu","--renderer","f27"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,row=row,name="f27")
    f27=stage(work,"f27",row,render,required=("episode_receipt.json",))
    final=config.output_root/row["expected_relative_output"]
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


def schedule(args):
    rows,_=plan.discover(args.mapping,args.raw_root,args.depth_root,
                         require_depth=args.require_depth)
    selected,counts=plan.select(rows,tasks=args.task,
                                 episodes_per_task=args.episodes_per_task)
    pending=[r for r in selected if not plan.completed_output(r,args.output_root)]
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
        require_depth=args.require_depth)
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
    jobs=[r for r in all_rows if not plan.completed_output(r,args.output_root)]
    if not jobs:
        event("ALL_DONE",total=len(selected),skipped_completed=len(selected))
        return 0
    nav_repo=args.nav_repo.resolve(strict=True)
    nav_setup=args.nav_setup or nav_repo/".g2_catkin_ws/devel/setup.bash"
    native_binary=args.native_binary or nav_repo/".g2_catkin_ws/devel/lib/mapping/gt_direct_color_episode"
    for p in (nav_setup,native_binary):
        if not p.is_file():
            raise ContractError("native ROS/catkin runtime missing: "+str(p))
    cpp=nav_repo/"mapping_8_3/mapping/src/gt/gt_direct_color_episode.cpp"
    if cpp.is_file() and cpp.stat().st_mtime_ns>native_binary.stat().st_mtime_ns:
        raise ContractError("native worker binary older than its committed source; rebuild before production")
    root=args.work_root or args.output_root/"_work"
    slots=_ports(args.gpus,args.workers_per_gpu,args.ros_port_base)
    args.output_root.mkdir(parents=True,exist_ok=True)
    root.mkdir(parents=True,exist_ok=True)
    q=queue.Queue()
    for row in jobs:q.put(row)
    failures=[]
    finished=[]
    started=time.monotonic()
    for r in all_rows:
        if plan.completed_output(r,args.output_root):
            finished.append(r["episode_id"])
    def worker(slot):
        gpu,subslot,port=slot
        config=WorkerConfig(
            nav_repo=nav_repo,nav_setup=nav_setup,native_binary=native_binary,
            python=Path(sys.executable),output_root=args.output_root,work_root=root,
            keep_work=args.keep_work,min_z=args.min_z,max_z=args.max_z,port=port,gpu=gpu,
            robocasa_repo=args.robocasa_repo,robosuite_repo=args.robosuite_repo)
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
                try:
                    subprocess.run(cmd,check=True)
                    if not plan.completed_output(row,args.output_root):
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
    if plan.completed_output(selected,args.output_root):
        event("EPISODE_REUSE",row=selected)
        return 0
    config=WorkerConfig(
        nav_repo=args.nav_repo.resolve(strict=True),nav_setup=args.nav_setup,
        native_binary=args.native_binary,python=Path(sys.executable),
        output_root=args.output_root,work_root=args.work_root,
        keep_work=args.keep_work,min_z=args.min_z,max_z=args.max_z,
        port=args.ros_port,gpu=args.gpu,
        robocasa_repo=args.robocasa_repo,robosuite_repo=args.robosuite_repo)
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
