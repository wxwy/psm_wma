"""Prove the F5 increment scope and exercise unchanged real source admission."""

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent
OUT = BASE / "static-final"
OUT.mkdir()
ROOT = Path("/workspace/work/psm-wma-runtime-evidence-formal")
CHILD = ROOT / "cosmos-framework"
OLD_ROOT = "427b4d09cdd8070820a39b93ebf2ff832a23e359"
NEW_ROOT = "7c74dc26ac4837f193727ecf847b9b64554c18b2"
OLD_CHILD = "0ae313e329d290fc6b8a50fda1112820fb7ac485"
NEW_CHILD = "53c3c95202e14d3b72d236eee6899a80acf82989"
STORE = "cosmos_framework/evaluation/robocasa_v2/store.py"
CLI = "scripts/robocasa_eval_v2/cli.py"
ENTRY = "tools/v3/eval_v2_production_tests/entry_test.py"
TEST = "tools/v3/eval_v2_production_tests/runtime_evidence_test.py"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def tree(repo, commit, name):
    return ast.parse(git(repo, "show", commit + ":" + name))


root_paths = git(ROOT, "diff", "--name-only", OLD_ROOT, NEW_ROOT).splitlines()
child_paths = git(CHILD, "diff", "--name-only", OLD_CHILD, NEW_CHILD).splitlines()
assert set(root_paths) == {"cosmos-framework", CLI, ENTRY, TEST}
assert child_paths == [STORE]
assert git(ROOT, "rev-parse", "HEAD") == NEW_ROOT
assert git(CHILD, "rev-parse", "HEAD") == git(ROOT, "rev-parse", "HEAD:cosmos-framework") == NEW_CHILD
assert git(ROOT, "status", "--porcelain=v1") == git(CHILD, "status", "--porcelain=v1") == ""
old_store, new_store = tree(CHILD, OLD_CHILD, STORE), tree(CHILD, NEW_CHILD, STORE)
added = []
retained = []
for node in new_store.body:
    if isinstance(node, ast.FunctionDef) and node.name == "write_runtime_probe":
        added.append(node.name)
        assert [a.arg for a in node.args.args] == ["path", "value"]
        assert not node.args.kwonlyargs and node.args.kwarg is None
    elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MAX_RUNTIME_PROBE" for t in node.targets):
        added.append("MAX_RUNTIME_PROBE")
    else:
        retained.append(node)
new_store.body = retained
assert sorted(added) == ["MAX_RUNTIME_PROBE", "write_runtime_probe"]
assert ast.dump(old_store) == ast.dump(new_store)
old_entry, new_entry = tree(ROOT, OLD_ROOT, ENTRY), tree(ROOT, NEW_ROOT, ENTRY)
removed = []
for node in ast.walk(next(n for n in new_entry.body if isinstance(n, ast.FunctionDef) and n.name == "fake_prepare")):
    if isinstance(node, ast.Dict):
        pairs = list(zip(node.keys, node.values))
        for key, value in pairs:
            if isinstance(key, ast.Constant) and key.value in ("runtime", "runtime_probe_evidence"):
                removed.append(key.value)
        pairs = [(k, v) for k, v in pairs if not (isinstance(k, ast.Constant) and k.value in ("runtime", "runtime_probe_evidence"))]
        node.keys, node.values = [k for k, _ in pairs], [v for _, v in pairs]
assert sorted(removed) == ["runtime", "runtime_probe_evidence"]
assert ast.dump(old_entry) == ast.dump(new_entry)
protected = ["scripts/robocasa_eval_v2/identity.py", "scripts/robocasa_vendor.py",
             "scripts/robocasa_eval_v2/runtime.py", "scripts/robocasa_eval_v2/resources.py",
             "scripts/robocasa_eval_v2/config.py", "scripts/robocasa_episode_resume/model_identity.py"]
for path in protected:
    assert git(ROOT, "rev-parse", OLD_ROOT + ":" + path) == git(ROOT, "rev-parse", NEW_ROOT + ":" + path)
names = [CLI, ENTRY, TEST, "cosmos-framework/" + STORE]
env = dict(os.environ, CUDA_VISIBLE_DEVICES="", LD_LIBRARY_PATH="", PYTHONDONTWRITEBYTECODE="1",
           PYTHONPATH=f"{ROOT}:{CHILD}:{ROOT}/scripts", RUFF_CACHE_DIR=str(OUT / "cache"))
commands = [
    [sys.executable, "-m", "ruff", "check", *names],
    [sys.executable, "-m", "ruff", "format", "--check", *names],
    ["git", "diff", "--check", OLD_ROOT, NEW_ROOT],
    ["git", "-C", str(CHILD), "diff", "--check", OLD_CHILD, NEW_CHILD],
    [sys.executable, "-B", "-c", "import json;from robocasa_eval_v2.identity import verify_source;from cosmos_framework.evaluation.robocasa_v2 import store;print(json.dumps({'source':verify_source(),'store_import':store.__file__}))"],
]
checks = []
for i, argv in enumerate(commands):
    with (OUT / f"check_{i}.log").open("w") as stream:
        code = subprocess.run(argv, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT).returncode
    checks.append({"argv": argv, "exit_code": code})
    assert code == 0
actual = json.loads((OUT / "check_4.log").read_text())
assert actual == {"source": [NEW_ROOT, NEW_CHILD, NEW_ROOT], "store_import": str(CHILD / STORE)}
for name in names:
    ast.parse((ROOT / name).read_text(), filename=name)
bindings = {}
for name in [*names, *protected]:
    child = name.startswith("cosmos-framework/")
    repo, ref, relative = (CHILD, NEW_CHILD, name.removeprefix("cosmos-framework/")) if child else (ROOT, NEW_ROOT, name)
    bindings[name] = {"commit": ref, "git_blob": git(repo, "rev-parse", ref + ":" + relative),
                      "sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}
proof = {"formal_root": NEW_ROOT, "parent_root": OLD_ROOT, "child": NEW_CHILD, "parent_child": OLD_CHILD,
         "root_changed": root_paths, "child_changed": child_paths,
         "ordinary_store_AST_unchanged_except": added,
         "entry_AST_unchanged_except_fake_prepare_fixture_fields": removed,
         "protected_Root_blobs_unchanged": protected, "checks": checks, "syntax_files": len(names),
         "actual_unmodified_verify_source_and_import": actual, "bindings": bindings}
(OUT / "proof.json").write_text(json.dumps(proof, indent=2) + "\n")
(OUT / "root.diff").write_text(git(ROOT, "diff", OLD_ROOT, NEW_ROOT) + "\n")
(OUT / "child.diff").write_text(git(CHILD, "diff", OLD_CHILD, NEW_CHILD) + "\n")
print(json.dumps({"formal_root": NEW_ROOT, "child": NEW_CHILD, "checks_exit": [c["exit_code"] for c in checks],
                  "syntax_files": len(names), "scope_proof": "PASS", "protected": protected}, indent=2))
