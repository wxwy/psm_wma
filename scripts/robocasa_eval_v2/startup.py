"""Finite startup reservations; measurement and process work stay outside locks."""

from __future__ import annotations

import contextlib
import threading


class StartupBudget:
    _MAX_RETRIES = 128

    def __init__(self, cfg, measure):
        self.cfg, self.measure = cfg, measure
        if cfg.get("local_evidence_profile") == "sim_shared_vae":
            self.settings = cfg["sim_shared_vae"]["resources"]
        else:
            self.settings = cfg["streaming_resources"]
        self.lock = threading.Lock()
        self.pending = {}
        self.version = 0
        self.initializers = threading.BoundedSemaphore(
            self.settings["initialization_concurrency"]
        )

    @contextlib.contextmanager
    def reserve(self, key, kind, gpu):
        settings = self.settings
        reservation = (
            settings[f"{kind}_startup_rss_bytes"],
            settings[f"{kind}_startup_gpu_bytes"],
            gpu,
        )
        self._reconcile(key, reservation, complete=False)
        try:
            yield
            self._reconcile(key, reservation, complete=True)
        finally:
            with self.lock:
                # Successful transfer already retired this owner. A reused key
                # must not be removed by the old context's exception cleanup.
                if self.pending.get(key) is reservation:
                    self.pending.pop(key)
                    self.version += 1

    def _reconcile(self, key, reservation, *, complete):
        settings = self.settings
        for _ in range(self._MAX_RETRIES):
            with self.lock:
                version = self.version
            measured = self.measure()
            with self.lock:
                if version != self.version:
                    continue
                if complete:
                    if self.pending.get(key) is not reservation:
                        raise RuntimeError("startup ownership changed")
                    pending = [r for k, r in self.pending.items() if k != key]
                else:
                    if key in self.pending:
                        raise RuntimeError("duplicate startup ownership")
                    pending = [*self.pending.values(), reservation]
                if "owned_gpu_bytes" not in measured or "rss_bytes" not in measured:
                    raise RuntimeError(
                        "BLOCKED_RESOURCE: missing owned resource measurements"
                    )
                if (
                    measured["rss_bytes"] + sum(r[0] for r in pending)
                    > self.cfg["max_rss_bytes"]
                ):
                    raise RuntimeError("BLOCKED_RESOURCE: startup RSS reservation")
                devices = {r[2] for r in [*pending, reservation] if r[2] is not None}
                for device in devices | measured["owned_gpu_bytes"].keys():
                    if device not in measured["owned_gpu_bytes"]:
                        raise RuntimeError(
                            "BLOCKED_RESOURCE: missing selected GPU measurement"
                        )
                    required = measured["owned_gpu_bytes"][device] + sum(
                        r[1] for r in pending if r[2] == device
                    )
                    if required > settings["max_owned_gpu_bytes"]:
                        raise RuntimeError("BLOCKED_RESOURCE: startup GPU reservation")
                # Check + transfer share one metadata lock and epoch. Only the
                # current owner's reservation is replaced by measured usage;
                # all other in-flight promises remain charged.
                if complete:
                    self.pending.pop(key)
                else:
                    self.pending[key] = reservation
                self.version += 1
                return
        raise RuntimeError("BLOCKED_RESOURCE: startup reservation contention")
