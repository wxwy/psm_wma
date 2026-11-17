"""Route A scoped CPU/static runner; immutable per-attempt output directories."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-child")
    parser.add_argument("--format", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    child = root / "cosmos-framework"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    paths = [f"cosmos_framework/model/generator/mot/{name}.py" for name in (
        "global_memory", "global_spatial", "global_memory_test", "global_spatial_test"
    )]
    tests = [path for path in paths if path.endswith("_test.py")]
    tests.append("cosmos_framework/model/generator/mot/g2_contracts_test.py")
    env = dict(os.environ)
    explicit = dict(
        CUDA_VISIBLE_DEVICES="", COSMOS_DEVICE="cpu", COSMOS_TRAINING="0", COSMOS_INTERNAL="0",
        LD_LIBRARY_PATH="", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONPATH=str(child),
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1", RUFF_CACHE_DIR=str(out / "ruff"),
    )
    env.update(explicit)

    def save(name, data):
        (out / name).write_text(json.dumps(data, indent=2) + "\n")

    def git(repo, *command):
        return subprocess.check_output(["git", "-C", str(repo), *command], text=True).strip()

    def identity():
        return dict(root=git(root, "rev-parse", "HEAD"), child=git(child, "rev-parse", "HEAD"),
                    root_gitlink=git(root, "rev-parse", "HEAD:cosmos-framework"),
                    root_status=git(root, "status", "--porcelain"), child_status=git(child, "status", "--porcelain"))

    def fingerprints():
        names = set(git(child, "ls-files").splitlines()) | set(paths)
        return {name: hashlib.sha256((child / name).read_bytes()).hexdigest()
                for name in sorted(names) if name.endswith((".py", ".toml")) and (child / name).is_file()}

    commands = []

    def run(name, command):
        started = time.monotonic()
        with (out / f"{name}.log").open("w") as log:
            result = subprocess.run(command, cwd=child, env=env, stdout=log, stderr=subprocess.STDOUT)
        commands.append(dict(name=name, argv=command, cwd=str(child), exit_code=result.returncode,
                             duration_seconds=time.monotonic() - started))
        save("commands.json", commands)
        if result.returncode:
            print((out / f"{name}.log").read_text()[-10000:], flush=True)
            raise RuntimeError(f"{name} failed ({result.returncode})")

    state = dict(status="RUNNING", independent_review="NOT_CLAIMED", gpu="NOT_RUN", integration="NOT_RUN")
    save("environment.json", explicit)
    start_identity = identity()
    save("identity.json", start_identity)
    try:
        if args.expected_child:
            assert start_identity["child"] == args.expected_child
            assert not start_identity["child_status"], "final Child must be clean"
            assert not args.format, "never format committed verification source"
        if args.format:
            run("lint_fix", [sys.executable, "-m", "ruff", "check", "--fix", *paths])
            run("format", [sys.executable, "-m", "ruff", "format", *paths])
        before = fingerprints()
        save("source_before.json", before)
        run("versions", [sys.executable, "-c", "import sys,torch,pytest,importlib.metadata as m; print(sys.version); print('torch',torch.__version__); print('pytest',pytest.__version__); print('ruff',m.version('ruff')); print('cuda_initialized',torch.cuda.is_initialized()); assert not torch.cuda.is_initialized()"])
        inventory_code = """
import json, pathlib, sys, torch
from cosmos_framework.model.generator.mot.global_memory import GlobalMemoryReader, GlobalMemoryProjector
from cosmos_framework.model.generator.mot.g2_contracts import GlobalMemoryConfig
config = GlobalMemoryConfig(enabled=True)
modules = {'reader': GlobalMemoryReader(24, config, latent_channels=4), 'projector': GlobalMemoryProjector(80, config)}
result = {'fixture_only': True, 'text_dim': 24, 'latent_channels': 4, 'model_dim': 80,
          'parameters': {owner + '.' + name: {'shape': list(p.shape), 'numel': p.numel(), 'requires_grad': p.requires_grad}
                         for owner, module in modules.items() for name, p in module.named_parameters()}}
result['total_numel'] = sum(p['numel'] for p in result['parameters'].values())
pathlib.Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + '\\n')
assert not torch.cuda.is_initialized()
"""
        run("inventory", [sys.executable, "-c", inventory_code, str(out / "parameter_inventory.json")])
        run("lint", [sys.executable, "-m", "ruff", "check", *paths])
        run("format_check", [sys.executable, "-m", "ruff", "format", "--check", *paths])
        for path in paths:
            source = (child / path).read_text()
            ast.parse(source, filename=path)
            compile(source, path, "exec", dont_inherit=True)
        run("pytest", [sys.executable, "-m", "pytest", "--noconftest", "-c", "/dev/null", "-p", "no:cacheprovider",
                       "--basetemp=" + str(out / "pytest_tmp"), "--junitxml=" + str(out / "junit.xml"), "-q", *tests])
        suites = list(ET.parse(out / "junit.xml").getroot().iter("testsuite"))
        counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
        assert counts["tests"] and not any(counts[k] for k in ("failures", "errors", "skipped"))
        after = fingerprints()
        save("source_after.json", after)
        assert before == after, "source changed during verification"
        if args.expected_child:
            assert identity() == start_identity
        state.update(status="PASS", junit=counts, source_unchanged=True, source_files=len(before),
                     peak_child_rss_mib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024,
                     attention_validation="test-only CPU reference; actual GPU dispatcher NOT_RUN")
    except Exception as error:
        state.update(status="FAIL", error=repr(error))
    save("result.json", state)
    print(json.dumps(state, indent=2), flush=True)
    return state["status"] != "PASS"


if __name__ == "__main__":
    raise SystemExit(main())
