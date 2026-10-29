"""External, one-case observer: no runtime changes until run() has returned."""

import functools
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

import pytest

NODE = "tools/v3/eval_v2_production_tests/scheduler_test.py::test_900_exact_episode_major_dispatch_real_store_path_and_index_no_model_per_episode"
OUT = Path(os.environ["SYNTHETIC900_DIAGNOSTIC_DIR"])
CALLS = 0


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def pytest_collection_modifyitems(items):
    if [item.nodeid for item in items] != [NODE]:
        raise pytest.UsageError("diagnostic requires exactly the original single nodeid")


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_call(item):
    from robocasa_eval_v2 import runtime

    assert item.nodeid == NODE
    original = runtime.Runtime.run
    code_path = Path(original.__code__.co_filename).resolve()
    root = Path.cwd().resolve()
    assert code_path == root / "scripts/robocasa_eval_v2/runtime.py"
    save("instrumentation.json", {
        "nodeid": NODE,
        "module_file": runtime.__file__,
        "original_code_file": str(code_path),
        "original_code_sha256": hashlib.sha256(code_path.read_bytes()).hexdigest(),
        "plugin_file": __file__,
        "plugin_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "observes_only_after_run_returns_or_raises": True,
        "traceback_includes_locals": False,
    })

    def capture(self, error, report, mode, elapsed):
        try:
            frames = [] if error is None else [
                {"file": frame.filename, "line": frame.lineno,
                 "function": frame.name, "source": frame.line}
                for frame in traceback.extract_tb(error.__traceback__)
            ]
            if error is not None:
                with (OUT / "internal_traceback.txt").open("x") as stream:
                    traceback.print_exception(type(error), error, error.__traceback__, file=stream)
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            save("runtime_return.json", {
                "calls": CALLS, "mode": mode,
                "elapsed_s": elapsed, "store_root": str(self.store.root),
                "runtime_class": f"{type(self).__module__}.{type(self).__qualname__}",
                "error_type": None if error is None else type(error).__name__,
                "error_repr": None if error is None else repr(error),
                "frames": frames, "report": report,
                "diagnostic": "INCONCLUSIVE" if error is None else "EXCEPTION_CAPTURED",
            })
        except Exception:
            print("DIAGNOSTIC_CAPTURE_FAILED", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

    @functools.wraps(original)
    def observed(self, *args, **kwargs):
        global CALLS
        CALLS += 1
        started = time.monotonic()
        try:
            result = original(self, *args, **kwargs)
        except BaseException as error:
            capture(self, error, None, "raised", time.monotonic() - started)
            raise
        capture(self, result[1], result[0], "returned", time.monotonic() - started)
        return result

    runtime.Runtime.run = observed
    try:
        yield
    finally:
        runtime.Runtime.run = original
        save("wrapper_restored.json", {"calls": CALLS, "restored": runtime.Runtime.run is original})
