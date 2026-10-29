"""Record standard-library-only source/identity checks before and after one run."""

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/work/psm-wma-ready-startup-formal")
BASE = Path(__file__).resolve().parent
OUT = BASE / "run"
OLD = BASE.parent / "author-full-after-review"
EXPECTED_ROOT = "9657fb6ab590f228d760362e506d5dd1b626880a"
EXPECTED_CHILD = "0ae313e329d290fc6b8a50fda1112820fb7ac485"


def git(directory, *args):
    return subprocess.check_output(["git", "-C", str(directory), *args], text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


phase = sys.argv[1]
assert phase in {"before", "after"}
if phase == "before":
    OUT.mkdir()
baseline = json.loads((OLD / "source_sha256.json").read_text())
state = {
    "phase": phase, "utc": datetime.now(timezone.utc).isoformat(),
    "root": git(ROOT, "rev-parse", "HEAD"),
    "child": git(ROOT / "cosmos-framework", "rev-parse", "HEAD"),
    "gitlink": git(ROOT, "ls-tree", "HEAD", "cosmos-framework").split()[2],
    "root_status": git(ROOT, "status", "--porcelain=v1", "--untracked-files=all"),
    "child_status": git(ROOT / "cosmos-framework", "status", "--porcelain=v1", "--untracked-files=all"),
    "source_sha256": {name: digest(ROOT / name) for name in baseline},
    "original_fail_artifacts_sha256": {
        str(p.relative_to(OLD)): digest(p)
        for p in sorted(OLD.glob("*")) if p.is_file()
    },
    "python": sys.version, "python_executable": sys.executable,
    "pytest": importlib.metadata.version("pytest"), "platform": platform.platform(),
}
assert state["root"] == EXPECTED_ROOT
assert state["child"] == state["gitlink"] == EXPECTED_CHILD
assert state["root_status"] == state["child_status"] == ""
assert state["source_sha256"] == baseline
if phase == "after":
    before = json.loads((OUT / "source_before.json").read_text())
    assert state["source_sha256"] == before["source_sha256"]
    assert state["original_fail_artifacts_sha256"] == before["original_fail_artifacts_sha256"]
    state["source_unchanged"] = True
    state["old_fail_artifacts_unchanged"] = True
(OUT / f"source_{phase}.json").write_text(json.dumps(state, indent=2) + "\n")
print(json.dumps({k: state[k] for k in ("phase", "root", "child", "gitlink", "root_status", "child_status")}))
