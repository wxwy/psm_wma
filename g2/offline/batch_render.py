"""Resource-bounded, multi-GPU F27 *View-only* episode batch scheduler.

The scheduler NEVER imports Mujoco, EGL or GPU libraries: every slot launches
a fresh child process, pinned to a physical MUJOCO_EGL_DEVICE_ID. Its inputs
are already verified per-episode snapshots, prepared 10mm color and native
dual-map artifacts. It does not create those upstream artifacts.

Root output is immutable per attempt. A validated episode receipt is required
before a job can become DONE. Batch success is not training/H1 acceptance.
"""

import argparse
import concurrent.futures
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import sys
import threading
import time

from g2.io import ContractError, digest, read_json

SCHEMA = "g2_gpu_batch_render_v1"
PLAN_SCHEMA = "g2_gpu_batch_pinned_plan_v1"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")
GIT_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
MAX_JOBS = 10000
MAX_GPUS = 8
REPORT_LIMIT = 100
WRITE_LOCK = threading.Lock()


@dataclass(frozen=True)
class Episode:
    episode_id: str
    inputs: Path
    prepared: Path
    native: Path
    input_sha256: str
    prepared_sha256: str
    native_sha256: str
    frames: tuple
    layout: int

    @property
    def count(self):
        return len(self.frames)


@dataclass(frozen=True)
class Slot:
    gpu: int
    index: int

    @property
    def label(self):
        return f"GPU{self.gpu}_worker{self.index:02d}"


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def source_identity(episode):
    return dict(
        id=episode.episode_id,
        inputs=str(episode.inputs),
        prepared=str(episode.prepared),
        native_output=str(episode.native),
        inputs_sha256=episode.input_sha256,
        color_manifest_sha256=episode.prepared_sha256,
        native_complete_sha256=episode.native_sha256,
        frames=list(episode.frames),
        layout=episode.layout,
    )


def absolute_existing_path(text, *, directory, field):
    if not isinstance(text, str) or not text.strip() or not Path(text).is_absolute():
        raise ContractError(f"{field} must be an absolute path")
    path = Path(text).resolve(strict=True)
    if directory != path.is_dir():
        raise ContractError(f"{field} has incorrect file/directory kind")
    return path


def pinned_episode(row):
    if not isinstance(row, dict) or set(row) != {
        "id",
        "inputs",
        "prepared",
        "native_output",
    }:
        raise ContractError("batch jobs require id/inputs/prepared/native_output")
    eid = row["id"]
    if not isinstance(eid, str) or not ID.fullmatch(eid) or eid in (".", ".."):
        raise ContractError("unsafe G2 episode job ID")
    inputs = absolute_existing_path(row["inputs"], directory=False, field="inputs")
    prepared = absolute_existing_path(row["prepared"], directory=True, field="prepared")
    native = absolute_existing_path(
        row["native_output"], directory=True, field="native_output"
    )
    cm = prepared / "color_manifest.json"
    nc = native / "F24_NATIVE_FULL_EPISODE_COMPLETE.json"
    if not cm.is_file() or not nc.is_file():
        raise ContractError("prepared/native episode completion receipts are missing")
    source = read_json(inputs)
    color = read_json(cm)
    complete = read_json(nc)
    if not isinstance(source, dict) or source.get("layout") not in (1, 10):
        raise ContractError("G2 render batch requires source Layout1/Layout10")
    states = source.get("states")
    if not isinstance(states, list) or not 2 <= len(states) <= 300:
        raise ContractError("invalid G2 episode state window")
    frames = tuple(x.get("frame") for x in states if isinstance(x, dict))
    if (
        len(frames) != len(states)
        or any(type(x) is not int or x < 0 for x in frames)
        or len(set(frames)) != len(frames)
        or list(frames) != sorted(frames)
    ):
        raise ContractError("duplicate, unordered or invalid native episode frames")
    if any(s.get("reference_views") for s in states):
        raise ContractError(
            "new Visual-Mesh views cannot match legacy reference_views; "
            "use source-verified inputs without obsolete pixel reference "
            "and a prepared manifest bound to those exact input bytes"
        )
    inputs_sha = digest(inputs)
    if (
        color.get("complete") is not True
        or color.get("source_inputs_sha256") != inputs_sha
        or color.get("layout") != source["layout"]
        or color.get("frames") != list(frames)
        or color.get("complete_episode_states") != len(frames)
    ):
        raise ContractError("prepared color provenance/episode coverage mismatch")
    color_rows = color.get("states")
    if (
        not isinstance(color_rows, list)
        or [x.get("frame") for x in color_rows if isinstance(x, dict)] != list(frames)
        or [x.get("state_id") for x in color_rows if isinstance(x, dict)]
        != list(range(len(frames)))
    ):
        raise ContractError("prepared state IDs or frame ordering incomplete")
    if (
        complete.get("complete_state_count") != len(frames)
        or complete.get("native_color_full_F22_sha_equal_every_state") is not True
        or complete.get("native_dual_map_same_process") is not True
        or complete.get("source_known_region_is_TEST_ONLY_NOT_CERTIFIED") is not True
    ):
        raise ContractError("native dual-map episode is incomplete/not reviewed")
    if color.get("training_ready") is not False:
        raise ContractError("batch refuses to promote prepared data to training-ready")
    return Episode(
        eid,
        inputs,
        prepared,
        native,
        inputs_sha,
        digest(cm),
        digest(nc),
        frames,
        source["layout"],
    )


def read_plan_manifest(path):
    path = Path(path).resolve(strict=True)
    data = read_json(path, limit=24 * 1024 * 1024)
    if (
        not isinstance(data, dict)
        or data.get("schema") != SCHEMA
        or set(data) != {"schema", "jobs", "training_ready"}
        or data.get("training_ready") is not False
        or not isinstance(data["jobs"], list)
        or not 1 <= len(data["jobs"]) <= MAX_JOBS
    ):
        raise ContractError("invalid G2 batch manifest/size/training gate")
    jobs = [pinned_episode(x) for x in data["jobs"]]
    ids = [x.episode_id for x in jobs]
    if len(ids) != len(set(ids)):
        raise ContractError("duplicate G2 batch episode ID")
    return path, jobs


def source_commit(repo):
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    ).stdout.strip()
    if not GIT_OBJECT_ID.fullmatch(result):
        raise ContractError("cannot pin repository HEAD")
    return result


def source_overlap(output_root, jobs):
    output = output_root.resolve()
    for job in jobs:
        for source in (job.inputs, job.prepared, job.native):
            if output == source or output in source.parents or source in output.parents:
                raise ContractError("batch output overlaps a protected input source")


def pinned_plan(manifest, jobs, repo, *, python):
    manifest_sha = digest(manifest)
    root_source = source_commit(repo)
    source = dict(
        schema=PLAN_SCHEMA,
        manifest=str(manifest),
        manifest_sha256=manifest_sha,
        repo_root=str(repo),
        git_commit=root_source,
        python=str(python),
        mode="GPU_F27_SURFACE_REGISTRY_H1_APPROVED_NOT_TRAINING_READY",
        training_ready=False,
        jobs=[source_identity(j) for j in jobs],
    )
    source["plan_sha256"] = hashlib.sha256(canonical(source)).hexdigest()
    return source


def verify_output_root(root, jobs, *, create):
    if not root.is_absolute():
        raise ContractError("output root must be absolute")
    for parent in (root, *root.parents):
        if parent.is_symlink():
            raise ContractError("output root must not contain a symlink")
    source_overlap(root, jobs)
    if root.exists():
        if not root.is_dir():
            raise ContractError("output root is not a directory")
    elif create:
        root.mkdir(parents=True)
    return root.resolve()


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}.{threading.get_ident()}")
    with tmp.open("x", encoding="utf-8") as f:
        json.dump(
            data, f, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False
        )
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def validate_episode_receipt(out, episode):
    """Require F27 source-bound, material-aware evidence, never a legacy view."""
    receipt_path = out / "episode_receipt.json"
    if not receipt_path.is_file() or receipt_path.is_symlink():
        raise ContractError("missing episode completion receipt")
    result = read_json(receipt_path)
    if (
        result.get("schema") != "g2_repository_native_view_episode_v1"
        or result.get("complete") is not True
        or result.get("training_ready") is not False
        or result.get("source_inputs_sha256") != episode.input_sha256
        or result.get("spatial_state_count") != episode.count
        or result.get("view_opaque_geometry_source")
        != "SURFACE_REGISTRY_VISUAL_GEOMETRY"
        or result.get("semantic_owner_optional") is not True
        or result.get("source_material_identity_per_pixel") is not True
        or result.get("native_scene_graph_modified") is not False
        or result.get("source_alpha_model")
        != "FRONT_SURFACE_PER_GEOM_SORTED_ALPHA_NO_REFRACTION"
        or result.get("renderer_backend") != "gpu"
        or result.get("view_meters_per_pixel") != 0.01
    ):
        raise ContractError("F27 material/geometry episode proof is missing")
    rows = result.get("states")
    if (
        not isinstance(rows, list)
        or len(rows) != episode.count
        or [r.get("frame") for r in rows] != list(episode.frames)
        or [r.get("state_id") for r in rows] != list(range(episode.count))
    ):
        raise ContractError("F27 episode states incomplete or unordered")
    source_states = read_json(episode.inputs).get("states", [])
    image_count = 0
    for row, source_state in zip(rows, source_states):
        if (
            type(row.get("view_count")) is not int
            or row["view_count"] < 1
            or row.get("view_opaque_visual_geometry_from_source") is not True
            or row.get("source_surfel_geom_color_training_ready") is not False
            or type(row.get("surface_registry_count")) is not int
            or row["surface_registry_count"] < 1
            or type(row.get("transparent_visible_pixels")) is not int
            or row["transparent_visible_pixels"] < 0
            or type(row.get("unbound_visible_pixels")) is not int
            or row["unbound_visible_pixels"] < 0
            or row.get("alpha_sidecar_count") != row["transparent_visible_pixels"]
        ):
            raise ContractError("F27 per-state surface/alpha evidence missing")
        state = out / f"state_{row['state_id']:06d}_frame_{row['frame']:06d}"
        dc = state / "direct_color_views.json"
        reg = state / "surface_registry.json"
        native = state / "g2_original_gpu" / "views.json"
        if any(not p.is_file() or p.is_symlink() for p in (dc, reg, native)):
            raise ContractError("F27 view, registry or numeric provenance missing")
        d, registry, nv = read_json(dc), read_json(reg), read_json(native)
        if (
            d.get("frame_id") != row["frame"]
            or d.get("training_ready") is not False
            or d.get("visual_geometry_source")
            != "SURFACE_REGISTRY_VISUAL_GEOMETRY"
            or d.get("surface_material_identity_per_pixel") is not True
            or d.get("source_scene_graph_unchanged") is not True
            or d.get("unknown_visual_color_regions_retained") is not True
            or d.get("transparent_visible_pixels")
            != row["transparent_visible_pixels"]
            or d.get("unbound_visible_pixels") != row["unbound_visible_pixels"]
            or d.get("view_count") != row["view_count"]
            or registry.get("schema") != "g2_surface_registry_v1"
            or registry.get("native_scene_graph_modified") is not False
            or registry.get("frame_id") != row["frame"]
            or registry.get("source_sha256") != d.get("source_sha256")
            or registry.get("scene_id") != d.get("scene_id")
            or not isinstance(registry.get("surfaces"), list)
            or len(registry["surfaces"]) != row["surface_registry_count"]
            or nv.get("frame_id") != row["frame"]
            or nv.get("source_sha256") != d.get("source_sha256")
            or nv.get("training_ready") is not False
        ):
            raise ContractError("F27 surface registry or scene/alpha identity differs")
        if source_state.get("scene_graph"):
            graph = state / "scene_graph.json"
            if (
                not graph.is_file()
                or graph.is_symlink()
                or digest(graph) != source_state["scene_graph"]["sha256"]
            ):
                raise ContractError("F27 native scene graph missing or modified")
        views = d.get("views")
        native_views = nv.get("views")
        if (
            not isinstance(views, list)
            or len(views) != row["view_count"]
            or not isinstance(native_views, dict)
        ):
            raise ContractError("F27 view list incomplete")
        for view in views:
            rel = Path(view.get("rgb_file", ""))
            native_name = view.get("native_view")
            if (
                rel.is_absolute()
                or ".." in rel.parts
                or len(rel.parts) < 2
                or not isinstance(native_name, str)
                or native_name not in native_views
                or native_views[native_name].get("image_generated") is not True
                or not (state / rel).is_file()
                or (state / rel).is_symlink()
                or digest(state / rel) != view.get("sha256")
            ):
                raise ContractError("F27 view PNG or source direction invalid")
            native_rel = Path(native_name)
            if native_rel.is_absolute() or ".." in native_rel.parts:
                raise ContractError("unsafe F27 native view directory")
            view_dir = state / "g2_original_gpu" / native_rel
            for name in ("geometry.npz", "view.json", "geometry_valid.png", "color_valid.png"):
                if not (view_dir / name).is_file() or (view_dir / name).is_symlink():
                    raise ContractError("F27 per-pixel geometry/material proof missing")
        image_count += len(views)
    return dict(
        status="DONE_NOT_TRAINING_CERTIFIED",
        episode_id=episode.episode_id,
        frames=episode.count,
        view_images=image_count,
        receipt_sha256=digest(receipt_path),
        renderer_mode="F27_SURFACE_REGISTRY_VISUAL_GEOMETRY",
        training_ready=False,
        output=str(out),
    )


def gpu_free_mib(gpu):
    """Real physical GPU free-memory snapshot; not a reservation."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "-i",
                str(gpu),
                "--query-gpu=memory.free",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            capture_output=True,
            timeout=8,
            check=True,
        )
        value = int(result.stdout.strip())
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as exc:
        raise ContractError(f"GPU {gpu} free-memory check failed") from exc
    if value < 0:
        raise ContractError("invalid GPU memory counter")
    return value


def available_slots(gpus, workers_per_gpu):
    if (
        not isinstance(gpus, (tuple, list))
        or not gpus
        or len(gpus) > MAX_GPUS
        or any(type(x) is not int or x < 0 for x in gpus)
        or len(set(gpus)) != len(gpus)
        or type(workers_per_gpu) is not int
        or not 1 <= workers_per_gpu <= 8
    ):
        raise ContractError("invalid GPU list or workers-per-GPU")
    return [Slot(gpu, index) for index in range(workers_per_gpu) for gpu in gpus]


def child_command(python, episode, destination):
    return [
        str(python),
        "-m",
        "g2.offline.episode",
        "render",
        "--inputs",
        str(episode.inputs),
        "--prepared",
        str(episode.prepared),
        "--native-output",
        str(episode.native),
        "--output",
        str(destination),
        "--backend",
        "gpu",
        "--surface-registry-source",
    ]


def ensure_root_plan(root, plan):
    path = root / "_batch_plan.json"
    if not path.exists():
        atomic_json(path, plan)
    else:
        previous = read_json(path)
        if previous != plan:
            raise ContractError(
                "batch output has another immutable manifest, source hash, "
                "repository HEAD or Python environment; choose a new output root"
            )
    return path


def live_orphan_attempt(root, job):
    """Fail closed when an earlier scheduler died but an EGL child is still live."""
    for state in sorted((root / "_attempts").glob(f"{job.episode_id}_attempt_*.json")):
        try:
            record = read_json(state)
        except (OSError, ValueError):
            continue
        if (
            record.get("id") != job.episode_id
            or record.get("status") != "RUNNING"
            or type(record.get("pid")) is not int
        ):
            continue
        pid = record["pid"]
        proc = Path(f"/proc/{pid}/cmdline")
        try:
            arguments = proc.read_bytes()
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        if (
            b"g2.offline.episode" in arguments
            and str(record.get("output", "")).encode() in arguments
        ):
            raise ContractError(
                f"orphaned G2 renderer PID {pid} still alive for {job.episode_id}; "
                "refusing a duplicate EGL renderer"
            )


def inspect_existing(root, episode):
    """Find completed output and count all immutable recorded attempts.

    A crashed child may never have created its destination; the external
    attempt receipt still consumes an attempt number on resume.
    """
    path = root / episode.episode_id
    if path.is_symlink():
        raise ContractError("symlinked job folder is prohibited")
    count = 0
    recorded = root / "_attempts"
    if recorded.is_dir():
        for f in sorted(
            recorded.glob(f"{episode.episode_id}_attempt_[0-9][0-9][0-9][0-9].json")
        ):
            if f.is_symlink():
                raise ContractError("symlinked G2 attempt receipt is forbidden")
            rec = read_json(f)
            if rec.get("id") != episode.episode_id:
                raise ContractError("recorded attempt belongs to another episode")
            number = int(f.stem.rsplit("_attempt_", 1)[1])
            expected = path / f"attempt_{number:04d}"
            if rec.get("output") != str(expected):
                raise ContractError("G2 attempt receipt destination mismatch")
            count = max(count, number)
    if not path.is_dir():
        return None, count
    for attempt in sorted(path.glob("attempt_[0-9][0-9][0-9][0-9]")):
        if attempt.is_symlink() or not attempt.is_dir():
            raise ContractError("symlinked attempt directory is prohibited")
        number = int(attempt.name[-4:])
        count = max(count, number)
        if (attempt / "episode_receipt.json").exists():
            try:
                result = validate_episode_receipt(attempt, episode)
                return result, count
            except (OSError, ValueError):
                # Incomplete/corrupt attempt cannot become DONE.
                continue
    return None, count


def tail_log(path, max_bytes=5000):
    if not path.is_file():
        return ""
    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        f.seek(max(0, f.tell() - max_bytes))
        return f.read().decode("utf-8", errors="replace")[-max_bytes:]


def terminate_group(process):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=4)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=4)


def render_attempt(
    slot,
    episode,
    destination,
    log,
    root,
    *,
    python,
    repo,
    timeout_seconds,
    cancel,
    command_factory=None,
):
    cmd = (command_factory or child_command)(python, episode, destination)
    if not isinstance(cmd, list) or any(not isinstance(x, str) for x in cmd):
        raise ContractError("renderer command must be explicit argv")
    env = os.environ.copy()
    env.update(
        MUJOCO_GL="egl",
        PYOPENGL_PLATFORM="egl",
        MUJOCO_EGL_DEVICE_ID=str(slot.gpu),
        CUDA_VISIBLE_DEVICES=str(slot.gpu),
        PYTHONDONTWRITEBYTECODE="1",
    )
    # Child process never shares an EGL context with this CPU scheduler.
    # Extra pre-existing PYTHONPATH entries (e.g. authorized ROS runtime)
    # remain accessible, but repo V3 wins name resolution.
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    label = f"{episode.episode_id}_{destination.name}"
    state = root / "_attempts" / f"{label}.json"
    started = time.monotonic()
    record = dict(
        schema="g2_gpu_render_attempt_v1",
        status="STARTING",
        id=episode.episode_id,
        output=str(destination),
        slot=slot.label,
        physical_egl_gpu=slot.gpu,
        gpu_environment={
            k: env[k]
            for k in (
                "MUJOCO_EGL_DEVICE_ID",
                "CUDA_VISIBLE_DEVICES",
                "MUJOCO_GL",
                "PYOPENGL_PLATFORM",
            )
        },
        command=cmd,
        training_ready=False,
    )
    if cancel.is_set():
        return dict(status="CANCELLED", error="batch cancelled before launch")
    atomic_json(state, record)
    try:
        with log.open("x", encoding="utf-8") as output:
            output.write(
                f"slot={slot.label} physical_EGL_GPU={slot.gpu} "
                f"job={episode.episode_id}\n"
            )
            output.flush()
            proc = subprocess.Popen(
                cmd,
                cwd=repo,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            record.update(status="RUNNING", pid=proc.pid)
            atomic_json(state, record)
            reason = None
            while proc.poll() is None:
                if cancel.is_set():
                    reason = "CANCELLED"
                    terminate_group(proc)
                    break
                if timeout_seconds and time.monotonic() - started > timeout_seconds:
                    reason = "TIMEOUT"
                    terminate_group(proc)
                    break
                time.sleep(0.2)
            rc = proc.wait()
        seconds = round(time.monotonic() - started, 3)
        if reason is None and rc == 0:
            try:
                certified = validate_episode_receipt(destination, episode)
                result = dict(certified, seconds=seconds, slot=slot.label)
            except (OSError, ValueError) as exc:
                result = dict(
                    status="FAILED_VALIDATION",
                    error=str(exc),
                    seconds=seconds,
                    exit_code=rc,
                    log=str(log),
                    slot=slot.label,
                )
        else:
            result = dict(
                status=reason or "FAILED_PROCESS",
                exit_code=rc,
                seconds=seconds,
                log=str(log),
                error=tail_log(log),
                slot=slot.label,
            )
    except OSError as exc:
        result = dict(
            status="FAILED_LAUNCH",
            error=str(exc),
            log=str(log),
            seconds=round(time.monotonic() - started, 3),
            slot=slot.label,
        )
    record.update(result)
    atomic_json(state, record)
    return result


def process_job(
    slot,
    episode,
    root,
    *,
    python,
    repo,
    max_attempts,
    timeout_seconds,
    min_free_mib,
    cancel,
    command_factory=None,
):
    completed, existing_count = inspect_existing(root, episode)
    if completed:
        return dict(completed, reused_existing=True, slot=slot.label)
    if existing_count >= max_attempts:
        return dict(
            status="FAILED_EXHAUSTED",
            episode_id=episode.episode_id,
            attempts_existing=existing_count,
            slot=slot.label,
            training_ready=False,
        )
    live_orphan_attempt(root, episode)
    last = None
    for attempt_number in range(existing_count + 1, max_attempts + 1):
        if cancel.is_set():
            break
        if min_free_mib:
            try:
                free = gpu_free_mib(slot.gpu)
            except ValueError as exc:
                return dict(
                    status="BLOCKED_GPU_PROBE",
                    episode_id=episode.episode_id,
                    error=str(exc),
                    slot=slot.label,
                )
            if free < min_free_mib:
                return dict(
                    status="BLOCKED_GPU_RESOURCE",
                    episode_id=episode.episode_id,
                    available_mib=free,
                    required_free_mib=min_free_mib,
                    slot=slot.label,
                    training_ready=False,
                )
        destination = root / episode.episode_id / f"attempt_{attempt_number:04d}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() or destination.is_symlink():
            raise ContractError("G2 immutable attempt path already exists")
        log = root / "_logs" / f"{episode.episode_id}_attempt_{attempt_number:04d}.log"
        last = render_attempt(
            slot,
            episode,
            destination,
            log,
            root,
            python=python,
            repo=repo,
            timeout_seconds=timeout_seconds,
            cancel=cancel,
            command_factory=command_factory,
        )
        if last["status"] == "DONE_NOT_TRAINING_CERTIFIED":
            return dict(
                last,
                episode_id=episode.episode_id,
                attempt=attempt_number,
                reused_existing=False,
            )
        if last["status"] == "CANCELLED":
            break
    return dict(
        status=(last["status"] if last else "CANCELLED"),
        episode_id=episode.episode_id,
        slot=slot.label,
        last_failure=last,
        training_ready=False,
        attempts_total=max_attempts,
    )


def run_jobs(
    jobs,
    root,
    slots,
    *,
    python,
    repo,
    max_attempts,
    timeout_seconds,
    min_free_mib,
    cancel,
    command_factory=None,
):
    tasks = queue.Queue()
    for item in jobs:
        tasks.put(item)
    results = []
    started = time.monotonic()

    def worker(slot):
        local = []
        while not cancel.is_set():
            try:
                item = tasks.get_nowait()
            except queue.Empty:
                break
            try:
                result = process_job(
                    slot,
                    item,
                    root,
                    python=python,
                    repo=repo,
                    max_attempts=max_attempts,
                    timeout_seconds=timeout_seconds,
                    min_free_mib=min_free_mib,
                    cancel=cancel,
                    command_factory=command_factory,
                )
            except Exception as exc:
                result = dict(
                    status="FAILED_INTERNAL",
                    error=f"{type(exc).__name__}: {exc}",
                    episode_id=item.episode_id,
                    slot=slot.label,
                    training_ready=False,
                )
            atomic_json(root / "_receipts" / f"{item.episode_id}.json", result)
            with WRITE_LOCK:
                print(
                    json.dumps(
                        dict(
                            job=item.episode_id,
                            status=result["status"],
                            slot=slot.label,
                        ),
                        sort_keys=True,
                    ),
                    flush=True,
                )
            local.append(result)
            tasks.task_done()
        return local

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(slots)) as pool:
        futures = [pool.submit(worker, slot) for slot in slots]
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())
    elapsed = round(time.monotonic() - started, 3)
    done = [x for x in results if x["status"] == "DONE_NOT_TRAINING_CERTIFIED"]
    failed = [x for x in results if x["status"] not in ("DONE_NOT_TRAINING_CERTIFIED",)]
    metrics = dict(
        schema="g2_gpu_batch_run_report_v1",
        selected_jobs=len(jobs),
        completed=len(done),
        not_done=len(failed),
        remaining_unstarted=tasks.qsize(),
        worker_slots=[s.label for s in slots],
        completed_by_gpu={
            str(gpu): sum(
                x.get("slot", "").startswith(f"GPU{gpu}_worker")
                and x["status"] == "DONE_NOT_TRAINING_CERTIFIED"
                for x in results
            )
            for gpu in sorted({s.gpu for s in slots})
        },
        elapsed_wall_seconds=elapsed,
        completed_episodes_per_hour=(
            round(len(done) * 3600 / elapsed, 4) if elapsed else None
        ),
        gpu_memory_guard_mib=min_free_mib,
        training_ready=False,
        human_gate="PENDING_HUMAN",
        results=sorted(results, key=lambda item: item["episode_id"]),
    )
    return metrics


def parse_gpus(text):
    if not isinstance(text, str):
        raise ContractError("GPU selection must be comma-separated")
    pieces = text.split(",")
    if any(not x.isdecimal() for x in pieces):
        raise ContractError("physical EGL GPU IDs must be nonnegative integers")
    gpus = [int(x) for x in pieces]
    available_slots(gpus, 1)
    return gpus


def run_command(args):
    manifest, jobs = read_plan_manifest(args.manifest)
    repo = absolute_existing_path(args.repo_root, directory=True, field="repo_root")
    if not (repo / "g2" / "offline" / "episode.py").is_file():
        raise ContractError("repository root does not contain G2 episode render")
    python = absolute_existing_path(args.python, directory=False, field="python")
    root = verify_output_root(Path(args.output_root), jobs, create=False)
    plan = pinned_plan(manifest, jobs, repo, python=python)

    if args.action == "plan":
        preview = dict(
            schema=PLAN_SCHEMA,
            manifest_sha256=plan["manifest_sha256"],
            git_commit=plan["git_commit"],
            total_jobs=len(jobs),
            total_prepared_states=sum(j.count for j in jobs),
            examples=[source_identity(j) for j in jobs[:3]],
            output_root=str(root),
            rendered_training_ready=False,
            live_gpu_or_episode_processes_started=False,
            resume_supported=True,
        )
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        return 0

    if args.action == "report":
        pinned = root / "_batch_plan.json"
        report = root / "_batch_run_report.json"
        if not pinned.is_file() or not report.is_file():
            raise ContractError("batch run plan and report not yet available")
        existing = read_json(pinned)
        if existing.get("plan_sha256") != plan["plan_sha256"]:
            raise ContractError("batch manifest/repository/source changed since run")
        payload = read_json(report)
        print(
            json.dumps(
                {k: v for k, v in payload.items() if k != "results"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if (
        args.action != "run"
        or not args.allow_experimental
        or type(args.max_jobs) is not int
        or args.max_jobs < 1
    ):
        raise ContractError(
            "GPU batch requires explicit run --allow-experimental "
            "--max-jobs N; H1 and training remain unapproved"
        )
    if (
        not 1 <= args.max_attempts <= 10
        or not 0 <= args.timeout_seconds
        or not 0 <= args.min_free_mib <= 262144
    ):
        raise ContractError("invalid retry/timeout/free-memory limits")
    slots = available_slots(parse_gpus(args.gpus), args.workers_per_gpu)
    if not jobs:
        raise ContractError("no complete episodes to dispatch")
    root = verify_output_root(root, jobs, create=True)
    lock_path = root / "_batch.lock"
    if lock_path.is_symlink():
        raise ContractError("batch lock symlink is prohibited")
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ContractError("another G2 batch scheduler owns this output") from exc
        ensure_root_plan(root, plan)
        for section in ("_logs", "_attempts", "_receipts"):
            folder = root / section
            if folder.is_symlink():
                raise ContractError("unsafe batch metadata folder")
            folder.mkdir(exist_ok=True)

        to_dispatch = []
        already = []
        for episode in jobs:
            completed, _ = inspect_existing(root, episode)
            if completed:
                already.append(episode.episode_id)
            elif len(to_dispatch) < args.max_jobs:
                to_dispatch.append(episode)

        print(
            json.dumps(
                dict(
                    event="START_BATCH",
                    jobs_total=len(jobs),
                    jobs_reused=len(already),
                    jobs_scheduled=len(to_dispatch),
                    gpu_slots=[s.label for s in slots],
                    max_attempts=args.max_attempts,
                    min_free_mib=args.min_free_mib,
                    timeout_seconds=args.timeout_seconds,
                    manifest_sha256=plan["manifest_sha256"],
                    training_ready=False,
                ),
                ensure_ascii=False,
            ),
            flush=True,
        )

        cancel = threading.Event()
        previous = {}

        def request_shutdown(sig, frame):
            del frame
            cancel.set()
            print(
                json.dumps(
                    dict(event="SHUTDOWN_REQUESTED", signal=int(sig)),
                    ensure_ascii=False,
                ),
                flush=True,
            )

        for sig in (signal.SIGTERM, signal.SIGINT):
            previous[sig] = signal.getsignal(sig)
            signal.signal(sig, request_shutdown)
        try:
            metrics = run_jobs(
                to_dispatch,
                root,
                slots,
                python=python,
                repo=repo,
                max_attempts=args.max_attempts,
                timeout_seconds=args.timeout_seconds,
                min_free_mib=args.min_free_mib,
                cancel=cancel,
            )
        finally:
            for sig, prior in previous.items():
                signal.signal(sig, prior)

        metrics.update(
            manifest_sha256=plan["manifest_sha256"],
            git_commit=plan["git_commit"],
            gpus=[s.gpu for s in slots if s.index == 0],
            workers_per_gpu=args.workers_per_gpu,
            jobs_reused_before_run=len(already),
            total_manifest_jobs=len(jobs),
            total_done_through_run=len(already) + metrics["completed"],
            selected_max_jobs=args.max_jobs,
            signal_cancelled=cancel.is_set(),
            max_attempts_total=args.max_attempts,
        )
        atomic_json(root / "_batch_run_report.json", metrics)
        print(
            json.dumps(
                {k: v for k, v in metrics.items() if k != "results"},
                indent=2,
                ensure_ascii=False,
            ),
            flush=True,
        )
        if cancel.is_set():
            return 130
        if metrics["not_done"] or metrics["remaining_unstarted"]:
            return 2
        return 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "run", "report"))
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument(
        "--gpus", help="physical NVIDIA/EGL device indices, e.g. 4,5,6,7"
    )
    parser.add_argument(
        "--workers-per-gpu",
        type=int,
        choices=range(1, 9),
        default=1,
        metavar="{1..8}",
        help="1..8 independent EGL worker processes per selected GPU",
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=0,
        help="required on run; limit NEW jobs in a run",
    )
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=0,
        help="optional per-attempt watchdog; 0 means no time limit (default)",
    )
    parser.add_argument(
        "--min-free-mib",
        type=int,
        default=0,
        help="optional GPU free VRAM check; 0 disables the guard (default)",
    )
    parser.add_argument(
        "--allow-experimental",
        action="store_true",
        help="acknowledge H1 PENDING / training_ready=false",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return run_command(args)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(
            json.dumps(
                dict(
                    event="BATCH_REFUSED",
                    reason=f"{type(exc).__name__}: {exc}",
                    training_ready=False,
                ),
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
