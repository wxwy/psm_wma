"""Only fake shell training/processes. No Torch, dataset, model or GPU imports."""

from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/no_ttt_console.py"
PROGRESS = "[CorrectedV3][progress] step=1/30000 loss=1.25\n"
RAW = (
    "Cosmos initializing\n"
    "[rank1] warning: synthetic rank1\n"
    '[NoTTT][cpu_loader] {"wait_ms":3}\n'
    + PROGRESS
    + '[CorrectedV3][train] {"iteration":1}\n'
    + "[CorrectedV3][checkpoint] saved\n"
    + "stderr Traceback: synthetic test diagnostic\n"
    + "[rank1] [CorrectedV3][progress] must not echo\n"
)


def _script(tmp_path, source):
    path = tmp_path / "fake_training.py"
    path.write_text(source)
    return [sys.executable, str(path)]


def _command(tmp_path, command, *, job="no_ttt_shell_test"):
    return [
        sys.executable,
        str(HELPER),
        str(tmp_path / "output root"),
        job,
        "--",
        *command,
    ]


def _logs(tmp_path):
    return list((tmp_path / "output root/_launch_logs").rglob("launch_*.log"))


def _run(command, *, env=None):
    return subprocess.run(command, capture_output=True, env=env, timeout=15)


def _read_until(process, marker, timeout=5):
    result = b""
    until = time.monotonic() + timeout
    while marker not in result and time.monotonic() < until:
        if select.select([process.stdout], [], [], 0.05)[0]:
            chunk = os.read(process.stdout.fileno(), 65536)
            if not chunk:
                break
            result += chunk
    assert marker in result, result
    return result


@pytest.mark.parametrize("code", [0, 7])
def test_full_stdout_stderr_saved_before_progress_copy_and_exact_exit(tmp_path, code):
    marker = tmp_path / "namespace_checked.json"
    command = _script(
        tmp_path,
        f"import os,json,pathlib\n"
        f"assert not pathlib.Path({str(tmp_path / 'output root/no_ttt_shell_test')!r}).exists()\n"
        f"pathlib.Path({str(marker)!r}).write_text(json.dumps(dict(unbuffered=os.environ.get('PYTHONUNBUFFERED'))))\n"
        f"os.write(1,{RAW[: RAW.index('stderr')].encode()!r})\n"
        f"os.write(2,{RAW[RAW.index('stderr') :].encode()!r})\nraise SystemExit({code})\n",
    )
    result = _run(_command(tmp_path, command))
    assert result.returncode == code
    lines = result.stdout.decode().splitlines(keepends=True)
    assert lines[0].startswith("[NoTTT][log] full log: ")
    assert lines[1:] == [PROGRESS]
    assert len(_logs(tmp_path)) == 1 and _logs(tmp_path)[0].read_bytes() == RAW.encode()
    assert json.loads(marker.read_text()) == {"unbuffered": "1"}
    assert not (tmp_path / "output root/no_ttt_shell_test").exists()
    if code:
        assert b"[NoTTT][failed] exit=7" in result.stderr
        assert b"stderr Traceback: synthetic test diagnostic" in result.stderr
        assert os.fsencode(_logs(tmp_path)[0]) in result.stderr
    else:
        assert not result.stderr


def test_warning_only_no_progress_is_not_an_empty_grep_failure(tmp_path):
    command = _script(
        tmp_path, "import os\nos.write(2,b'warning only; not a failed process\\n')\n"
    )
    result = _run(_command(tmp_path, command))
    assert result.returncode == 0 and not result.stderr
    assert len(result.stdout.splitlines()) == 1
    assert _logs(tmp_path)[0].read_bytes() == b"warning only; not a failed process\n"


def test_each_resume_uses_exclusive_new_log_without_overwriting_history(tmp_path):
    command = _script(tmp_path, f"import os\nos.write(1,{PROGRESS.encode()!r})\n")
    args = _command(tmp_path, command)
    for _ in range(3):
        assert _run(args).returncode == 0
    logs = _logs(tmp_path)
    assert len(logs) == 3 and len({path.name for path in logs}) == 3
    assert all(
        path.read_bytes() == PROGRESS.encode() and path.stat().st_mode & 0o077 == 0
        for path in logs
    )


def test_unbuffered_partial_line_huge_json_and_invalid_bytes_preserve_all_raw(tmp_path):
    raw = (
        b"json="
        + b"x" * 200000
        + b"\n\xff\xfe\n"
        + PROGRESS.encode()
        + b"unterminated diagnostic"
    )
    command = _script(
        tmp_path,
        f"import os\nraw={raw!r}\nfor start in range(0,len(raw),7): os.write(1,raw[start:start+7])\n",
    )
    result = _run(_command(tmp_path, command))
    assert result.returncode == 0
    assert result.stdout.decode().splitlines(keepends=True)[1:] == [PROGRESS]
    assert _logs(tmp_path)[0].read_bytes() == raw


def test_progress_is_visible_while_training_runs_and_already_present_in_log(tmp_path):
    command = _script(
        tmp_path,
        f"import os,time\nos.write(1,{PROGRESS.encode()!r})\ntime.sleep(120)\n",
    )
    process = subprocess.Popen(
        _command(tmp_path, command), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        visible = _read_until(process, PROGRESS.encode())
        assert visible.startswith(b"[NoTTT][log]")
        assert (
            process.poll() is None
            and _logs(tmp_path)[0].read_bytes() == PROGRESS.encode()
        )
        process.send_signal(signal.SIGTERM)
        _, err = process.communicate(timeout=12)
        assert process.returncode == 143 and b"[NoTTT][failed] exit=143" in err
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            process.communicate(timeout=12)


def test_log_open_failure_never_starts_training(tmp_path):
    root = tmp_path / "output root"
    root.mkdir()
    (root / "_launch_logs").write_text("cannot replace this existing file")
    marker = tmp_path / "must_not_execute"
    command = _script(
        tmp_path, f"import pathlib\npathlib.Path({str(marker)!r}).touch()\n"
    )
    result = _run(_command(tmp_path, command))
    assert result.returncode != 0 and b"[NoTTT][failed]" in result.stderr
    assert (
        not marker.exists()
        and (root / "_launch_logs").read_text() == "cannot replace this existing file"
    )


@pytest.mark.parametrize("fault", ["write", "sync", "selector"])
def test_log_write_sync_or_pipe_setup_error_is_fail_closed_with_diagnosis(
    tmp_path, fault
):
    pid_file = tmp_path / "owned_pid"
    command = _script(
        tmp_path,
        f"import os,pathlib,time\npathlib.Path({str(pid_file)!r}).write_text(str(os.getpid()))\n"
        + (
            f"os.write(1,{PROGRESS.encode()!r})\ntime.sleep(120)\n"
            if fault == "write"
            else "print('done')\n"
        ),
    )
    # Fault injection exists ONLY in this standalone CPU test bootstrap.
    bootstrap = tmp_path / "fault_bootstrap.py"
    patches = {
        "write": "original=os.write\ndef bad(fd,data):\n if fd>2: raise OSError(28,'synthetic ENOSPC')\n return original(fd,data)\nos.write=bad\n",
        "sync": "def bad(fd): raise OSError(5,'synthetic fsync error')\nos.fsync=bad\n",
        "selector": "def bad(*a,**k): raise OSError(24,'synthetic selector error')\nselectors.DefaultSelector=bad\n",
    }
    bootstrap.write_text(
        "import os,runpy,sys,selectors\n"
        + patches[fault]
        + f"sys.argv={_command(tmp_path, command)[1:]!r}\n"
        + f"runpy.run_path({str(HELPER)!r},run_name='__main__')\n"
    )
    result = _run([sys.executable, str(bootstrap)])
    assert result.returncode != 0 and b"[NoTTT][failed]" in result.stderr
    assert b"synthetic" in result.stderr and b"full log:" in result.stderr
    assert len(_logs(tmp_path)) == 1
    if fault == "write":
        assert PROGRESS.encode() not in b"".join(
            result.stdout.splitlines(keepends=True)[1:]
        )
    if pid_file.exists():
        assert not Path(f"/proc/{int(pid_file.read_text())}").exists()


def test_command_exec_failure_has_log_and_explicit_nonzero(tmp_path):
    result = _run(_command(tmp_path, [str(tmp_path / "missing-executable")]))
    assert (
        result.returncode != 0
        and b"No such file" in result.stderr
        and b"[NoTTT][failed]" in result.stderr
    )
    assert len(_logs(tmp_path)) == 1


def _tree_command(tmp_path, *, late=False, exit_code=None):
    ready = tmp_path / "ready.json"
    child_code = (
        "import signal,time,pathlib,os; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
        f"pathlib.Path({str(tmp_path)!r},'rank_ready_'+str(os.getpid())).touch(); time.sleep(120)"
    )
    body = (
        "import os,sys,json,pathlib,signal,subprocess,time\n"
        f"children=[subprocess.Popen([sys.executable,'-c',{child_code!r}],start_new_session=True)]\n"
        f"ready=pathlib.Path({str(ready)!r})\n"
        "def publish(): ready.write_text(json.dumps([os.getpid(),*[p.pid for p in children]]))\n"
    )
    if late:
        body += (
            "def stop(sig,frame):\n"
            f" children.append(subprocess.Popen([sys.executable,'-c',{child_code!r}],start_new_session=True))\n publish()\n"
            "signal.signal(signal.SIGTERM,stop)\n"
        )
    body += "publish()\nprint('[CorrectedV3][progress] tree-ready',flush=True)\n"
    body += (
        f"raise SystemExit({exit_code})\n"
        if exit_code is not None
        else "while True: time.sleep(.05)\n"
    )
    return _script(tmp_path, body), ready


@pytest.mark.parametrize(
    "sig,late",
    [(signal.SIGINT, False), (signal.SIGTERM, False), (signal.SIGTERM, True)],
)
def test_interrupt_reaps_separate_session_ranks_including_late_child_and_spares_foreign(
    tmp_path, sig, late
):
    command, ready = _tree_command(tmp_path, late=late)
    foreign = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    process = subprocess.Popen(
        _command(tmp_path, command), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        until = time.monotonic() + 5
        initial = None
        while time.monotonic() < until:
            try:
                initial = json.loads(ready.read_text())
                if all(
                    (tmp_path / f"rank_ready_{pid}").exists() for pid in initial[1:]
                ):
                    break
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            time.sleep(0.01)
        assert initial and all(
            (tmp_path / f"rank_ready_{pid}").exists() for pid in initial[1:]
        )
        process.send_signal(sig)
        out, err = process.communicate(timeout=12)
        owned = json.loads(ready.read_text())
        assert process.returncode == 128 + sig
        assert f"[NoTTT][failed] exit={128 + sig}".encode() in err
        assert all(not Path(f"/proc/{pid}").exists() for pid in owned)
        assert foreign.poll() is None
        assert len(owned) == (3 if late else 2)
        assert (
            out.startswith(b"[NoTTT][log]")
            and b"tree-ready" in _logs(tmp_path)[0].read_bytes()
        )
        print(
            json.dumps(
                {
                    "signal": int(sig),
                    "late_child": late,
                    "owned_reaped": owned,
                    "foreign_survived": True,
                }
            )
        )
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            process.communicate(timeout=12)
        foreign.terminate()
        foreign.wait(timeout=5)


def test_failed_parent_exit_cannot_leave_rank_holding_log_pipe_forever(tmp_path):
    command, ready = _tree_command(tmp_path, exit_code=7)
    result = _run(_command(tmp_path, command))
    assert result.returncode == 7 and b"[NoTTT][failed] exit=7" in result.stderr
    assert all(
        not Path(f"/proc/{pid}").exists() for pid in json.loads(ready.read_text())
    )


@pytest.mark.parametrize("world", [4, 8])
def test_real_standard_launcher_default_split_preserves_original_fake_training_argv_and_env(
    tmp_path, world
):
    script = (
        ROOT
        / "scripts"
        / (
            "train_v3_matched_no_ttt_4gpu.sh"
            if world == 4
            else "train_v3_matched_no_ttt.sh"
        )
    )
    capture = tmp_path / "argv.json"
    fake = tmp_path / "fake python"
    fake.write_text(
        f"#!{sys.executable}\nimport os,json,pathlib,sys\n"
        f"pathlib.Path({str(capture)!r}).write_text(json.dumps(dict(argv=sys.argv[1:],cwd=os.getcwd(),"
        "env={k:os.environ[k] for k in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONUNBUFFERED','JOB_NAME')})))\n"
        f"os.write(1,{RAW.encode()!r})\n"
    )
    fake.chmod(0o755)
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("NOTTT_")
    }
    env.update(
        PYTHON=str(fake),
        JOB_NAME="no_ttt_shell_world4_ga4" if world == 4 else "no_ttt_shell_world8_ga2",
    )
    for key in (
        "OUTPUT_ROOT",
        "SOURCE_ROOT",
        "CACHE_ROOT",
        "DATASET_INDEX_ROOT",
        "EDGE_POLICY_CHECKPOINT",
        "WAN_VAE_PATH",
        "BASE_CHECKPOINT_PATH",
        "EXPECTED_ROOT",
        "EXPECTED_CHILD",
    ):
        env[key] = str(tmp_path / f"{key} with spaces")
    env.pop("CUDA_VISIBLE_DEVICES", None)
    result = _run(["bash", str(script), "resume", "12220"], env=env)
    assert result.returncode == 0 and result.stdout.decode().splitlines(keepends=True)[
        1:
    ] == [PROGRESS]
    data = json.loads(capture.read_text())
    assert data["argv"][:4] == [
        "-m",
        "torch.distributed.run",
        "--standalone",
        f"--nproc_per_node={world}",
    ]
    assert data["cwd"] == str(ROOT / "cosmos-framework")
    for key, value in {
        "--ga": "4" if world == 4 else "2",
        "--world-size": str(world),
        "--t": "16",
        "--b": "8",
        "--max-iter": "30000",
        "--warmup": "500",
        "--save-iter": "100",
        "--formal-execution-until": "12220",
        "--phase": "resume",
    }.items():
        assert data["argv"][data["argv"].index(key) + 1] == value
    assert (
        data["env"]["PYTHONUNBUFFERED"]
        == data["env"]["HF_HUB_OFFLINE"]
        == data["env"]["TRANSFORMERS_OFFLINE"]
        == "1"
    )
    logs = list(
        (Path(env["OUTPUT_ROOT"]) / "_launch_logs" / env["JOB_NAME"]).glob("*.log")
    )
    assert len(logs) == 1 and logs[0].read_bytes() == RAW.encode()


@pytest.mark.parametrize("world", [4, 8])
@pytest.mark.parametrize("phase", ["fresh", "resume"])
def test_entire_training_command_and_key_env_equal_frozen_original(
    tmp_path, world, phase
):
    name = (
        "train_v3_matched_no_ttt_4gpu.sh"
        if world == 4
        else "train_v3_matched_no_ttt.sh"
    )
    root = tmp_path / "synthetic worktree"
    scripts, child = root / "scripts", root / "cosmos-framework"
    scripts.mkdir(parents=True)
    (child / "examples").mkdir(parents=True)
    (child / "examples/psm_wma_robocasa_corrected_phase5.py").touch()
    launcher = scripts / name
    (scripts / "no_ttt_console.py").write_bytes(HELPER.read_bytes())
    capture = tmp_path / "capture.json"
    fake = tmp_path / "capture python"
    keys = [
        "CUDA_VISIBLE_DEVICES",
        "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE",
        "PYTHONPATH",
        "JOB_NAME",
        "NOTTT_LOADER_WORKERS",
        "NOTTT_PREFETCH_FACTOR",
        "NOTTT_PERSISTENT_WORKERS",
        "NOTTT_LOADER_TIMEOUT_S",
    ]
    fake.write_text(
        f"#!{sys.executable}\nimport os,sys,json,pathlib\n"
        f"pathlib.Path({str(capture)!r}).write_text(json.dumps(dict(argv=sys.argv,cwd=os.getcwd(),"
        f"env={{key:os.environ.get(key) for key in {keys!r}}})))\n"
        "print('[CorrectedV3][progress] captured')\n"
    )
    fake.chmod(0o755)
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("NOTTT_")
    }
    env.pop("CUDA_VISIBLE_DEVICES", None)
    env.update(
        PYTHON=str(fake),
        JOB_NAME="no_ttt_frozen_world4_ga4"
        if world == 4
        else "no_ttt_frozen_world8_ga2",
    )
    if world == 4:
        env.update(
            NOTTT_LOADER_WORKERS="8",
            NOTTT_PREFETCH_FACTOR="1",
            NOTTT_PERSISTENT_WORKERS="1",
            NOTTT_LOADER_TIMEOUT_S="120",
        )
    for key in (
        "OUTPUT_ROOT",
        "SOURCE_ROOT",
        "CACHE_ROOT",
        "DATASET_INDEX_ROOT",
        "EDGE_POLICY_CHECKPOINT",
        "WAN_VAE_PATH",
        "BASE_CHECKPOINT_PATH",
        "EXPECTED_ROOT",
        "EXPECTED_CHILD",
    ):
        env[key] = str(tmp_path / f"{key} with spaces")
    launcher.write_bytes(
        subprocess.check_output(
            ["git", "show", f"3332d1825de8778e3d6dbb7e9ba98cbffff487c6:scripts/{name}"],
            cwd=ROOT,
        )
    )
    original = _run(["bash", str(launcher), phase, "12220"], env=env)
    assert original.returncode == 0
    expected = json.loads(capture.read_text())
    launcher.write_bytes((ROOT / "scripts" / name).read_bytes())
    current = _run(["bash", str(launcher), phase, "12220"], env=env)
    assert current.returncode == 0
    assert json.loads(capture.read_text()) == expected
    assert current.stdout.splitlines()[1:] == [b"[CorrectedV3][progress] captured"]
