"""External, diagnostic-only generation boundary observer for Issue35 K16.

No extra inference, CUDA synchronization, RNG draw, input/output inspection,
per-layer hooks, profiler, compiler flags or allocator resets are performed.
CUDA event spans include device idle gaps; they are not kernel execution sums.
"""

from __future__ import annotations

import argparse
import functools
import gc
import hashlib
import json
import os
from pathlib import Path
import resource
import runpy
import subprocess
import sys
import threading
import time


FORMAL_ROOT = "1b184204e301a51a7a20ed4dde1a11689589cf2d"
FORMAL_CHILD = "d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2"
METHOD = "generate_samples_from_batch"


def source_identity(root: Path) -> dict:
    def git(repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

    return {
        "root": git(root, "rev-parse", "HEAD"),
        "child": git(root / "cosmos-framework", "rev-parse", "HEAD"),
        "gitlink": git(root, "rev-parse", "HEAD:cosmos-framework"),
        "root_status": git(root, "status", "--porcelain"),
        "child_status": git(root / "cosmos-framework", "status", "--porcelain"),
    }


def require_formal(identity):
    expected = dict(root=FORMAL_ROOT, child=FORMAL_CHILD, gitlink=FORMAL_CHILD, root_status="", child_status="")
    if identity != expected:
        raise ValueError("diagnostic requires the exact clean approved implementation Pair")


def host_snapshot():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    snapshot = {
        "monotonic_ns": time.perf_counter_ns(),
        "unix_ns": time.time_ns(),
        "process_cpu_ns": time.process_time_ns(),
        "thread_cpu_ns": time.thread_time_ns(),
        "thread_id": threading.get_native_id(),
        "minor_faults": usage.ru_minflt,
        "major_faults": usage.ru_majflt,
        "voluntary_context_switches": usage.ru_nvcsw,
        "involuntary_context_switches": usage.ru_nivcsw,
        "gc_counts": gc.get_count(),
    }
    try:
        snapshot["thread_schedstat"] = [int(v) for v in Path("/proc/thread-self/schedstat").read_text().split()[:3]]
    except (OSError, ValueError) as error:
        snapshot["schedstat_unavailable"] = type(error).__name__
    return snapshot


def compile_counts(torch):
    """Read only already-imported counters; never import/reset a compiler here."""
    module = sys.modules.get("torch._dynamo.utils")
    if module is None:
        return None
    return {
        str(group): {str(k): v for k, v in values.items() if type(v) is int}
        for group, values in module.counters.items()
    }


class GenerationProbe:
    def __init__(self, model_class, torch, stream, *, cuda_device=0, cuda_events=True):
        self.model_class, self.torch, self.stream = model_class, torch, stream
        self.cuda_device, self.cuda_events = cuda_device, cuda_events
        self.calls, self.errors, self.pending = 0, [], {}
        self.active, self.gc_starts = None, {}
        self.original = getattr(model_class, METHOD)
        self.had_own_method = METHOD in model_class.__dict__
        self.previous_owned = model_class.__dict__.get(METHOD)
        self.gc_callback = self._gc
        self.wrapper = None

    def error(self, operation, error):
        if len(self.errors) < 128:
            self.errors.append({"operation": operation, "error_type": type(error).__name__})

    def emit(self, row):
        try:
            self.stream.write(json.dumps(row, allow_nan=False) + "\n")
            self.stream.flush()
        except Exception as error:
            self.error("write", error)

    def collect(self, operation, fn):
        try:
            return fn()
        except Exception as error:
            self.error(operation, error)
            return None

    def _gc(self, phase, info):
        active = self.active
        if active is None:
            return
        key = (threading.get_ident(), info["generation"])
        now = time.perf_counter_ns()
        if phase == "start":
            self.gc_starts[key] = now
        elif phase == "stop":
            start = self.gc_starts.pop(key, None)
            if len(active["gc"]) < 256:
                active["gc"].append(
                    {
                        "generation": info["generation"],
                        "start_ns": start,
                        "end_ns": now,
                        "collected": info.get("collected"),
                        "uncollectable": info.get("uncollectable"),
                    }
                )
            else:
                active["gc_dropped"] += 1

    def cuda_snapshot(self):
        if not self.torch.cuda.is_initialized():
            return None
        stats = self.torch.cuda.memory_stats(self.cuda_device)
        keys = (
            "allocated_bytes.all.current",
            "reserved_bytes.all.current",
            "active_bytes.all.current",
            "inactive_split_bytes.all.current",
            "num_alloc_retries",
            "num_ooms",
            "num_sync_all_streams",
            "num_device_alloc",
            "num_device_free",
        )
        return {key: stats[key] for key in keys if key in stats}

    def start_events(self):
        if not self.cuda_events or not self.torch.cuda.is_initialized():
            return None
        current = self.torch.cuda.current_stream(self.cuda_device)
        start, end = self.torch.cuda.Event(enable_timing=True), self.torch.cuda.Event(enable_timing=True)
        start.record(current)
        return start, end, current

    def drain(self):
        for call, (start, end) in list(self.pending.items()):
            try:
                if not end.query():
                    continue
                elapsed = start.elapsed_time(end)
                self.emit({"type": "cuda_span", "call": call, "cuda_event_ms": elapsed})
                del self.pending[call]
            except Exception as error:
                self.error("event_query", error)
                del self.pending[call]

    def invoke(self, instance, args, kwargs):
        # The authorized replay is serial. Do not serialize/lock a native call
        # if another caller violates that diagnostic precondition.
        if self.active is not None:
            self.error("concurrent_or_reentrant_generation", RuntimeError())
            return self.original(instance, *args, **kwargs)
        entry = time.perf_counter_ns()
        self.drain()
        self.calls += 1
        call = self.calls
        row = {
            "type": "generation",
            "call": call,
            "pid": os.getpid(),
            "cache_flags": {
                key: kwargs.get(key, True)
                for key in ("use_prefix_text_kv_cache", "use_prefix_pack_templates", "use_prefix_projection_cache")
            },
            "gc": [],
            "gc_dropped": 0,
        }
        row["host_before"] = self.collect("host_before", host_snapshot)
        row["cuda_before"] = self.collect("cuda_before", self.cuda_snapshot)
        row["compile_before"] = self.collect("compile_before", lambda: compile_counts(self.torch))
        events = self.collect("event_start", self.start_events)
        self.active = row
        begin = time.perf_counter_ns()
        row["call_start_ns"] = begin
        row["observer_pre_ns"] = begin - entry
        try:
            result = self.original(instance, *args, **kwargs)
        except BaseException as error:
            row["outcome"], row["exception_type"] = "raised", type(error).__name__
            raise
        else:
            row["outcome"] = "returned"
            return result
        finally:
            finish = time.perf_counter_ns()
            self.active = None
            self.gc_starts.clear()
            row["call_end_ns"] = finish
            row["host_wall_ms"] = (finish - begin) / 1e6
            if events is not None:
                start, end, current = events
                try:
                    end.record(current)
                    self.pending[call] = (start, end)
                except Exception as error:
                    self.error("event_end", error)
            row["host_after"] = self.collect("host_after", host_snapshot)
            row["cuda_after"] = self.collect("cuda_after", self.cuda_snapshot)
            row["compile_after"] = self.collect("compile_after", lambda: compile_counts(self.torch))
            row["observer_post_before_write_ns"] = time.perf_counter_ns() - finish
            self.emit(row)
            self.drain()
            if len(self.pending) > 256:
                oldest = next(iter(self.pending))
                self.emit({"type": "cuda_span_unavailable", "call": oldest, "reason": "pending_limit"})
                del self.pending[oldest]
                self.error("pending_limit", RuntimeError())

    def __enter__(self):
        @functools.wraps(self.original)
        def observed(instance, *args, **kwargs):
            return self.invoke(instance, args, kwargs)

        self.wrapper = observed
        setattr(self.model_class, METHOD, observed)
        gc.callbacks.append(self.gc_callback)
        return self

    def __exit__(self, *exception):
        if getattr(self.model_class, METHOD) is self.wrapper:
            if self.had_own_method:
                setattr(self.model_class, METHOD, self.previous_owned)
            else:
                delattr(self.model_class, METHOD)
        else:
            self.error("method_replaced_by_runner", RuntimeError())
        if self.gc_callback in gc.callbacks:
            gc.callbacks.remove(self.gc_callback)
        self.drain()
        for call in self.pending:
            self.emit({"type": "cuda_span_unavailable", "call": call, "reason": "not_ready_no_added_sync"})
        self.pending.clear()
        self.emit(
            {
                "type": "observer_summary",
                "calls": self.calls,
                "errors": self.errors,
                "cuda_events": self.cuda_events,
                "added_cuda_synchronizations": 0,
            }
        )
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cuda-device", type=int, default=0, help="CUDA-visible index, not physical GPU index")
    parser.add_argument("--no-cuda-events", action="store_true", help="host-only control for diagnostic perturbation")
    parser.add_argument("runner_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    root, runner, out = args.root.resolve(), args.runner.resolve(), args.out.resolve()
    if root in out.parents or out == root or root in runner.parents:
        raise ValueError("probe output and existing replay runner must remain outside the formal worktree")
    require_formal(before := source_identity(root))
    runner_hash = hashlib.sha256(runner.read_bytes()).hexdigest()
    out.mkdir(parents=True, exist_ok=False)
    metadata = {
        "status": "RUNNING",
        "source_before": before,
        "runner": str(runner),
        "runner_sha256": runner_hash,
        "runner_args": args.runner_args,
        "case": "K16/source64 only; runner retains input and numerical assertions",
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "pid": os.getpid(),
        "observational_only": True,
        "env": {k: os.environ.get(k) for k in ("CUDA_VISIBLE_DEVICES", "OMP_NUM_THREADS", "TORCH_LOGS")},
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    saved_argv, saved_cwd, saved_path = sys.argv, Path.cwd(), sys.path[:]
    forwarded = args.runner_args[1:] if args.runner_args[:1] == ["--"] else args.runner_args
    original_raised = False
    probe = None
    try:
        sys.path[:0] = [str(root), str(root / "cosmos-framework"), str(runner.parent)]
        import torch
        from cosmos_framework.model.generator.omni_mot_model import OmniMoTModel

        sys.argv = [str(runner), *forwarded]
        os.chdir(root)
        with (out / "generation.jsonl").open("x") as stream:
            with GenerationProbe(
                OmniMoTModel, torch, stream, cuda_device=args.cuda_device, cuda_events=not args.no_cuda_events
            ) as probe:
                try:
                    runpy.run_path(str(runner), run_name="__main__")
                except SystemExit as exit_status:
                    if exit_status.code not in (None, 0):
                        raise
        metadata["status"] = "RECORDED" if probe.calls and not probe.errors else "DIAGNOSTIC_INCOMPLETE"
    except BaseException as error:
        original_raised = True
        metadata["status"] = "RUNNER_RAISED"
        metadata["runner_exception_type"] = type(error).__name__
        raise
    finally:
        sys.argv = saved_argv
        sys.path[:] = saved_path
        os.chdir(saved_cwd)
        try:
            after = source_identity(root)
            require_formal(after)
            metadata["source_after"] = after
            metadata["source_unchanged"] = after == before
            metadata["runner_unchanged"] = hashlib.sha256(runner.read_bytes()).hexdigest() == runner_hash
            if not metadata["source_unchanged"] or not metadata["runner_unchanged"]:
                metadata["status"] = "SOURCE_CHANGED"
        except Exception as error:
            metadata["status"], metadata["identity_error"] = "SOURCE_CHECK_FAILED", type(error).__name__
        metadata["calls"] = 0 if probe is None else probe.calls
        metadata["observer_errors"] = [] if probe is None else probe.errors
        try:
            (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        except OSError:
            if not original_raised:
                raise
    return 0 if metadata["status"] == "RECORDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
