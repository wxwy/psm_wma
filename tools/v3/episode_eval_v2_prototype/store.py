"""Design-only flat Episode store and bounded, recoverable Task-stream restart.

No legacy ingestion, inference, ffmpeg, simulator, GPU or subprocess exists here.
A single coordinator holds the run lease; real multi-GPU transport is a later Gate.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import stat
import uuid
from pathlib import Path

from tools.v3.episode_eval_v2_prototype.contract import canonical, digest, validate_manifest, validate_result

MAX_JSON = 256 * 1024


def safe(path):
    path = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f"symlink path forbidden: {path}")
    return path


def sync_dir(path):
    fd = os.open(safe(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def mkdir(path):
    path = safe(path)
    if path.exists():
        if not path.is_dir():
            raise ValueError("directory required")
        return
    mkdir(path.parent)
    path.mkdir()
    sync_dir(path.parent)


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def read(path):
    path = safe(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_JSON:
            raise ValueError("ordinary bounded JSON required")
        raw = stream.read(MAX_JSON + 1)
        after = os.fstat(stream.fileno())

    def witness(s):
        return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns

    if len(raw) > MAX_JSON or witness(before) != witness(after) or witness(after) != witness(path.stat()):
        raise ValueError("JSON changed during read")
    return json.loads(
        raw, object_pairs_hook=_pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON"))
    )


def write(path, value, *, replace=False):
    path = safe(path)
    payload = canonical(value) + b"\n"
    if len(payload) > MAX_JSON:
        raise ValueError("oversized JSON")
    mkdir(path.parent)
    temporary = path.parent / f".pending-{uuid.uuid4().hex}"
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path, follow_symlinks=False)
        sync_dir(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def check_state(value, task, manifest):
    if (
        not isinstance(value, dict)
        or set(value) != {"task", "generation", "stream_id", "manifest_digest"}
        or value["task"] != task
        or value["manifest_digest"] != manifest["digest"]
        or type(value["generation"]) is not int
        or not 0 <= value["generation"] <= 100000
        or not isinstance(value["stream_id"], str)
        or len(value["stream_id"]) != 32
        or any(c not in "0123456789abcdef" for c in value["stream_id"])
    ):
        raise ValueError("invalid Task stream state")
    return value


class Store:
    def __init__(self, root, manifest):
        self.root = safe(root)
        self.manifest = validate_manifest(manifest)
        self.held = False
        self.active_tasks = set()

    def create(self):
        # Never adopt an existing/empty/old431 directory, even by changing schema.
        mkdir(self.root.parent)
        self.root.mkdir()
        sync_dir(self.root.parent)
        (self.root / "_internal").mkdir()
        fd = os.open(self.root / "_internal/.run.lock", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.fsync(fd)
        os.close(fd)
        sync_dir(self.root / "_internal")
        write(self.root / "manifest.json", self.manifest)
        (self.root / "tasks").mkdir()
        (self.root / "logs").mkdir()
        sync_dir(self.root)

    @contextlib.contextmanager
    def locked(self):
        if self.held:
            raise RuntimeError("nested lease")
        if read(self.root / "manifest.json") != self.manifest:
            raise ValueError("new run experiment identity mismatch")
        path = safe(self.root / "_internal/.run.lock")
        fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError("ordinary lease required")
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if (os.fstat(fd).st_dev, os.fstat(fd).st_ino) != (path.stat().st_dev, path.stat().st_ino):
                raise ValueError("lease inode changed")
            if read(self.root / "manifest.json") != self.manifest:
                raise ValueError("manifest changed before lease")
            self.held = True
            try:
                yield self
            finally:
                self.held = False
                self.active_tasks.clear()
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def _lease(self):
        if not self.held:
            raise RuntimeError("coordinator lease required")

    def _task(self, task):
        if task not in self.manifest["tasks"]:
            raise ValueError("unplanned Task")
        return safe(self.root / "tasks" / task)

    def _state_path(self, task):
        self._task(task)
        return self.root / "_internal/task_state" / f"{task}.json"

    def state(self, task):
        value = read(self._state_path(task))
        return check_state(value, task, self.manifest)

    def rows(self, task):
        directory = self._task(task) / "episodes"
        state_path = safe(self._state_path(task))
        if not state_path.exists():
            task_path = self._task(task)
            if task_path.exists() and any(p.name != "summary.json" for p in task_path.iterdir()):
                raise ValueError("Task artifacts lack stream authority")
            return []
        state = self.state(task)
        if not directory.exists():
            raise ValueError("missing active Episode directory; recover restart journal first")
        rows = []
        for ep in sorted(directory.iterdir()):
            safe(ep)
            if not ep.is_dir() or not ep.name.startswith("ep_") or not ep.name[3:].isdecimal():
                raise ValueError("unexpected Episode directory")
            index = int(ep.name[3:])
            if ep.name != f"ep_{index:03d}" or not 0 <= index < self.manifest["episodes_per_task"]:
                raise ValueError("out-of-plan Episode")
            result = safe(ep / "result.json")
            if not result.exists():
                continue  # Interrupted output is not a complete Episode.
            document = read(result)
            if not isinstance(document, dict) or document.get("commit_sha256") != digest(
                {k: v for k, v in document.items() if k != "commit_sha256"}
            ):
                raise ValueError("corrupt Episode commit")
            row = {k: v for k, v in document.items() if k != "commit_sha256"}
            validate_result(self.manifest, row)
            if (
                row["task"] != task
                or row["episode"] != index
                or row["generation"] != state["generation"]
                or row["stream_id"] != state["stream_id"]
            ):
                raise ValueError("Episode from another Task/generation/stream")
            rows.append(row)
        if [row["episode"] for row in rows] != list(range(len(rows))):
            raise ValueError("non-prefix results cannot claim a continuous reset stream")
        if any(row["outcome"] == "invalid" for row in rows[:-1]):
            raise ValueError("Episode written after runtime invalidated the stream")
        return rows

    def _journal(self, task):
        self._task(task)
        return self.root / "_internal/restart_pending" / f"{task}.json"

    def recover_restart(self, task):
        self._lease()
        pending = safe(self._journal(task))
        if not pending.exists():
            return False
        journal = read(pending)
        old, new = journal.get("old"), journal.get("new")
        check_state(old, task, self.manifest)
        check_state(new, task, self.manifest)
        # Only self-generated adjacent transitions; never a user-supplied move path.
        if (
            not isinstance(old, dict)
            or not isinstance(new, dict)
            or new != dict(old, generation=old.get("generation", -1) + 1, stream_id=new.get("stream_id"))
            or old.get("task") != task
            or old.get("manifest_digest") != self.manifest["digest"]
            or old.get("stream_id") == new.get("stream_id")
        ):
            raise ValueError("invalid restart transition")
        current = self.state(task)
        active = safe(self._task(task) / "episodes")
        archive = safe(
            self.root / "_internal/abandoned" / task / f"generation_{old['generation']:06d}_{old['stream_id']}"
        )
        mkdir(archive.parent)
        if current == old:
            if active.exists() and not archive.exists():
                os.rename(active, archive)
                sync_dir(active.parent)
                sync_dir(archive.parent)
            elif active.exists() and archive.exists() and any(active.iterdir()):
                raise ValueError("ambiguous restart has two nonempty active streams")
            elif not active.exists() and not archive.exists():
                raise ValueError("restart lost both active and archived evidence")
            active.mkdir(exist_ok=True)
            sync_dir(active.parent)
            write(self._state_path(task), new, replace=True)
        elif current != new or not archive.is_dir():
            raise ValueError("restart state diverged")
        else:
            active.mkdir(exist_ok=True)
            sync_dir(active.parent)
        self.state(task)  # Validate newly published state before allowing a producer.
        pending.unlink()
        sync_dir(pending.parent)
        return True

    def begin_task(self, task):
        self._lease()
        if task in self.active_tasks:
            raise RuntimeError("Task already scheduled in this lease")
        recovered = self.recover_restart(task)
        path = safe(self._state_path(task))
        if path.exists():
            if recovered and not any((self._task(task) / "episodes").iterdir()):
                self.active_tasks.add(task)
                return {"action": "restart_full_task", **self.state(task)}
            rows = self.rows(task)
            if len(rows) == self.manifest["episodes_per_task"] and all(r["outcome"] != "invalid" for r in rows):
                return {"action": "reuse_complete_task", **self.state(task)}
            old = self.state(task)
            new = dict(old, generation=old["generation"] + 1, stream_id=uuid.uuid4().hex)
            write(self._journal(task), {"old": old, "new": new})
            self.recover_restart(task)
            self.active_tasks.add(task)
            return {"action": "restart_full_task", **new}
        # An interrupted initial claim without an Episode directory fails closed
        # on next read; never pretend a possibly lost scene stream was restored.
        state = {
            "task": task,
            "generation": 0,
            "stream_id": uuid.uuid4().hex,
            "manifest_digest": self.manifest["digest"],
        }
        write(path, state)
        mkdir(self._task(task) / "episodes")
        sync_dir(self._task(task))
        self.active_tasks.add(task)
        return {"action": "start_full_task", **state}

    def commit(self, row):
        self._lease()
        validate_result(self.manifest, row)
        task, episode = row["task"], row["episode"]
        if task not in self.active_tasks:
            raise RuntimeError("Task not owned by this coordinator lease")
        state = self.state(task)
        if row["generation"] != state["generation"] or row["stream_id"] != state["stream_id"]:
            raise ValueError("stale producer must not commit after restart")
        prefix = self.rows(task)
        if episode != len(prefix) or (prefix and prefix[-1]["outcome"] == "invalid"):
            raise ValueError("duplicate/out-of-order/post-invalid Episode")
        directory = safe(self._task(task) / "episodes" / f"ep_{episode:03d}")
        mkdir(directory)
        write(directory / "result.json", {**row, "commit_sha256": digest(row)})

    def record_process_error(self, *, task, stage, message):
        self._lease()
        if task is not None:
            self._task(task)
        if not all(isinstance(x, str) and x for x in (stage, message)):
            raise ValueError("typed process error")
        write(
            self.root / "_internal/process_errors" / f"{uuid.uuid4().hex}.json",
            {"task": task, "stage": stage, "message": message},
        )

    def summary(self):
        expected = self.manifest["episodes_per_task"]
        for path in (self.root / "tasks").iterdir():
            safe(path)
            if path.name not in self.manifest["tasks"] or not path.is_dir():
                raise ValueError("unplanned Task artifacts")
        table, indexed = {}, []
        for task in self.manifest["tasks"]:
            rows = self.rows(task)
            count = {key: sum(r["outcome"] == key for r in rows) for key in ("success", "failure", "invalid")}
            valid = count["success"] + count["failure"]
            complete = valid == expected and not count["invalid"]
            table[task] = {
                **count,
                "pending": expected - len(rows),
                "valid": valid,
                "expected": expected,
                "sr": count["success"] / expected if complete else None,
                "partial_sr_valid_only": count["success"] / valid if valid else None,
            }
            by_index = {row["episode"]: row for row in rows}
            indexed.extend(by_index.get(i, {"task": task, "episode": i, "outcome": "pending"}) for i in range(expected))
        totals = {
            key: sum(row[key] for row in table.values())
            for key in ("success", "failure", "invalid", "pending", "valid", "expected")
        }
        errors_path = safe(self.root / "_internal/process_errors")
        errors = [read(p) for p in sorted(errors_path.iterdir())] if errors_path.exists() else []
        complete = totals["valid"] == totals["expected"] and not totals["invalid"]
        return {
            "prototype_only": True,
            "manifest_digest": self.manifest["digest"],
            "status": "complete"
            if complete and not errors
            else "complete_with_process_errors"
            if complete
            else "partial",
            **totals,
            "sr": totals["success"] / totals["expected"] if complete else None,
            "partial_sr_valid_only": totals["success"] / totals["valid"] if totals["valid"] else None,
            "results_qualified": complete and not errors,
            "runtime_gate_approved": False,
            "process_errors": errors,
            "tasks": table,
        }, indexed

    def publish_views(self):
        self._lease()
        report, rows = self.summary()
        for task, info in report["tasks"].items():
            write(self._task(task) / "summary.json", info, replace=True)
        # One coordinator atomically rebuilds the full index, never append authority.
        # Up to900 bounded prototype rows: bound independently from single JSON.
        target = safe(self.root / "episodes.jsonl")
        temporary = self.root / f".index-{uuid.uuid4().hex}"
        try:
            with temporary.open("xb") as stream:
                for row in rows:
                    stream.write(canonical(row) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            sync_dir(self.root)
        finally:
            temporary.unlink(missing_ok=True)
        write(self.root / "summary.json", report, replace=True)
        return report
