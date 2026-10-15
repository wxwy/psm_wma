"""E1 CPU contracts: dummy subprocesses only, no simulator/model/CUDA assets."""

from __future__ import annotations

import contextlib
import ctypes
import hashlib
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import eval_robocasa_18task_queue as queue


def wait_file(path, timeout=3):
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() >= deadline:
            raise AssertionError(f"dummy process did not create {path}")
        time.sleep(0.01)


def assert_gone(test, pid):
    with test.assertRaises(ProcessLookupError):
        os.kill(pid, 0)


class OwnedProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = (self.root / "process.log").open("ab", buffering=0)
        self.addCleanup(self.log.close)
        self.reaper = queue.child_subreaper()
        self.reaper.__enter__()
        self.addCleanup(self.reaper.__exit__, None, None, None)

    def spawn(self, code):
        owned = queue.OwnedProcess(
            [sys.executable, "-u", "-c", code], cwd=self.root, env=os.environ.copy(), log=self.log
        )
        self.addCleanup(owned.close, 0.3)
        return owned

    def tree(self):
        # Both generations ignore TERM. Child acknowledges its handler before
        # parent readiness, so this verifies a real KILL fallback, not a race.
        child = "import signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); pathlib.Path('child_ready').touch(); time.sleep(30)"
        parent = f"""import signal,time,subprocess,sys,pathlib
signal.signal(signal.SIGTERM,signal.SIG_IGN)
p=subprocess.Popen([sys.executable,'-u','-c',{child!r}])
pathlib.Path('child_pid').write_text(str(p.pid))
while not pathlib.Path('child_ready').exists(): time.sleep(.01)
pathlib.Path('actions.jsonl').write_text('partial evidence\\n')
print('dummy started',flush=True)
pathlib.Path('ready').touch()
time.sleep(30)
"""
        owned = self.spawn(parent)
        wait_file(self.root / "ready")
        return owned, int((self.root / "child_pid").read_text())

    def test_normal_exit_and_idempotent_cleanup(self):
        owned = self.spawn('print("done")')
        self.assertEqual(owned.wait_task(timeout=2, stop=threading.Event()), 0)
        owned.close(0.3)
        owned.close(0.3)
        assert_gone(self, owned.process.pid)

    def test_deadline_kills_term_ignoring_parent_and_child_preserving_evidence(self):
        owned, child = self.tree()
        started = time.monotonic()
        with self.assertRaises(queue.TaskDeadlineExceeded):
            owned.wait_task(timeout=0.1, stop=threading.Event())
        owned.close(0.3)
        self.assertLess(time.monotonic() - started, 3)
        self.assertEqual((self.root / "actions.jsonl").read_text(), "partial evidence\n")
        self.assertIn(b"dummy started", (self.root / "process.log").read_bytes())
        self.assertEqual(owned.process.returncode, -signal.SIGKILL)
        assert_gone(self, owned.process.pid)
        assert_gone(self, child)

    def test_stop_cancels_running_task_and_reaps_descendants(self):
        owned, child = self.tree()
        stop = threading.Event()
        timer = threading.Timer(0.1, stop.set)
        timer.start()
        self.addCleanup(timer.join, 1)
        with self.assertRaises(queue.ExecutionCancelled):
            owned.wait_task(timeout=5, stop=stop)
        owned.close(0.3)
        assert_gone(self, child)

    def test_cleanup_does_not_signal_unrelated_process(self):
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
        self.addCleanup(lambda: unrelated.poll() is None and unrelated.kill())
        self.addCleanup(lambda: unrelated.wait(timeout=2) if unrelated.poll() is not None else None)
        owned = self.spawn("import time; time.sleep(30)")
        owned.close(0.3)
        self.assertIsNone(unrelated.poll())
        unrelated.terminate()
        unrelated.wait(timeout=2)

    def test_reaps_child_after_parent_exits_itself(self):
        code = "import subprocess,sys,pathlib; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); pathlib.Path('pid').write_text(str(p.pid))"
        owned = self.spawn(code)
        wait_file(self.root / "pid")
        child = int((self.root / "pid").read_text())
        owned.process.wait(timeout=2)
        owned.close(0.3)
        assert_gone(self, child)

    def test_cleanup_failure_is_bounded_and_explicit(self):
        owned = self.spawn("import time; time.sleep(30)")
        with patch.object(owned, "_reap_until", return_value=False):
            with self.assertRaises(queue.ProcessCleanupError):
                owned.close(0.01)
        owned.close(0.3)

    def test_subreaper_setting_is_restored(self):
        libc = ctypes.CDLL(None)
        before = ctypes.c_int()
        libc.prctl(37, ctypes.byref(before), 0, 0, 0)
        with queue.child_subreaper():
            current = ctypes.c_int()
            libc.prctl(37, ctypes.byref(current), 0, 0, 0)
            self.assertEqual(current.value, 1)
        after = ctypes.c_int()
        libc.prctl(37, ctypes.byref(after), 0, 0, 0)
        self.assertEqual(before.value, after.value)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.checkpoint = self.base / "checkpoint"
        (self.checkpoint / "model").mkdir(parents=True)
        self.config = self.base / "config.yaml"
        self.config.write_text("synthetic: true\n")
        self.out = self.base / "output"
        self.spawned = []
        self.completed = threading.Event()
        self.manifest = None
        self.pid_files = []

    def identity(self, **kwargs):
        identity = {"protocol": kwargs["protocol"]}
        digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.manifest = {"identity": identity, "digest": digest}
        return self.manifest

    def run_queue(self, *, failure=None, tasks=1, gpus="fake0,fake1", task_timeout=2, observe=False, resume=False):
        argv = [
            "queue",
            "--checkpoint-path",
            str(self.checkpoint),
            "--dataset-root",
            str(self.base),
            "--output-dir",
            str(self.out),
            "--config-file",
            str(self.config),
            "--server-python",
            sys.executable,
            "--sim-python",
            sys.executable,
            "--gpus",
            gpus,
            "--expected-tasks",
            str(tasks),
            "--timeout",
            "1",
            "--shutdown-timeout",
            ".3",
        ]
        if task_timeout is not None:
            argv.extend(("--task-timeout", str(task_timeout)))
        if resume:
            argv.append("--resume")
        real_owned = queue.OwnedProcess
        real_close = real_owned.close
        close_failed = set()

        def spawn(command, **kwargs):
            server = "--port" in command
            gpu = kwargs["env"]["CUDA_VISIBLE_DEVICES"]
            if server and gpu == "fake1" and failure == "popen":
                self.assertTrue(self.completed.wait(5))
                raise OSError("synthetic server Popen failure after tasks complete")
            if server:
                code = "import time; time.sleep(30)"
            else:
                dest = Path(command[command.index("--output-dir") + 1])
                if failure == "sim_popen":
                    raise OSError("synthetic simulator Popen failure")
                digest = command[command.index("--evaluation-run-digest") + 1]
                rows = [dict(ep=0, evaluation_run_digest=digest, policy=True, outcome="success", error=None)]
                if failure == "partial":
                    rows = []
                script = f"import json,pathlib,time; p=pathlib.Path({str(dest)!r}); (p/'actions.jsonl').write_text('partial evidence\\n'); print('sim evidence',flush=True); (p/'results.json').write_text({json.dumps(rows)!r}); "
                if failure in {"hang", "cancel", "signal"}:
                    child_ready = dest / "child_ready"
                    child_script = f"import signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); pathlib.Path({str(child_ready)!r}).touch(); time.sleep(30)"
                    script = f"""import signal,time,subprocess,sys,pathlib
signal.signal(signal.SIGTERM,signal.SIG_IGN)
p=pathlib.Path({str(dest)!r})
c=subprocess.Popen([sys.executable,'-u','-c',{child_script!r}])
(p/'child_pid').write_text(str(c.pid))
while not (p/'child_ready').exists(): time.sleep(.01)
(p/'actions.jsonl').write_text('partial evidence\\n')
print('sim evidence',flush=True)
(p/'ready').touch()
time.sleep(30)
"""
                    self.pid_files.append(dest / "child_pid")
                else:
                    script += "raise SystemExit(7)" if failure in {"nonzero", "partial"} else "time.sleep(.02)"
                if failure == "malformed":
                    script += f"; (p/'results.json').write_text('broken json')"
                code = script
            owned = real_owned([sys.executable, "-u", "-c", code], **kwargs)
            self.spawned.append(owned)
            if not server:
                owned.test_task = True

                # Observer waits for actual artifact publication, not wall-clock guessing.
                def watch():
                    if failure in {"hang", "cancel", "signal"}:
                        wait_file(Path(command[command.index("--output-dir") + 1]) / "ready")
                    else:
                        owned.process.wait(timeout=3)
                    self.completed.set()
                    if failure == "signal":
                        os.kill(os.getpid(), signal.SIGTERM)

                watcher = threading.Thread(target=watch)
                watcher.start()
                self.addCleanup(watcher.join, 4)
            return owned

        def ready(server, port, timeout, stop):
            if failure == "stuck_worker":
                if not stop.wait(20):
                    raise AssertionError("coordinator did not enforce its join deadline")
                raise queue.ExecutionCancelled("injected stuck worker released by watchdog cancellation")
            if port == 8913 and failure in {"ready", "cancel"}:
                self.assertTrue(self.completed.wait(5))
                raise RuntimeError("synthetic server readiness failure")
            return {"local_memory": {"mode": "required"}}

        def close(owned, timeout):
            if failure == "cleanup" and not getattr(owned, "test_task", False) and owned.pgid not in close_failed:
                close_failed.add(owned.pgid)
                raise queue.ProcessCleanupError("synthetic cleanup exception after completed tasks")
            return real_close(owned, timeout)

        parse_errors = []
        stop_observer = threading.Event()

        def read_summary():
            while not stop_observer.wait(0.001):
                try:
                    json.loads((self.out / "screening_summary.json").read_text())
                except FileNotFoundError:
                    pass
                except Exception as exc:
                    parse_errors.append(str(exc))

        observer = threading.Thread(target=read_summary)
        if observe:
            observer.start()
        try:
            with (
                patch.object(sys, "argv", argv),
                patch.object(
                    queue, "discover_task_datasets", return_value=[(f"task{i}", self.base) for i in range(tasks)]
                ),
                patch.object(queue, "build_evaluation_identity", side_effect=self.identity),
                patch.object(queue, "OwnedProcess", side_effect=spawn),
                patch.object(real_owned, "close", close),
                patch.object(queue, "wait_server", side_effect=ready),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                code = queue.main()
        finally:
            stop_observer.set()
            if observe:
                observer.join(timeout=2)
            # Test failures must not leave dummy CPU processes behind either.
            for owned in self.spawned:
                real_close(owned, 0.3)
        self.assertFalse(parse_errors)
        for owned in self.spawned:
            assert_gone(self, owned.process.pid)
        for path in self.pid_files:
            if path.exists():
                assert_gone(self, int(path.read_text()))
        return code, json.loads((self.out / "screening_summary.json").read_text())

    def assert_error(self, result, *, exception=None):
        code, summary = result
        self.assertNotEqual(code, 0)
        self.assertEqual(summary["status"], "FAILED")
        self.assertEqual(summary["execution_status"], "FAILED")
        self.assertFalse(summary["sr_valid"])
        self.assertIsNone(summary["sr"])
        self.assertTrue(summary["worker_errors"])
        ledger = [json.loads(line) for line in (self.out / "worker_errors.jsonl").read_text().splitlines()]
        self.assertEqual(ledger, summary["worker_errors"])
        for error in summary["worker_errors"]:
            self.assertTrue(
                {
                    "worker_id",
                    "gpu",
                    "phase",
                    "exception_type",
                    "message",
                    "traceback",
                    "server_log",
                    "task_log",
                    "returncode",
                    "timestamp",
                }
                <= error.keys()
            )
            self.assertTrue(error["traceback"])
        if exception:
            self.assertIn(exception, [e["exception_type"] for e in summary["worker_errors"]])
        return summary

    def test_original_18_task_success(self):
        code, summary = self.run_queue(tasks=18, gpus="fake0,fake1,fake2", observe=True)
        self.assertEqual(code, 0)
        self.assertEqual(summary["status"], "COMPLETE")
        self.assertEqual(summary["total_trials"], 18)
        self.assertEqual(summary["total_successes"], 18)
        self.assertEqual(summary["worker_errors"], [])
        self.assertEqual(summary["sr"], 1)
        self.assertTrue(summary["sr_valid"])

    def test_server_popen_failure_after_all_tasks_cannot_disappear(self):
        summary = self.assert_error(self.run_queue(failure="popen"), exception="OSError")
        self.assertEqual(summary["total_successes"], 1)
        self.assertEqual(summary["task_statistics_status"], "COMPLETE")
        self.assertEqual(summary["diagnostic_sr"], 1)
        error = next(e for e in summary["worker_errors"] if e["exception_type"] == "OSError")
        self.assertTrue(error["server_log"].endswith("action_server.log"))
        self.assertIn("synthetic server Popen failure", error["traceback"])

    def test_ready_failure_after_completion(self):
        summary = self.assert_error(self.run_queue(failure="ready"), exception="RuntimeError")
        self.assertEqual(summary["total_trials"], 1)
        self.assertEqual(summary["task_statistics_status"], "COMPLETE")

    def test_cleanup_exception_after_completed_tasks(self):
        self.assert_error(self.run_queue(failure="cleanup", gpus="fake0"), exception="ProcessCleanupError")

    def test_nonzero_exit_retains_complete_business_results(self):
        summary = self.assert_error(self.run_queue(failure="nonzero", gpus="fake0"))
        self.assertEqual(summary["total_successes"], 1)
        self.assertEqual(summary["worker_errors"][0]["returncode"], 7)
        self.assertTrue(summary["worker_errors"][0]["task_log"].endswith("eval.log"))

    def test_nonzero_partial_results_and_actions_preserved(self):
        self.assert_error(self.run_queue(failure="partial", gpus="fake0"))
        self.assertEqual(json.loads((self.out / "task0/results.json").read_text()), [])
        self.assertEqual((self.out / "task0/actions.jsonl").read_text(), "partial evidence\n")

    def test_simulator_start_failure_records_assigned_task(self):
        summary = self.assert_error(self.run_queue(failure="sim_popen", gpus="fake0"), exception="OSError")
        self.assertEqual(summary["worker_errors"][0]["task"], "task0")
        self.assertTrue(summary["tasks"]["task0"]["infrastructure_failure"])

    def test_result_parse_exception_is_preserved(self):
        self.assert_error(self.run_queue(failure="malformed", gpus="fake0"), exception="JSONDecodeError")
        self.assertEqual((self.out / "task0/results.json").read_text(), "broken json")

    def test_task_timeout_reaps_ignoring_parent_and_child(self):
        started = time.monotonic()
        summary = self.assert_error(
            self.run_queue(failure="hang", gpus="fake0", task_timeout=0.5), exception="TaskDeadlineExceeded"
        )
        self.assertEqual(summary["worker_errors"][0]["returncode"], -signal.SIGKILL)
        self.assertLess(time.monotonic() - started, 5)
        self.assertEqual((self.out / "task0/actions.jsonl").read_text(), "partial evidence\n")

    def test_worker_failure_cancels_other_workers_hung_simulator(self):
        started = time.monotonic()
        summary = self.assert_error(self.run_queue(failure="cancel", task_timeout=5))
        self.assertLess(time.monotonic() - started, 5)
        self.assertIn("ExecutionCancelled", [e["exception_type"] for e in summary["worker_errors"]])

    def test_coordinator_sigterm_is_cancellation_not_success(self):
        self.assert_error(
            self.run_queue(failure="signal", gpus="fake0", task_timeout=5), exception="ExecutionCancelled"
        )

    def test_worker_join_watchdog_cancels_stuck_worker(self):
        started = time.monotonic()
        summary = self.assert_error(
            self.run_queue(failure="stuck_worker", gpus="fake0", task_timeout=0.01),
            exception="TaskDeadlineExceeded",
        )
        self.assertLess(time.monotonic() - started, 18)
        self.assertTrue(any(e["phase"] == "coordinator" for e in summary["worker_errors"]))

    def test_deadline_is_bound_into_identity(self):
        self.run_queue(gpus="fake0", task_timeout=1)
        protocol = self.manifest["identity"]["protocol"]
        self.assertEqual(protocol["task_timeout_s"], 1)
        self.assertEqual(protocol["shutdown_timeout_s"], 0.3)
        self.assertEqual(protocol["execution_contract"], "v3_screening_e1_owned_process_groups")

    def test_invalid_timeouts_fail_before_any_process_or_asset(self):
        for flag in ["--timeout", "--task-timeout", "--shutdown-timeout"]:
            for value in ["nan", "inf", "-inf", "0", "-1"]:
                with (
                    self.subTest(flag=flag, value=value),
                    patch.object(
                        sys,
                        "argv",
                        [
                            "queue",
                            "--checkpoint-path",
                            "/absent",
                            "--dataset-root",
                            "/absent",
                            "--output-dir",
                            "/absent",
                            "--sim-python",
                            sys.executable,
                            flag + "=" + value,
                        ],
                    ),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    with self.assertRaises(SystemExit) as error:
                        queue.main()
                    self.assertEqual(error.exception.code, 2)

    def test_default_deadline_is_explicit(self):
        self.run_queue(gpus="fake0", task_timeout=None)
        self.assertEqual(self.manifest["identity"]["protocol"]["task_timeout_s"], 3600)

    def test_atomic_publication_preserves_last_record_after_encoding_error(self):
        path = self.base / "summary.json"
        queue.atomic_write_json(path, {"status": "RUNNING"})
        with self.assertRaises(ValueError):
            queue.atomic_write_json(path, {"bad": float("nan")})
        self.assertEqual(json.loads(path.read_text()), {"status": "RUNNING"})
        queue.atomic_write_json(path, {"status": "FAILED", "worker_errors": ["preserved"]})
        self.assertEqual(json.loads(path.read_text())["worker_errors"], ["preserved"])
        self.assertEqual(list(self.base.glob(".summary.json*")), [])

    def test_new_execution_preserves_previous_execution_evidence(self):
        _, first = self.run_queue(gpus="fake0")
        history = self.out / f"execution_{first['execution_id']}.json"
        frozen = history.read_bytes()
        second = self.assert_error(self.run_queue(failure="popen", resume=True))
        self.assertNotEqual(first["execution_id"], second["execution_id"])
        self.assertEqual(history.read_bytes(), frozen)
        self.assertEqual(second["total_trials"], 1)
        self.assertEqual(len(list(self.out.glob("execution_*.json"))), 2)


class ServerWaitTests(unittest.TestCase):
    def test_ready_timeout_is_bounded(self):
        process = type("Process", (), {"poll": lambda self: None})()
        with patch.object(queue, "_read_json", side_effect=OSError("not ready")):
            with self.assertRaisesRegex(RuntimeError, "not ready"):
                queue.wait_server(process, 1, 0.02, threading.Event())

    def test_startup_stop_does_not_wait_for_timeout(self):
        stop = threading.Event()
        stop.set()
        process = type("Process", (), {"poll": lambda self: None})()
        with self.assertRaises(queue.ExecutionCancelled):
            queue.wait_server(process, 1, 30, stop)


if __name__ == "__main__":
    unittest.main()
