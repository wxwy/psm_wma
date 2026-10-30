"""CPU-only subprocess boundaries for production Runtime/Worker/HTTP tests.

Not a production launcher. No Cosmos weights/CUDA/RoboCasa/EGL/real DCP. Kernel
byte-stream evidence is explicitly doubled, while the real parser is exercised.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import socket
import time
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["MUJOCO_GL"] = "disable"


def kernel_fixture():
    original = Path.open
    values = {
        "/proc/sys/kernel/random/boot_id": b"432a2285-71d7-4fe4-aad4-aa191c149381\n",
        "/proc/self/timens_offsets": b"monotonic 0 0\nboottime 0 0\n",
    }

    def opened(path, *args, **kwargs):
        if str(path) not in values:
            return original(path, *args, **kwargs)
        mode = args[0] if args else kwargs.get("mode", "r")
        data = values[str(path)]
        return io.BytesIO(data) if "b" in mode else io.StringIO(data.decode("ascii"))

    Path.open = opened


def run_server(argv):
    import threading
    from http.server import ThreadingHTTPServer

    import numpy as np
    import pytest
    import torch
    from PIL import Image

    from cosmos_framework.inference.robocasa_batch_transactions import (
        BatchedSessionTransactions,
    )
    from cosmos_framework.inference.robocasa_session_transactions_test import (
        make_adapter,
    )
    from cosmos_framework.scripts.robocasa_transactions_b1_test import service, server
    from tools.v3.eval_v2_production_tests.native_test import RAW

    parser = argparse.ArgumentParser()
    for name in (
        "checkpoint-path",
        "config-file",
        "port",
        "local-memory-max-sessions",
        "transaction-slot-ids",
        "transaction-run-lease",
        "transaction-manifest-digest",
        "transaction-owner-token-file",
        "transaction-max-batch-size",
        "transaction-batch-wait-ms",
        "transaction-timeout-s",
    ):
        parser.add_argument("--" + name, required=True)
    args, _ = parser.parse_known_args(argv)
    patch = pytest.MonkeyPatch()
    obj = service(patch)
    obj.cfg.seed = 0
    ids = tuple(args.transaction_slot_ids.split(","))
    obj.local_memory_adapter, obj.model = make_adapter(len(ids))

    def decode(value):
        image = Image.open(io.BytesIO(base64.b64decode(value)))
        return torch.from_numpy(np.array(image, copy=True)).permute(2, 0, 1)

    obj.local_memory_adapter.decode_image = decode
    patch.setattr(server, "_decode_base64_png_to_rgb_uint8", decode)
    calls = []

    def generate(batch, **kwargs):
        n = len(batch["prompt"])
        assert len(kwargs["_local_memory_prefixes"]) == n
        calls.append(n)
        if "--cpu-exit-after-live-slots" in argv:
            assert len(ids) == 2 and n == 1
            # Hold the first real B=1 generation, allowing the other HTTP
            # request to enqueue. Observe real leases/tickets without changing
            # the production queue, batch wait, commit or cancellation path.
            limit = time.monotonic() + 20
            while True:
                with obj.transactions._lock:
                    live = [
                        t
                        for t in obj.transactions._tickets.values()
                        if obj.transactions._leases.get(t.lease.slot_id) == t.lease
                        and t.state in ("GENERATING", "QUEUED")
                        and not t.cancelled
                        and obj.transactions.clock() < t.deadline
                    ]
                    tickets = [{**t.lease.identity(), "state": t.state} for t in live]
                if {t["slot_id"] for t in tickets} == set(ids):
                    break
                if time.monotonic() >= limit:
                    raise TimeoutError("CPU Server fault needs two live Slot requests")
                time.sleep(0.01)
            print(
                "CPU_SERVER_FAULT "
                + json.dumps(
                    {"pid": os.getpid(), "native_size": n, "tickets": tickets}
                ),
                flush=True,
            )
            os._exit(23)  # Both owned Slots are active and uncommitted.
        print(
            "CPU_NATIVE_BATCH "
            + json.dumps(
                {
                    "size": n,
                    "prefix_present": [
                        p is not None for p in kwargs["_local_memory_prefixes"]
                    ],
                    "pid": os.getpid(),
                    "model_loads": 1,
                }
            ),
            flush=True,
        )
        action = torch.zeros(1, 17, 64)
        # _denormalize_action minmax maps [-1,1] to [0,1].
        action[:, 1:, :15] = torch.tensor(RAW) * 2 - 1
        return {
            "action": [action.clone() for _ in range(n)],
            "vision": [torch.zeros(1, 3, 1, 8, 8) for _ in range(n)],
        }

    obj.model.generate_samples_from_batch = generate
    obj.transactions = BatchedSessionTransactions(
        obj.local_memory_adapter,
        obj._transaction_batch,
        lambda: None,
        decode_media=obj._transaction_decode_media,
        max_batch_size=int(args.transaction_max_batch_size),
        batch_wait_ms=float(args.transaction_batch_wait_ms),
        owner_token=Path(args.transaction_owner_token_file).read_text(),
        run_lease=args.transaction_run_lease,
        manifest_digest=args.transaction_manifest_digest,
        slot_ids=ids,
        timeout_s=float(args.transaction_timeout_s),
        model_lock=threading.Lock(),
    )
    obj.get_info = lambda: {
        "checkpoint": str((Path(args.checkpoint_path) / "model").resolve()),
        "config_file": str(Path(args.config_file).resolve()),
        "raw_action_dim": 15,
        "action_chunk_size": 16,
        "max_action_dim": 64,
        "num_steps": 2,
        "guidance": 1.0,
        "fps": 20,
        "seed": 0,
        "requires_state": True,
        "local_memory": {"enabled": True, "mode": "required", "action_dim": 15},
        "session_transactions": obj.transactions.info(),
    }
    http = ThreadingHTTPServer(("127.0.0.1", int(args.port)), server._ActionHandler)
    http.service = obj
    print(
        "CPU_MODEL_OWNER_READY " + json.dumps({"pid": os.getpid(), "model_loads": 1}),
        flush=True,
    )
    try:
        http.serve_forever(poll_interval=0.05)
    finally:
        http.server_close()
        obj.transactions.close()
        patch.undo()


def run_sim(argv):
    import numpy as np
    from cosmos_framework.simulation.robocasa import closed_loop_eval as native
    from cosmos_framework.simulation.robocasa.eval_v2_worker import serve
    from tools.v3.eval_v2_production_tests.native_test import Env

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--control-fd", type=int, required=True)
    args = parser.parse_args(argv)
    import hashlib

    raw = args.config.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == args.config_sha256
    cfg = json.loads(raw)
    run = Path(cfg["task_root"]).parents[1]
    events = run / "_internal/cpu_fixture_events"
    events.mkdir(exist_ok=True)
    ready = run / "_internal/cpu_fixture_ready"
    ready.mkdir(exist_ok=True)
    (ready / cfg["physical_slot_id"]).write_text(str(os.getpid()))
    path = events / (cfg["physical_slot_id"] + ".jsonl")
    manifest = json.loads((run / "manifest.json").read_text())
    expected = min(
        len(cfg["tasks"]),
        len(manifest["execution"]["gpu_ids"]) * manifest["execution"]["sims_per_gpu"],
    )

    def log(kind, task, **kwargs):
        with path.open("a") as f:
            f.write(
                json.dumps(
                    {
                        "kind": kind,
                        "pid": os.getpid(),
                        "time": time.monotonic(),
                        "task": task,
                        **kwargs,
                    }
                )
                + "\n"
            )

    native.build_state_token = lambda _: [0.0] * 15

    class FakeEnv(Env):
        def __init__(self, task, grant):
            super().__init__(success_at=32)
            self.task = task
            self.rng = np.random.default_rng(grant["seed"])
            log("make", task, seed=grant["seed"])

        def reset(self):
            self.scene = int(self.rng.integers(0, 2**31))
            log("reset", self.task, scene=self.scene)
            return super().reset()

        def get_ep_meta(self):
            return {
                "lang": "actual " + self.task,
                "layout_id": self.scene,
                "cpu_synthetic": True,
            }

        def step(self, action):
            if self.steps == 0:
                log("execute_begin", self.task)
                limit = time.monotonic() + 120
                while len(list(ready.iterdir())) < expected:
                    if time.monotonic() >= limit:
                        raise TimeoutError(
                            "CPU fixture startup overlap barrier expired"
                        )
                    time.sleep(0.01)
            time.sleep(0.005)
            result = super().step(action)
            if self.steps == 32:
                log("execute_end", self.task)
            return result

        def close(self):
            log("close", self.task)

    serve(
        socket.socket(fileno=args.control_fd),
        cfg,
        factory=lambda task, spec, grant: FakeEnv(task, grant),
    )


def main():
    import sys

    kernel_fixture()
    mode = sys.argv[1]
    if mode == "server":
        run_server(sys.argv[2:])
    elif mode == "sim":
        run_sim(sys.argv[2:])
    else:
        raise ValueError("CPU fixture mode required")


if __name__ == "__main__":
    main()
