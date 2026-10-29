"""Static review proof for the exact Root-only synchronization increment."""

import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = Path("/workspace/work/psm-wma-inflight-snapshot-formal")
OLD = "9657fb6ab590f228d760362e506d5dd1b626880a"
NEW = "a139b5a35877a79e0a56c2208f3002f731972b11"
RUNTIME = "scripts/robocasa_eval_v2/runtime.py"
TEST = "tools/v3/eval_v2_production_tests/runtime_progress_test.py"
OUT = BASE / "static"
OUT.mkdir()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


assert git("rev-parse", "HEAD") == NEW
assert git("status", "--porcelain=v1") == ""
changed = git("diff", "--name-only", OLD, NEW).splitlines()
assert changed == [RUNTIME, TEST]
old = ast.parse(git("show", OLD + ":" + RUNTIME))
new = ast.parse((ROOT / RUNTIME).read_text())
replaced = 0
for node in ast.walk(old):
    for field in ("body", "orelse", "finalbody"):
        statements = getattr(node, field, None)
        if not isinstance(statements, list):
            continue
        for i, statement in enumerate(statements):
            if isinstance(statement, ast.For) and ast.unparse(statement.iter) == "scheduler.inflight.items()":
                block = ast.parse("with scheduler._lock:\n    inflight_snapshot = tuple(scheduler.inflight.items())\n").body[0]
                statement.iter = ast.Name(id="inflight_snapshot", ctx=ast.Load())
                statements.insert(i, block)
                replaced += 1
assert replaced == 1
assert ast.dump(old) == ast.dump(new)
for name in (RUNTIME, TEST):
    ast.parse((ROOT / name).read_text(), filename=name)
commands = [
    ["/workspace/.venvs/psm-wma-cpu/bin/ruff", "check", RUNTIME, TEST],
    ["/workspace/.venvs/psm-wma-cpu/bin/ruff", "format", "--check", RUNTIME, TEST],
    ["git", "diff", "--check", OLD, NEW],
]
checks = []
for i, argv in enumerate(commands):
    with (OUT / f"check_{i}.log").open("w") as stream:
        code = subprocess.run(argv, cwd=ROOT, env=dict(os.environ, RUFF_CACHE_DIR=str(OUT / "cache")),
                              stdout=stream, stderr=subprocess.STDOUT).returncode
    checks.append({"argv": argv, "exit_code": code})
    assert code == 0
proof = {"formal_root": NEW, "parent_root": OLD,
         "child_gitlink": git("ls-tree", NEW, "cosmos-framework").split()[2],
         "changed_files": changed, "only_runtime_ast_change": "same-lock tuple snapshot; original For target/body/else and all other runtime AST unchanged",
         "ruff_and_diff": checks, "syntax_files": 2,
         "source_bindings": {name: {"sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
                                    "git_blob": git("rev-parse", NEW + ":" + name)} for name in (RUNTIME, TEST)}}
assert proof["child_gitlink"] == "0ae313e329d290fc6b8a50fda1112820fb7ac485"
(OUT / "proof.json").write_text(json.dumps(proof, indent=2) + "\n")
(OUT / "formal.diff").write_text(git("diff", OLD, NEW) + "\n")
print(json.dumps(proof, indent=2))
