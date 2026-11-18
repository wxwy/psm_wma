"""One resident batch encoder process per GPU, using the existing numeric writer."""

from __future__ import annotations

import importlib
import json
import os
import signal
import threading
import time
import uuid

from g2.io import digest

from .batch_contract import record_path, unpack_prep
from .batch_queue import BatchQueue
from .contract import CacheError, contained, fingerprint
from .storage import (
    _fsync_directory,
    _load,
    build_lock,
    inspect_view_payload,
    write_view_payload,
)
from .streaming import EventSpool, _chunk_metadata, validate_chunk


def encoder_factory(spec):
    test_factory = spec.get("_test_encoder_factory")
    if test_factory:
        module, name = test_factory.split(":", 1)
        encoder = getattr(importlib.import_module(module), name)(
            **spec.get("_test_encoder_args", {})
        )
        if not encoder.descriptor().get("test_only"):
            raise CacheError("private CPU factory must be explicitly test-only")
        return encoder
    from .batch_encoding import WanBatchEncoder

    return WanBatchEncoder(
        spec["weights"],
        cosmos_root=spec["cosmos_root"],
        device="cuda:0",
        max_batch_size=spec["max_batch_size_per_gpu"],
    )


def device_identity(encoder, physical_gpu):
    if encoder.descriptor().get("test_only"):
        return dict(kind="TEST_ONLY_CPU", name="FAKE_NO_GPU", uuid="TEST_ONLY")
    import torch

    properties = torch.cuda.get_device_properties(0)
    return dict(
        kind="cuda",
        name=properties.name,
        uuid=str(properties.uuid),
        capability=[properties.major, properties.minor],
        total_bytes=properties.total_memory,
        physical_gpu=str(physical_gpu),
    )


def _point(spool, phase, requested):
    if requested != phase:
        return
    marker = spool.root / ".isolated-test-crash-once"
    try:
        fd = os.open(
            marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
    except FileExistsError:
        return
    with os.fdopen(fd, "w") as f:
        f.write(phase + "\n")
        f.flush()
        os.fsync(f.fileno())
    _fsync_directory(marker.parent)
    os._exit(77)


def execute_claim(queue, encoder, claim, *, physical_gpu, crash_once=None):
    """Fsync each immutable record before ACK; never replace a replay value."""
    from io import BytesIO

    import numpy as np
    import torch
    from PIL import Image

    from .streaming import FinalPixelEvent, validate_event

    spool = queue.spool
    context = claim["context"]
    batch = context["batch_id"]
    started = time.perf_counter()
    if encoder.descriptor() != spool.recipe["encoder"]:
        raise CacheError("worker encoder differs from the shared numerical recipe")
    with build_lock(spool.root / "batch_locks" / batch):
        queue.fence(batch, claim["token"])
        paths = [
            contained(spool.root, record_path(context, p), allow_missing=True)
            for p in range(len(context["members"]))
        ]
        # A killed atomic writer can leave only its own temporary file. The
        # per-batch lock and fenced context make this cleanup exclusive.
        directory = paths[0].parent
        if directory.exists():
            for tmp in directory.iterdir():
                if tmp.name.startswith(".view-") and tmp.name.endswith(".tmp"):
                    if tmp.is_symlink() or not tmp.is_file():
                        raise CacheError("untrusted numeric temporary input")
                    tmp.unlink()
                    _fsync_directory(directory)
        existing = {}
        for position, path in enumerate(paths):
            if path.exists():
                info = inspect_view_payload(path)
                validate_chunk(
                    info, context["members"][position]["event"], spool.recipe
                )
                prep = unpack_prep(info["metadata"], 0)
                if (
                    prep["_batch_context"] != context
                    or prep["numerical_execution"]["position"] != position
                ):
                    raise CacheError(
                        "existing chunk belongs to a different batch numerical context"
                    )
                existing[position] = info
        produced = None
        encode_s = 0.0
        if len(existing) != len(paths):
            images = []
            for member, raw in zip(
                context["members"], queue.inputs(claim), strict=True
            ):
                desc = member["event"]
                event = FinalPixelEvent(
                    png_bytes=raw,
                    **{k: tuple(v) if k == "size_wh" else v for k, v in desc.items()},
                )
                validate_event(event)
                with Image.open(BytesIO(raw)) as image:
                    images.append(np.array(image, copy=True))
            queue.native_attempt(claim)
            tick = time.perf_counter()
            produced = encoder.encode_batch(images, spool.recipe["preprocessing"])
            encode_s = time.perf_counter() - tick
            queue.native_attempt(claim, getattr(encoder, "last_metrics", {}))
            if len(produced) != len(paths):
                raise CacheError("batch returned the wrong member count")
            # Compare every previously fsynced value before publishing any missing row.
            for position, info in existing.items():
                value, _, _ = _load(paths[position])
                if not torch.equal(value["latents"][0], produced[position][0]):
                    raise CacheError(
                        "same-context replay changed a persisted value; no silent replacement"
                    )
        origin = dict(
            worker=claim["worker"],
            attempt=claim["token"],
            physical_gpu=str(physical_gpu),
            device=device_identity(encoder, physical_gpu),
            encoder_descriptor_sha256=fingerprint(spool.recipe["encoder"]),
        )
        io_started = time.perf_counter()
        for position, path in enumerate(paths):
            queue.fence(batch, claim["token"])
            if position in existing:
                info = existing[position]
            else:
                latent, prep = produced[position]
                if (
                    type(latent) is not torch.Tensor
                    or latent.device.type != "cpu"
                    or latent.dtype != torch.float32
                    or list(latent.shape) != [48, 16, 16]
                    or not torch.isfinite(latent).all()
                ):
                    raise CacheError(
                        "worker accepts only the finite full FP32 spatial grid"
                    )
                prep = dict(
                    prep,
                    _batch_context=context,
                    numerical_execution=dict(
                        batch_id=batch,
                        position=position,
                        actual_batch_size=len(paths),
                        origin=origin,
                    ),
                )
                info = write_view_payload(
                    path,
                    _chunk_metadata(
                        context["members"][position]["event"], spool.recipe, prep
                    ),
                    latent.unsqueeze(0),
                )
                if info["bytes"] > claim["reserved_bytes"] // len(paths):
                    raise CacheError(
                        "numeric file exceeds its finite reservation; input retained"
                    )
            _point(spool, "numeric_fsynced", crash_once)
            validate_chunk(info, context["members"][position]["event"], spool.recipe)
            if digest(path) != info["sha256"]:
                raise CacheError("numeric chunk changed before ACK")
            queue.ack(claim, position, info["sha256"])
            _point(spool, f"after_ack:{position}", crash_once)
        # Revalidate every persisted chunk before releasing any replay input.
        for position, path in enumerate(paths):
            info = inspect_view_payload(path)
            validate_chunk(info, context["members"][position]["event"], spool.recipe)
            with spool._db() as db:
                member = context["members"][position]
                expected = db.execute(
                    "SELECT result_sha FROM events WHERE job=? AND id=?",
                    (member["job"], member["event"]["event_id"]),
                ).fetchone()
            if expected is None or expected[0] != info["sha256"]:
                raise CacheError("numeric bytes changed before whole-batch commit")
        metric = getattr(encoder, "last_metrics", {}) if produced is not None else {}
        queue.complete(
            claim,
            dict(
                encode_seconds=encode_s,
                io_ack_seconds=time.perf_counter() - io_started,
                peak_allocated_bytes=metric.get("peak_allocated_bytes", 0),
                peak_reserved_bytes=metric.get("peak_reserved_bytes", 0),
            ),
        )
        return dict(
            batch_id=batch,
            actual_batch_size=len(paths),
            native_input_shape=context["input_shape"],
            reused_files=len(existing),
            native_called=produced is not None,
            encode_seconds=encode_s,
            wall_seconds=time.perf_counter() - started,
            metrics=metric,
        )


def worker_main(spool_root, spec, physical_gpu, stop_event, parent_pid):
    # Spawn imports this module without importing Torch; bind CUDA first.
    os.environ.update(
        CUDA_VISIBLE_DEVICES=str(physical_gpu),
        COSMOS_DEVICE="cuda",
        COSMOS_TRAINING="0",
        COSMOS_INTERNAL="0",
        PYTHONDONTWRITEBYTECODE="1",
        CUBLAS_WORKSPACE_CONFIG=":4096:8",
    )
    try:
        import ctypes

        if os.name == "posix":
            ctypes.CDLL(None).prctl(1, signal.SIGTERM)
    except (AttributeError, OSError):
        pass
    if os.getppid() != parent_pid:
        return
    spool = EventSpool.open(spool_root)
    queue = BatchQueue(
        spool, lease_s=spec["lease_s"], batch_wait_ms=spec["batch_wait_ms"]
    )
    encoder = encoder_factory(spec)
    worker = uuid.uuid4().hex
    queue.register_worker(worker, physical_gpu)
    current, halted = {}, threading.Event()
    errors = []

    def heartbeat():
        while not halted.wait(spec["heartbeat_s"]):
            if os.getppid() != parent_pid:
                os._exit(78)
            try:
                value = current.copy()
                queue.heartbeat(worker, value.get("batch"), value.get("token"))
            except Exception as exc:
                errors.append(str(exc))
                return

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    logs = spool.root / "worker_logs"
    logs.mkdir(exist_ok=True)
    try:
        with (logs / f"{worker}.jsonl").open("a") as log:
            # Do not let the first spawned process drain the queue before the
            # remaining devices have registered. No GPU/model work is locked.
            ready_deadline = time.monotonic() + spec["worker_timeout_s"]
            while not stop_event.is_set():
                with spool._db() as db:
                    ready = {
                        r[0]
                        for r in db.execute(
                            "SELECT DISTINCT gpu FROM engine_workers WHERE state!='stopped' AND seen>=?",
                            (time.time() - spec["lease_s"],),
                        )
                    }
                if ready >= {str(g) for g in spec["gpus"]}:
                    break
                if time.monotonic() > ready_deadline:
                    raise CacheError("GPU worker registration timed out")
                stop_event.wait(spec["poll_interval_s"])
            while not stop_event.is_set() and not errors:
                claim = queue.claim(worker)
                if claim is None:
                    stop_event.wait(spec["poll_interval_s"])
                    continue
                current.update(batch=claim["context"]["batch_id"], token=claim["token"])
                try:
                    result = execute_claim(
                        queue,
                        encoder,
                        claim,
                        physical_gpu=physical_gpu,
                        crash_once=spec.get("test_crash_once"),
                    )
                    log.write(
                        json.dumps(
                            dict(
                                result,
                                worker=worker,
                                physical_gpu=str(physical_gpu),
                                test_only=bool(encoder.descriptor().get("test_only")),
                            ),
                            sort_keys=True,
                        )
                        + "\n"
                    )
                    log.flush()
                    os.fsync(log.fileno())
                except BaseException as exc:
                    queue.fail(claim, str(exc))
                    log.write(
                        json.dumps(
                            dict(
                                batch_id=claim["context"]["batch_id"],
                                error=str(exc),
                                worker=worker,
                            ),
                            sort_keys=True,
                        )
                        + "\n"
                    )
                    log.flush()
                    return
                finally:
                    current.clear()
    finally:
        halted.set()
        thread.join(timeout=spec["heartbeat_s"] + 1)
        with spool._db() as db:
            db.execute(
                "UPDATE engine_workers SET state='stopped',seen=0 WHERE id=?", (worker,)
            )
