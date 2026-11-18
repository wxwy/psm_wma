"""One immutable plan and the original producer queue, supervised through VAE GC.

This module is inert on import. Real production requires --manual-start and
fixed-code/config/environment preflight. It never deletes old datasets.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from g2.io import digest, read_json
from g2.latent_cache.contract import CacheError, fingerprint
from g2.latent_cache.storage import atomic_json, build_lock

from .work_lifecycle import init_root, real_path

SCHEMA = "g2_one_shot_production_v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECIPE = "3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1"
PATH_FIELDS = (
    "python",
    "nav_repo",
    "nav_setup",
    "native_binary",
    "robocasa_repo",
    "robosuite_repo",
    "raw_root",
    "flat_root",
    "depth_root",
    "mapping",
    "weights",
    "output_root",
    "work_root",
    "spool_root",
    "run_root",
)
DEFAULTS = dict(
    schema=SCHEMA,
    root_sha="",
    child_sha="d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2",
    nav_sha="70eb7b447e65d793b0ebe18b258291ce46f057c1",
    expected_recipe_id=DEFAULT_RECIPE,
    expected_numpy="2.2.5",
    mapping_sha256="",
    final_source_format="working_v1",
    keep_full_audit=False,
    audit_archive_root=None,
    audit_retention_policy=None,
    source_protected_roots=[],
    renderer_pythonpath=[],
    renderer_gpus=[4, 5, 6, 7],
    workers_per_gpu=8,
    vae_gpu=7,
    vae_engine=None,
    allow_shared_gpu_processes=False,
    expected_dataset_episodes=9126,
    expected_selected_episodes=9126,
    expected_task_count=18,
    tasks=[],
    episodes_per_task=None,
    expected_episode_ids=None,
    sample_mode=False,
    profile=dict(
        sixview_png=True,
        island_png=True,
        scene_graph=True,
        spatial_metadata=True,
        task_entities=True,
        selection=True,
        selection_top_variant="clean",
        language=True,
        robot_pose=True,
        marker_variants=True,
        view_vae=True,
    ),
    height=256,
    width=256,
    storage_dtype="float32",
    max_events=32,
    max_spool_bytes=256 * 1024**2,
    max_result_bytes=4 * 1024**3,
    max_records=100000,
    max_active_jobs=32,
    min_work_free_bytes=64 * 1024**3,
    min_spool_free_bytes=8 * 1024**3,
    min_output_free_bytes=8 * 1024**3,
    admission_timeout_s=600,
    drain_timeout_s=1800,
    monitor_interval_s=5,
    ros_port_base=21500,
    max_attempts=2,
)


def load_config(path):
    value = read_json(path)
    if not isinstance(value, dict) or set(value) - set(DEFAULTS) - set(PATH_FIELDS):
        raise CacheError("unknown production config fields")
    cfg = {**DEFAULTS, **value}
    for key in PATH_FIELDS:
        if not isinstance(cfg.get(key), str) or not Path(cfg[key]).is_absolute():
            raise CacheError("explicit absolute production path required: " + key)
        if Path(cfg[key]) != Path(os.path.abspath(cfg[key])):
            raise CacheError("production paths must be canonical (no '..'): " + key)
    if cfg["schema"] != SCHEMA:
        raise CacheError("unknown production schema")
    if (
        cfg["final_source_format"] not in ("working_v1", "capsule_v2")
        or type(cfg["keep_full_audit"]) is not bool
    ):
        raise CacheError("unknown explicit final source format/audit policy")
    if cfg["final_source_format"] == "working_v1" and any(
        cfg[k] not in (None, False)
        for k in ("keep_full_audit", "audit_archive_root", "audit_retention_policy")
    ):
        raise CacheError(
            "working-v1 profile may not implicitly retire or archive source"
        )
    if not isinstance(cfg["source_protected_roots"], list) or any(
        not isinstance(p, str) or not Path(p).is_absolute()
        for p in cfg["source_protected_roots"]
    ):
        raise CacheError(
            "extra source-retention protected roots must be absolute paths"
        )
    if cfg["keep_full_audit"] and not cfg["source_protected_roots"]:
        raise CacheError(
            "external audit requires explicit existing G1/cache/checkpoint protected roots"
        )
    from g2.latent_cache.storage import _hex

    for key in ("root_sha", "child_sha", "nav_sha"):
        v = cfg[key]
        if (
            not isinstance(v, str)
            or len(v) != 40
            or any(c not in "0123456789abcdef" for c in v)
        ):
            raise CacheError("fixed Git SHA required: " + key)
    _hex(cfg["expected_recipe_id"])
    _hex(cfg["mapping_sha256"])
    for key in (
        "expected_dataset_episodes",
        "expected_selected_episodes",
        "expected_task_count",
        "max_events",
        "max_spool_bytes",
        "max_result_bytes",
        "max_records",
        "max_active_jobs",
        "max_attempts",
        "height",
        "width",
    ):
        if type(cfg[key]) is not int or cfg[key] < 1:
            raise CacheError("positive finite production limit required: " + key)
    for key in ("min_work_free_bytes", "min_spool_free_bytes", "min_output_free_bytes"):
        if type(cfg[key]) is not int or cfg[key] < 0:
            raise CacheError("invalid free-space reserve")
    for key in ("admission_timeout_s", "drain_timeout_s", "monitor_interval_s"):
        if (
            type(cfg[key]) not in (int, float)
            or not math.isfinite(cfg[key])
            or cfg[key] <= 0
        ):
            raise CacheError("finite timeout required: " + key)
    if type(cfg["sample_mode"]) is not bool:
        raise CacheError("sample_mode must be explicit boolean")
    if type(cfg["allow_shared_gpu_processes"]) is not bool:
        raise CacheError("shared GPU authorization must be explicit boolean")
    if cfg["vae_engine"] is not None:
        from g2.latent_cache.batch_engine import engine_config

        cfg["vae_engine"] = engine_config(
            cfg["vae_engine"], allow_test=cfg["sample_mode"]
        )
        if not set(cfg["vae_engine"]["gpus"]) <= {4, 5, 6, 7}:
            raise CacheError("batch engine must stay within approved GPUs4-7")
        if cfg["max_events"] < cfg["vae_engine"]["max_batch_size_per_gpu"]:
            raise CacheError("queue must admit at least one full per-GPU batch")
    if not cfg["sample_mode"] and (
        cfg["tasks"]
        or cfg["episodes_per_task"] is not None
        or cfg["expected_selected_episodes"] != 9126
        or cfg["expected_dataset_episodes"] != 9126
        or cfg["expected_task_count"] != 18
    ):
        raise CacheError("full mode is exactly9126/all18, no manual episode batching")
    if not cfg["sample_mode"] and (
        cfg["renderer_gpus"] != [4, 5, 6, 7] or cfg["workers_per_gpu"] != 8
    ):
        raise CacheError("full production preserves original GPUs4-7 x8 renderer slots")
    if cfg["max_attempts"] > 5:
        raise CacheError("at most5 bounded producer attempts")
    from .atomic_6views_run import _ports

    _ports(cfg["renderer_gpus"], cfg["workers_per_gpu"], cfg["ros_port_base"])
    if not set(cfg["renderer_gpus"]) <= set((4, 5, 6, 7)) or cfg["vae_gpu"] not in (
        4,
        5,
        6,
        7,
    ):
        raise CacheError("production GPU allocation must stay within approved4-7")
    if cfg["max_active_jobs"] > len(cfg["renderer_gpus"]) * cfg["workers_per_gpu"]:
        raise CacheError("active-work cap exceeds renderer slots")
    from .output_profile import OutputProfile

    profile = OutputProfile.from_dict(cfg["profile"])
    if any(
        not getattr(profile, key)
        for key, enabled in DEFAULTS["profile"].items()
        if enabled is True
    ):
        raise CacheError(
            "production requires the full spatial/language/PNG/VAE profile"
        )
    cfg["profile"] = profile.to_dict()
    from g2.latent_cache.encoding import validate_wan_canvas

    validate_wan_canvas(cfg["height"], cfg["width"])
    if cfg["height"] != 256 or cfg["width"] != 256 or cfg["storage_dtype"] != "float32":
        raise CacheError(
            "this P0 launcher preserves approved B1/256/FP32 configuration"
        )
    for p in cfg["renderer_pythonpath"]:
        if not isinstance(p, str) or not Path(p).is_absolute():
            raise CacheError("renderer overlay paths must be absolute")
    cfg["config_id"] = fingerprint(cfg)
    return cfg


def isolated_env(cfg, *, renderer=False):
    env = os.environ.copy()
    env.pop("PYTHONHOME", None)
    paths = [str(ROOT), str(ROOT / "cosmos-framework")]
    if renderer:
        paths += cfg["renderer_pythonpath"]
    env.update(
        PYTHONPATH=os.pathsep.join(paths),
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
        COSMOS_TRAINING="0",
        COSMOS_INTERNAL="0",
        COSMOS_DEVICE="cuda",
    )
    return env


def git_pin(repo, expected):
    actual = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != expected or subprocess.check_output(
        ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"],
        text=True,
    ):
        raise CacheError("fixed clean checkout required: " + str(repo))
    return actual


def validate_paths(cfg):
    roots = {
        key: real_path(cfg[key])
        for key in ("output_root", "work_root", "spool_root", "run_root")
    }
    protected = [
        Path(cfg[k]).resolve()
        for k in (
            "raw_root",
            "flat_root",
            "depth_root",
            "weights",
            "nav_repo",
            "robocasa_repo",
            "robosuite_repo",
        )
    ] + [ROOT]
    for key, p in roots.items():
        for other, q in roots.items():
            if key != other and (p == q or p in q.parents or q in p.parents):
                raise CacheError("production namespaces overlap: " + key + "/" + other)
        for q in protected:
            if p == q or p in q.parents or q in p.parents:
                raise CacheError(
                    "production namespace overlaps protected data/code: " + key
                )
    for key in ("python", "nav_setup", "native_binary", "mapping", "weights"):
        if not Path(cfg[key]).is_file():
            raise CacheError("required runtime file missing: " + key)
    if not os.access(cfg["python"], os.X_OK) or not os.access(
        cfg["native_binary"], os.X_OK
    ):
        raise CacheError("Python/native runtime must already be executable")
    for key in (
        "raw_root",
        "flat_root",
        "depth_root",
        "nav_repo",
        "robocasa_repo",
        "robosuite_repo",
    ):
        if not Path(cfg[key]).is_dir():
            raise CacheError("required input/runtime directory missing: " + key)
    if digest(cfg["mapping"]) != cfg["mapping_sha256"]:
        raise CacheError("immutable mapping checksum differs")
    nav = Path(cfg["nav_repo"]).resolve()
    for key in ("nav_setup", "native_binary"):
        if nav not in Path(cfg[key]).resolve().parents:
            raise CacheError(
                "native runtime must belong to the pinned nav checkout: " + key
            )
    for p in cfg["renderer_pythonpath"]:
        if (
            not Path(p).is_dir()
            or (Path(p) / "g2").exists()
            or (Path(p) / "cosmos_framework").exists()
        ):
            raise CacheError(
                "renderer overlay must contain dependencies, not another Root/Child"
            )
    return roots


def environment_probe(cfg):
    """Descriptor only; no VAE construction, CUDA initialization or download."""
    import importlib.metadata as md

    import numpy as np

    from g2.latent_cache.contract import make_recipe, preprocessing_recipe
    from g2.latent_cache.encoding import WanSingleFrameEncoder

    encoder = WanSingleFrameEncoder(
        cfg["weights"], device="cuda:0", cosmos_root=ROOT / "cosmos-framework"
    )
    if cfg["vae_engine"] is None:
        recipe = make_recipe(
            encoder.descriptor(),
            preprocessing_recipe(cfg["height"], cfg["width"]),
            storage_dtype=cfg["storage_dtype"],
        )
    else:
        from g2.latent_cache.batch_contract import make_batch_recipe
        from g2.latent_cache.batch_encoding import WanBatchEncoder

        encoder = WanBatchEncoder(
            cfg["weights"],
            device="cuda:0",
            cosmos_root=ROOT / "cosmos-framework",
            max_batch_size=cfg["vae_engine"]["max_batch_size_per_gpu"],
        )
        recipe = make_batch_recipe(
            encoder.descriptor(),
            max_batch_size=cfg["vae_engine"]["max_batch_size_per_gpu"],
        )
    if (
        np.__version__ != cfg["expected_numpy"]
        or recipe["recipe_id"] != cfg["expected_recipe_id"]
    ):
        raise CacheError(
            "VAE original-environment NumPy/recipe mismatch; renderer overlay is forbidden here"
        )
    return dict(
        recipe_id=recipe["recipe_id"],
        numpy=np.__version__,
        numpy_origin=np.__file__,
        python=sys.executable,
        torch=md.version("torch"),
        model_loaded=False,
        recipe=recipe,
    )


def gpu_preflight(cfg):
    from .process_control import owned_groups

    if not shutil.which("nvidia-smi"):
        raise CacheError("nvidia-smi required for production resource preflight")
    rows = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader,nounits"],
        text=True,
        timeout=15,
    )
    available = {
        int(line.split(",")[0]): line.split(",")[1].strip()
        for line in rows.splitlines()
        if line.strip()
    }
    selected = set(cfg["renderer_gpus"]) | set(
        cfg["vae_engine"]["gpus"] if cfg["vae_engine"] else [cfg["vae_gpu"]]
    )
    if not selected <= set(available):
        raise CacheError("configured physical GPUs are not present")
    apps = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-compute-apps=gpu_uuid,pid",
            "--format=csv,noheader,nounits",
        ],
        text=True,
        timeout=15,
    )
    own = {pid for group in owned_groups(cfg["config_id"]).values() for pid in group}
    foreign = []
    for line in apps.splitlines():
        fields = [s.strip() for s in line.split(",")]
        if (
            len(fields) == 2
            and fields[0] in {available[g] for g in selected}
            and fields[1].isdigit()
            and int(fields[1]) not in own
        ):
            foreign.append(int(fields[1]))
    if foreign and not cfg["allow_shared_gpu_processes"]:
        raise CacheError(
            "selected GPUs have unowned processes; stop them manually before launch: "
            + str(sorted(set(foreign)))
        )
    return dict(
        selected=sorted(selected),
        foreign_processes=sorted(set(foreign)),
        sharing_explicitly_authorized=cfg["allow_shared_gpu_processes"],
    )


def claim_output(cfg):
    output = real_path(cfg["output_root"])
    output.mkdir(parents=True, exist_ok=True)
    marker = output / ".g2_stage_a_dataset_root.json"
    binding = dict(
        schema="g2_owned_production_output_v1",
        config_id=cfg["config_id"],
        output=str(output),
    )
    with build_lock(output.parent / (".g2-output-lock-" + output.name)):
        if marker.exists():
            if read_json(marker) != binding:
                raise CacheError("output belongs to a different run")
        else:
            if any(output.iterdir()):
                raise CacheError("refuse to overwrite or claim old/unowned dataset")
            atomic_json(marker, binding)


def preflight(cfg):
    roots = validate_paths(cfg)
    from g2.latent_cache.retirement_policy import from_config, validate_policy

    validate_policy(from_config(cfg), cfg["spool_root"])
    if Path(sys.executable).absolute() != Path(cfg["python"]).absolute():
        raise CacheError("controller must use the configured original interpreter")
    git_pin(ROOT, cfg["root_sha"])
    git_pin(ROOT / "cosmos-framework", cfg["child_sha"])
    git_pin(cfg["nav_repo"], cfg["nav_sha"])
    link = subprocess.check_output(
        ["git", "ls-tree", cfg["root_sha"], "cosmos-framework"], cwd=ROOT, text=True
    ).split()[2]
    if link != cfg["child_sha"]:
        raise CacheError("Root Gitlink differs")
    result = subprocess.run(
        [
            cfg["python"],
            "-m",
            "tools.g2.run_stage_a_production",
            "environment",
            "--config",
            cfg["_config_path"],
        ],
        cwd=ROOT,
        env=isolated_env(cfg),
        capture_output=True,
        text=True,
        check=True,
    )
    environment = json.loads(result.stdout)
    # Existing binaries only; production never compiles or installs source.
    native = Path(cfg["native_binary"])
    binaries = (
        ROOT / "g2/bin/libfast_surface_cells.so",
        native.parent / "gt_oracle_native",
        native,
    )
    for p in binaries:
        if not p.is_file():
            raise CacheError("prebuilt native component missing: " + str(p))
    free = {
        k: shutil.disk_usage(
            p if p.exists() else next(a for a in p.parents if a.exists())
        ).free
        for k, p in roots.items()
    }
    return dict(
        schema="g2_full_production_preflight_v1",
        config_id=cfg["config_id"],
        roots={k: str(v) for k, v in roots.items()},
        environment=environment,
        runtime_sha256={str(p): digest(p) for p in (*binaries, Path(cfg["nav_setup"]))},
        resources=gpu_preflight(cfg),
        free_bytes=free,
        production_started=False,
        training_ready=False,
    )


def consumer_command(cfg, action, stop_file):
    if cfg["vae_engine"] is not None:
        cmd = [
            cfg["python"],
            "-m",
            "tools.g2.run_spatial_vae_engine",
            action,
            "--mode",
            "sync",
            "--spool-root",
            cfg["spool_root"],
            "--weights",
            cfg["weights"],
            "--cosmos-root",
            str(ROOT / "cosmos-framework"),
            "--engine-config",
            str(Path(cfg["run_root"]) / "vae_engine.json"),
            "--expected-recipe-id",
            cfg["expected_recipe_id"],
        ]
        for flag, key in (
            ("--max-events", "max_events"),
            ("--max-spool-bytes", "max_spool_bytes"),
            ("--max-result-bytes", "max_result_bytes"),
            ("--max-records", "max_records"),
        ):
            cmd += [flag, str(cfg[key])]
        if action == "--execute":
            cmd += ["--serve", "--resume", "--stop-file", str(stop_file)]
        if cfg["sample_mode"]:
            cmd += ["--isolated-test"]
        if cfg["final_source_format"] == "capsule_v2":
            cmd += [
                "--source-policy",
                str(Path(cfg["run_root"]) / "source_policy.json"),
            ]
        return cmd
    cmd = [
        cfg["python"],
        "-m",
        "tools.g2.consume_spatial_view_vae_events",
        action,
        "--spool-root",
        cfg["spool_root"],
        "--weights",
        cfg["weights"],
        "--cosmos-root",
        str(ROOT / "cosmos-framework"),
        "--device",
        "cuda:0",
        "--height",
        str(cfg["height"]),
        "--width",
        str(cfg["width"]),
        "--storage-dtype",
        cfg["storage_dtype"],
        "--expected-recipe-id",
        cfg["expected_recipe_id"],
        "--max-events",
        str(cfg["max_events"]),
        "--max-spool-bytes",
        str(cfg["max_spool_bytes"]),
        "--max-result-bytes",
        str(cfg["max_result_bytes"]),
        "--max-records",
        str(cfg["max_records"]),
    ]
    if action == "--execute":
        cmd += ["--serve", "--stop-file", str(stop_file)]
    if cfg["final_source_format"] == "capsule_v2":
        cmd += ["--source-policy", str(Path(cfg["run_root"]) / "source_policy.json")]
    return cmd


def producer_args(cfg, action="run"):
    from .atomic_6views_run import parser

    run = Path(cfg["run_root"])
    argv = [
        action,
        "--raw-root",
        cfg["raw_root"],
        "--flat-root",
        cfg["flat_root"],
        "--depth-root",
        cfg["depth_root"],
        "--mapping",
        cfg["mapping"],
        "--output-root",
        cfg["output_root"],
        "--work-root",
        cfg["work_root"],
        "--plan-root",
        str(run / "plan"),
        "--output-profile",
        str(run / "profile.json"),
        "--expected",
        str(cfg["expected_dataset_episodes"]),
        "--batch-size",
        "100",
        "--resume",
        "--require-depth",
        "--gpus",
        ",".join(map(str, cfg["renderer_gpus"])),
        "--workers-per-gpu",
        str(cfg["workers_per_gpu"]),
        "--ros-port-base",
        str(cfg["ros_port_base"]),
        "--nav-repo",
        cfg["nav_repo"],
        "--nav-setup",
        cfg["nav_setup"],
        "--native-binary",
        cfg["native_binary"],
        "--robocasa-repo",
        cfg["robocasa_repo"],
        "--robosuite-repo",
        cfg["robosuite_repo"],
        "--sim-direct-geometry-only",
        "--sim-color-only",
        "--sim-direct-material",
        "--scene-event-index",
        "--sg-event-index",
        "--lazy-texel-decode",
        "--managed-work-cleanup",
        "--require-prebuilt",
        "--max-attempts",
        str(cfg["max_attempts"]),
        "--vae-spool",
        cfg["spool_root"],
    ]
    for path in cfg["renderer_pythonpath"]:
        argv += ["--renderer-pythonpath", path]
    for task in cfg["tasks"]:
        argv += ["--task", task]
    if cfg["episodes_per_task"] is not None:
        argv += ["--episodes-per-task", str(cfg["episodes_per_task"])]
    if action == "run":
        argv += ["--manual-start", "--allow-experimental"]
    args = parser().parse_args(argv)
    args.gpus = list(cfg["renderer_gpus"])
    return args


def prepare_plan(cfg):
    from .atomic_6views_run import _load_selection, schedule

    args = producer_args(cfg, "plan")
    schedule(args)
    index = read_json(Path(cfg["run_root"]) / "plan/index.json")
    if (
        index["episodes_total"] != cfg["expected_selected_episodes"]
        or len(index["tasks_selected"]) != cfg["expected_task_count"]
    ):
        raise CacheError(
            "immutable selection count/tasks differ from configured production"
        )
    if not cfg["sample_mode"]:
        from .task_entities import FIXTURE_RULES, OBJECT_RULES

        if set(index["tasks_selected"]) != set(FIXTURE_RULES) | set(OBJECT_RULES):
            raise CacheError("full plan does not cover the18 supported Atomic tasks")
    expected = math.ceil(index["episodes_pending"] / 100)
    if index["batches_total"] != expected and not index["resume"]:
        raise CacheError("immutable plan package count differs")
    rows = _load_selection(Path(cfg["run_root"]) / "plan")
    if len(rows) != cfg["expected_selected_episodes"]:
        raise CacheError("pinned plan does not contain every selected episode")
    if cfg["expected_episode_ids"] is not None and sorted(
        r["episode_id"] for r in rows
    ) != sorted(cfg["expected_episode_ids"]):
        raise CacheError("sample global episode identities differ")
    return producer_args(cfg, "run"), rows, index


class Supervisor:
    def __init__(self, cfg, spool, rows):
        self.cfg, self.spool, self.rows = cfg, spool, rows
        self.run = Path(cfg["run_root"])
        self.stop_file = self.run / "STOP_REQUESTED.json"
        self.failed = threading.Event()
        self.condition = threading.Condition()
        self.reserved = set()
        self.started = time.monotonic()
        self.peak_work = 0
        self.peak_pending = 0
        self.run_id = cfg["config_id"]
        self.consumer = None
        self.failed_ids = []

    def stopping(self):
        return self.stop_file.exists() or self.failed.is_set()

    def admit(self, row):
        deadline = time.monotonic() + self.cfg["admission_timeout_s"]
        while not self.stopping():
            with self.condition:
                with self.spool._db() as db:
                    active = {
                        json.loads(r[0])["episode_key"]
                        for r in db.execute("SELECT scope FROM jobs")
                    }
                key = f"{row['task_class']}/episode_{row['episode_id']:06d}"
                occupied = active | self.reserved
                enough = (
                    shutil.disk_usage(self.cfg["work_root"]).free
                    >= self.cfg["min_work_free_bytes"]
                    and shutil.disk_usage(self.cfg["spool_root"]).free
                    >= self.cfg["min_spool_free_bytes"]
                    and shutil.disk_usage(self.cfg["output_root"]).free
                    >= self.cfg["min_output_free_bytes"]
                )
                # An interrupted existing job may finish/reclaim its work; new
                # jobs wait behind the same finite resource admission gate.
                if key in active or (
                    len(occupied) < self.cfg["max_active_jobs"] and enough
                ):
                    self.reserved.add(key)
                    return True
                if time.monotonic() >= deadline:
                    self.failed.set()
                    raise CacheError(
                        "disk/active-work backpressure timed out; retained work was not deleted"
                    )
                if self.consumer is not None and self.consumer.poll() is not None:
                    self.failed.set()
                    raise CacheError(
                        "VAE consumer exited before full production completion"
                    )
                self.condition.wait(0.2)
        return False

    def result(self, row, status):
        key = f"{row['task_class']}/episode_{row['episode_id']:06d}"
        with self.condition:
            self.reserved.discard(key)
            if status == "FAILED":
                self.failed_ids.append(row["episode_id"])
                self.failed.set()
            self.condition.notify_all()

    def worker(self, command, check=False):
        from .process_control import start_owned, terminate_owned

        child = start_owned(
            command,
            env=isolated_env(self.cfg, renderer=True),
            run_id=self.run_id,
            cwd=ROOT,
        )
        while child.poll() is None:
            if self.stopping():
                terminate_owned(self.run_id)
                break
            if self.consumer is not None and self.consumer.poll() is not None:
                self.failed.set()
                terminate_owned(self.run_id)
                break
            time.sleep(0.1)
        return subprocess.CompletedProcess(command, child.wait())

    def progress(self, phase):
        def size(root):
            total = 0
            for directory, dirs, files in os.walk(root, followlinks=False):
                dirs[:] = [d for d in dirs if not (Path(directory) / d).is_symlink()]
                for name in files:
                    p = Path(directory) / name
                    try:
                        if not p.is_symlink():
                            total += p.stat().st_size
                    except FileNotFoundError:
                        pass
            return total

        stats = self.spool.stats()
        work = size(self.cfg["work_root"])
        pending = stats["pending_bytes"]
        self.peak_work = max(self.peak_work, work)
        self.peak_pending = max(self.peak_pending, pending)
        elapsed = max(0.001, time.monotonic() - self.started)
        gpu = []
        if shutil.which("nvidia-smi"):
            p = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,memory.used,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            gpu = [
                x
                for x in p.stdout.splitlines()
                if x.split(",")[0].strip() in set(map(str, self.cfg["renderer_gpus"]))
            ]
        record = dict(
            schema="g2_full_production_progress_v1",
            phase=phase,
            elapsed_s=elapsed,
            spool=stats,
            native_work_bytes=work,
            spool_disk_bytes=size(self.cfg["spool_root"]),
            peak_native_work_bytes=self.peak_work,
            peak_pending_png_bytes=self.peak_pending,
            completed_per_hour=stats["completed_jobs"] / elapsed * 3600,
            loadavg=list(os.getloadavg()),
            controller_cpu_times=list(os.times()),
            gpu_rows=gpu,
            free_work_bytes=shutil.disk_usage(self.cfg["work_root"]).free,
            free_spool_bytes=shutil.disk_usage(self.cfg["spool_root"]).free,
            free_output_bytes=shutil.disk_usage(self.cfg["output_root"]).free,
            failed_ids=self.failed_ids,
            training_ready=False,
        )
        with (self.run / "progress.jsonl").open("a") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        atomic_json(self.run / "progress.json", record, replace=True)
        return record

    def execute(self, args):
        from .atomic_6views_run import _completed, _output_profile, schedule
        from .process_control import start_owned, terminate_owned

        env = isolated_env(self.cfg)
        env["CUDA_VISIBLE_DEVICES"] = (
            ",".join(map(str, self.cfg["vae_engine"]["gpus"]))
            if self.cfg["vae_engine"]
            else str(self.cfg["vae_gpu"])
        )
        consumer_stop = self.run / "CONSUMER_STOP.json"
        consumer_stop.unlink(missing_ok=True)

        def request_stop(signum, frame):
            atomic_json(
                self.stop_file, dict(config_id=self.run_id, signal=signum), replace=True
            )

        old_handlers = {}
        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGINT, signal.SIGTERM):
                old_handlers[sig] = signal.signal(sig, request_stop)
        with (self.run / "vae_consumer.log").open("a") as log:
            self.consumer = start_owned(
                consumer_command(self.cfg, "--execute", consumer_stop),
                env=env,
                run_id=self.run_id,
                cwd=ROOT,
                stdout=log,
            )
            finished = threading.Event()

            def monitor():
                while not finished.wait(self.cfg["monitor_interval_s"]):
                    try:
                        self.progress("RUNNING")
                    except Exception as exc:
                        self.failed.set()
                        atomic_json(
                            self.run / "MONITOR_FAILED.json",
                            dict(error=str(exc)),
                            replace=True,
                        )

            thread = threading.Thread(target=monitor)
            thread.start()
            try:
                rc = schedule(
                    args,
                    admission=self.admit,
                    on_result=self.result,
                    run_worker=self.worker,
                )
                deadline = time.monotonic() + self.cfg["drain_timeout_s"]
                while not self.stopping() and self.spool.stats()["active_jobs"]:
                    if self.consumer.poll() is not None:
                        raise CacheError("consumer exited during final drain")
                    if time.monotonic() >= deadline:
                        raise CacheError("final VAE/work cleanup drain timed out")
                    time.sleep(0.2)
                complete = False
                if not self.stopping() and rc in (0, 75):
                    profile = _output_profile(args)
                    complete = all(_completed(args, r, profile) for r in self.rows)
                    if not complete:
                        raise CacheError(
                            "queue drained without all strict episode COMPLETE"
                        )
                    if (
                        self.spool.stats()["active_jobs"]
                        or self.spool.stats()["failed_jobs"]
                    ):
                        raise CacheError("active or failed jobs remain")
                result = self.progress(
                    "DONE"
                    if complete
                    else "STOPPED"
                    if self.stop_file.exists()
                    else "FAILED"
                )
                result.update(
                    complete=complete,
                    sample_mode=self.cfg["sample_mode"],
                    selected=len(self.rows),
                    config_id=self.cfg["config_id"],
                    training_ready=False,
                )
                atomic_json(self.run / "result.json", result, replace=True)
                return 0 if complete else 75 if self.stop_file.exists() else 2
            except Exception as exc:
                self.failed.set()
                atomic_json(
                    self.run / "result.json",
                    dict(
                        schema="g2_full_production_result_v1",
                        phase="FAILED",
                        complete=False,
                        error=str(exc),
                        config_id=self.run_id,
                        training_ready=False,
                    ),
                    replace=True,
                )
                raise
            finally:
                finished.set()
                thread.join(15)
                atomic_json(
                    consumer_stop,
                    dict(config_id=self.cfg["config_id"], stop=True),
                    replace=True,
                )
                try:
                    self.consumer.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    terminate_owned(self.run_id)
                terminate_owned(self.run_id)
                for sig, old in old_handlers.items():
                    signal.signal(sig, old)


def run(cfg, *, resume=False):
    from g2.latent_cache.streaming import EventSpool

    from .process_control import terminate_owned

    roots = validate_paths(cfg)
    run_root = roots["run_root"]
    run_root.mkdir(parents=True, exist_ok=True)
    with build_lock(run_root / "controller"):
        marker = run_root / "run_manifest.json"
        stable = {k: v for k, v in cfg.items() if k != "_config_path"}
        if marker.exists():
            if not resume or read_json(marker) != stable:
                raise CacheError("existing run requires exact-config resume")
            terminate_owned(cfg["config_id"])
        elif any(p.name != "controller" for p in run_root.iterdir()):
            raise CacheError("refuse nonempty unowned production run root")
        else:
            atomic_json(marker, stable)
        pre = preflight(cfg)
        atomic_json(run_root / "preflight.json", pre, replace=True)
        profile = run_root / "profile.json"
        if profile.exists() and read_json(profile) != cfg["profile"]:
            raise CacheError("profile changed on resume")
        if not profile.exists():
            atomic_json(profile, cfg["profile"])
        claim_output(cfg)
        from g2.latent_cache.retirement_policy import from_config

        policy = from_config(cfg)
        if policy is not None:
            path = run_root / "source_policy.json"
            if path.exists() and read_json(path) != policy:
                raise CacheError("source policy changed on resume")
            if not path.exists():
                atomic_json(path, policy)
        env = isolated_env(cfg)
        if cfg["vae_engine"] is not None:
            path = run_root / "vae_engine.json"
            if path.exists() and read_json(path) != cfg["vae_engine"]:
                raise CacheError("batch engine configuration changed on resume")
            if not path.exists():
                atomic_json(path, cfg["vae_engine"])
        env["CUDA_VISIBLE_DEVICES"] = (
            ",".join(map(str, cfg["vae_engine"]["gpus"]))
            if cfg["vae_engine"]
            else str(cfg["vae_gpu"])
        )
        subprocess.run(
            consumer_command(cfg, "--initialize", run_root / "CONSUMER_STOP.json"),
            cwd=ROOT,
            env=env,
            check=True,
        )
        spool = EventSpool.open(cfg["spool_root"])
        if resume:
            with spool._db() as db:
                failed = [
                    r[0]
                    for r in db.execute("SELECT id FROM jobs WHERE error IS NOT NULL")
                ]
            for job in failed:
                spool.retry(job)
            if spool.source_policy is not None:
                from g2.latent_cache.source_retirement import resume_pending

                with spool._db() as db:
                    retiring = [
                        r[0]
                        for r in db.execute(
                            "SELECT id FROM jobs WHERE retirement IS NOT NULL AND done=2"
                        )
                    ]
                # Repair source transactions before the original planner checks
                # partially swapped episode markers. No renderer is running.
                for job in retiring:
                    if not resume_pending(spool, job):
                        raise CacheError(
                            "source retirement still has an active reader/writer"
                        )
            atomic_json(
                run_root / "resume_receipt.json",
                dict(retried_jobs=failed, config_id=cfg["config_id"]),
                replace=True,
            )
        args, rows, index = prepare_plan(cfg)
        if not resume and index["batches_total"] != math.ceil(
            cfg["expected_selected_episodes"] / 100
        ):
            raise CacheError(
                "fresh full run must include every selected episode in one immutable plan"
            )
        init_root(
            cfg["work_root"],
            cfg["spool_root"],
            cfg["output_root"],
            protected=(
                cfg["raw_root"],
                cfg["flat_root"],
                cfg["depth_root"],
                ROOT,
                cfg["nav_repo"],
            ),
        )
        (run_root / "STOP_REQUESTED.json").unlink(missing_ok=True)
        return Supervisor(cfg, spool, rows).execute(args)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "action",
        choices=("preflight", "run", "resume", "progress", "stop", "environment"),
    )
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--manual-start", action="store_true")
    args = p.parse_args(argv)
    try:
        cfg = load_config(args.config)
        cfg["_config_path"] = str(args.config.absolute())
        run_root = Path(cfg["run_root"])
        if args.action == "environment":
            result = environment_probe(cfg)
        elif args.action == "preflight":
            result = preflight(cfg)
        elif args.action == "progress":
            result = read_json(run_root / "progress.json")
        elif args.action == "stop":
            manifest = read_json(run_root / "run_manifest.json")
            if manifest["config_id"] != cfg["config_id"]:
                raise CacheError("stop config differs from running owner")
            atomic_json(
                run_root / "STOP_REQUESTED.json",
                dict(config_id=cfg["config_id"], requested=True),
                replace=True,
            )
            result = dict(
                stop_requested=True, config_id=cfg["config_id"], data_deleted=False
            )
        else:
            if not args.manual_start:
                p.error("only Owner may run/resume with --manual-start")
            return run(cfg, resume=args.action == "resume")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps(dict(status="ERROR", error=str(exc))), file=sys.stderr)
        return 2
