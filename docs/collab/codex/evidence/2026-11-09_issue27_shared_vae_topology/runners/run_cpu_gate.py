"""Issue27 exact-pair author CPU gate; synthetic model/Sim boundaries only."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True, type=Path)
parser.add_argument("--evidence-dir", required=True, type=Path)
parser.add_argument("--expected-root", required=True)
parser.add_argument("--expected-child", required=True)
args = parser.parse_args()
root = args.root.resolve()
child = root / "cosmos-framework"
out = args.evidence_dir.resolve()
out.mkdir(parents=True, exist_ok=False)


def git(directory, *arguments):
    return subprocess.check_output(["git", "-C", str(directory), *arguments], text=True).strip()


identity = {"root": git(root, "rev-parse", "HEAD"), "child": git(child, "rev-parse", "HEAD"),
            "gitlink": git(root, "rev-parse", "HEAD:cosmos-framework")}
assert identity == {"root": args.expected_root, "child": args.expected_child, "gitlink": args.expected_child}, identity
assert not git(root, "status", "--porcelain") and not git(child, "status", "--porcelain"), "clean exact worktrees required"
(out / "source_identity.json").write_text(json.dumps(identity, indent=2) + "\n")
(out / "versions.json").write_text(json.dumps({"python": sys.version, "packages": {
    name: importlib.metadata.version(name) for name in ("torch", "pytest", "ruff", "omegaconf")}}, indent=2) + "\n")
new = []
for repo, base in ((root, "e58cef1f53d2382d39c871ce5a50e4acdd5ce268"),
                   (child, "b0dbd115d03e801ec4d0788c30ee0b0e9655d4db")):
    new += [repo / name for name in git(repo, "diff", "--name-only", base, "HEAD", "--", "*.py").splitlines()]
new = sorted(set(new))
tests = [child / "cosmos_framework" / p for p in (
    "inference/robocasa_vae_daemon_test.py", "inference/robocasa_boundary_capture_test.py", "inference/robocasa_feature_evidence_test.py",
    "inference/robocasa_feature_trace_test.py", "inference/robocasa_feature_transactions_test.py",
    "scripts/robocasa_feature_http_test.py", "simulation/robocasa/sim_shared_vae_client_test.py",
    "inference/robocasa_local_memory_policy_test.py", "inference/robocasa_vae_worker_test.py",
    "inference/robocasa_vae_client_test.py", "inference/robocasa_vae_encoder_test.py",
    "inference/robocasa_vae_protocol_test.py",
    "inference/robocasa_boundary_batch_test.py", "inference/robocasa_shared_policy_batch_test.py",
    "inference/robocasa_shared_ready_test.py", "inference/robocasa_shared_memory_test.py",
    "inference/robocasa_vae_topology_test.py", "scripts/robocasa_shared_feature_batch_test.py",
)]
legacy = [child / "cosmos_framework/inference" / p for p in (
    "robocasa_session_transactions_test.py",
    "robocasa_dual_mode_test.py",
    "local_memory_online_test.py",
    "robocasa_composite_visual_test.py",
    "robocasa_batch_transactions_test.py",
)]
legacy += [child / "cosmos_framework/simulation/robocasa" / p for p in (
    "eval_v2_transactions_test.py", "closed_loop_eval_contract_test.py", "closed_loop_eval_lifecycle_test.py",
)]
root_tests = [root / p for p in (
    "tools/v3/eval_v2_batch_tests/actor_source_witness_test.py", "tools/v3/eval_v2_production_tests/worker_test.py", "tools/v3/eval_v2_batch_tests/shared_vae_test.py", "tools/v3/eval_v2_batch_tests/config_test.py",
    "tools/v3/eval_v2_batch_tests/render_mapping_test.py", "tools/v3/eval_v2_batch_tests/render_devices_test.py",
    "tools/v3/eval_v2_batch_tests/owner_gpu_resource_policy_test.py",
    "tools/v3/eval_v2_production_tests/contract_test.py",
    "tools/v3/eval_v2_batch_tests/shared_vae_topology_test.py",
    "tools/v3/eval_v2_batch_tests/shared_vae_routing_test.py",
    "tools/v3/eval_v2_batch_tests/shared_vae_cli_test.py",
    "tools/v3/eval_v2_batch_tests/shared_vae_server_wire_test.py",
)]
streaming_tests = [root / "tools/v3/eval_v2_streaming_tests" / name for name in (
    "capacity_test.py", "resource_test.py", "startup_completion_test.py",
)]
assert new and all(p.is_file() for p in (*tests, *legacy, *root_tests)), "focused source/test scope missing"
(out / "static_scope.json").write_text(json.dumps(list(map(str, new)), indent=2) + "\n")
env = os.environ.copy()
overrides = dict(
    CUDA_VISIBLE_DEVICES="", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTEST_ADDOPTS="",
    HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1",
    OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
    PYTHONPATH=os.pathsep.join(map(str, (root, child, root / "scripts"))),
    RUFF_CACHE_DIR=str(out / "cache/ruff"), XDG_CACHE_HOME=str(out / "cache/xdg"),
)
env.update(overrides)
(out / "environment_overrides.json").write_text(json.dumps(overrides, indent=2) + "\n")


def snapshot():
    files = [p for p in child.rglob("*.py") if ".git" not in p.parts and "__pycache__" not in p.parts]
    for package in sorted((child / "docs/designs").glob("issue23_sim_shared_vae_stage*")):
        files += list(package.rglob("*"))
    for folder in (root / "scripts", root / "tools"):
        files += list(folder.rglob("*.py"))
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}


before = snapshot()
(out / "source_before.json").write_text(json.dumps(before, indent=2) + "\n")
state = {"scope": "ISSUE27_GENERIC_SHARED_VAE_TOPOLOGY_AUTHOR_CPU", "status": "RUNNING", "steps": [],
         "real_weights_gpu_egl_sim_policy_integration_sr": "NOT_RUN"}


def save():
    (out / "gate.json").write_text(json.dumps(state, indent=2) + "\n")


def run(name, command, timeout=180):
    step = dict(name=name, argv=list(map(str, command)), cwd=str(root), timeout_s=timeout)
    state["steps"].append(step)
    save()
    start = time.monotonic()
    with (out / f"{name}.log").open("wb") as log:
        result = subprocess.Popen(step["argv"], cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
                                  start_new_session=True)
        try:
            result.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(result.pid, signal.SIGKILL)
            result.wait(timeout=5)
            raise
    step.update(exit_code=result.returncode, elapsed_s=round(time.monotonic() - start, 3))
    print(f"{name}: exit={result.returncode}", flush=True)
    save()
    if result.returncode:
        raise RuntimeError(f"{name} failed; see {name}.log")


try:
    run("ruff_check", [sys.executable, "-m", "ruff", "check", *new])
    run("ruff_format", [sys.executable, "-m", "ruff", "format", "--check", *new])
    for path in new:
        compile(path.read_text(), str(path), "exec")
    state["syntax_files"] = len(new)
    red = json.loads((Path(__file__).parent / "red-final-test-bytes/result.json").read_text())
    state["red_green_test_hashes_equal"] = all(
        hashlib.sha256((root / name).read_bytes()).hexdigest() == sha
        for name, sha in red["test_hashes"].items())
    assert state["red_green_test_hashes_equal"]
    probe = """import json
from cosmos_framework.inference.robocasa_vae_daemon_test import _tokenizer
from cosmos_framework.inference.robocasa_vae_daemon import worker_constructor_config, loaded_vae_identity
from cosmos_framework.inference.robocasa_vae_protocol import canonical_json
t=_tokenizer()
print(json.dumps({'constructor':worker_constructor_config(t),'canonical_constructor':canonical_json(worker_constructor_config(t)).decode(),'identity':loaded_vae_identity(t)},sort_keys=True))
"""
    run("native_baseline", [sys.executable, "-c", probe])
    def probe_json(path):
        records = [json.loads(line) for line in path.read_text().splitlines() if line.startswith("{")]
        assert len(records) == 1 and set(records[0]) == {"constructor", "canonical_constructor", "identity"}
        return records[0]
    old_native = probe_json(root / "docs/collab/codex/evidence/2026-11-08_issue24_stage3a_h1_omegaconf/red-old-code/native_baseline.log")
    new_native = probe_json(out / "native_baseline.log")
    assert old_native == new_native, "native constructor bytes or loaded identity changed"
    state["native_constructor_and_identity_unchanged"] = True
    for name, paths in (("stage3_focused", tests), ("root_lifecycle_config", root_tests), ("legacy_protection", legacy), ("streaming_bounds", streaming_tests)):
        run(name, [sys.executable, "-m", "pytest", "--noconftest", "-c", "/dev/null", "-p", "no:cacheprovider",
                   "-q", *paths, f"--basetemp={out / (name + '_tmp')}", f"--junitxml={out / (name + '.xml')}"], 240)
        suites = list(ET.parse(out / f"{name}.xml").getroot().iter("testsuite"))
        counts = {key: sum(int(s.get(key, "0")) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
        state[name] = counts
        if not counts["tests"] or any(counts[key] for key in ("failures", "errors", "skipped")):
            raise RuntimeError(f"nonclean JUnit: {counts}")
    state["status"] = "PASS"
except Exception as error:
    state.update(status="FAIL", error=repr(error))
finally:
    for group in ("stage3_focused", "root_lifecycle_config", "legacy_protection", "streaming_bounds"):
        xml_path = out / (group + ".xml")
        if xml_path.exists():
            tree = ET.parse(xml_path).getroot()
            suites = list(tree.iter("testsuite"))
            state[group] = {key: sum(int(s.get(key, "0")) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
            state[group]["testcase_elements"] = sum(1 for _ in tree.iter("testcase"))
    after = snapshot()
    (out / "source_after.json").write_text(json.dumps(after, indent=2) + "\n")
    state["source_unchanged"] = before == after and not git(root, "status", "--porcelain") and not git(child, "status", "--porcelain")
    if before != after:
        state.update(status="FAIL", error="source changed during validation")
    save()
print(json.dumps({key: state.get(key) for key in ("status", "stage3_focused", "root_lifecycle_config", "legacy_protection", "streaming_bounds", "source_unchanged")}))
raise SystemExit(0 if state["status"] == "PASS" else 1)
