"""The final CPU entry must propagate PASS/FAIL/BLOCKED to its shell caller."""

import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("status", [0, 1])
def test_entry_propagates_underlying_gate_exit_code(monkeypatch, status):
    monkeypatch.syspath_prepend(str(ROOT / "tools/v3"))
    import run_eval_v2_transactions_b1_cpu_gate as base

    calls = []

    def complete(**kwargs):
        calls.append(kwargs)
        return status

    monkeypatch.setattr(base, "main", complete)
    with pytest.raises(SystemExit) as error:
        runpy.run_path(
            str(ROOT / "tools/v3/run_eval_v2_batch_b2_cpu_gate.py"), run_name="__main__"
        )
    assert error.value.code == status
    assert calls[0]["extra_tests"] == {
        "phase_b_runtime": ["tools/v3/eval_v2_batch_tests"]
    }


def test_actual_wrong_pair_is_nonzero_BLOCKED_before_project_tests(tmp_path):
    directory = tmp_path / "external_gate_evidence"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/v3/run_eval_v2_batch_b2_cpu_gate.py"),
            "--root-worktree",
            str(ROOT),
            "--expected-root",
            "0" * 40,
            "--expected-child",
            "1" * 40,
            "--evidence-dir",
            str(directory),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    gate = json.loads((directory / "gate.json").read_text())
    assert gate["status"] == "BLOCKED" and gate["steps"] == []
