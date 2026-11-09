"""Two early real Local requests; stop own native coordinator after capture.

Do not run No-TTT or finish/report Episode SR. All private source configs and
tensor payloads remain on the selected server. Normal source/mode checks stay on.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

import yaml

p = argparse.ArgumentParser()
p.add_argument("--base", type=Path, required=True)
p.add_argument("--root", type=Path, required=True)
p.add_argument("--source-config-dir", type=Path, required=True)
p.add_argument("--hooks", type=Path, required=True)
a = p.parse_args()
a.base.mkdir(parents=True, exist_ok=False, mode=0o700)


def git(r, *args):
    return subprocess.check_output(["git", "-C", str(r), *args], text=True).strip()


before = dict(
    root=git(a.root, "rev-parse", "HEAD"),
    child=git(a.root / "cosmos-framework", "rev-parse", "HEAD"),
    gitlink=git(a.root, "rev-parse", "HEAD:cosmos-framework"),
    root_status=git(a.root, "status", "--porcelain"),
    child_status=git(a.root / "cosmos-framework", "status", "--porcelain"),
)
assert before["root"] == "18be4a80a5ae4d97bc7d287034d24efab847c496"
assert (
    before["child"] == before["gitlink"] == "193627f42f4cd1ba6d563aefb8fa8f9428ecb56d"
)
assert not before["root_status"] and not before["child_status"]
(a.base / "source_before.json").write_text(json.dumps(before, indent=2) + "\n")
results = []
for k, target in [(1, 32), (16, 64)]:
    case = a.base / ("k%d" % k)
    case.mkdir()
    cfg = yaml.safe_load((a.source_config_dir / ("k%d.yaml" % k)).read_text())
    assert cfg.get("local_memory_mode", "required") == "required" and cfg[
        "gpu_ids"
    ] == [6]
    assert cfg.get("sims_per_gpu", 1) == cfg.get("max_infer_batch_size", 1) == 1
    old_output = cfg["output_dir"]
    cfg["output_dir"] = str(case / "run")
    with socket.socket() as s:
        s.bind(("0.0.0.0", 0))
        cfg["base_port"] = s.getsockname()[1]
    path = case / "config.yaml"
    path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    capture = case / "capture"
    env = dict(
        os.environ,
        CUDA_VISIBLE_DEVICES="6",
        LD_LIBRARY_PATH="",
        PYTHONDONTWRITEBYTECODE="1",
        MUJOCO_GL="egl",
        PYOPENGL_PLATFORM="egl",
        __EGL_VENDOR_LIBRARY_FILENAMES=cfg["sim_shared_vae"]["egl_vendor_json"],
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        TOKENIZERS_PARALLELISM="false",
        OMP_NUM_THREADS="2",
        OPENBLAS_NUM_THREADS="2",
        MKL_NUM_THREADS="2",
        PYTHONPATH=str(a.hooks)
        + ":"
        + str(a.root)
        + ":"
        + str(a.root / "cosmos-framework")
        + ":"
        + str(a.root / "scripts"),
        ISSUE35_CAPTURE_DIR=str(capture),
        ISSUE35_TARGET_SOURCE_STEP=str(target),
    )
    original_startup = a.root / "cosmos-framework/sitecustomize.py"
    if original_startup.exists():
        env.update(
            ISSUE35_ORIGINAL_STARTUP=str(original_startup),
            ISSUE35_ORIGINAL_STARTUP_SHA256=hashlib.sha256(
                original_startup.read_bytes()
            ).hexdigest(),
        )
    argv = [
        cfg["server_python"],
        str(a.hooks.parent / "capture_entry.py"),
        "fresh",
        "--config",
        str(path),
    ]
    (case / "command.json").write_text(
        json.dumps(
            dict(
                argv=argv,
                cwd=str(a.root),
                target_source_step=target,
                k=k,
                config_changes=["output_dir", "base_port"],
                external_cli_wrapper="capture_entry.py delegates native_main; startup helper hash-bound",
                source_config_sha256=hashlib.sha256(
                    (a.source_config_dir / ("k%d.yaml" % k)).read_bytes()
                ).hexdigest(),
                config_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            ),
            indent=2,
        )
        + "\n"
    )
    with (case / "coordinator.log").open("x") as log:
        proc = subprocess.Popen(
            argv,
            cwd=a.root,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        start = time.monotonic()
        done = False
        while proc.poll() is None and time.monotonic() - start < 900:
            if (capture / "capture_ready.json").exists():
                done = True
                proc.send_signal(
                    signal.SIGINT
                )  # Only our coordinator, native owned cleanup.
                break
            if capture.exists() and (
                list(capture.glob("capture_error_*.txt"))
                or (capture / "unsupported_parent.json").exists()
            ):
                proc.send_signal(signal.SIGINT)
                break
            time.sleep(0.25)
        if proc.poll() is None and not done:
            proc.send_signal(signal.SIGINT)
        exit_code = proc.wait(timeout=120)
    evidence = case / "run/_internal"
    registered = list((evidence / "processes").glob("*.json"))
    closed = list((evidence / "process_closed").glob("*.json"))
    result = dict(
        k=k,
        target_source_step=target,
        coordinator_exit=exit_code,
        capture_complete=done,
        intentional_early_stop_after_capture=done,
        not_an_sr_run=True,
        owned_process_records=len(registered),
        owned_close_receipts=len(closed),
        recorded_source_steps=json.loads((capture / "capture_ready.json").read_text())[
            "captured_source_steps"
        ]
        if done
        else [],
    )
    (case / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    results.append(result)
    if not done or len(registered) != len(closed):
        raise RuntimeError(
            "diagnostic capture or native owned cleanup incomplete; preserve evidence"
        )
after = dict(
    root=git(a.root, "rev-parse", "HEAD"),
    child=git(a.root / "cosmos-framework", "rev-parse", "HEAD"),
    gitlink=git(a.root, "rev-parse", "HEAD:cosmos-framework"),
    root_status=git(a.root, "status", "--porcelain"),
    child_status=git(a.root / "cosmos-framework", "status", "--porcelain"),
)
assert before == after
(a.base / "source_after.json").write_text(json.dumps(after, indent=2) + "\n")
(a.base / "capture_result.json").write_text(
    json.dumps(
        dict(
            status="CAPTURE_COMPLETE_NOT_SR",
            source_unchanged=True,
            identity=after,
            cases=results,
        ),
        indent=2,
    )
    + "\n"
)
