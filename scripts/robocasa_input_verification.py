"""Invocation-local Config/Task guards after the real strong bundle validation.

No persistent metadata trust and no vendor/runtime probe substitution. The caller
snapshots before its normal SHA reads, then binds those hashes only if all input
witnesses remain stable. Subsequent batches stat-check instead of rereading bytes.
"""

from __future__ import annotations

import copy
import os
import stat
import threading
from pathlib import Path


def input_observation(path):
    path = Path(os.path.abspath(path))
    canonical = path.resolve(strict=True)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"ordinary config/task metadata file required: {path}")
    return (str(canonical), info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def snapshot_inputs(config_file, tasks):
    paths = [Path(config_file), *(Path(directory) / "extras/dataset_meta.json" for _, directory in tasks)]
    return {str(path.absolute()): input_observation(path) for path in paths}


class InvocationInputGuard:
    def __init__(self, config_file, manifest, before):
        identity = manifest["identity"]
        self.config_file = Path(config_file).absolute()
        self.expected = {str(self.config_file): identity["config_sha256"]}
        self.expected.update(
            {
                str((Path(row["dataset_dir"]) / "extras/dataset_meta.json").absolute()): row["env_metadata_sha256"]
                for row in identity["tasks"]
            }
        )
        if set(before) != set(self.expected):
            raise ValueError("config/task observation inventory differs from verified manifest")
        self.before, self.identity = dict(before), copy.deepcopy(identity)
        self._lock = threading.Lock()
        self.checks = 0
        self.verify(manifest, "initial_verified_bundle")

    def verify(self, manifest, phase):
        # Keep job/source hashes tied to the originally fully verified bundle.
        expected = manifest["identity"]
        if expected["config_sha256"] != self.identity["config_sha256"] or expected["tasks"] != self.identity["tasks"]:
            raise ValueError(f"config/task manifest changed during {phase}")
        for path, prior in self.before.items():
            try:
                unchanged = input_observation(path) == prior
            except OSError as error:
                raise ValueError(f"input file changed during {phase}: {path}") from error
            if not unchanged:
                kind = "action server config file" if path == str(self.config_file) else "task metadata"
                raise ValueError(f"{kind} changed during {phase}: {path}")
        with self._lock:
            self.checks += 1
        return {
            "status": "UNCHANGED_INVOCATION_INPUTS",
            "files_checked": len(self.before),
            "bytes_read": 0,
            "scope": "stat_guard_of_this_invocations_verified_config_and_task_SHA",
        }
