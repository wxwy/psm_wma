"""CPU-only queue integration: real local HTTP/PIDs/Git, synthetic simulator/results.

No Torch/CUDA/model/simulator imports. Child process fixtures are stdlib-only.
Run directly with Python, or pytest --noconftest and an external empty config.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("screening_queue", ROOT / "scripts/eval_robocasa_18task_queue.py")
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)
TASKS = {"CloseFridge", "TurnOnSinkFaucet", "PickPlaceSinkToCounter", "NavigateKitchen"}


def _info(checkpoint: Path, config: Path) -> dict:
    # Effective fields exposed by the unchanged Child get_info()/Local adapter.
    return {
        "checkpoint": str(checkpoint),
        "config_file": str(config),
        "raw_action_dim": 15,
        "max_action_dim": 64,
        "action_chunk_size": 16,
        "requires_state": True,
        "num_steps": 30,
        "guidance": 1.0,
        "fps": 20,
        "seed": 0,
        "local_memory": {"enabled": True, "mode": "required", "action_dim": 15},
    }


def _serve(port: int, info: dict) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps(info).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


def _start_http(port: int, info: dict, **kwargs):
    return subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--serve", str(port), json.dumps(info)], **kwargs
    )


def _ready(proc, port):
    until = time.monotonic() + 5
    while time.monotonic() < until:
        if proc.poll() is not None:
            raise RuntimeError("fixture HTTP server exited")
        try:
            return queue_module._read_json(f"http://127.0.0.1:{port}/info", timeout=0.2)
        except OSError:
            time.sleep(0.01)
    raise RuntimeError("fixture HTTP startup timeout")


def _stop(proc):
    if proc.poll() is None:
        proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)


def _free_base(count):
    for _ in range(100):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        try:
            queue_module.require_free_ports(list(range(port, port + count)))
            return port
        except (OSError, RuntimeError, ValueError):
            continue
    raise RuntimeError("no fixture port range")


def _git(root, *args):
    return subprocess.check_output(
        ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
        stderr=subprocess.STDOUT,
        text=True,
    ).strip()


def _repo(root):
    root.mkdir()
    _git(root, "init", "-q")
    (root / "fixture.txt").write_text("synthetic source\n")
    _git(root, "add", "fixture.txt")
    _git(root, "-c", "user.name=CPU Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")


def _scenario(case, parent, count):
    """Invoke the actual queue main/identity with only server/simulator boundaries replaced."""
    root = parent / "source"
    _repo(root)
    child = root / "cosmos-framework"
    _repo(child)
    _git(root, "update-index", "--add", "--cacheinfo", f"160000,{_git(child, 'rev-parse', 'HEAD')},cosmos-framework")
    _git(root, "-c", "user.name=CPU Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "gitlink")
    queue_module.ROOT, queue_module.CHILD = root, child
    checkpoint = parent / "job/checkpoints/iter_000004000"
    (checkpoint / "model").mkdir(parents=True)
    (checkpoint / "model/.metadata").write_bytes(b"tiny synthetic metadata, not a real DCP")
    (checkpoint / "model/__0_0.distcp").write_bytes(b"synthetic")
    config = checkpoint.parent.parent / "config.yaml"
    config.write_text("synthetic: true\n")
    dataset = parent / "datasets"
    for task in TASKS:
        meta = dataset / task / "lerobot/extras/dataset_meta.json"
        meta.parent.mkdir(parents=True)
        meta.write_text(json.dumps({"env_args": {"env_name": task}}))
    observed_tasks = queue_module.discover_task_datasets(dataset, 4)
    assert {name for name, _ in observed_tasks} == TASKS
    output = parent / "evaluation"
    base = _free_base(count)
    calls, servers, foreign = [], [], []
    sim_calls = []
    all_tasks_done = threading.Event()

    def popen(command, **kwargs):
        calls.append(command)
        gpu = kwargs["env"]["CUDA_VISIBLE_DEVICES"]
        assert command[1:3] == ["-m", "cosmos_framework.scripts.action_policy_server_robocasa"]
        assert command[command.index("--local-memory-max-sessions") + 1] == "1"
        if case == "late_launch_failure" and gpu == "1":
            assert all_tasks_done.wait(8), "healthy worker did not complete"
            raise OSError("injected second worker launch failure after all tasks")
        port = int(command[command.index("--port") + 1])
        info = _info(checkpoint, config)
        if case == "wrong_checkpoint":
            info["checkpoint"] = str(checkpoint.with_name("iter_000003900"))
        if case == "wrong_config":
            info["config_file"] = str(parent / "another.yaml")
        if case == "wrong_mode":
            info["local_memory"]["mode"] = "off"
        if case == "changed_config":
            config.write_text("synthetic: changed after identity\n")
        if case == "foreign_race":
            old = _start_http(port, info, stdout=kwargs["stdout"], stderr=subprocess.STDOUT)
            foreign.append(old)
            _ready(old, port)
            proc = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
        else:
            proc = _start_http(port, info, stdout=kwargs["stdout"], stderr=subprocess.STDOUT)
        servers.append(proc)
        return proc

    def run(command, **kwargs):
        assert command[1].endswith("closed_loop_eval.py")
        sim_calls.append(command)
        directory = Path(command[command.index("--output-dir") + 1])
        digest = command[command.index("--evaluation-run-digest") + 1]
        if case == "sim_failure" and len(sim_calls) == 1:
            return SimpleNamespace(returncode=7)
        rows = [
            {
                "ep": index,
                "policy": index % 2 == 0,
                "outcome": "success" if index % 2 == 0 else "behavioral_failure",
                "error": None,
                "evaluation_run_digest": digest,
            }
            for index in range(5)
        ]
        (directory / "results.json").write_text(json.dumps(rows))
        for index in range(5):
            (directory / f"rollout{index}.mp4").write_bytes(b"synthetic video witness, not an MP4 encoding")
        if len(sim_calls) == 4:
            all_tasks_done.set()
            if case == "server_dies_after_tasks":
                _stop(servers[0])
        return SimpleNamespace(returncode=0)

    # Proxy only the queue module's external process boundaries. Real immutable
    # identity still invokes real Git; the rest of the host subprocess module is intact.
    queue_module.subprocess = SimpleNamespace(
        Popen=popen, run=run, STDOUT=subprocess.STDOUT, TimeoutExpired=subprocess.TimeoutExpired
    )
    argv = [
        "queue",
        "--checkpoint-path",
        str(checkpoint),
        "--config-file",
        str(config),
        "--dataset-root",
        str(dataset),
        "--output-dir",
        str(output),
        "--server-python",
        sys.executable,
        "--sim-python",
        sys.executable,
        "--gpus",
        ",".join(str(index) for index in range(count)),
        "--base-port",
        str(base),
        "--expected-tasks",
        "4",
        "--num-test-episodes",
        "5",
        "--num-steps",
        "30",
        "--guidance",
        "1.0",
        "--timeout",
        "5",
    ]
    error = None
    with ExitStack() as stack:
        if case == "occupied_port":
            occupied = stack.enter_context(socket.socket())
            occupied.bind(("0.0.0.0", base + count - 1))
            occupied.listen()
        try:
            with patch.object(sys, "argv", argv):
                rc = queue_module.main()
        except (RuntimeError, ValueError, SystemExit) as exc:
            rc, error = 1, f"{type(exc).__name__}: {exc}"
        finally:
            foreign_alive = all(proc.poll() is None for proc in foreign)
            server_exits = [proc.poll() for proc in servers]
            for proc in [*servers, *foreign]:
                _stop(proc)
    report = {
        "case": case,
        "rc": rc,
        "error": error,
        "server_commands": len(calls),
        "sim_calls": len(sim_calls),
        "server_exits": server_exits,
        "foreign_alive_before_fixture_cleanup": foreign_alive,
        "thread_names": [thread.name for thread in threading.enumerate() if thread.name.startswith("robocasa-gpu-")],
        "output_exists": output.exists(),
    }
    if (output / "screening_summary.json").exists():
        report["summary"] = json.loads((output / "screening_summary.json").read_text())
    (parent / "report.json").write_text(json.dumps(report))


class ServerIdentityTests(unittest.TestCase):
    def test_effective_info_exact_fields_and_malformed_values_fail_closed(self):
        checkpoint, config = Path("/synthetic/iter_000004000"), Path("/synthetic/config.yaml")
        good = _info(checkpoint, config)
        queue_module.validate_server_info(good, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0)
        changes = {
            "checkpoint": [None, "/synthetic/iter_000003900", "iter_000004000"],
            "config_file": [None, "/other/config.yaml"],
            "raw_action_dim": [None, 12, "15", True],
            "max_action_dim": [None, 32],
            "action_chunk_size": [None, 32, 0],
            "requires_state": [None, False, 1],
            "num_steps": [None, 29, "30"],
            "guidance": [None, 2.0, float("nan"), True],
            "fps": [None, 30],
            "seed": [None, 1],
            "local_memory": [None, {"enabled": True, "mode": "off"}, {"enabled": True, "mode": "required"}],
        }
        for field, values in changes.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    bad = copy.deepcopy(good)
                    bad[field] = value
                    with self.assertRaises(ValueError):
                        queue_module.validate_server_info(
                            bad, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0
                        )
        with self.assertRaises(ValueError):
            queue_module.validate_server_info([], checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0)

    def test_process_exit_during_ready_check_is_rejected(self):
        checkpoint, config = Path("/synthetic/iter_000004000"), Path("/synthetic/config.yaml")
        process = SimpleNamespace(poll=unittest.mock.Mock(side_effect=[None, 7]), returncode=7)
        with (
            patch.object(queue_module, "_read_json", return_value=_info(checkpoint, config)),
            patch.object(queue_module, "require_owned_listener"),
            self.assertRaisesRegex(RuntimeError, "exited during identity"),
        ):
            queue_module.wait_server(
                process, 1234, 1, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0
            )

    def test_invalid_port_range_is_rejected(self):
        for port in (0, 65536, -1, True):
            with self.subTest(port=port), self.assertRaises(ValueError):
                queue_module.require_free_ports([port])

    def test_unverifiable_listener_ownership_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "cannot verify"):
            queue_module.require_owned_listener(SimpleNamespace(pid=999999999), 1234)

    def test_ready_connection_timeout_and_already_dead_server(self):
        checkpoint, config = Path("/synthetic/iter_000004000"), Path("/synthetic/config.yaml")
        process = SimpleNamespace(poll=lambda: None)
        with patch.object(queue_module, "_read_json", side_effect=OSError("synthetic connection refused")):
            with self.assertRaisesRegex(RuntimeError, "not ready before timeout"):
                queue_module.wait_server(
                    process, 1234, 0.01, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0
                )
        process = SimpleNamespace(poll=lambda: 9, returncode=9)
        with self.assertRaisesRegex(RuntimeError, "exited early"):
            queue_module.wait_server(
                process, 1234, 1, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0
            )


class QueueIntegrationTests(unittest.TestCase):
    def scenario(self, case, count=2):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            with (parent / "console.log").open("w") as log:
                process = subprocess.Popen(
                    [sys.executable, str(Path(__file__).resolve()), "--scenario", case, directory, str(count)],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    rc = process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    self.fail("CPU queue fixture hung; owned process group killed")
            self.assertEqual(rc, 0, (parent / "console.log").read_text())
            report = json.loads((parent / "report.json").read_text())
            self.assertEqual(report["thread_names"], [], report)
            self.assertTrue(all(code is not None for code in report["server_exits"]), report)
            print("QUEUE_WITNESS " + json.dumps(report, sort_keys=True))
            return report

    def test_four_tasks_five_episodes_complete_on_one_two_or_four_workers(self):
        for count in (1, 2, 4):
            with self.subTest(workers=count):
                report = self.scenario("normal", count)
                self.assertEqual(report["rc"], 0)
                self.assertEqual(report["server_commands"], count)
                summary = report["summary"]
                self.assertEqual(set(summary["tasks"]), TASKS)
                self.assertEqual(summary["status"], "COMPLETE")
                self.assertEqual(summary["total_trials"], 20)
                self.assertEqual(summary["total_successes"], 12)
                self.assertEqual(summary["sr"], 0.6)
                self.assertEqual(summary["worker_errors"], {})
                for row in summary["tasks"].values():
                    self.assertEqual(row["trials"], 5)
                    self.assertEqual(len(row["rollout_mp4s"]), 5)

    def test_occupied_nonfirst_port_refuses_all_workers_before_output_claim(self):
        report = self.scenario("occupied_port")
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["server_commands"], 0)
        self.assertEqual(report["sim_calls"], 0)
        self.assertFalse(report["output_exists"])
        self.assertIn("unavailable", report["error"])

    def test_wrong_checkpoint_config_and_mode_stop_before_simulator(self):
        for case in ("wrong_checkpoint", "wrong_config", "wrong_mode"):
            with self.subTest(case=case):
                report = self.scenario(case)
                self.assertEqual(report["rc"], 1)
                self.assertEqual(report["sim_calls"], 0)
                self.assertTrue(report["summary"]["worker_errors"])
                self.assertIsNone(report["summary"]["sr"])

    def test_foreign_listener_race_with_identical_info_is_not_our_process(self):
        report = self.scenario("foreign_race", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["sim_calls"], 0)
        self.assertTrue(report["foreign_alive_before_fixture_cleanup"])
        self.assertIn("does not own port", str(report["summary"]["worker_errors"]))

    def test_config_content_change_during_startup_is_rejected(self):
        report = self.scenario("changed_config", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["sim_calls"], 0)
        self.assertIn("changed since evaluation identity", str(report["summary"]["worker_errors"]))

    def test_launch_error_after_all_tasks_does_not_disappear_from_summary_or_exit(self):
        report = self.scenario("late_launch_failure")
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["summary"]["total_trials"], 20)
        self.assertEqual(report["summary"]["status"], "INCOMPLETE")
        self.assertIsNone(report["summary"]["sr"])
        self.assertIn("injected second worker", str(report["summary"]["worker_errors"]))

    def test_server_exit_after_completed_tasks_is_not_screening_success(self):
        report = self.scenario("server_dies_after_tasks", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["summary"]["total_trials"], 20)
        self.assertIn("exited during screening", str(report["summary"]["worker_errors"]))
        self.assertIsNone(report["summary"]["sr"])

    def test_simulator_failure_keeps_error_and_nonzero_exit(self):
        report = self.scenario("sim_failure", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["summary"]["task_failures"], 1)
        self.assertEqual(report["summary"]["status"], "INCOMPLETE")
        self.assertIsNone(report["summary"]["sr"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        _serve(int(sys.argv[2]), json.loads(sys.argv[3]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--scenario":
        _scenario(sys.argv[2], Path(sys.argv[3]), int(sys.argv[4]))
    else:
        unittest.main()
