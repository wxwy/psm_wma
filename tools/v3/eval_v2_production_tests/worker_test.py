"""Actual native Worker serve/default branch with CPU external boundary doubles."""

import hashlib
import importlib.metadata
import socket
import threading
from pathlib import Path

from cosmos_framework.evaluation.robocasa_v2.wire import receive, send
from cosmos_framework.simulation.robocasa import eval_v2_adapter
from cosmos_framework.simulation.robocasa import eval_v2_worker as worker

from tools.v3.eval_v2_production_tests.native_test import Env, native


def cfg(tmp_path):
    directory = tmp_path / "lerobot"
    (directory / "extras").mkdir(parents=True)
    metadata = directory / "extras/dataset_meta.json"
    metadata.write_text('{"env_args":{}}')
    from cosmos_framework.simulation.robocasa import eval_v2_slot
    from tools.v3.eval_v2_production_tests.store_test import fresh

    value = fresh(tmp_path, episodes=1)
    with value.locked():
        value.begin_task("CloseFridge")
        attempt = value.begin_episode("CloseFridge", 0)
        grant = value.allocate_environment("CloseFridge", "1" * 32)
    files = {
        "worker": Path(worker.__file__),
        "native": Path(native.__file__),
        "adapter": Path(eval_v2_adapter.__file__),
        "slot": Path(eval_v2_slot.__file__),
    }
    return {
        "nonce": "cpu",
        "task": "CloseFridge",
        "physical_slot_id": "1" * 32,
        "manifest_digest": value.manifest["digest"],
        "coordinator_lease_id": attempt["lease_id"],
        "episodes_per_task": 1,
        "task_root": str(value.root / "_internal/tasks"),
        "tasks": {
            "CloseFridge": {
                "dataset_dir": str(directory),
                "metadata_sha256": hashlib.sha256(metadata.read_bytes()).hexdigest(),
                "horizon": 2,
            }
        },
        "_test_attempt": attempt,
        "_test_grant": grant,
        "settings": {
            "horizon": 2,
            "server_url": "http://unused",
            "predict_timeout_s": 0.1,
        },
        "runtime_args": {},
        "dataset_dir": str(directory),
        "metadata_sha256": hashlib.sha256(metadata.read_bytes()).hexdigest(),
        "work_root": str(tmp_path / "slots"),
        "simulation_libraries": {
            n: importlib.metadata.version(n)
            for n in ["numpy", "scipy", "Pillow", "requests"]
        },
        "source_files": {
            k: {
                "path": str(p.resolve()),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for k, p in files.items()
        },
    }


def run_worker(configuration, monkeypatch):
    parent, child = socket.socketpair()
    errors = []
    env = Env(initial=True)
    monkeypatch.setattr(
        native,
        "verify_runtime",
        lambda *a: {
            "digest": "r" * 64,
            "protocol": {"official_horizons": {"CloseFridge": 2}},
        },
    )
    monkeypatch.setattr(native, "make_env", lambda *a, **k: env)

    def run():
        try:
            worker.serve(child, configuration)
        except BaseException as e:
            errors.append(e)

    thread = threading.Thread(target=run)
    thread.start()
    parent.settimeout(2)
    return parent, thread, errors, env


def test_default_worker_attests_sources_before_environment_and_handles_initial_success(
    tmp_path, monkeypatch
):
    conf = cfg(tmp_path)
    channel, thread, errors, env = run_worker(conf, monkeypatch)
    try:
        ready = receive(channel)
        assert ready["kind"] == "READY" and ready["runtime_digest"] == "r" * 64
        send(
            channel,
            {
                "nonce": "cpu",
                "request_id": "start",
                "op": "start_episode",
                "attempt": conf["_test_attempt"],
                "grant": conf["_test_grant"],
            },
        )
        assert receive(channel)["state"] == "ENV_READY"
        send(channel, {"nonce": "cpu", "request_id": "1", "op": "initialize"})
        result = receive(channel)
        assert result["initial_success"] is True and env.resets == 1 and not env.actions
        send(channel, {"nonce": "cpu", "request_id": "2", "op": "close"})
        assert receive(channel)["closed"]
    finally:
        channel.close()
        thread.join(2)
    assert not thread.is_alive() and not errors


def test_wrong_import_source_is_fatal_before_any_reset(tmp_path, monkeypatch):
    conf = cfg(tmp_path)
    conf["source_files"]["native"]["sha256"] = "0" * 64
    channel, thread, errors, env = run_worker(conf, monkeypatch)
    try:
        assert receive(channel)["kind"] == "FATAL"
    finally:
        channel.close()
        thread.join(2)
    assert errors and "source mismatch" in str(errors[0]) and env.resets == 0


def test_simulator_library_drift_is_fatal_before_any_reset(tmp_path, monkeypatch):
    conf = cfg(tmp_path)
    conf["simulation_libraries"]["numpy"] = "unexpected"
    channel, thread, errors, env = run_worker(conf, monkeypatch)
    try:
        assert receive(channel)["kind"] == "FATAL"
    finally:
        channel.close()
        thread.join(2)
    assert errors and "libraries changed" in str(errors[0]) and env.resets == 0
