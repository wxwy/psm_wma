"""Durable invocation leases, source references and logical reservations.

Original manifests and Episode evidence are read under their original identity.
Catalogs are observations, never completion authority: every reuse scans the
original source again. Only the latest/current convenience views are replaced.
"""

from __future__ import annotations

import contextlib
import copy
import fcntl
import hashlib
import json
import os
import re
import stat
import time
import uuid
from pathlib import Path

from robocasa_episode_resume import MAX_RECOVERY_BYTES, bounded_episode_count, bounded_episode_index, bounded_records
from robocasa_episode_resume.episode_evidence import _completed_progress, scan_legacy_run
from robocasa_episode_resume.model_identity import (
    IdentityInputError,
    compare_model_identity,
    legacy_ingest,
    reuse_verification_record,
    verification_record,
    verify_model_observation,
)
from robocasa_episode_resume.plan import source_key, verified_scan_records
from robocasa_episode_resume.scene_sampling import SAMPLER_VERSION
from robocasa_eval_results import _marker

_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}\Z")
_MUTABLE_WITNESSES = {"attempt.json", "episode_progress.jsonl", "results.json", "process_cleanup.json"}


class ResumeStoreError(ValueError):
    """Fail closed before launching with an ambiguous or unsafe durable input."""

    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code


def _fail(code, message):
    raise ResumeStoreError(code, message)


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _bytes(value):
    return _canonical(value) + b"\n"


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _safe(path):
    path = Path(os.path.abspath(path))
    if any(part.is_symlink() for part in (path, *path.parents)):
        _fail("UNSAFE_PATH", f"symlink path: {path}")
    return path


def _name(value, field):
    if not isinstance(value, str) or not _NAME.fullmatch(value) or value in {".", ".."}:
        _fail("UNSAFE_PATH", f"invalid {field}: {value!r}")
    return value


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            _fail("INVALID_DOCUMENT", f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _witness(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _raw(path):
    path = _safe(path)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_RECOVERY_BYTES:
                _fail("INVALID_DOCUMENT", f"ordinary bounded JSON file required: {path}")
            raw = stream.read(MAX_RECOVERY_BYTES + 1)
            after = os.fstat(stream.fileno())
        if (
            len(raw) > MAX_RECOVERY_BYTES
            or _witness(before) != _witness(after)
            or _witness(after) != _witness(path.stat())
        ):
            _fail("DOCUMENT_CHANGED", str(path))
        return raw
    except OSError as error:
        raise ResumeStoreError("INVALID_DOCUMENT", f"{path}: {error}") from error


def _read(path):
    raw = _raw(path)
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_pairs,
            parse_constant=lambda value: _fail("INVALID_DOCUMENT", f"nonfinite JSON: {value}"),
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ResumeStoreError("INVALID_DOCUMENT", f"{path}: {error}") from error
    if not isinstance(value, dict):
        _fail("INVALID_DOCUMENT", f"JSON object required: {path}")
    return value, _sha(raw)


def _fsync_dir(path):
    fd = os.open(_safe(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _mkdir(path):
    path = _safe(path)
    if path.exists():
        if not path.is_dir():
            _fail("UNSAFE_PATH", f"directory required: {path}")
        return
    if not path.parent.exists():
        _mkdir(path.parent)
    path.mkdir()
    _fsync_dir(path.parent)


def _write(path, value, *, replace=False):
    """Publish a fully fsynced file; immutable destinations use exclusive link."""
    path = _safe(path)
    raw = _bytes(value)
    if len(raw) > MAX_RECOVERY_BYTES:
        _fail("INVALID_DOCUMENT", "persistent document exceeds 64 MiB")
    _mkdir(path.parent)
    temporary = path.parent / f".pending-{uuid.uuid4().hex}"
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            if path.exists() and not stat.S_ISREG(path.stat().st_mode):
                _fail("UNSAFE_PATH", f"regular convenience pointer required: {path}")
            os.replace(temporary, path)
        else:
            os.link(temporary, path, follow_symlinks=False)
        _fsync_dir(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _manifest(path):
    manifest, digest = _read(path)
    identity = manifest.get("identity")
    if not isinstance(identity, dict) or manifest.get("digest") != _sha(_canonical(identity)):
        _fail("INVALID_MANIFEST_DIGEST", str(path))
    return manifest, digest


def _core(record):
    return {key: value for key, value in record["source_ref"]["hashes"].items() if key not in _MUTABLE_WITNESSES}


class RunStore:
    """One evaluation namespace with the same advisory lease as legacy Queue."""

    def __init__(
        self,
        output_root,
        *,
        current_identity_reader,
        resume=False,
        current_provenance=None,
        allow_relocated_legacy_checkpoint=False,
        model_identity_request=None,
    ):
        if not callable(current_identity_reader):
            raise TypeError("current_identity_reader is required")
        if type(allow_relocated_legacy_checkpoint) is not bool:
            raise TypeError("allow_relocated_legacy_checkpoint requires a boolean")
        if allow_relocated_legacy_checkpoint and resume is not True:
            raise ValueError("legacy checkpoint relocation requires explicit --resume")
        self.root = _safe(output_root)
        self.control = self.root / "_resume_v2"
        self.current_identity_reader = current_identity_reader
        self.resume = resume
        self.current_provenance = current_provenance
        self.allow_relocated_legacy_checkpoint = allow_relocated_legacy_checkpoint
        if model_identity_request is not None and (
            not isinstance(model_identity_request, dict)
            or set(model_identity_request) != {"checkpoint", "num_steps", "action_horizon", "guidance"}
        ):
            raise TypeError("model_identity_request requires exactly the four model parameters")
        self.model_identity_request = copy.deepcopy(model_identity_request)
        self.verification_events = []
        self._cache_hit = False
        self.current_identity = None
        self._preview_identity = None
        self._held = False
        self._fresh = False
        self._legacy_decision = None
        self._legacy_manifest_hash = None
        self._reports = {}
        self._owned_invocations = set()

    def _full_identity(self, reason):
        self._cache_hit = False
        identity = self.current_identity_reader()
        telemetry = copy.deepcopy(identity.get("checkpoint_read_telemetry", {}))
        telemetry.update(cache_hit=False, model_payload_bytes_read=telemetry.get("bytes_read"), reason=reason)
        self.verification_events.append(telemetry)
        return identity

    def _read_current_identity(self):
        # A cache is never sufficient without the original independently admitted
        # strong anchor; old runs conservatively establish it through full reads.
        if self.model_identity_request is not None:
            try:
                record, _ = _read(self.control / "input_verification.json")
                anchor, anchor_sha = _read(self.control / "model_identity.json")
                identity = reuse_verification_record(
                    record,
                    anchor=anchor,
                    anchor_sha256=anchor_sha,
                    run_root=self.root,
                    requested=self.model_identity_request,
                )
            except (OSError, IdentityInputError, ResumeStoreError) as error:
                reason = getattr(error, "code", type(error).__name__)
            else:
                self._cache_hit = True
                self.verification_events.append(copy.deepcopy(identity["checkpoint_read_telemetry"]))
                return identity
        else:
            reason = "CACHE_NOT_CONFIGURED"
        return self._full_identity(reason)

    def _persist_verification(self):
        self._require_lease()
        if self.model_identity_request is None or self._cache_hit:
            return
        anchor = self.control / "model_identity.json"
        if not anchor.exists():
            return  # Fresh/legacy anchor publication belongs to begin_invocation.
        stored, anchor_sha = _read(anchor)
        self._match(stored)
        record = verification_record(self.current_identity, run_root=self.root, anchor_sha256=anchor_sha)
        _write(self.control / "input_verification.json", record, replace=True)
        self._cache_hit = True

    def _match(self, old):
        result = compare_model_identity(old, self.current_identity)
        if result["status"] != "MATCH":
            _fail("MODEL_MISMATCH", json.dumps(result["errors"], ensure_ascii=False, sort_keys=True))

    def _admit(self, *, own_fresh=False):
        _safe(self.root)
        compare_model_identity(self.current_identity, self.current_identity)
        if not self.root.exists():
            return {"status": "FRESH", "model_identity": self.current_identity}
        if not self.root.is_dir():
            _fail("UNSAFE_PATH", "evaluation root must be a directory")
        if not self.resume and not own_fresh:
            _fail("RESUME_REQUIRED", "existing evaluation namespace needs explicit resume")
        lock = _safe(self.root / ".run.lock")
        if not lock.exists() or not stat.S_ISREG(lock.stat().st_mode):
            _fail("MISSING_RUN_LOCK", "existing evaluation requires its original ordinary .run.lock")
        anchor = _safe(self.control / "model_identity.json")
        root_manifest = _safe(self.root / "evaluation_manifest.json")
        if anchor.exists():
            stored, _ = _read(anchor)
            self._match(stored)
            if root_manifest.exists():
                old, observed = _manifest(root_manifest)
                nested = old["identity"].get("model_identity")
                if nested is not None:
                    self._match(nested)
                else:
                    migration = self.control / "legacy_migration.json"
                    if not migration.exists():
                        _fail("MISSING_LEGACY_MIGRATION", "strong anchor lacks original legacy admission witness")
                    witness, _ = _read(migration)
                    if (
                        witness.get("original_manifest_sha256") != observed
                        or witness.get("model_identity_digest") != stored["digest"]
                    ):
                        _fail("LEGACY_MANIFEST_CHANGED", "original legacy manifest differs from admitted source")
        elif root_manifest.exists():
            old, observed = _manifest(root_manifest)
            nested = old["identity"].get("model_identity")
            if nested is not None:
                self._match(nested)
            else:
                decision = legacy_ingest(
                    old,
                    self.current_identity,
                    current_provenance=self.current_provenance,
                    allow_relocated_checkpoint=self.allow_relocated_legacy_checkpoint,
                )
                if decision["status"] == "MODEL_MISMATCH":
                    _fail("MODEL_MISMATCH", json.dumps(decision["errors"], ensure_ascii=False, sort_keys=True))
                self._legacy_decision, self._legacy_manifest_hash = decision, observed
        elif not own_fresh:
            _fail("UNKNOWN_RUN_NAMESPACE", "existing root has neither original manifest nor strong model anchor")
        # Validate durable source identities before creating an invocation, even
        # if the caller later requests a different subset of Tasks.
        for reservation in self._reservations():
            self._source(reservation)
        return {"status": "FRESH" if own_fresh else "MATCH", "model_identity": self.current_identity}

    def preview(self):
        """Read-only admission. The next lease reuses this outside hash once."""
        self.current_identity = self._read_current_identity()
        result = self._admit()
        self._preview_identity = self.current_identity
        return result

    @contextlib.contextmanager
    def locked(self):
        if self._held:
            raise RuntimeError("nested evaluation lease is unsupported")
        self.current_identity = self._preview_identity or self._read_current_identity()
        self._preview_identity = None
        self._admit()
        outside_identity = self.current_identity
        fresh = not self.root.exists()
        if fresh:
            # Exclusive creation prevents two fresh callers claiming a namespace.
            _mkdir(self.root.parent)
            self.root.mkdir()
            _fsync_dir(self.root.parent)
        self._fresh = fresh
        lock = _safe(self.root / ".run.lock")
        flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
        if fresh:
            flags |= os.O_CREAT | os.O_EXCL
        fd = os.open(lock, flags, 0o600)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                _fail("UNSAFE_PATH", "regular .run.lock required")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ResumeStoreError("RUN_LOCKED", "another Queue owns .run.lock") from error
            if _witness(os.fstat(fd)) != _witness(_safe(lock).stat()):
                _fail("RUN_LOCK_CHANGED", "the acquired run lease no longer names the original lock")
            if fresh:
                os.fsync(fd)
                _fsync_dir(self.root)
            try:
                verify_model_observation(outside_identity)
            except IdentityInputError:
                # A real race requires another full read, then the SAME strict
                # comparison. Stable cold inputs are not hashed twice.
                self.current_identity = self._full_identity("INPUT_CHANGED_BEFORE_LEASE")
            self._match(outside_identity)
            self._admit(own_fresh=fresh)
            self._held = True
            try:
                yield self
            finally:
                self._held = False
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def _require_lease(self):
        if not self._held:
            raise RuntimeError("mutation requires the evaluation run lease")

    def _reservations(self):
        invocation_root = _safe(self.root / "_invocations")
        if not invocation_root.exists():
            return []
        paths = []
        for invocation in sorted(invocation_root.iterdir()):
            _safe(invocation)
            if not invocation.is_dir():
                _fail("INVALID_INVOCATION", str(invocation))
            directory = _safe(invocation / "reservations")
            if directory.exists():
                if not directory.is_dir():
                    _fail("INVALID_RESERVATION", str(directory))
                for path in sorted(directory.iterdir()):
                    _safe(path)
                    if path.suffix != ".json":
                        _fail("INVALID_RESERVATION", str(path))
                    document, _ = _read(path)
                    document["_path"] = str(path)
                    paths.append(document)
        return bounded_records(paths, "source reservations")

    def _source(self, reservation):
        if reservation.get("schema") != "psm_eval_batch_reservation_v1":
            _fail("INVALID_RESERVATION", "unknown batch reservation schema")
        self._match(reservation.get("model_identity"))
        invocation = Path(reservation["_path"]).parent.parent
        task = _name(reservation.get("task"), "task")
        batch_id = _name(reservation.get("batch_id"), "batch_id")
        expected = invocation / "sources" / task / batch_id
        if reservation.get("source_root") != str(expected):
            _fail("SOURCE_PATH_MISMATCH", "reservation source must stay in its own invocation sandbox")
        path = _safe(expected / "evaluation_manifest.json")
        rows = bounded_records(reservation.get("reservations", []), "batch reservations")
        bounded_episode_count(len(rows), "batch reservations")
        seen = set()
        for physical, row in enumerate(rows):
            logical = bounded_episode_index(row.get("logical_episode_index"))
            if logical in seen or row.get("source_episode") != physical or row.get("task") != task:
                _fail("INVALID_RESERVATION_MAPPING", str(path))
            seen.add(logical)
            if row.get("attempt") != "attempt_0001" or row.get("original_digest") != reservation.get("source_digest"):
                _fail("INVALID_RESERVATION_MAPPING", "wrong original attempt identity")
        if not path.exists():
            return None  # A durable reservation still reserves all its slots.
        manifest, observed = _manifest(path)
        if observed != reservation.get("source_manifest_sha256") or manifest["digest"] != reservation.get(
            "source_digest"
        ):
            _fail("SOURCE_MANIFEST_CHANGED", str(path))
        self._match(manifest["identity"].get("model_identity"))
        context = {"invocation_id": invocation.name, "batch_id": batch_id, "source_root": str(expected)}
        if manifest["identity"].get("source_context") != context:
            _fail("SOURCE_CONTEXT_MISMATCH", str(path))
        protocol = manifest["identity"].get("protocol", {})
        if protocol.get("seed") != reservation.get("effective_seed") or protocol.get("trials") != len(rows):
            _fail("INVALID_RESERVATION_MAPPING", "actual seed/trials disagree with durable source mapping")
        return manifest

    def _scan_reserved(self, reservation, *, sim_python, requested_media, deadline=None, stop=None):
        manifest = self._source(reservation)
        if manifest is None:
            return {
                "records": [],
                "diagnostics": [{"code": "RESERVED_SOURCE_NOT_CREATED", "path": reservation["source_root"]}],
            }
        source_root = Path(reservation["source_root"])
        scan = scan_legacy_run(
            source_root,
            sim_python=sim_python,
            tasks=[reservation["task"]],
            requested_media=requested_media,
            deadline=deadline,
            stop=stop,
        )
        mapping = {row["source_episode"]: row for row in reservation["reservations"]}
        records = verified_scan_records(scan)
        for record in records:
            if record["source_ref"]["attempt"] != "attempt_0001" or record["source_episode"] not in mapping:
                _fail("UNRESERVED_SOURCE_EPISODE", str(record["source_ref"]))
            row = mapping[record["source_episode"]]
            record.update(
                logical_episode_index=row["logical_episode_index"],
                requested_seed=reservation["requested_seed"],
                sampling_protocol=(
                    "legacy_task_stream"
                    if reservation["sampling_mode"] == "fresh_task_stream"
                    else reservation.get("sampler", {}).get("sampler_version", SAMPLER_VERSION)
                ),
                sampling_mode=reservation["sampling_mode"],
                seed_family=copy.deepcopy(reservation.get("seed_family")),
                reservation_source_ref={"path": reservation["_path"], "original_digest": manifest["digest"]},
            )
        return {**scan, "records": records}

    def _legacy_allocations(self, manifest, *, diagnostics):
        """Project original Task allocation, never infer completed outcomes.

        A valid original C01 stream proves that this Task attempted its original
        manifest's bounded trial allocation. Retain the unclosed logical tail
        across shrink/restart, with both original manifest and stream witnesses.
        """
        trials = bounded_episode_count(manifest["identity"]["protocol"]["trials"], "legacy trials")
        bounded_episode_count(len(manifest["identity"]["tasks"]) * trials, "total legacy allocation")
        manifest_path = self.root / "evaluation_manifest.json"
        reference = {
            "path": str(manifest_path),
            "sha256": _sha(_raw(manifest_path)),
            "original_digest": manifest["digest"],
        }
        observations = []
        for task_row in manifest["identity"]["tasks"]:
            task = task_row["task"]
            task_dir = _safe(self.root / task)
            if not task_dir.is_dir():
                continue
            streams, numeric = [], {}
            for attempt in sorted(task_dir.iterdir()):
                _safe(attempt)
                match = re.fullmatch(r"attempt_(\d{4,})", attempt.name)
                if match and attempt.is_dir():
                    numeric.setdefault(int(match[1]), []).append(attempt)
            for paths in numeric.values():
                if len(paths) != 1:
                    continue
                attempt = paths[0]
                path = _safe(attempt / "episode_progress.jsonl")
                try:
                    _marker(attempt, manifest["digest"])
                    before = _witness(path.stat())
                    completed, _ = _completed_progress(
                        attempt, digest=manifest["digest"], attempt_id=f"{task}/{attempt.name}"
                    )
                    raw = _raw(path)
                    if before != _witness(path.stat()) or len(completed) > trials:
                        _fail("DOCUMENT_CHANGED", str(path))
                    streams.append({"path": str(path), "sha256": _sha(raw)})
                except (OSError, ValueError) as error:
                    diagnostics.append(
                        {
                            "code": "LEGACY_ALLOCATION_STREAM_EXCLUDED",
                            "task": task,
                            "path": str(path),
                            "message": str(error),
                        }
                    )
            if streams:
                observations.extend(
                    {
                        "task": task,
                        "logical_episode_index": slot,
                        "kind": "legacy_original_task_allocation",
                        "source_ref": copy.deepcopy(reference),
                        "progress_source_refs": copy.deepcopy(streams),
                        "original_manifest_trials": trials,
                    }
                    for slot in range(trials)
                )
        return bounded_records(observations, "legacy allocation observations")

    def discover_history(self, *, sim_python, requested_media=None):
        """Fresh source validation, followed by catalog consistency comparison."""
        if self.current_identity is None:
            raise RuntimeError("preview or acquire the lease before reading history")
        records, diagnostics, documents, sources, observations = [], [], [], [], []
        root_manifest = _safe(self.root / "evaluation_manifest.json")
        if root_manifest.exists():
            scan = scan_legacy_run(self.root, sim_python=sim_python, requested_media=requested_media)
            records.extend(verified_scan_records(scan))
            diagnostics.extend(scan["diagnostics"])
            observations.extend(self._legacy_allocations(scan["original_manifest"], diagnostics=diagnostics))
            sources.append(str(root_manifest))
        for reservation in self._reservations():
            scan = self._scan_reserved(reservation, sim_python=sim_python, requested_media=requested_media)
            records.extend(scan["records"])
            diagnostics.extend(scan["diagnostics"])
            documents.append(reservation["_path"])
            sources.append(str(Path(reservation["source_root"]) / "evaluation_manifest.json"))
        records = bounded_records(records)
        fresh = {source_key(record): record for record in records}
        catalogs = []
        directory = _safe(self.control / "catalog")
        if directory.exists():
            for path in sorted(directory.iterdir()):
                value, _ = _read(path)
                if value.get("schema") != "psm_eval_episode_reference_v1":
                    _fail("INVALID_CATALOG", str(path))
                if value.get("model_identity_digest") != self.current_identity["digest"]:
                    _fail("CATALOG_MODEL_MISMATCH", str(path))
                previous = value.get("record")
                if not isinstance(previous, dict):
                    _fail("INVALID_CATALOG", str(path))
                key = source_key(previous)
                if key in fresh and _core(previous) != _core(fresh[key]):
                    _fail("SOURCE_EVIDENCE_CHANGED", key)
                if key not in fresh:
                    diagnostics.append({"code": "CATALOG_SOURCE_NOT_REVALIDATED", "source_key": key, "path": str(path)})
                catalogs.append(str(path))
                # The observation preserves known logical tails after interruption.
                documents.append(str(path))
        return {
            "records": records,
            "diagnostics": diagnostics,
            "recovery_documents": documents,
            "catalogs": catalogs,
            "source_manifests": sources,
            "recovery_observations": observations,
        }

    def begin_invocation(self, plan, resolved_config, *, initial_manifest=None):
        self._require_lease()
        invocation_id = _name(plan.get("invocation_id"), "invocation_id")
        if self._legacy_decision is not None and not (self.control / "legacy_migration.json").exists():
            _write(
                self.control / "legacy_migration.json",
                {
                    "schema": "psm_eval_legacy_migration_v1",
                    "original_manifest_sha256": self._legacy_manifest_hash,
                    "model_identity_digest": self.current_identity["digest"],
                    "decision": self._legacy_decision,
                },
            )
        anchor = self.control / "model_identity.json"
        if not anchor.exists():
            _write(anchor, self.current_identity)
        else:
            self._match(_read(anchor)[0])
        self._persist_verification()
        if initial_manifest is not None and not (self.root / "evaluation_manifest.json").exists():
            manifest = copy.deepcopy(initial_manifest)
            manifest["identity"]["model_identity"] = copy.deepcopy(self.current_identity)
            manifest["digest"] = _sha(_canonical(manifest["identity"]))
            _write(self.root / "evaluation_manifest.json", manifest)
        path = _safe(self.root / "_invocations" / invocation_id)
        _mkdir(path.parent)
        path.mkdir()  # This invocation id is never reopened or overwritten.
        _fsync_dir(path.parent)
        _write(
            path / "invocation_manifest.json",
            {
                "schema": "psm_eval_resume_invocation_v1",
                "invocation_id": invocation_id,
                "created_ns": time.time_ns(),
                "model_identity": self.current_identity,
                "current_provenance": self.current_provenance,
            },
        )
        _write(path / "resume_plan.json", plan)
        _write(path / "resolved_config.json", resolved_config)
        self._owned_invocations.add(str(path))
        return path

    def reserve_batch(self, invocation, batch, source_manifest):
        self._require_lease()
        invocation = _safe(invocation)
        if str(invocation) not in self._owned_invocations:
            _fail("INVALID_INVOCATION", str(invocation))
        task = _name(batch.get("task"), "task")
        if not task.isidentifier() or task == "all":
            _fail("INVALID_TASK", task)
        episodes = copy.deepcopy(bounded_records(batch.get("episodes", []), "batch episodes"))
        bounded_episode_count(len(episodes), "batch episodes")
        seen = set()
        for physical, episode in enumerate(episodes):
            logical = bounded_episode_index(episode.get("logical_episode_index"))
            if logical in seen or episode.get("source_episode") != physical:
                _fail("INVALID_RESERVATION_MAPPING", "physical Episodes must be 0..N-1 and logical slots unique")
            seen.add(logical)
        seed = batch.get("effective_seed")
        if type(seed) is not int or seed < 0:
            _fail("INVALID_RESERVATION_MAPPING", "effective_seed must be a nonnegative integer")
        manifest = copy.deepcopy(source_manifest)
        if not isinstance(manifest.get("identity"), dict):
            _fail("INVALID_MANIFEST", "batch needs original runtime-bound manifest")
        protocol = manifest["identity"].get("protocol", {})
        if (
            type(protocol.get("trials")) is not int
            or type(protocol.get("seed")) is not int
            or protocol.get("trials") != len(episodes)
            or protocol.get("seed") != seed
        ):
            _fail("INVALID_RESERVATION_MAPPING", "source manifest must describe actual batch seed and trials")
        if task not in {row.get("task") for row in manifest["identity"].get("tasks", [])}:
            _fail("INVALID_TASK", "source manifest must retain actual Task metadata")
        batch_id = _name(batch.get("batch_id", f"batch_{uuid.uuid4().hex}"), "batch_id")
        source_root = invocation / "sources" / task / batch_id
        manifest["identity"]["model_identity"] = copy.deepcopy(self.current_identity)
        manifest["identity"]["source_context"] = {
            "invocation_id": invocation.name,
            "batch_id": batch_id,
            "source_root": str(source_root),
        }
        manifest["digest"] = _sha(_canonical(manifest["identity"]))
        reservation_path = invocation / "reservations" / f"{batch_id}.json"
        sampler = batch.get("sampler", {})
        requested_seed = batch.get("requested_seed", sampler.get("requested_seed", seed))
        if type(requested_seed) is not int or requested_seed < 0:
            _fail("INVALID_RESERVATION_MAPPING", "requested_seed must be a nonnegative integer")
        mode = batch.get("sampling_mode", sampler.get("sampling_mode"))
        if mode not in {"fresh_task_stream", "resume_gap_independent"}:
            _fail("INVALID_RESERVATION_MAPPING", "unknown scene sampling mode")
        rows = [
            dict(
                episode,
                task=task,
                original_digest=manifest["digest"],
                attempt="attempt_0001",
                reservation_id=_sha(
                    _canonical({"task": task, "logical_episode_index": episode["logical_episode_index"]})
                ),
                source_ref={"path": str(reservation_path), "original_digest": manifest["digest"]},
            )
            for episode in episodes
        ]
        document = {
            "schema": "psm_eval_batch_reservation_v1",
            "task": task,
            "batch_id": batch_id,
            "source_root": str(source_root),
            "source_digest": manifest["digest"],
            "source_manifest_sha256": _sha(_bytes(manifest)),
            "model_identity": self.current_identity,
            "effective_seed": seed,
            "requested_seed": requested_seed,
            "sampling_mode": mode,
            "seed_family": {"requested_seed": requested_seed, "sampler_version": sampler.get("sampler_version")},
            "sampler": sampler,
            "reservations": rows,
        }
        # Reserve first. Any crash afterwards remains a pending logical slot,
        # rather than allocating a fresh higher ID after restart.
        _write(reservation_path, document)
        _write(source_root / "evaluation_manifest.json", manifest)
        attempt = source_root / task / "attempt_0001"
        _mkdir(attempt)
        _write(
            attempt / "attempt.json",
            {
                "schema": "psm_robocasa_task_attempt_v1",
                "attempt_id": "attempt_0001",
                "evaluation_run_digest": manifest["digest"],
                "status": "RUNNING",
            },
        )
        return {
            "source_root": source_root,
            "attempt_dir": attempt,
            "source_manifest": manifest,
            "source_manifest_path": source_root / "evaluation_manifest.json",
            "dataset_dir": Path(batch["dataset_dir"]),
            "task": task,
            "seed": seed,
            "num_test_episodes": len(episodes),
            "episodes": episodes,
            "reservation_path": reservation_path,
            "batch_id": batch_id,
            "sampler": sampler,
        }

    def read_reserved_batch(self, job, *, sim_python, requested_media=None, deadline=None, stop=None):
        document, _ = _read(job["reservation_path"])
        document["_path"] = str(Path(job["reservation_path"]).absolute())
        return self._scan_reserved(
            document, sim_python=sim_python, requested_media=requested_media, deadline=deadline, stop=stop
        )

    def publish_catalog(self, records):
        self._require_lease()
        paths = []
        for record in bounded_records(records):
            if record.get("verified") is not True:
                _fail("UNVERIFIED_CATALOG_SOURCE", "only freshly scanner-validated records may be observed")
            key = source_key(record)
            value = {
                "schema": "psm_eval_episode_reference_v1",
                "model_identity_digest": self.current_identity["digest"],
                "record": record,
                "completed_slots": [record],
            }
            path = self.control / "catalog" / f"{key}_{_sha(_canonical(value))}.json"
            if not path.exists():
                _write(path, value)
            paths.append(path)
        return paths

    def write_report(self, invocation, report):
        """Append a snapshot; replace only this invocation's mutable UI view."""
        self._require_lease()
        invocation = _safe(invocation)
        if str(invocation) not in self._owned_invocations:
            _fail("INVALID_INVOCATION", str(invocation))
        sequence = self._reports.get(str(invocation), 0)
        snapshot = invocation / "snapshots" / f"{sequence:06d}.json"
        _write(snapshot, report)
        self._reports[str(invocation)] = sequence + 1
        current = invocation / "current_summary.json"
        _write(current, report, replace=True)
        _write(
            self.root / "latest_invocation.json",
            {
                "schema": "psm_eval_latest_invocation_v1",
                "invocation_id": invocation.name,
                "invocation_dir": str(invocation),
                "summary_path": str(current),
                "report_path": str(snapshot),
                "model_identity_digest": self.current_identity["digest"],
            },
            replace=True,
        )
        return snapshot
