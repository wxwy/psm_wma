"""Actual Numba cache writes stay outside the immutable simulator vendor source."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "robocasa_queue_cache_contract", ROOT / "scripts/eval_robocasa_18task_queue.py"
)
queue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(queue)


@pytest.mark.parametrize("explicit_hf", [False, True])
def test_launch_env_redirects_cache_writes_without_replacing_explicit_hf_home(tmp_path, monkeypatch, explicit_hf):
    monkeypatch.setenv("NUMBA_CACHE_DIR", str(tmp_path / "unsafe-vendor-cache"))
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "unsafe-matplotlib-cache"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "unsafe-xdg-cache"))
    if explicit_hf:
        monkeypatch.setenv("HF_HOME", str(tmp_path / "owner-huggingface"))
    else:
        monkeypatch.delenv("HF_HOME", raising=False)
    cache = tmp_path / "external-cache"
    env = queue.launch_environment(cache)
    for name in ("NUMBA_CACHE_DIR", "MPLCONFIGDIR", "XDG_CACHE_HOME"):
        assert Path(env[name]).is_relative_to(cache)
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert env["PYTHONPATH"].split(os.pathsep)[0] == str(queue.CHILD)
    if explicit_hf:
        assert env["HF_HOME"] == str(tmp_path / "owner-huggingface")
    else:
        assert Path(env["HF_HOME"]).is_relative_to(cache)
    assert os.environ["NUMBA_CACHE_DIR"] == str(tmp_path / "unsafe-vendor-cache")
    assert not cache.exists()  # Environment preparation itself is read-only.


def test_actual_numba_jit_cache_leaves_tracked_source_tree_clean(tmp_path, monkeypatch):
    source = tmp_path / "tracked-vendor"
    source.mkdir()
    module = source / "jit_module.py"
    module.write_text(
        "from numba import njit\n@njit(cache=True)\ndef square_plus_one(value):\n    return value * value + 1\n"
    )
    git = ["git", "-C", str(source)]
    subprocess.run([*git, "init", "-q"], check=True, capture_output=True)
    subprocess.run([*git, "add", "jit_module.py"], check=True, capture_output=True)
    subprocess.run(
        [
            *git,
            "-c",
            "user.name=CPU Fixture",
            "-c",
            "user.email=cpu-fixture@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
        capture_output=True,
    )
    original = module.read_bytes()
    cache = tmp_path / "external-cache"
    env = queue.launch_environment(cache)
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["MUJOCO_GL"] = "disable"
    # This is an explicit CPU dependency, not a skipped proof if Numba is absent.
    executable = os.environ.get("PSM_NUMBA_PYTHON", sys.executable)
    run = subprocess.run(
        [
            executable,
            "-B",
            "-c",
            "import json, jit_module; print(json.dumps({'result': jit_module.square_plus_one(7)}))",
        ],
        env=env,
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert json.loads(run.stdout)["result"] == 50
    assert list(Path(env["NUMBA_CACHE_DIR"]).rglob("*.nbi"))
    assert list(Path(env["NUMBA_CACHE_DIR"]).rglob("*.nbc"))
    assert not list(source.rglob("__pycache__"))
    assert module.read_bytes() == original
    assert subprocess.check_output([*git, "status", "--porcelain=v1", "--untracked-files=all"], text=True) == ""
