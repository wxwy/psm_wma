"""Finite startup reservations; measurement and process work stay outside locks."""

from __future__ import annotations

import contextlib
import threading


class StartupBudget:
    def __init__(self, cfg, measure):
        self.cfg, self.measure = cfg, measure
        self.lock = threading.Lock()
        self.pending = {}
        self.version = 0
        self.initializers = threading.BoundedSemaphore(
            cfg["streaming_resources"]["initialization_concurrency"]
        )

    @contextlib.contextmanager
    def reserve(self, key, kind, gpu):
        settings = self.cfg["streaming_resources"]
        reservation = (
            settings[f"{kind}_startup_rss_bytes"],
            settings[f"{kind}_startup_gpu_bytes"],
            gpu,
        )
        while True:
            with self.lock:
                version = self.version
            measured = self.measure()
            if "owned_gpu_bytes" not in measured or "rss_bytes" not in measured:
                raise RuntimeError(
                    "BLOCKED_RESOURCE: missing owned resource measurements"
                )
            with self.lock:
                if version != self.version:
                    continue
                if key in self.pending:
                    raise RuntimeError("duplicate startup ownership")
                pending = [*self.pending.values(), reservation]
                if (
                    measured["rss_bytes"] + sum(r[0] for r in pending)
                    > self.cfg["max_rss_bytes"]
                ):
                    raise RuntimeError("BLOCKED_RESOURCE: startup RSS reservation")
                for device in {r[2] for r in pending if r[2] is not None}:
                    if device not in measured["owned_gpu_bytes"]:
                        raise RuntimeError(
                            "BLOCKED_RESOURCE: missing selected GPU measurement"
                        )
                    required = measured["owned_gpu_bytes"][device] + sum(
                        r[1] for r in pending if r[2] == device
                    )
                    if required > settings["max_owned_gpu_bytes"]:
                        raise RuntimeError("BLOCKED_RESOURCE: startup GPU reservation")
                self.pending[key] = reservation
                self.version += 1
                break
        try:
            yield
            self.measure()  # Real post-start footprint must pass before reservation transfer.
        finally:
            with self.lock:
                self.pending.pop(key)
                self.version += 1
