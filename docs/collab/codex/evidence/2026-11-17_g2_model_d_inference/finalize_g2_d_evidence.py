"""Build the review receipt from local Git, original JUnit and immutable source hashes."""
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

root = Path(__file__).resolve().parents[1]
child = root / "cosmos-framework"
fixed = "6991142cb94256f497347db40f58ad0ee3f482aa"
base = "3bdfaa64af45a42eb2b5adde582505d33a5f08f2"
evidence = root / "docs/collab/codex/evidence/2026-11-17_g2_model_d_inference"
evidence.mkdir(parents=True, exist_ok=True)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=child, text=True).strip()


assert git("rev-parse", "HEAD") == fixed
assert git("status", "--porcelain") == ""
shutil.copytree(root / "work/g2-d-evidence", evidence / "raw", dirs_exist_ok=True)
for name in ("run_g2_d_cpu.sh", "run_g2_d_static.sh"):
    shutil.copyfile(root / "work" / name, evidence / name)
shutil.copyfile(__file__, evidence / "finalize_g2_d_evidence.py")
suite = ET.parse(evidence / "raw/final-01/junit.xml").getroot()
cases = suite.findall(".//testcase")
assert len(cases) == 361 and not suite.findall(".//failure") and not suite.findall(".//error") and not suite.findall(".//skipped")
by_module = Counter(case.get("classname") for case in cases)
assert len(by_module) == 17
before = (evidence / "raw/final-01/source-before.sha256").read_bytes()
after = (evidence / "raw/final-01/source-after.sha256").read_bytes()
assert before == after and len(before.splitlines()) == 1114
for line in before.decode().splitlines():
    sha, path = line.split("  ", 1)
    assert hashlib.sha256((child / path).read_bytes()).hexdigest() == sha
owned = git("diff", "--name-only", f"{base}..{fixed}").splitlines()
assert len(owned) == 12
protected = {}
for revision in (
    "7e888f217dfcddc35ed73782f65c6e0890c72c3a",
    "4209b151ecc11ab2043b9d08037d43b5e3903618",
    "f262d7ff4156d83356e1d7f790adea2a61e85c6d",
    "68d84e819d114c6ce817403afacad994b2fb8f35",
):
    for path in git("diff-tree", "--no-commit-id", "--name-only", "-r", revision).splitlines():
        if not path.endswith(".py"):
            continue
        # C's later commit supersedes C's initial helper/transforms/loader files.
        authority = "f262d7ff4156d83356e1d7f790adea2a61e85c6d" if revision == "68d84e819d114c6ce817403afacad994b2fb8f35" else revision
        expected, actual = git("rev-parse", f"{authority}:{path}"), git("rev-parse", f"{fixed}:{path}")
        assert expected == actual, (path, authority)
        protected[path] = {"authority": authority, "git_blob": actual}
root_link = subprocess.check_output(["git", "ls-tree", "HEAD", "cosmos-framework"], cwd=root, text=True).split()[2]
assert root_link == "d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2"
receipt = {
    "status": "AUTHOR_SCOPED_CPU_PASS_CANDIDATE",
    "observed_at_cst": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
    "root_baseline": "7a357620b4cc1f6817749c8a8275771cfbb4049c",
    "root_gitlink_unchanged": root_link,
    "fixed_child": fixed,
    "fixed_child_tree": git("rev-parse", f"{fixed}^{{tree}}"),
    "review_base": base,
    "c0": "ec9356fafd1fd18cc0bd552b7eb23428f59df7f6",
    "dependencies": {"B": "7e888f217dfcddc35ed73782f65c6e0890c72c3a", "A": "4209b151ecc11ab2043b9d08037d43b5e3903618", "C": "f262d7ff4156d83356e1d7f790adea2a61e85c6d"},
    "cpu": {"passed": len(cases), "failed": 0, "errors": 0, "skipped": 0, "modules": dict(sorted(by_module.items())), "counts_are_not_added_to_prior_runs": True},
    "source": {"python_fingerprints": 1114, "before_after_equal": True, "clean_fixed_child": True,
               "fingerprint_file_sha256": hashlib.sha256(before).hexdigest(),
               "owned_files": {path: hashlib.sha256((child / path).read_bytes()).hexdigest() for path in owned},
               "protected_route_files": protected},
    "static": {"ruff_strict_files": 11, "legacy_I001_exception_files": 1,
               "legacy_exception_identical_to_base": (evidence / "raw/final-01/baseline-I001.log").read_bytes() == (evidence / "raw/final-01/current-I001.log").read_bytes(),
               "format_files": 12, "syntax_files": 12},
    "not_run": ["real checkpoint/Wan/Cosmos", "GPU BF16/compiled cache parity", "GPU latency/memory", "actual rollout provider/GT binding", "DATA_B/C real state15/alignment", "simulation/closed loop/SR", "real FSDP/distributed cache"],
    "explicitly_unsupported": ["multi-rank Session condition runtime", "guidance != 1", "expert map playback", "cross-Session/machine sharing", "training cache reuse"],
    "child_draft": "https://github.com/wxwy/cosmos-framework/pull/16",
}
(evidence / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"passed": len(cases), "modules": len(by_module), "D_testcases": sum(count for name, count in by_module.items() if name.split(".")[-1].startswith("g2_") and ".inference." in name or name.endswith("g2_policy_server_test")), "files": len(owned), "protected_files": len(protected)}, ensure_ascii=False))
