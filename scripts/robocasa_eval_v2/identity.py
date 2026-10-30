"""Strict scientific identity and trusted readonly model hash cache reuse."""

from __future__ import annotations

import subprocess
from pathlib import Path

from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest, digest
from cosmos_framework.evaluation.robocasa_v2.store import read
from eval_robocasa_18task_queue import discover_task_datasets, launch_environment
from robocasa_episode_resume.model_identity import (
    build_model_identity,
    reuse_verification_record,
    verify_model_observation,
)
from robocasa_vendor import collect_runtime, dataset_provenance, sha256_file

from robocasa_eval_v2.config import execution

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "cosmos-framework"
SOURCE_PATHS = ["scripts", "configs", "third_party", "cosmos-framework"]


# robocasa1.0.1 /6f90063c TARGET_TASKS["atomic_seen"], read without importing a simulator.
ATOMIC_TASKS = (
    "CloseBlenderLid",
    "CloseFridge",
    "CloseToasterOvenDoor",
    "CoffeeSetupMug",
    "NavigateKitchen",
    "OpenCabinet",
    "OpenDrawer",
    "OpenStandMixerHead",
    "PickPlaceCounterToCabinet",
    "PickPlaceCounterToStove",
    "PickPlaceDrawerToCounter",
    "PickPlaceSinkToCounter",
    "PickPlaceToasterToCounter",
    "SlideDishwasherRack",
    "TurnOffStove",
    "TurnOnElectricKettle",
    "TurnOnMicrowave",
    "TurnOnSinkFaucet",
)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def verify_source(frozen=None):
    actual = git(ROOT, "rev-parse", "HEAD")
    child = git(CHILD, "rev-parse", "HEAD")
    root = frozen or actual
    if (
        git(ROOT, "ls-files", "--others", "--exclude-standard", "--", *SOURCE_PATHS)
        or git(ROOT, "diff", "--name-only", root, "HEAD", "--", *SOURCE_PATHS)
        or git(ROOT, "diff", "--name-only", "HEAD", "--", *SOURCE_PATHS)
        or git(CHILD, "status", "--porcelain")
        or git(ROOT, "rev-parse", f"{root}:cosmos-framework") != child
    ):
        raise ValueError("unreviewed/dirty production source or Child identity drift")
    return root, child, actual


def discover(cfg):
    mapping = dict(discover_task_datasets(Path(cfg["dataset_root"]), None))
    order = sorted(mapping) if cfg["tasks"] == "all" else list(cfg["tasks"])
    if any(t not in ATOMIC_TASKS for t in order):
        raise ValueError(
            "only RoboCasa365 Target Atomic-Seen tasks are supported by this protocol"
        )
    if any(t not in mapping for t in order):
        raise ValueError("unknown Task class")
    if cfg["tasks"] == "all" and set(order) != set(ATOMIC_TASKS):
        raise ValueError("all requires18 atomic Tasks")
    return [(t, mapping[t]) for t in order]


def interpreter_libraries(executable, environment, names):
    code = "import importlib.metadata as m,json,sys;print('PSM_LIBRARIES '+json.dumps({n:m.version(n) for n in sys.argv[1:]}))"
    completed = subprocess.run(
        [str(executable), "-B", "-c", code, *names],
        env=dict(environment, CUDA_VISIBLE_DEVICES="", MUJOCO_GL="disable"),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    import json

    values = [
        json.loads(line[len("PSM_LIBRARIES ") :])
        for line in completed.stdout.splitlines()
        if line.startswith("PSM_LIBRARIES ")
    ]
    if len(values) != 1 or set(values[0]) != set(names):
        raise ValueError("interpreter library attestation missing")
    return values[0]


def runtime_environment(cache):
    """Keep vendor/model import caches outside source and training directories."""
    cache = Path(cache)
    environment = launch_environment(cache)
    environment.update(
        NUMBA_CACHE_DIR=str(cache / "numba"),
        MPLCONFIGDIR=str(cache / "matplotlib"),
        XDG_CACHE_HOME=str(cache / "xdg"),
        HF_HOME=str(cache / "huggingface"),
    )
    return environment


def prepare(cfg, *, cache, anchor=None, manifest=None):
    tasks = discover(cfg)
    frozen = manifest["experiment"]["root_sha"] if manifest else None
    root, child, actual = verify_source(frozen)
    if sha256_file(Path(cfg["vendor_lock"])) != sha256_file(
        ROOT / "third_party/robosuite_patches/vendor.lock.json"
    ):
        raise ValueError("vendor lock differs from reviewed production source")
    requested = {
        "checkpoint": Path(cfg["checkpoint"]),
        "num_steps": cfg["prediction_steps"],
        "action_horizon": 16,
        "guidance": cfg["guidance"],
    }
    cached = Path(cfg["output_dir"]) / "_internal/verification_cache.json"
    model = None
    if anchor and cached.exists():
        try:
            model = reuse_verification_record(
                read(cached),
                anchor=anchor["model"],
                anchor_sha256=digest(anchor),
                run_root=cfg["output_dir"],
                requested=requested,
            )
        except (ValueError, OSError):
            pass
    if model is None:
        model = build_model_identity(**requested)
    if anchor and model["digest"] != anchor["model"]["digest"]:
        raise ValueError("Checkpoint/model sampling identity changed")
    environment = runtime_environment(cache)
    attestation = collect_runtime(
        sim_python=Path(cfg["sim_python"]),
        lock_path=Path(cfg["vendor_lock"]),
        asset_manifest=cfg.get("asset_manifest"),
        tasks=[t for t, _ in tasks],
        simulation_env=environment,
    )
    runtime = attestation["evaluation_runtime"]
    sim_libraries = interpreter_libraries(
        cfg["sim_python"], environment, ["numpy", "scipy", "Pillow", "requests"]
    )
    server_libraries = interpreter_libraries(
        cfg["server_python"], environment, ["torch", "numpy", "Pillow"]
    )
    runtime_identity = digest(
        {
            "vendor": runtime["digest"],
            "simulation_libraries": sim_libraries,
            "server_libraries": server_libraries,
            "server_python_binary": sha256_file(Path(cfg["server_python"]).resolve()),
        }
    )
    metadata = {
        t: sha256_file(directory / "extras/dataset_meta.json") for t, directory in tasks
    }
    result = build_manifest(
        tasks=[t for t, _ in tasks],
        episodes=cfg["episodes_per_task"],
        seed=cfg["seed"],
        horizons=runtime["protocol"]["official_horizons"],
        formal=len(tasks) == 18 and cfg["episodes_per_task"] == 50,
        execution=execution(cfg),
        experiment={
            "model_digest": model["digest"],
            "config_sha256": sha256_file(Path(cfg["config_file"])),
            "runtime_digest": runtime_identity,
            "root_sha": root,
            "child_sha": child,
            "task_metadata": metadata,
        },
    )
    if manifest is not None and result != manifest:
        raise ValueError(
            "immutable scientific protocol/config/Task/source identity changed"
        )
    clock_preflight = {}
    if execution(cfg) is not None:
        clock_preflight = {
            name: clock_environment(cfg[name], environment)
            for name in ("server_python", "sim_python")
        }
        if len({v["domain"] for v in clock_preflight.values()}) != 1:
            raise ValueError("Client/Server clock domains differ")
    inputs = {
        "clock_preflight": clock_preflight,
        "model": model,
        "runtime": runtime,
        "simulation_libraries": sim_libraries,
        "server_libraries": server_libraries,
        "tasks": {t: str(d) for t, d in tasks},
        "dataset_provenance": [
            dataset_provenance(d / "extras/dataset_meta.json") for _, d in tasks
        ],
        "actual_root": actual,
        "formal_root": root,
        "child": child,
        "runtime_probe_evidence": attestation["runtime_probe_evidence"],
    }
    return result, inputs, environment


_INPUT_WITNESSES = {}


def guard(cfg, manifest, inputs, *, source=True):
    if source:
        verify_source(manifest["experiment"]["root_sha"])
    verify_model_observation(inputs["model"])
    checks = [(Path(cfg["config_file"]), manifest["experiment"]["config_sha256"])]
    checks += [
        (
            Path(d) / "extras/dataset_meta.json",
            manifest["experiment"]["task_metadata"][t],
        )
        for t, d in inputs["tasks"].items()
    ]
    for path, expected in checks:

        def stamp():
            value = path.stat()
            return (
                value.st_dev,
                value.st_ino,
                value.st_size,
                value.st_mtime_ns,
                value.st_ctime_ns,
            )

        before = stamp()
        key = str(path), expected
        if _INPUT_WITNESSES.get(key) != before:
            if sha256_file(path) != expected or stamp() != before:
                raise ValueError("configuration/Task input changed during Run")
            _INPUT_WITNESSES[key] = before


def clock_environment(executable, environment):
    """Normal exec, CPU-only deployment condition. No namespace reconfiguration."""
    import json

    code = (
        "import os,json;from cosmos_framework.inference.robocasa_session_transactions import monotonic_clock_domain;"
        "a=os.readlink('/proc/self/ns/time');b=os.readlink('/proc/self/ns/time_for_children');"
        "assert a==b,'active/children time namespace mismatch';"
        "print('PSM_CLOCK '+json.dumps(dict(domain=monotonic_clock_domain(),active=a,children=b,normal_exec=True)))"
    )
    value = subprocess.run(
        [str(executable), "-B", "-c", code],
        cwd=CHILD,
        env=dict(environment, CUDA_VISIBLE_DEVICES="", MUJOCO_GL="disable"),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    rows = [
        json.loads(line[len("PSM_CLOCK ") :])
        for line in value.stdout.splitlines()
        if line.startswith("PSM_CLOCK ")
    ]
    if len(rows) != 1:
        raise ValueError("clock environment attestation missing")
    return rows[0]
