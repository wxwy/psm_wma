"""Shared multi-GPU engine: persistent EventSpool authority, two source adapters.

Import/plan is CPU-only and does not load Torch, Wan, MuJoCo or a renderer.
Workers own models; the coordinator owns discovery and existing finalization.
"""

from __future__ import annotations

import concurrent.futures
import copy
import json
import math
import multiprocessing
import os
import signal
import threading
import time
from pathlib import Path

from g2.io import digest, read_json

from .batch_contract import make_batch_recipe
from .batch_finalize import cpu_initializer, finalize_job
from .batch_queue import BatchQueue
from .batch_worker import encoder_factory, worker_main
from .contract import CacheError
from .storage import atomic_json, build_lock
from .streaming import ConsumerLimits, EventSpool, QueueBackpressure

ENGINE_SCHEMA = "g2_multigpu_batch_engine_v1"
DEFAULTS = dict(
    schema=ENGINE_SCHEMA,
    gpus=[4, 5, 6, 7],
    max_batch_size_per_gpu=32,
    batch_wait_ms=500,
    lease_s=60,
    heartbeat_s=5,
    worker_timeout_s=300,
    max_worker_restarts=3,
    discovery_interval_s=2,
    idle_timeout_s=600,
    max_active_jobs=32,
    min_free_disk_bytes=8 * 1024**3,
    poll_interval_s=0.1,
    test_crash_once=None,
)


def discover_published(dataset_root, *, tasks=None, episodes=None):
    """Ignore staging/unpublished directories without weakening legacy scans."""
    from g2.offline.atomic_6views_catalog import EPISODE_NAME

    from .contract import contained, safe_relative

    root = Path(dataset_root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise CacheError("published dataset must be a real existing directory")
    if (root / "COMPLETE.json").is_file():
        manifest = read_json(contained(root, "episode_manifest.json"))
        task, eid = manifest.get("task_class"), manifest.get("episode_id")
        if not isinstance(task, str) or type(eid) is not int or eid < 0:
            raise CacheError("invalid published episode identity")
        if (tasks and task not in tasks) or (episodes and eid not in episodes):
            return []
        return [root]
    if not (root / "tasks").exists():
        return []
    available = contained(root, "tasks")
    found = []
    for task in sorted(available.iterdir()):
        if tasks and task.name not in tasks:
            continue
        safe_relative(task.name)
        directory = contained(available, task.name + "/episodes", allow_missing=True)
        if not directory.exists():
            continue  # mkdir task precedes mkdir episodes and episode publication.
        if not directory.is_dir():
            raise CacheError("published task episodes namespace must be a directory")
        for ep in sorted(directory.iterdir()):
            match = EPISODE_NAME.fullmatch(ep.name)
            if not match or (episodes and int(match.group(1)) not in episodes):
                continue
            path = contained(directory, ep.name)
            if (path / "COMPLETE.json").is_file():
                found.append(path)
    return found


def engine_config(value=None, *, allow_test=False):
    value = {} if value is None else value
    if not isinstance(value, dict) or set(value) - set(DEFAULTS):
        raise CacheError("unknown batch engine configuration")
    cfg = copy.deepcopy({**DEFAULTS, **value})
    if cfg["schema"] != ENGINE_SCHEMA:
        raise CacheError("unknown batch engine schema")
    gpus = cfg["gpus"]
    if (
        not isinstance(gpus, list)
        or not gpus
        or len(gpus) > 8
        or len(set(gpus)) != len(gpus)
        or any(type(n) is not int or not 0 <= n < 128 for n in gpus)
    ):
        raise CacheError("explicit unique physical GPU indices required")
    for key in (
        "max_batch_size_per_gpu",
        "max_active_jobs",
        "min_free_disk_bytes",
        "max_worker_restarts",
    ):
        if type(cfg[key]) is not int or cfg[key] < (
            0 if key in ("max_worker_restarts", "min_free_disk_bytes") else 1
        ):
            raise CacheError("invalid finite engine bound: " + key)
    if cfg["max_batch_size_per_gpu"] > 32:
        raise CacheError("per-GPU batch exceeds32")
    for key in (
        "batch_wait_ms",
        "lease_s",
        "heartbeat_s",
        "worker_timeout_s",
        "discovery_interval_s",
        "idle_timeout_s",
        "poll_interval_s",
    ):
        v = cfg[key]
        if (
            type(v) not in (int, float)
            or not math.isfinite(v)
            or v < (0 if key == "batch_wait_ms" else 0.001)
        ):
            raise CacheError("finite positive engine timing required: " + key)
    if (
        not 2 * cfg["heartbeat_s"] < cfg["lease_s"] <= 3600
        or cfg["batch_wait_ms"] > 60000
    ):
        raise CacheError("lease must exceed two heartbeats and wait must be bounded")
    fault = cfg["test_crash_once"]
    if fault is not None and (
        not allow_test
        or fault not in {"numeric_fsynced", *[f"after_ack:{i}" for i in range(32)]}
    ):
        raise CacheError("fault injection requires an explicit isolated test scope")
    return cfg


class IdleClock:
    """Busy/in-flight work never ages toward idle; heartbeats are not new work."""

    def __init__(self, timeout=600):
        self.timeout, self.since = timeout, None

    def observe(self, now, *, busy, new_work=False):
        if busy or new_work:
            self.since = None
            return False
        if self.since is None:
            self.since = now
        return now - self.since >= self.timeout


class CapacityWatchdog:
    """Bound a circular numeric-budget wait, while allowing source-ready/GC."""

    def __init__(self, timeout):
        self.timeout, self.since, self.signature = timeout, None, None

    def observe(self, now, *, blocked, signature):
        if not blocked:
            self.since, self.signature = None, None
        elif self.since is None or self.signature != signature:
            self.since, self.signature = now, signature
        elif now - self.since >= self.timeout:
            raise CacheError(
                "numeric capacity cannot progress within the configured worker timeout; full source and fixed-batch results retained; explicit capacity review required"
            )


def initialize(
    spool_root,
    *,
    weights,
    cosmos_root,
    config=None,
    source_policy=None,
    lifecycle="streaming_v1",
    limits=ConsumerLimits(512, 512 * 1024**2),
    max_result_bytes=4 * 1024**3,
    max_records=100000,
    _test_factory=None,
    allow_test=False,
):
    cfg = engine_config(config, allow_test=allow_test)
    spec = dict(
        cfg,
        weights=str(Path(weights).absolute()),
        cosmos_root=str(Path(cosmos_root).absolute()),
    )
    if _test_factory:
        spec["_test_encoder_factory"] = _test_factory
    encoder = encoder_factory(spec)
    recipe = make_batch_recipe(
        encoder.descriptor(), max_batch_size=cfg["max_batch_size_per_gpu"]
    )
    if limits.max_events < cfg["max_batch_size_per_gpu"]:
        raise CacheError("pending queue must hold at least one maximum batch")
    spool = EventSpool(
        spool_root,
        recipe,
        limits=limits,
        max_result_bytes=max_result_bytes,
        max_records=max_records,
        source_policy=source_policy,
        lifecycle=lifecycle,
    )
    return spool, spec


class BatchEngine:
    def __init__(
        self,
        spool,
        spec,
        *,
        mode,
        dataset_root=None,
        tasks=None,
        episodes=None,
        stop_file=None,
        expected=None,
        producer_done=None,
        resume=False,
        finalize_workers=0,
        clock=time.monotonic,
    ):
        if (
            mode not in ("sync", "independent")
            or (mode == "independent") != spool.view_first
        ):
            raise CacheError(
                "engine input mode differs from the explicit source lifecycle"
            )
        if mode == "independent" and spool.source_policy is not None:
            raise CacheError(
                "independent B does not implicitly retire source; use explicit Stage C"
            )
        if mode == "independent" and dataset_root is None:
            raise CacheError("continuous discovery requires a published dataset root")
        if (
            type(finalize_workers) is not int
            or not 0 <= finalize_workers <= 8
            or (mode != "independent" and finalize_workers)
        ):
            raise CacheError(
                "CPU finalizers require an explicit independent B count in 0..8"
            )
        self.spool, self.spec, self.mode, self.resume, self.clock = (
            spool,
            spec,
            mode,
            resume,
            clock,
        )
        self.data = Path(dataset_root).absolute() if dataset_root is not None else None
        self.tasks, self.episodes = sorted(tasks or []), sorted(episodes or [])
        self.stop_file = Path(stop_file) if stop_file else None
        self.expected = Path(expected).absolute() if expected else None
        self.producer_done = Path(producer_done).absolute() if producer_done else None
        self.queue = BatchQueue(
            spool, lease_s=spec["lease_s"], batch_wait_ms=spec["batch_wait_ms"]
        )
        self.encoder = encoder_factory(spec)  # descriptor only; no coordinator model.
        if self.encoder.descriptor() != spool.recipe["encoder"]:
            raise CacheError("coordinator source/weights differ from the shared recipe")
        self._leases, self._sources, self._seen = {}, {}, {}
        self._processes, self._restarts = {}, {gpu: 0 for gpu in spec["gpus"]}
        self._mp = multiprocessing.get_context("spawn")
        self._stop = self._mp.Event()
        self._last_discovery, self._last_progress = float("-inf"), float("-inf")
        self._idle = IdleClock(spec["idle_timeout_s"])
        self._capacity = CapacityWatchdog(
            max(spec["worker_timeout_s"], spec["batch_wait_ms"] / 1000 + 1)
        )
        self._new_work = False
        self._paused = False
        self.finalize_workers = finalize_workers
        self._finalize_pool = None
        self._finalizers = {}
        self._started = self.clock()
        self._publish_binding()

    def _publish_binding(self):
        value = dict(
            schema=ENGINE_SCHEMA,
            spec=self.spec,
            mode=self.mode,
            dataset_root=str(self.data) if self.data else None,
            tasks=self.tasks,
            episodes=self.episodes,
            expected=str(self.expected) if self.expected else None,
            expected_sha256=digest(self.expected) if self.expected else None,
            producer_done=str(self.producer_done) if self.producer_done else None,
            recipe_id=self.spool.recipe["recipe_id"],
        )
        path = self.spool.root / "engine_config.json"
        if path.exists():
            if read_json(path) != value:
                raise CacheError(
                    "engine/source/GPU/scope configuration differs; no implicit resume"
                )
            if not self.resume:
                raise CacheError("existing engine requires explicit resume")
        else:
            atomic_json(path, value)

    def _target_lease(self, target):
        from .posthoc import coordinator

        target = str(Path(target).absolute())
        if target not in self._leases:
            lease = build_lock(coordinator(target))
            lease.__enter__()
            self._leases[target] = lease

    def _release(self, target):
        lease = self._leases.pop(str(target), None)
        if lease:
            lease.__exit__(None, None, None)

    def _recover(self):
        from .source_retirement import resume_pending

        with self.spool._db() as db:
            jobs = [dict(r) for r in db.execute("SELECT * FROM jobs")]
        for row in jobs:
            self._target_lease(row["target"])
            if row["done"]:
                if self.spool.source_policy is not None and not resume_pending(
                    self.spool, row["id"]
                ):
                    continue
                if self.spool.reap(row["id"]):
                    self._release(row["target"])
            elif self.mode == "independent" and row["source_ready"] is None:
                # A manager can die between durable register and offer. Unlike
                # sync's legitimately producing row, this input was published.
                # The original offer revalidates full source and pinned scope.
                self.spool.offer_source(row["id"])
        if self.resume:
            self.queue.retry_failed()

    def _spawn(self, gpu):
        process = self._mp.Process(
            target=worker_main,
            args=(str(self.spool.root), self.spec, gpu, self._stop, os.getpid()),
            daemon=True,
        )
        process.start()
        self._processes[gpu] = process

    def _supervise(self):
        with self.spool._db() as db:
            over = db.execute(
                "SELECT w.pid FROM engine_batches b JOIN engine_workers w ON w.id=b.worker WHERE b.state='running' AND b.started<?",
                (time.time() - self.spec["worker_timeout_s"],),
            ).fetchall()
        hung = {r[0] for r in over}
        for gpu, process in list(self._processes.items()):
            if process.pid in hung and process.is_alive():
                process.terminate()
                process.join(5)
                if process.is_alive():
                    process.kill()
                    process.join(5)
            if process.is_alive():
                continue
            process.join()
            self.queue.expire_dead_worker(process.pid)
            self._restarts[gpu] += 1
            if self._restarts[gpu] > self.spec["max_worker_restarts"]:
                raise CacheError(
                    "owned GPU worker restart budget exhausted; retain all sources"
                )
            self._spawn(gpu)

    def _discover(self):
        if (
            self.mode != "independent"
            or self.clock() - self._last_discovery < self.spec["discovery_interval_s"]
        ):
            return
        from .builder import verify_episode
        from .final_source import PROFILE_SCHEMA
        from .sealed_source import scan_source

        self._last_discovery = self.clock()
        with self.spool._db() as db:
            count = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            # While the bounded active ledger is full, scanning every completed
            # Episode cannot admit a single new job. Defer work until a tombstone
            # frees capacity; never delay draining existing GPU inputs.
            if count >= self.spec["max_active_jobs"]:
                return
            known = {r[0] for r in db.execute("SELECT target FROM jobs")}
            archived = {r[0] for r in db.execute("SELECT target FROM completed")}
        roots = discover_published(
            self.data, tasks=self.tasks or None, episodes=self.episodes or None
        )
        for root in roots:
            root = Path(root).absolute()
            marker = root / "COMPLETE.json"
            if not marker.is_file():
                continue  # Never read an in-progress source.
            tag = digest(marker)
            if self._seen.get(str(root)) == tag or str(root) in known:
                continue
            if count >= self.spec["max_active_jobs"]:
                break
            if str(root) in archived:
                # Archives already passed full numerical/source verification.
                # Recheck their signed scope, all declared product bytes and
                # per-View PT hashes without decompressing/parsing every prior
                # Episode's giant source JSON or loading every tensor.
                from .contract import contained
                from .ledger_archive import verify_archived_payload_bytes

                # Stage C is a separately audited transaction that legitimately
                # replaces the *working* source/receipt identities recorded in
                # an earlier Stage-B tombstone. Its new capsule must take the
                # original posthoc-aware full verifier, not a false "tamper"
                # verdict against the pre-retirement identity set.
                if (
                    read_json(contained(root, "episode_manifest.json")).get("schema")
                    == PROFILE_SCHEMA
                ):
                    from g2.offline.stage_a import validate_profile_episode

                    validate_profile_episode(root)
                    verify_episode(
                        root, expected_recipe_id=self.spool.recipe["recipe_id"]
                    )
                else:
                    verify_archived_payload_bytes(self.spool, root)
                self._seen[str(root)] = tag
                continue
            self._target_lease(root)
            from g2.offline.stage_a import validate_profile_episode

            manifest = validate_profile_episode(root)
            if root != self.data and (
                root.parent.parent.name != manifest["task_class"]
                or root.name != f"episode_{manifest['episode_id']:06d}"
            ):
                raise CacheError(
                    "published manifest differs from its catalogue location"
                )
            if manifest["output_profile"]["view_vae"]:
                raise CacheError(
                    "independent watcher requires original View-only publications"
                )
            key = f"{manifest['task_class']}/episode_{manifest['episode_id']:06d}"
            if (root / "vae_cache/COMPLETE.json").exists():
                verify_episode(root, expected_recipe_id=self.spool.recipe["recipe_id"])
                self._seen[str(root)] = tag
                self._release(root)
                continue
            if manifest["schema"] == PROFILE_SCHEMA:
                raise CacheError("retired publication has no valid batch cache")
            scan_source(root, view_first=True)
            job = self.spool.register(
                root,
                episode_key=key,
                source_fingerprint=manifest["source_fingerprint"],
                profile_id=manifest["output_profile"]["profile_id"],
            )
            self.spool.offer_source(job)
            self._seen[str(root)] = tag
            known.add(str(root))
            count += 1
            self._new_work = True

    def _refill(self, row):
        """Small verified owner list, not repeated gzip parses per numerical record."""
        from .final_source import load_source
        from .streaming import final_pixel_event

        job = row["id"]
        if job not in self._sources:
            source = load_source(row["target"])
            scope = json.loads(row["scope"])
            if (
                source["source_fingerprint"] != scope["source_fingerprint"]
                or source["profile_id"] != scope["profile_id"]
            ):
                raise CacheError("offered source identity conflicts with job")
            owners = []
            for vid, view in sorted(source["views"].items()):
                for owner in view["owners"]:
                    owners.append(
                        (owner["path"], source["final_pixel_events"][owner["event_id"]])
                    )
            # Deduplicate identical pixels reused by multiple geometry owners.
            self._sources[job] = list(
                {desc["event_id"]: (path, desc) for path, desc in owners}.values()
            )
        with self.spool._db() as db:
            present = {
                r[0] for r in db.execute("SELECT id FROM events WHERE job=?", (job,))
            }
        for relative, desc in self._sources[job]:
            if desc["event_id"] in present:
                continue
            event = final_pixel_event(
                Path(row["target"]) / relative,
                episode_key=desc["episode_key"],
                source_fingerprint=desc["source_fingerprint"],
                profile_id=desc["profile_id"],
                view_id=desc["view_id"],
                canonical_view_id=desc["canonical_view_id"],
                variant=desc["variant"],
                expected_size=desc["size_wh"],
            )
            if event.descriptor() != desc:
                raise CacheError("published PNG changed since source offer")
            try:
                self.spool.enqueue(job, event, timeout_s=0)
            except QueueBackpressure:
                return
            self._new_work = True
        self.spool.seal(job)
        self._sources.pop(job, None)

    def _finish_jobs_parallel(self):
        """Keep admission and GPU batch work progressing while CPU verifies cache.

        One spawned CPU process per sealed Episode performs the original
        build/receipt/reap transaction.  The parent retains the per-Episode
        lease, owns all scheduling, and propagates worker failures fail-closed.
        """
        for job_id, (target, future) in list(self._finalizers.items()):
            if not future.done():
                continue
            try:
                result = future.result()
            except BaseException as exc:
                raise CacheError("CPU finalization failed for " + job_id) from exc
            del self._finalizers[job_id]
            if result["archived"]:
                self._release(target)
                self._new_work = True
        with self.spool._db() as db:
            rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY rowid")]
        for row in rows:
            self._target_lease(row["target"])
            if row["error"]:
                raise CacheError("retained failed episode: " + row["error"])
            if row["id"] in self._finalizers:
                continue
            if row["done"] or (row["sealed"] and self.queue.finalizable(row["id"])):
                if len(self._finalizers) < self.finalize_workers:
                    future = self._finalize_pool.submit(
                        finalize_job,
                        str(self.spool.root),
                        row["id"],
                        self.spool.recipe["recipe_id"],
                    )
                    self._finalizers[row["id"]] = (row["target"], future)
                continue
            if row["source_ready"] and not row["sealed"]:
                self._refill(row)

    def _finish_jobs(self):
        if self._finalize_pool is not None:
            return self._finish_jobs_parallel()
        from .production import build_profile, cache_receipt

        with self.spool._db() as db:
            rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY rowid")]
        for row in rows:
            self._target_lease(row["target"])
            if row["error"]:
                raise CacheError("retained failed episode: " + row["error"])
            if row["done"]:
                if self.spool.reap(row["id"]):
                    self._release(row["target"])
                    self._new_work = True
                continue
            if row["source_ready"] and not row["sealed"]:
                self._refill(row)
                continue
            if not row["sealed"] or not self.queue.finalizable(row["id"]):
                continue
            build_profile(
                row["target"],
                self.encoder,
                preprocessing=self.spool.recipe["preprocessing"],
                storage_dtype="float32",
                resume=True,
                record_provider=lambda vid, record, recipe: self.spool.result(
                    row["id"], vid, record, recipe
                ),
                cleanup=True,
                posthoc=self.spool.view_first,
                _recipe=self.spool.recipe,
            )
            receipt = cache_receipt(row["target"])
            with self.spool._db() as db:
                audit = [
                    dict(batch_id=r["id"], attempts=json.loads(r["attempts"]))
                    for r in db.execute(
                        "SELECT DISTINCT b.id,b.attempts FROM engine_batches b JOIN engine_members m ON m.batch=b.id WHERE m.job=?",
                        (row["id"],),
                    )
                ]
                handoff = dict(
                    schema="g2_batch_verified_cache_handoff_v1",
                    verified_cache=receipt,
                    numerical_executions=audit,
                )
                db.execute(
                    "UPDATE jobs SET done=1,completion_receipt=? WHERE id=?",
                    (json.dumps(handoff, sort_keys=True), row["id"]),
                )
            if self.spool.reap(row["id"]):
                self._release(row["target"])
            self._new_work = True

    def _all_complete(self):
        """Idle is not corpus completion: both pinned scope and publisher signal."""
        if (
            self.expected is None
            or self.producer_done is None
            or not self.producer_done.is_file()
        ):
            return False
        from .builder import verify_episode

        expected, done = read_json(self.expected), read_json(self.producer_done)
        if (
            expected.get("schema") != "g2_vae_expected_episodes_v1"
            or done.get("schema") != "g2_view_publisher_done_v1"
            or done.get("complete") is not True
            or done.get("expected_sha256") != digest(self.expected)
            or done.get("dataset_root") != str(self.data)
            or done.get("failed_episodes") != []
        ):
            raise CacheError("invalid Stage-A-ended/pinned episode scope evidence")
        entries = expected.get("episodes")
        if (
            not isinstance(entries, list)
            or not entries
            or len({e["episode_key"] for e in entries}) != len(entries)
            or done.get("episode_count") != len(entries)
        ):
            raise CacheError("completion scope has missing or duplicate episodes")
        roots = discover_published(
            self.data, tasks=self.tasks or None, episodes=self.episodes or None
        )
        actual = {}
        for root in roots:
            manifest = read_json(root / "episode_manifest.json")
            actual[f"{manifest['task_class']}/episode_{manifest['episode_id']:06d}"] = (
                root,
                manifest["source_fingerprint"],
            )
        if set(actual) != {e["episode_key"] for e in entries}:
            return False
        if any(actual[e["episode_key"]][1] != e["source_fingerprint"] for e in entries):
            raise CacheError("source scope fingerprint differs")
        stats = self.spool.stats()
        if stats["active_jobs"]:
            return False
        for root, _ in actual.values():
            verify_episode(root, expected_recipe_id=self.spool.recipe["recipe_id"])
        return True

    def progress(self, status="RUNNING"):
        result = dict(
            schema=ENGINE_SCHEMA,
            status=status,
            mode=self.mode,
            recipe_id=self.spool.recipe["recipe_id"],
            elapsed_s=self.clock() - self._started,
            spool=self.spool.stats(),
            batch=self.queue.stats(),
            worker_restarts=self._restarts,
            cpu_finalize_workers=self.finalize_workers,
            cpu_finalizing_jobs=len(self._finalizers),
            training_ready=False,
            actual_max_batch_size_per_gpu=self.spec["max_batch_size_per_gpu"],
        )
        atomic_json(self.spool.root / "engine_progress.json", result, replace=True)
        return result

    def _shutdown(self):
        if self._finalize_pool is not None:
            # Let durable archive transactions finish before releasing source
            # leases. Never force-kill an in-flight published cache writer.
            self._finalize_pool.shutdown(wait=True, cancel_futures=True)
            self._finalize_pool = None
            self._finalizers.clear()
        self._stop.set()
        for process in self._processes.values():
            process.join(timeout=self.spec["worker_timeout_s"] + 5)
            if process.is_alive():
                process.terminate()
                process.join(5)
            if process.is_alive():
                process.kill()
                process.join(5)
            if process.exitcode:
                self.queue.expire_dead_worker(process.pid)
        for target in list(self._leases):
            self._release(target)

    def run(self):
        import shutil

        status, old = "FAILED", {}

        def request_stop(signum, frame):
            self._paused = True

        with build_lock(self.spool.root / "engine_coordinator"):
            try:
                self._recover()
                if self.finalize_workers:
                    self._finalize_pool = concurrent.futures.ProcessPoolExecutor(
                        max_workers=self.finalize_workers,
                        mp_context=self._mp,
                        initializer=cpu_initializer,
                        initargs=(self.spec,),
                    )
                for gpu in self.spec["gpus"]:
                    self._spawn(gpu)
                if threading.current_thread() is threading.main_thread():
                    for sig in (signal.SIGTERM, signal.SIGINT):
                        old[sig] = signal.signal(sig, request_stop)
                while True:
                    self._new_work = False
                    self._supervise()
                    if (
                        shutil.disk_usage(self.spool.root).free
                        < self.spec["min_free_disk_bytes"]
                    ):
                        raise CacheError("spool disk low watermark; source retained")
                    if self._paused or (self.stop_file and self.stop_file.exists()):
                        status = (
                            "PAUSED" if self.spool.stats()["active_jobs"] else "DRAINED"
                        )
                        break
                    self._discover()
                    self._finish_jobs()
                    self.queue.collect()
                    stats, batches = self.spool.stats(), self.queue.stats()
                    no_inflight = not (
                        batches["batch_states"].get("running", 0)
                        or batches["batch_states"].get("ready", 0)
                    )
                    pressure = (
                        self.queue.capacity_pressure()
                        if no_inflight and batches["pending_members"]
                        else dict(blocked=False)
                    )
                    self._capacity.observe(
                        self.clock(),
                        blocked=pressure["blocked"],
                        signature=(
                            json.dumps([stats, batches], sort_keys=True),
                            self._new_work,
                        ),
                    )
                    if stats["failed_jobs"] or batches["batch_states"].get("failed", 0):
                        raise CacheError(
                            "failed batches retained; explicit resume required"
                        )
                    if self.mode == "independent" and self._all_complete():
                        status = "ALL_COMPLETE"
                        break
                    busy = bool(
                        stats["active_jobs"]
                        or stats["pending_inputs"]
                        or batches["batch_states"].get("running", 0)
                        or batches["batch_states"].get("ready", 0)
                    )
                    if self.mode == "independent" and self._idle.observe(
                        self.clock(), busy=busy, new_work=self._new_work
                    ):
                        status = "IDLE_TIMEOUT"
                        break
                    if (
                        self.clock() - self._last_progress
                        >= self.spec["discovery_interval_s"]
                    ):
                        self.progress()
                        self._last_progress = self.clock()
                    self._stop.wait(self.spec["poll_interval_s"])
            except BaseException as exc:
                self.progress("FAILED")
                atomic_json(
                    self.spool.root / "engine_error.json",
                    dict(error=str(exc), source_retained=True),
                    replace=True,
                )
                raise
            finally:
                self._shutdown()
                for sig, handler in old.items():
                    signal.signal(sig, handler)
            result = self.progress(status)
            atomic_json(self.spool.root / "engine_result.json", result, replace=True)
            return result
