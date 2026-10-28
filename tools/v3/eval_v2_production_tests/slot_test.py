"""Phase A lifecycle with real native policy/HTTP/Local codecs and fake physics."""

import hashlib
from pathlib import Path
from cosmos_framework.evaluation.robocasa_v2.store import Store
from types import SimpleNamespace

import pytest
from cosmos_framework.evaluation.robocasa_v2.contract import result_record
from cosmos_framework.simulation.robocasa.eval_v2_slot import SimSlot
from robocasa_eval_v2.runtime import Runtime

from tools.v3.eval_v2_production_tests.native_test import Env, native, server
from tools.v3.eval_v2_production_tests.store_test import fresh


def slot_config(value, physical_slot_id, url):
    specs = {}
    for task in value.manifest["tasks"]:
        path = value.root.parent / "metadata" / task / "extras/dataset_meta.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"env_args":{"env_name":"' + task + '"}}')
        specs[task] = {
            "dataset_dir": str(path.parent.parent),
            "metadata_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "horizon": value.manifest["horizons"][task],
        }
    return {
        "tasks": specs,
        "task_root": str(value.root / "_internal/tasks"),
        "manifest_digest": value.manifest["digest"],
        "coordinator_lease_id": value.lease_id,
        "episodes_per_task": value.manifest["episodes_per_task"],
        "physical_slot_id": physical_slot_id,
        "settings": {
            "server_url": url,
            "predict_timeout_s": 2.0,
            "save_rollout_mp4": False,
            "save_generated_video": "none",
        },
    }


class TrackedEnv(Env):
    def __init__(self, task, seed, events, **kwargs):
        super().__init__(**kwargs)
        self.task, self.seed, self.events = task, seed, events
        import numpy as np

        self.rng = np.random.default_rng(seed)
        self.scenes = []
        events.append(("make", task, seed))

    def reset(self):
        self.events.append(("reset", self.task, self.seed))
        self.scenes.append(int(self.rng.integers(0, 2**31)))
        return super().reset()

    def get_ep_meta(self):
        return {
            "lang": "actual " + self.task,
            "layout_id": self.scenes[-1],
            "style_id": self.seed,
            "fixture": "CPU faithful fixture",
        }

    def close(self):
        self.events.append(("close", self.task, self.seed))


class CpuActor:
    def __init__(self, slot, pid):
        self.slot = slot
        self.owned = SimpleNamespace(
            proc=SimpleNamespace(pid=pid, poll=lambda: None), pgid=pid
        )
        self.record = {"cpu_owned_process_double": pid}
        self.channel = SimpleNamespace(shutdown=lambda *a: None)

    def request(self, op, *, deadline=None, **kwargs):
        if op == "start_episode":
            return self.slot.start_episode(
                kwargs["attempt"],
                grant=kwargs.get("grant"),
                health_only=kwargs.get("health_only", False),
            )
        if op == "initialize":
            return self.slot.initialize()
        if op == "execute":
            return self.slot.execute(
                kwargs["attempt"],
                reset_index=kwargs["reset_index"],
                directory=kwargs["directory"],
            )
        if op == "finish_without_session":
            return self.slot.finish_without_session()
        raise ValueError(op)

    def close(self):
        value = self.slot.close()
        return dict(value, close_error=None if value["clean"] else "quarantined Slot")


class CpuSlotRuntime(Runtime):
    """Only physical process/GPU/model boundaries are doubles, not Slot behavior."""

    def __init__(self, value, cfg, url, events, *, factory=None):
        super().__init__(value, cfg, {}, {}, resource_probe=lambda *a, **kw: None)
        self.url, self.events = url, events
        self.factory = factory
        self.server_loads = set()
        self.max_actors = 0

    def _actor(self, claim):
        worker = claim["physical_worker"]
        with self.setup_lock:
            if worker not in self.actors:
                self.server_loads.add(worker)
                slot = SimSlot(
                    slot_config(self.store, self.slot_ids[worker], self.url),
                    factory=self.factory
                    or (
                        lambda t, s, g: TrackedEnv(
                            t,
                            g["seed"],
                            self.events,
                            success_at=100 if t == "TaskA" else 1,
                        )
                    ),
                )
                self.actors[worker] = CpuActor(slot, 80000 + self.workers.index(worker))
                self.max_actors = max(self.max_actors, len(self.actors))
            return self._start_assignment(
                claim, self.actors[worker], {"CPU_model_server": worker}
            )


def prepare_monkey(monkeypatch):
    monkeypatch.setattr(native, "build_state_token", lambda _: [0.0] * 15)
    monkeypatch.setattr(
        "robocasa_eval_v2.runtime.identity.guard", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        "robocasa_eval_v2.runtime.group_members", lambda pgid: {pgid: "S"}
    )


def execute(slot, value, task, ep, *, grant=None):
    if task not in value.active_tasks:
        value.begin_task(task)
    a = value.begin_episode(task, ep)
    slot.start_episode(a, grant=grant)
    value.begin_initialization(a)
    response = slot.initialize()
    assert response["initial_success"] is False
    value.initialization_outcome(a, initial_success=False)
    value.bind_sampling(a, response["sampling"])
    directory = value._ledger(task, ep) / "work" / a["attempt_id"]
    result = slot.execute(
        a, reset_index=value.events(a)[-1]["data"]["reset_index"], directory=directory
    )
    row = result_record(
        value.manifest,
        task=task,
        episode=ep,
        generation=a["generation"],
        stream_id=a["stream_id"],
        attempt_id=a["attempt_id"],
        worker_id=a["worker_id"],
        seed=a["seed"],
        reset_index=value.events(a)[-1]["data"]["reset_index"],
        observation=result["observation"],
        instruction=result["instruction"],
        replans=result["replans"],
        elapsed_seconds=result["elapsed_seconds"],
        sampling=result["sampling"],
    )
    value.commit(row, staging=directory)
    return result, a


def test_reusable_slot_switch_order_unique_sessions_seed_and_same_task_reuse(
    tmp_path, monkeypatch
):
    prepare_monkey(monkeypatch)
    value = fresh(tmp_path, tasks=("TaskA", "TaskB"), episodes=3)
    events = []
    with server() as (url, calls), value.locked():
        value.begin_task("TaskA")
        value.begin_task("TaskB")
        slot = SimSlot(
            slot_config(value, "1" * 32, url),
            factory=lambda t, s, g: TrackedEnv(t, g["seed"], events),
        )
        sessions = []
        seeds = []
        for t, ep in [("TaskA", 0), ("TaskB", 0), ("TaskA", 1), ("TaskA", 2)]:
            grant = value.allocate_environment(t, "1" * 32) if slot.task != t else None
            result, a = execute(slot, value, t, ep, grant=grant)
            sessions.append(result["local_session"])
            seeds.append(result["sampling"])
            assert (
                result["instruction"] == "actual " + t
                and result["slot_state"] == "CLEAN"
            )
            assert "SESSION_CLOSING" in slot.history
        assert (
            len({s["session_id"] for s in sessions})
            == len({s["episode_id"] for s in sessions})
            == 4
        )
        assert all(s["start_frontier"] == 0 and s["reset_ack"] for s in sessions)
        assert seeds[0]["actual_seed"] != seeds[2]["actual_seed"]
        assert seeds[2]["environment_id"] == seeds[3]["environment_id"]
        assert (
            seeds[3]["environment_reset_index"]
            == seeds[2]["environment_reset_index"] + 1
        )
        assert [(e[0], e[1]) for e in events] == [
            ("make", "TaskA"),
            ("reset", "TaskA"),
            ("close", "TaskA"),
            ("make", "TaskB"),
            ("reset", "TaskB"),
            ("close", "TaskB"),
            ("make", "TaskA"),
            ("reset", "TaskA"),
            ("reset", "TaskA"),
        ]
        requests = [c["local_memory"] for c in calls if "local_memory" in c]
        assert all(
            m["reset"] is True and m["consumer_step"] == 0 and not m["evidence"]
            for m in requests
        )
        assert len([c for c in calls if c.get("_local_memory_command") == "reset"]) == 4
        slot.close()


@pytest.mark.parametrize("failure", ["reset_ack", "predicate", "media_cleanup"])
def test_local_or_runtime_failure_quarantines_slot_without_reuse(
    tmp_path, monkeypatch, failure
):
    prepare_monkey(monkeypatch)
    value = fresh(tmp_path, tasks=("TaskA", "TaskB"), episodes=1)
    events = []
    with server(reset_failure=failure == "reset_ack") as (url, calls), value.locked():
        value.begin_task("TaskA")
        value.begin_task("TaskB")
        slot = SimSlot(
            slot_config(value, "1" * 32, url),
            factory=lambda t, s, g: TrackedEnv(
                t, g["seed"], events, predicate_error=failure == "predicate"
            ),
        )
        if failure == "media_cleanup":
            from tools.v3.eval_v2_production_tests.native_test import BadMedia

            class Unsafe(BadMedia):
                def close(self):
                    return {"forced_encoder_cleanup": True}

            # Install only after start_episode creates the adapter below.
            grant = value.allocate_environment("TaskA", "1" * 32)
            a = value.begin_episode("TaskA", 0)
            slot.start_episode(a, grant=grant)
            slot.engine.media_factory = Unsafe
            value.begin_initialization(a)
            slot.initialize()
            value.initialization_outcome(a, initial_success=False)
            result = slot.execute(
                a,
                reset_index=0,
                directory=value._ledger("TaskA", 0) / "work" / a["attempt_id"],
            )
            assert (
                result["observation"]["outcome"] == "success"
                and result["media_process_fault"]
            )
        else:
            with pytest.raises(RuntimeError):
                execute(
                    slot,
                    value,
                    "TaskA",
                    0,
                    grant=value.allocate_environment("TaskA", "1" * 32),
                )
        assert slot.state == "FAILED_QUARANTINED"
        with pytest.raises(RuntimeError, match="not clean"):
            slot.start_episode(
                value.begin_episode("TaskB", 0),
                grant=value.allocate_environment("TaskB", "1" * 32),
            )
        assert not any(e[:2] == ("make", "TaskB") for e in events)
        slot.close()


@pytest.mark.parametrize("which", ["metadata", "grant", "task", "attempt"])
def test_slot_rejects_foreign_task_seed_grant_or_stale_attempt_before_reset(
    tmp_path, which
):
    value = fresh(tmp_path, episodes=2)
    events = []
    with value.locked():
        value.begin_task("CloseFridge")
        a = value.begin_episode("CloseFridge", 0)
        conf = slot_config(value, "1" * 32, "http://unused")
        grant = value.allocate_environment("CloseFridge", "1" * 32)
        slot = SimSlot(conf, factory=lambda t, s, g: TrackedEnv(t, g["seed"], events))
        if which == "metadata":
            path = (
                Path(conf["tasks"]["CloseFridge"]["dataset_dir"])
                / "extras/dataset_meta.json"
            )
            path.write_text("changed")
        elif which == "grant":
            grant = dict(grant, seed=grant["seed"] + 1)
        elif which == "task":
            a = dict(a, task="Unknown")
        else:
            slot.start_episode(a, grant=grant)
            # A real no-Session rejection is required before releasing this claim.
            slot.env.initial = True
            slot.initialize()
            slot.finish_without_session()
        with pytest.raises((ValueError, RuntimeError)):
            slot.start_episode(a, grant=grant)
        assert (
            not any(x[0] == "reset" for x in events)
            if which != "attempt"
            else len([x for x in events if x[0] == "reset"]) == 1
        )
        slot.close()


def test_seed_grant_resume_never_reuses_abandoned_creation_seed(tmp_path):
    value = fresh(tmp_path, episodes=1)
    with value.locked():
        value.begin_task("CloseFridge")
        a = value.allocate_environment("CloseFridge", "1" * 32)
        from tools.v3.eval_v2_production_tests.store_test import close_streams

        close_streams(value, "CloseFridge")
    with Store(value.root, value.manifest).locked() as resumed:
        resumed.begin_task("CloseFridge")
        b = resumed.allocate_environment("CloseFridge", "2" * 32)
        assert b["ordinal"] == a["ordinal"] + 1 and b["seed"] != a["seed"]


@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("three_then_legal", "admitted"),
        ("four_errors", "skipped_init_error"),
        ("initial_success", "admitted"),
    ],
)
def test_actual_slot_initialization_gate_opens_no_session_until_legal(
    tmp_path, monkeypatch, pattern, expected
):
    prepare_monkey(monkeypatch)
    value = fresh(tmp_path, episodes=1)
    events = []

    class RandomizationError(Exception):
        pass

    RandomizationError.__module__ = "robosuite.utils.errors"

    class InitEnv(TrackedEnv):
        def reset(self):
            self.events.append(("reset", self.task, self.seed))
            self.resets += 1
            self.steps = 0
            if (
                pattern == "three_then_legal" and self.resets <= 3
            ) or pattern == "four_errors":
                raise RandomizationError("CPU sampler rejected")
            self.initial = pattern == "initial_success" and self.resets < 3
            return self.obs

    with server() as (url, calls), value.locked():
        value.begin_task("CloseFridge")
        a = value.begin_episode("CloseFridge", 0)
        slot = SimSlot(
            slot_config(value, "1" * 32, url),
            factory=lambda t, s, g: InitEnv(t, g["seed"], events),
        )
        slot.start_episode(a, grant=value.allocate_environment("CloseFridge", "1" * 32))
        while True:
            value.begin_initialization(a)
            response = slot.initialize()
            assert not calls and slot.state == "ADMISSION"
            if response.get("error"):
                state = value.initialization_outcome(
                    a,
                    error=RandomizationError("CPU sampler rejected"),
                    stage=response["stage"],
                    safe_to_retry=response["safe_to_retry"],
                )
            else:
                state = value.initialization_outcome(
                    a, initial_success=response["initial_success"]
                )
            if state["status"] in ("admitted", "skipped_init_error"):
                break
        assert state["status"] == expected
        if expected == "skipped_init_error":
            assert slot.finish_without_session()["state"] == "CLEAN"
        else:
            with pytest.raises(RuntimeError):
                slot.finish_without_session()
        slot.close()


def test_fresh_session_starts_W0_then_completed_evidence_updates_only_it(
    tmp_path, monkeypatch
):
    # Faithful CPU server state model, not a claim about GPU Local-TTT numerics.
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest
    from tools.v3.eval_v2_production_tests.contract_test import manifest
    from tools.v3.eval_v2_production_tests.native_test import RAW

    prepare_monkey(monkeypatch)
    m = manifest(("TaskA", "TaskB"), 2)
    m = build_manifest(
        tasks=m["tasks"],
        episodes=2,
        seed=m["seed"],
        horizons={t: 17 for t in m["tasks"]},
        experiment=m["experiment"],
    )
    value = Store(tmp_path / "state_audit", m)
    value.create()
    weights = {}
    starts = []
    updates = []
    events = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            x = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if x.get("_local_memory_command") == "reset":
                weights.pop(x["session_id"])
                response = {
                    "local_memory": {"status": "reset", "session_id": x["session_id"]}
                }
            else:
                v = x["local_memory"]
                sid = v["session_id"]
                if v["reset"]:
                    assert (
                        sid not in weights
                        and v["consumer_step"] == 0
                        and not v["evidence"]
                    )
                    weights[sid] = 0
                    starts.append((sid, 0))
                weights[sid] += len(v["evidence"])
                if v["evidence"]:
                    updates.append((sid, weights[sid]))
                response = {
                    "action": [RAW] * 16,
                    "local_memory": {
                        k: v[k] for k in ("session_id", "episode_id", "consumer_step")
                    },
                }
            raw = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *a):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        with value.locked():
            value.begin_task("TaskA")
            value.begin_task("TaskB")
            slot = SimSlot(
                slot_config(value, "1" * 32, f"http://127.0.0.1:{http.server_port}"),
                factory=lambda t, s, g: TrackedEnv(t, g["seed"], events, success_at=17),
            )
            for task, ep in [("TaskA", 0), ("TaskB", 0), ("TaskA", 1)]:
                execute(
                    slot,
                    value,
                    task,
                    ep,
                    grant=value.allocate_environment(task, "1" * 32),
                )
                assert not weights and slot.state == "CLEAN"
            assert len(starts) == len(updates) == 3 and len({x[0] for x in starts}) == 3
            assert all(x[1] == 16 for x in updates)
            slot.close()
    finally:
        http.shutdown()
        http.server_close()
        thread.join(2)


@pytest.mark.parametrize("field", ["lease_id", "worker_id", "seed", "attempt_id"])
def test_slot_verifies_persisted_claim_before_any_environment_creation(tmp_path, field):
    value = fresh(tmp_path, episodes=1)
    events = []
    with value.locked():
        value.begin_task("CloseFridge")
        a = value.begin_episode("CloseFridge", 0)
        slot = SimSlot(
            slot_config(value, "1" * 32, "http://unused"),
            factory=lambda t, s, g: TrackedEnv(t, g["seed"], events),
        )
        bad = dict(a)
        bad[field] = a[field] + 1 if field == "seed" else "f" * 32
        with pytest.raises(ValueError):
            slot.start_episode(
                bad, grant=value.allocate_environment("CloseFridge", "1" * 32)
            )
        assert not events and slot.state == "IDLE"


def test_mid_episode_task_switch_is_rejected_before_close_or_make(
    tmp_path, monkeypatch
):
    prepare_monkey(monkeypatch)
    value = fresh(tmp_path, tasks=("TaskA", "TaskB"), episodes=1)
    events = []
    with value.locked():
        value.begin_task("TaskA")
        value.begin_task("TaskB")
        a = value.begin_episode("TaskA", 0)
        slot = SimSlot(
            slot_config(value, "1" * 32, "http://unused"),
            factory=lambda t, s, g: TrackedEnv(t, g["seed"], events),
        )
        slot.start_episode(a, grant=value.allocate_environment("TaskA", "1" * 32))
        slot.initialize()
        before = list(events)
        with pytest.raises(RuntimeError, match="owned idle Slot claim"):
            slot.switch_task("TaskB", value.allocate_environment("TaskB", "1" * 32))
        assert events == before and slot.state == "ADMISSION"
        slot.close()
