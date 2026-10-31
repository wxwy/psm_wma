"""CPU pipes and fake processes for the initialization/training display boundary."""

from __future__ import annotations

import importlib.util
import os
import signal
import subprocess

import pytest

from tools.v3 import no_ttt_console_test as base

START = base.START.encode()
PROGRESS = base.PROGRESS.encode()


@pytest.fixture
def display(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("boundary_console", base.HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    read_fd, write_fd = os.pipe()
    path = tmp_path / "raw.log"
    log_fd = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
    output = module._Output(os.fdopen(read_fd, "rb", buffering=0), log_fd)
    expected, visible = bytearray(), []

    def console(fd, value):
        assert fd == 1
        assert path.read_bytes() == expected  # Raw bytes must precede display.
        visible.append(value if isinstance(value, bytes) else value.encode())

    monkeypatch.setattr(module, "_console", console)

    def feed(piece):
        assert len(piece) <= 4096  # No blocked producer on a real small pipe.
        expected.extend(piece)
        assert os.write(write_fd, piece) == len(piece)
        output.poll(0)
        assert len(output.pending) <= 16384

    try:
        yield feed, output, visible, path
    finally:
        output.close()
        os.close(write_fd)
        os.close(log_fd)


def test_boundary_and_following_noise_in_same_read_keep_marker_and_rank0(display):
    feed, output, visible, path = display
    initial = b"environment\nmodel loaded\nDCP Resume restored\nconfig\n"
    raw = initial + START + b"loader JSON\n" + PROGRESS
    raw += b"[rank1] [CorrectedV3][progress] hidden\ncheckpoint details\n"
    feed(raw)
    assert output.training_started
    assert b"".join(visible) == initial + START + PROGRESS
    assert path.read_bytes() == raw


@pytest.mark.parametrize(
    "marker",
    [
        b"Starting training...\n",
        START,
        b"\x1b[32m" + START.rstrip(b"\n") + b"\x1b[0m\n",
        b"[10-31 15:00:00|[Node0/1][RANK0/4][MainProcess]| INFO|"
        b"cosmos_framework/trainer/__init__.py:999:train] Starting training...\n",
        b"[10-31 15:00:00|INFO|/workspace/project/cosmos_framework/trainer/"
        b"__init__.py:330:train] Starting training...\r\n",
    ],
)
def test_complete_fragmented_plain_or_actual_log_format_switches_once(display, marker):
    feed, output, visible, _ = display
    initial = "初始化和 Checkpoint 恢复中\n".encode()
    for piece in [initial, *(bytes([x]) for x in marker)]:
        feed(piece)
    assert output.training_started
    feed(b"hidden before progress\n" + PROGRESS + START + b"hidden after repeat\n")
    assert b"".join(visible) == initial + marker + PROGRESS


@pytest.mark.parametrize(
    "not_marker",
    [
        b'{"message":"Starting training..."}\n',
        b"configuration: Starting training...\n",
        b"[rank1] Starting training...\n",
        START.replace(b"|INFO|", b"|DEBUG|"),
        START.replace(b":train]", b":validate]"),
        START.replace(b"cosmos_framework/trainer/__init__.py", b"dataset.py"),
        START.rstrip(b"\n") + b" is only a quoted setting\n",
    ],
)
def test_message_in_config_wrong_source_or_rank_does_not_hide_initialization(
    display, not_marker
):
    feed, output, visible, _ = display
    initial = not_marker + b"DCP Resume still running\n"
    feed(initial)
    assert not output.training_started and b"".join(visible) == initial
    feed(START + b"hidden loader details\n" + PROGRESS)
    assert b"".join(visible) == initial + START + PROGRESS


def test_partial_marker_is_visible_immediately_but_switch_waits_for_newline(display):
    feed, output, visible, _ = display
    fragment = START.rstrip(b"\n")
    feed(fragment)
    assert not output.training_started and b"".join(visible) == fragment
    feed(b"\nloader JSON\n" + PROGRESS)
    assert output.training_started and b"".join(visible) == START + PROGRESS


def test_large_invalid_utf8_initialization_is_streamed_and_buffer_is_bounded(display):
    feed, output, visible, path = display
    initial = "恢复数据集 🌟".encode() + b"\xff\xfe" + b"x" * 70000
    for start in range(0, len(initial), 1024):
        feed(initial[start : start + 1024])
    assert b"".join(visible) == initial and not output.training_started
    feed(b"\n" + START)
    noise = b"loader JSON=" + b"y" * 90000 + b"\n"
    for start in range(0, len(noise), 1024):
        feed(noise[start : start + 1024])
    feed(PROGRESS + b"hidden unterminated training diagnostic")
    assert b"".join(visible) == initial + b"\n" + START + PROGRESS
    assert path.read_bytes().startswith(initial + b"\n" + START + noise)
    assert path.read_bytes().endswith(b"hidden unterminated training diagnostic")


def test_markerless_eof_keeps_all_initial_bytes_including_unterminated_text(tmp_path):
    raw = b"DCP Resume in progress\n\xff\xfetail without newline"
    command = base._script(tmp_path, f"import os\nos.write(1,{raw!r})\n")
    result = base._run(base._command(tmp_path, command))
    assert result.returncode == 0 and not result.stderr
    assert result.stdout.split(b"\n", 1)[1] == raw
    assert base._logs(tmp_path)[0].read_bytes() == raw


def test_initialization_failure_remains_visible_and_nonzero(tmp_path):
    raw = b"loading model\nTraceback: synthetic DCP Resume failure\n"
    command = base._script(
        tmp_path, f"import os\nos.write(2,{raw!r})\nraise SystemExit(9)\n"
    )
    result = base._run(base._command(tmp_path, command))
    assert result.returncode == 9
    assert result.stdout.split(b"\n", 1)[1] == raw
    assert b"[NoTTT][failed] exit=9" in result.stderr
    assert b"synthetic DCP Resume failure" in result.stderr
    assert base._logs(tmp_path)[0].read_bytes() == raw


def test_each_resume_starts_with_full_initialization_and_preserves_prior_log(tmp_path):
    raws = []
    for invocation in range(2):
        initial = f"Resume initialization {invocation}\n".encode()
        raw = initial + START + b"hidden loader telemetry\n" + PROGRESS
        raws.append(raw)
        command = base._script(tmp_path, f"import os\nos.write(1,{raw!r})\n")
        result = base._run(base._command(tmp_path, command))
        assert result.returncode == 0 and not result.stderr
        assert result.stdout.split(b"\n", 1)[1] == initial + START + PROGRESS
    logs = base._logs(tmp_path)
    assert len(logs) == 2 and {p.read_bytes() for p in logs} == set(raws)


def test_real_supervisor_streams_incomplete_resume_log_before_starting_training(
    tmp_path,
):
    initial = "DCP Resume 恢复中，尚未换行".encode()
    after = b"\n" + START + b"hidden loader telemetry\n" + PROGRESS
    command = base._script(
        tmp_path,
        f"import os,sys\nos.write(1,{initial!r})\nsys.stdin.buffer.read(1)\n"
        f"os.write(1,{after!r})\n",
    )
    process = subprocess.Popen(
        base._command(tmp_path, command),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        first = base._read_until(process, initial)
        assert (
            process.poll() is None and base._logs(tmp_path)[0].read_bytes() == initial
        )
        rest, err = process.communicate(input=b"x", timeout=12)
        assert process.returncode == 0 and not err
        assert (first + rest).split(b"\n", 1)[1] == initial + b"\n" + START + PROGRESS
        assert base._logs(tmp_path)[0].read_bytes() == initial + after
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            process.communicate(timeout=12)
