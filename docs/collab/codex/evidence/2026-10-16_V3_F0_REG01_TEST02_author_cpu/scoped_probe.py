"""Author-only CPU reproduction; not the DS V2 full-dependency environment."""

from __future__ import annotations

import ast
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

CHILD = Path("/workspace/psm_wma/cosmos-framework")
OUT = Path(__file__).resolve().parent
BASE = "0fb7f587f56048a8ffaa12e2fdb7891abc0fb021"
PROD = "examples/psm_wma_robocasa_corrected_phase5.py"
TEST = "examples/psm_wma_robocasa_phase5_f0_test.py"
REGRESSION = "examples/psm_wma_robocasa_corrected_phase5_test.py"


def original(name):
    return subprocess.check_output(["git", "-C", str(CHILD), "show", f"{BASE}:{name}"], text=True)


def load_source(name, source, path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def run_trainer_cases(label, source):
    module = load_source("f0_probe_" + label, source, CHILD / TEST)
    stream = io.StringIO()
    with tempfile.TemporaryDirectory() as directory:
        # A real external module execution (rather than __getattr__) is required:
        # import-from converts a missing attribute into ImportError, which the
        # Trainer intentionally handles as optional-Megatron absence.
        Path(directory, "core.py").write_text("import torch\nannotation_dtype = torch.dtype\nparallel_state = None\n")
        parent = types.ModuleType("megatron")
        parent.__path__ = [directory]
        with patch.dict(sys.modules, {"megatron": parent}):
            sys.modules.pop("megatron.core", None)
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(module.TrainerTests)
            names = [case.id().split(".")[-1] for case in suite]
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (OUT / f"{label}_trainer9.log").write_text(stream.getvalue())
    return {
        "names": names,
        "run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
    }


def run_original_regression(label, phase_source):
    phase = load_source("f0_phase_" + label, phase_source, CHILD / PROD)
    tree = ast.parse((CHILD / REGRESSION).read_text())
    names = {"_bounded_args", "test_formal_and_resume_require_accepted_index_before_data_open"}
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    module = ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *functions],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    environment = {"Path": Path, "SimpleNamespace": types.SimpleNamespace, "pytest": pytest, "phase5": phase}
    exec(compile(module, str(CHILD / REGRESSION), "exec"), environment)
    try:
        with tempfile.TemporaryDirectory() as directory:
            environment["test_formal_and_resume_require_accepted_index_before_data_open"](Path(directory))
    except Exception as exc:
        return {"passed": False, "exception": f"{type(exc).__name__}: {exc}"}
    return {
        "passed": True,
        "scope": "unchanged function/helper AST, original pytest.raises assertions; full module imports not executed",
    }


def main():
    old_prod, old_test = original(PROD), original(TEST)
    new_prod, new_test = (CHILD / PROD).read_text(), (CHILD / TEST).read_text()
    assert (CHILD / REGRESSION).read_text() == original(REGRESSION)
    old_tree, new_tree = ast.parse(old_prod), ast.parse(new_prod)
    old_pre = next(n for n in old_tree.body if isinstance(n, ast.FunctionDef) and n.name == "preflight")
    new_pre = next(n for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name == "preflight")
    assert sorted(map(ast.dump, old_pre.body)) == sorted(map(ast.dump, new_pre.body))
    old_tree.body.remove(old_pre)
    new_tree.body.remove(new_pre)
    assert ast.dump(old_tree) == ast.dump(new_tree)
    report = {
        "environment": "minimal CPU + explicit annotation-evaluating Megatron stand-in; NOT real full V2",
        "unchanged_regression_sha256": hashlib.sha256((CHILD / REGRESSION).read_bytes()).hexdigest(),
        "production_change_is_only_preflight_guard_reordering": True,
        "before_regression": run_original_regression("before", old_prod),
        "after_regression": run_original_regression("after", new_prod),
        "before_trainer": run_trainer_cases("before", old_test),
        "after_trainer": run_trainer_cases("after", new_test),
    }
    assert report["before_regression"]["passed"] is False
    assert report["after_regression"]["passed"] is True
    assert report["before_trainer"]["run"] == report["before_trainer"]["errors"] == 9
    assert report["after_trainer"]["run"] == 9
    assert (
        report["after_trainer"]["errors"]
        == report["after_trainer"]["failures"]
        == report["after_trainer"]["skipped"]
        == 0
    )
    assert report["before_trainer"]["names"] == report["after_trainer"]["names"]
    old_class = next(n for n in ast.parse(old_test).body if isinstance(n, ast.ClassDef) and n.name == "TrainerTests")
    new_class = next(n for n in ast.parse(new_test).body if isinstance(n, ast.ClassDef) and n.name == "TrainerTests")
    for old_case, new_case in zip(old_class.body, new_class.body):
        if not isinstance(old_case, ast.FunctionDef) or not old_case.name.startswith("test_"):
            continue
        old_assertions = [
            ast.dump(n)
            for n in ast.walk(old_case)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith("assert")
        ]
        new_assertions = [
            ast.dump(n)
            for n in ast.walk(new_case)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith("assert")
        ]
        assert old_assertions == new_assertions, old_case.name
    report["all_nine_existing_test_assertions_unchanged"] = True
    (OUT / "scoped_probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
