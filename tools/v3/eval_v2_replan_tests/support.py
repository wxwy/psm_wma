"""Actual dispatcher/actor/client with synthetic model output and CPU kernel files."""

import ast
import base64
import io
import json
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest
from cosmos_framework.inference import robocasa_session_transactions as transactions
from cosmos_framework.inference.robocasa_batch_transactions import (
    BatchedSessionTransactions,
    BatchOutput,
    MediaCandidate,
)
from cosmos_framework.simulation.robocasa.eval_v2_transactions import PolicyTransport
from PIL import Image

RAW = [0.2, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.5]
CHILD = Path(__file__).resolve().parents[3] / "cosmos-framework"


@pytest.fixture
def clock_kernel(monkeypatch):
    """Explicit file double; real production parser still checks the clock domain."""
    original = transactions.Path.open
    records = {
        "/proc/sys/kernel/random/boot_id": b"432a2285-71d7-4fe4-aad4-aa191c149381\n",
        "/proc/self/timens_offsets": b"monotonic 0 0\nboottime 0 0\n",
    }

    def kernel_open(path, *args, **kwargs):
        if str(path) in records:
            return io.BytesIO(records[str(path)])
        return original(path, *args, **kwargs)

    monkeypatch.setattr(transactions.Path, "open", kernel_open)


def png_frames():
    value = []
    for color in ("red", "green", "blue"):
        stream = io.BytesIO()
        Image.new("RGB", (32, 32), color).save(stream, format="PNG")
        value.append(base64.b64encode(stream.getvalue()).decode())
    return value


def production_function(name, namespace=None):
    """Compile the exact production function, excluding model/CUDA import setup."""
    source = CHILD / "cosmos_framework/scripts/action_policy_server_robocasa.py"
    tree = ast.parse(source.read_text())
    node = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name
    )
    scope = dict(
        Reply=transactions.Reply,
        json_bytes=transactions.json_bytes,
        strict_json=transactions.strict_json,
        transaction_capacity=transactions.transaction_capacity,
    )
    scope.update(namespace or {})
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), scope)
    return scope[name]


class Response:
    def __init__(self, reply):
        self.status_code, self.reply = reply.status, reply

    def json(self):
        return self.reply.json()


class Direct:
    def __init__(self, service):
        self.service, self.calls = service, []
        self.dispatch = production_function("transaction_dispatch")

    def request(self, method, url, **kwargs):
        path = urlsplit(url).path
        self.calls.append((method, path, kwargs))
        return Response(
            self.dispatch(
                self.service, method, path, kwargs.get("json"), kwargs.get("headers")
            )
        )


@pytest.fixture
def systems(clock_kernel):
    owned = []

    def make(**kwargs):
        frames = png_frames()
        service = SimpleNamespace(calls=[], transactions=None)

        def generate(payloads, updates):
            service.calls.extend(payloads)
            return BatchOutput(
                [[list(RAW) for _ in range(16)] for _ in payloads],
                tuple(MediaCandidate(frames, 4096) for _ in payloads),
            )

        options = dict(
            owner_token="cpu-owner",
            run_lease="run",
            manifest_digest="a" * 64,
            slot_ids=tuple(f"slot{i}" for i in range(8)),
            timeout_s=5,
            max_batch_size=1,
            batch_wait_ms=1,
            decode_media=lambda value: value,
            media_drain_timeout_s=10,
        )
        options.update(kwargs)
        actor = BatchedSessionTransactions(
            SimpleNamespace(mode="off", memory=None), generate, lambda: None, **options
        )
        service.transactions = actor
        owned.append(actor)
        return service, actor, Direct(service)

    yield make
    for actor in owned:
        assert actor.close(timeout_s=3), "CPU actor did not quiesce"


def registration(direct, slot=0, generation=1):
    return direct.request(
        "POST",
        "http://cpu/v2/session/register",
        headers={"X-Cosmos-Owner": "cpu-owner"},
        json={
            "run_lease": "run",
            "manifest_digest": "a" * 64,
            "slot_id": f"slot{slot}",
            "generation": generation,
            "task": "CloseFridge",
            "episode_index": 0,
            "attempt_id": f"attempt-{generation}",
        },
    ).json()


def client(direct, assignment, mode="all", **kwargs):
    settings = dict(
        server_url="http://cpu",
        predict_timeout_s=5,
        max_infer_batch_size=1,
        execution_profile="phase_b",
        local_memory_mode="off",
        save_generated_video=mode,
        media_drain_timeout_s=5,
        encoder_grace_s=0.1,
        save_rollout_mp4=False,
        horizon=160,
    )
    settings.update(kwargs)
    value = PolicyTransport(
        settings,
        assignment,
        time.monotonic() + 30,
        transport=direct,
        media_transport=direct,
    )
    return value


def payload():
    return dict(
        image="synthetic",
        prompt="close the fridge",
        domain_name="robocasa",
        image_size=256,
        state=[0.0] * 15,
    )


def predict(value):
    return value.post(value.base + "/predict", json=payload(), timeout=5).json()


def reserved(direct, actor, assignment, *, frontier=0, replan=0):
    lease = assignment["lease"]
    request = payload()
    request["inference"] = {
        "session_id": lease["session_id"],
        "episode_id": lease["episode_id"],
        "request_index": frontier,
    }
    request["media"] = {"replan": replan, "required": True}
    key = transactions.digest(
        {
            "protocol": actor.protocol,
            **{k: v for k, v in lease.items() if k != "capability"},
            "frontier": frontier,
        }
    )
    sha = transactions.digest(request)
    record = dict(
        lease=lease,
        request_key=key,
        payload_sha256=sha,
        replan=replan,
        frontier=frontier,
    )
    return (
        direct.request("POST", "http://cpu/v2/media/reserve", json=record),
        request,
        record,
    )


@contextmanager
def http_server(service, before=None):
    dispatch = production_function("transaction_dispatch")
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def handle_request(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            record = json.loads(raw) if raw else None
            calls.append((self.command, self.path, record))
            if before:
                before(self.command, self.path, record)
            try:
                reply = dispatch(
                    service, self.command, self.path, record, dict(self.headers)
                )
            except (ValueError, RuntimeError) as error:
                reply = transactions.Reply(
                    400, transactions.json_bytes({"error": str(error)})
                )
            self.send_response(reply.status)
            self.send_header("Content-Length", str(len(reply.body)))
            self.end_headers()
            self.wfile.write(reply.body)

        do_POST = do_GET = handle_request

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)
        assert not thread.is_alive()
