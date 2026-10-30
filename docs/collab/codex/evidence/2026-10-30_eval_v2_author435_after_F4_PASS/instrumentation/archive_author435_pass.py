"""Archive one completed author CPU435 Gate; never execute project code/tests.

Run only after the Gate and its shell wrapper have completed.  The source tree
and all original evidence remain read-only.  A NEW destination is mandatory.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET


FORMAL = "a139b5a35877a79e0a56c2208f3002f731972b11"
CHILD = "0ae313e329d290fc6b8a50fda1112820fb7ac485"
GROUPS = {"inference": 145, "phase_a_regression": 256, "phase_b_runtime": 34}
COUNT_KEYS = ("tests", "failures", "errors", "skipped")
SCRATCH = Path("/workspace/work/inflight-snapshot-evidence")
DEFAULT_SOURCE = Path("/workspace/work/psm-wma-inflight-snapshot-formal")
DEFAULT_DESTINATION = Path("/workspace/work/psm-wma-inflight-snapshot/docs/collab/codex/evidence/2026-10-30_eval_v2_author435_after_F4_PASS")
EXTRA_BINDINGS = (
    "scripts/robocasa_eval_v2_processes.py",
    "scripts/robocasa_processes.py",
    "scripts/robocasa_eval_v2_child.py",
    "cosmos-framework/cosmos_framework/__init__.py",
    "cosmos-framework/cosmos_framework/evaluation/robocasa_v2/store.py",
    "cosmos-framework/cosmos_framework/evaluation/robocasa_v2/scheduler.py",
    "cosmos-framework/cosmos_framework/evaluation/robocasa_v2/wire.py",
    "cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval.py",
)
PUBLIC_PATTERNS = (
    "manifest.json", "summary.json", "episodes.jsonl",
    "logs/*_server.log",
    "_internal/processes/*.json", "_internal/process_closed/*.json",
    "_internal/cpu_fixture_events/*.jsonl", "_internal/scheduler/*/*.json",
    "_internal/tasks/*/errors/*.json", "_internal/tasks/*/cleanup/*.json",
    "_internal/tasks/*/streams/*.json",
    "_internal/tasks/*/slots/*/attempts/*.json",
    "_internal/tasks/*/slots/*/events/*/*.json",
    "tasks/*/summary.json", "tasks/*/episodes/*/result.json",
    "tasks/*/episodes/*/predictions.jsonl",
)
SENSITIVE_KEYS = {"capability", "capabilities", "owner_token", "owner_capability"}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()


def read_json(path):
    require(path.is_file() and not path.is_symlink(), "Missing ordinary JSON original: " + str(path))
    return json.loads(path.read_bytes())


def body(path):
    value = read_json(path)
    if isinstance(value, dict) and set(value) == {"body", "sha256"}:
        require(sha(canonical(value["body"])) == value["sha256"],
                "Invalid sealed public record")
        return value["body"]
    return value


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def count_junit(path):
    require(path.is_file() and not path.is_symlink(), "Missing ordinary JUnit original: " + str(path))
    suites = list(ET.parse(path).getroot().iter("testsuite"))
    return {key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in COUNT_KEYS}


def records(path):
    return [body(p) for p in sorted(path.glob("*.json"))]


def json_lines(path):
    require(path.is_file() and not path.is_symlink(), "Missing ordinary JSONL original: " + str(path))
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def reject_sensitive_fields(value):
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in SENSITIVE_KEYS or normalized.endswith("_owner_token"):
                require(item in (None, "", False, [], {}),
                        "Nonempty capability/owner-token field in public evidence")
            reject_sensitive_fields(item)
    elif isinstance(value, list):
        for item in value:
            reject_sensitive_fields(item)


def privacy_check(path, secrets):
    raw = path.read_bytes()
    require(not any(secret in raw for secret in secrets),
            "Generated private capability value found in publication candidate")
    if path.suffix == ".json":
        reject_sensitive_fields(json.loads(raw))
    elif path.suffix == ".jsonl":
        for line in raw.splitlines():
            if line.strip():
                reject_sensitive_fields(json.loads(line))
    elif path.suffix in (".log", ".txt", ".xml"):
        require(re.search(rb'''["']?(?:capability|owner_token)["']?\s*[:=]\s*["'][^"']+["']''', raw) is None,
                "Nonempty capability/owner-token field in public text")
        # Structured marker lines remain original bytes, but their embedded
        # JSON also receives the recursive field check before publication.
        for line in raw.decode("utf-8").splitlines():
            opening = line.find("{")
            if opening >= 0:
                try:
                    value = json.loads(line[opening:])
                except json.JSONDecodeError:
                    continue
                reject_sensitive_fields(value)


def os_summary(run, expected, label):
    manifest = read_json(run / "manifest.json")
    processes = records(run / "_internal/processes")
    closed = records(run / "_internal/process_closed")
    receipts = {row["record"]["id"]: row for row in closed}
    require(set(receipts) == {row["id"] for row in processes},
            "OS witness lacks exact owned cleanup receipt set")
    require(all(row["cleanup"]["live_group"] is False for row in closed),
            "OS witness contains unclosed owned group")
    require(all(receipts[row["id"]]["record"] == row for row in processes),
            "OS witness cleanup receipt has a foreign process record")
    native, faults = [], []
    for log in sorted((run / "logs").glob("*_server.log")):
        for line in log.read_text().splitlines():
            if line.startswith("CPU_NATIVE_BATCH "):
                native.append(json.loads(line[len("CPU_NATIVE_BATCH "):]))
            elif line.startswith("CPU_SERVER_FAULT "):
                faults.append(json.loads(line[len("CPU_SERVER_FAULT "):]))
    events = [event for p in sorted((run / "_internal/cpu_fixture_events").glob("*.jsonl"))
              for event in json_lines(p)]
    scheduler = [body(p) for p in sorted((run / "_internal/scheduler").glob("*/*.json"))]
    results = [body(p) for p in sorted(run.glob("tasks/*/episodes/*/result.json"))]
    predictions = [row for p in sorted(run.glob("tasks/*/episodes/*/predictions.jsonl"))
                   for row in json_lines(p)]
    info = {"label": label, "raw_run": str(run), "G_N_episodes": list(expected),
            "owned_processes": len(processes), "owned_cleanup_receipts": len(closed),
            "servers": sum(p["kind"] == "server" for p in processes),
            "sim_processes": sum(p["kind"].startswith("simulator_slot:") for p in processes),
            "native_batch_histogram": dict(Counter(str(c["size"]) for c in native)),
            "native_request_total": sum(c["size"] for c in native),
            "prediction_rows": len(predictions), "result_records": len(results),
            "scheduler_records": len(scheduler), "fixture_events": len(events),
            "foreign_survival": "Carried by the passed test assertion; no separate raw external-process survival artifact exists.",
            "completed_resume": "Carried by the passed test assertions for no resource probe and unchanged result bytes; no separate before/after raw byte snapshot was written."}
    g, n, episodes = expected
    require(len(manifest["tasks"]) == n and manifest["episodes_per_task"] == episodes,
            "OS witness manifest topology mismatch")
    require(info["servers"] == min(g, n) and info["sim_processes"] == min(g * 2, n),
            "OS witness process topology mismatch")
    if label == "F3_server_death":
        require(expected == (1, 2, 2) and manifest["execution"]["max_infer_batch_size"] == 1,
                "F3 original cap1/two-Slot manifest mismatch")
        require(len(faults) == 1 and faults[0]["native_size"] == 1,
                "F3 must contain the actual cap1 server fault marker")
        fault = faults[0]
        require(len(fault["tickets"]) == 2 and
                {t["state"] for t in fault["tickets"]} == {"GENERATING", "QUEUED"},
                "F3 must prove two active real Slot requests")
        require(len({t["slot_id"] for t in fault["tickets"]}) == 2 and
                len({t["session_id"] for t in fault["tickets"]}) == 2,
                "F3 Slot/Session isolation missing")
        require(any(row["record"]["kind"] == "server" and
                    row["record"]["identity"]["pid"] == fault["pid"] and
                    row["cleanup"]["returncode"] == 23 for row in closed),
                "F3 actual server exit23 receipt missing")
        require(not results, "F3 unexpectedly published a valid Core result")
        faults_by_task = {
            task: records(run / "_internal/tasks" / task / "errors")
            for task in manifest["tasks"]
        }
        require(all(any(not (run / "_internal/tasks" / ticket["task"] /
                             "resolutions" / (row["id"] + ".json")).exists() and row["attempt"] is not None and
                        row["attempt"]["attempt_id"] == ticket["attempt_id"]
                        for row in faults_by_task[ticket["task"]])
                    for ticket in fault["tickets"]), "F3 fault ownership records missing")
        info["fault_marker"] = fault
        info["completed_resume"] = "Not part of the failure case."
    else:
        require(not faults and len(results) == n * episodes and
                len(predictions) == 2 * n * episodes and
                info["native_request_total"] == 2 * n * episodes,
                "Success OS witness result/request count mismatch")
        if expected == (1, 2, 2):
            require(any(c["size"] == 2 for c in native), "Required real B2 witness absent")
        require(all(p["transaction"]["assignment"]["session_id"] == p["local_memory"]["session_id"]
                    for p in predictions), "Public prediction Session/result mapping mismatch")
        require(sum(row["kind"] == "ROUND_BARRIER" for row in scheduler) == episodes and
                [(row["data"]["task"], row["data"]["episode"]) for row in scheduler
                 if row["kind"] == "DISPATCH"] ==
                [(task, episode) for episode in range(episodes) for task in manifest["task_order"]],
                "Raw D5 plan/barrier witness mismatch")
        intervals = {}
        for pid in {event["pid"] for event in events}:
            pairs, started = [], None
            for event in sorted((e for e in events if e["pid"] == pid), key=lambda e: e["time"]):
                if event["kind"] == "execute_begin":
                    started = event["time"]
                elif event["kind"] == "execute_end" and started is not None:
                    pairs.append((started, event["time"]))
                    started = None
            intervals[pid] = pairs
        overlapping = any(a != b and max(x[0], y[0]) < min(x[1], y[1])
                          for a, ia in intervals.items() for b, ib in intervals.items()
                          for x in ia for y in ib)
        require(overlapping, "Raw independent Sim execution overlap missing")
        info["raw_fixture_physics_overlap"] = overlapping
        info["foreign_survival"] = "Not asserted in this success case."
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--evidence", type=Path, default=SCRATCH / "author-full-after-code-review")
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    source, evidence, target = (p.resolve() for p in (args.source, args.evidence, args.destination))
    require(source == DEFAULT_SOURCE and evidence == SCRATCH / "author-full-after-code-review" and
            target == DEFAULT_DESTINATION, "This draft is locked to the one named author435 run and destination")
    require(source.is_dir() and evidence.is_dir() and not evidence.is_symlink(),
            "Formal source and original evidence directories must exist")
    require(not target.exists(), "Destination already exists")
    require(not target.is_relative_to(source) and not target.is_relative_to(evidence),
            "Publication must not modify the formal source or original evidence")
    exit_file = evidence.with_name(evidence.name + ".shell-exit.txt")
    console = evidence.with_name(evidence.name + ".console.log")
    require(exit_file.is_file() and not exit_file.is_symlink() and exit_file.read_text().strip() == "0",
            "Completed shell exit0 receipt required")
    require(console.is_file() and not console.is_symlink(), "Original complete Gate console required")
    gate = read_json(evidence / "gate.json")
    require(gate.get("status") == "PASS" and gate.get("source_unchanged") is True,
            "Completed PASS Gate with unchanged source required")
    require(gate.get("identities") == {"root": FORMAL, "child": CHILD, "gitlink": CHILD},
            "Gate exact Pair mismatch")
    require(gate.get("junit") == dict(zip(COUNT_KEYS, (435, 0, 0, 0))), "CPU435 counts required")
    require(count_junit(evidence / "junit.xml") == gate["junit"], "Combined JUnit mismatch")
    for group, count in GROUPS.items():
        wanted = dict(zip(COUNT_KEYS, (count, 0, 0, 0)))
        require(gate.get(group) == wanted and count_junit(evidence / (group + ".xml")) == wanted,
                "Group JUnit counts mismatch: " + group)
    require(len(gate["steps"]) == 6 and all(step.get("exit_code") == 0 for step in gate["steps"]),
            "All six completed import/static/test steps must exit0")
    require([step["name"] for step in gate["steps"]] ==
            ["import_origin", "ruff_check", "ruff_format", *GROUPS], "Unexpected Gate step sequence")
    require(git(source, "rev-parse", "HEAD").decode().strip() == FORMAL and
            git(source / "cosmos-framework", "rev-parse", "HEAD").decode().strip() == CHILD and
            git(source, "rev-parse", "HEAD:cosmos-framework").decode().strip() == CHILD,
            "Formal source exact Pair mismatch")
    require(not git(source, "status", "--porcelain=v1").strip() and
            not git(source / "cosmos-framework", "status", "--porcelain=v1").strip(),
            "Formal source worktrees must remain clean")
    watched = read_json(evidence / "source_sha256.json")
    require(len(watched) == 54 and all(re.fullmatch(r"[0-9a-f]{64}", value) for value in watched.values()),
            "Exactly54 original Gate source fingerprints required")
    environment = read_json(evidence / "environment.json")
    overrides = read_json(evidence / "environment_overrides.json")
    require(environment["packages"]["ruff"] == "0.12.7" and
            overrides.get("CUDA_VISIBLE_DEVICES") == "" and overrides.get("COSMOS_DEVICE") == "cpu",
            "Original CPU/Ruff environment mismatch")
    bindings = []
    for name in sorted(set(watched) | set(EXTRA_BINDINGS)):
        disk = source / name
        require(disk.is_file() and not disk.is_symlink(), "Missing ordinary bound source")
        require(disk.resolve().is_relative_to(source), "Source binding escapes the formal worktree")
        is_child = name.startswith("cosmos-framework/")
        repo, commit = (source / "cosmos-framework", CHILD) if is_child else (source, FORMAL)
        rel = name.removeprefix("cosmos-framework/") if is_child else name
        blob = git(repo, "rev-parse", commit + ":" + rel).decode().strip()
        raw = disk.read_bytes()
        require(raw == git(repo, "cat-file", "blob", blob), "GitBlob/source mismatch")
        require(name not in watched or sha(raw) == watched[name], "Gate watched source drift")
        bindings.append({"path": name, "commit": commit, "git_blob_sha": blob,
                         "sha256": sha(raw), "gate_watched": name in watched})
    origins = [line.strip() for line in (evidence / "import_origin.log").read_text().splitlines() if line.strip()]
    require(origins == [str(source / "cosmos-framework/cosmos_framework/__init__.py")],
            "Actual import-origin record mismatch")
    base = evidence / "phase_b_runtime_tmp"
    require(base.is_dir() and not base.is_symlink(), "Completed original PhaseB temp evidence required")
    phase_b_cases = list(ET.parse(evidence / "phase_b_runtime.xml").getroot().iter("testcase"))
    require(len(phase_b_cases) == 34,
            "Original PhaseB JUnit case list mismatch")
    phase_b_names = {case.attrib["name"] for case in phase_b_cases}
    require(all("test_real_OS_multisim_native_B2_delivery_D5_task_reuse_and_resume[" + suffix + "]"
                in phase_b_names for suffix in ("1-2-2", "2-3-1", "1-3-1")) and
            "test_owned_Server_death_faults_all_live_Slots_and_reaps_only_owned_groups" in phase_b_names,
            "Passed original JUnit lacks the four required OS cases")
    phase_a_names = {case.attrib["name"] for case in
                     ET.parse(evidence / "phase_a_regression.xml").getroot().iter("testcase")}
    require("test_progress_snapshot_allows_real_finish_during_file_read" in phase_a_names and
            "test_900_exact_episode_major_dispatch_real_store_path_and_index_no_model_per_episode" in phase_a_names,
            "Passed PhaseA JUnit lacks F4 progress and original synthetic900 regressions")
    runs = sorted(p / "run" for p in base.glob("test_real_OS_multisim_native_B*") if p.is_dir() and not p.is_symlink())
    failure_runs = sorted(p / "run" for p in base.glob("test_owned_Server_death_faults*") if p.is_dir() and not p.is_symlink())
    store_runs = sorted(p / "new900" for p in base.glob("test_two_real_fault_writers_pr*") if p.is_dir() and not p.is_symlink())
    require(len(runs) == 3 and len(failure_runs) == 1 and len(store_runs) == 1,
            "Expected three success OS runs, one F3 OS run, one Store concurrency run")
    selected, summaries, seen = [], [], set()
    for run in [*runs, *failure_runs]:
        m = read_json(run / "manifest.json")
        layout = (len(m["execution"]["gpu_ids"]), len(m["tasks"]), m["episodes_per_task"])
        failure = run in failure_runs
        label = "F3_server_death" if failure else "G%d_N%d_E%d" % layout
        require(failure or layout in {(1, 2, 2), (2, 3, 1), (1, 3, 1)}, "Unexpected topology")
        require(label not in seen, "Duplicate topology")
        seen.add(label)
        summaries.append(os_summary(run, layout, label))
        selected.extend((p, Path("os") / label / p.relative_to(run))
                        for pattern in PUBLIC_PATTERNS for p in sorted(run.glob(pattern)))
    store_run = store_runs[0]
    store_faults = sorted(store_run.glob("_internal/tasks/*/errors/*.json"))
    require(len(store_faults) == 2 and len({body(p)["id"] for p in store_faults}) == 2,
            "Store concurrent UUID fault originals missing")
    selected.extend((p, Path("store_concurrency") / p.relative_to(store_run))
                    for p in [store_run / "manifest.json", *store_faults])
    # Only generated test-owned server tokens are read, solely for leak checks.
    # Their values and hashes are never printed, serialized or published.
    private_files = sorted(p for run in [*runs, *failure_runs]
                           for p in (run / "_internal/server_capabilities").glob("*.txt"))
    secrets = [p.read_bytes().strip() for p in private_files]
    require(all(p.is_file() and not p.is_symlink() for p in private_files) and
            len(secrets) == 5 and all(len(s) >= 20 for s in secrets),
            "Expected five private generated test-owned Server capabilities")
    raw_names = ["gate.json", "environment.json", "environment_overrides.json", "source_sha256.json",
                 "import_origin.log", "ruff_check.log", "ruff_format.log", "junit.xml",
                 *[group + suffix for group in GROUPS for suffix in (".log", ".xml")]]
    require({p.name for p in evidence.iterdir() if p.is_file()} == set(raw_names),
            "Unexpected or missing top-level raw file: inspect before updating the explicit allowlist")
    selected.extend((evidence / name, Path("raw") / name) for name in raw_names)
    selected.extend([(console, Path("raw/console.log")), (exit_file, Path("raw/shell-exit.txt"))])
    launcher = SCRATCH / "run_author435_once.sh"
    require(launcher.is_file() and not launcher.is_symlink(), "Original one-run launcher required")
    selected.append((launcher, Path("raw/run_author435_once.sh")))
    unique = {str(dest): (original, dest) for original, dest in selected}
    require(len(unique) == len(selected), "Duplicate publication path")
    with tempfile.TemporaryDirectory(prefix="author435-package-", dir=SCRATCH) as scratch:
        stage = Path(scratch) / "publication"
        stage.mkdir()
        mappings = []
        for original, destination in sorted(unique.values(), key=lambda item: str(item[1])):
            require(original.is_file() and not original.is_symlink(), "Nonordinary public source")
            require(original.resolve() == original.absolute(), "Public original has a symlink ancestor")
            privacy_check(original, secrets)
            raw = original.read_bytes()
            output = stage / destination
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(raw)
            require(output.read_bytes() == raw, "Raw byte copy mismatch")
            mappings.append({"original": str(original), "published": str(destination),
                             "sha256": sha(raw), "bytes": len(raw)})
        def save(name, value):
            (stage / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
        save("original_to_published.json", mappings)
        save("source_gitblob_bindings.json", {"formal_root": FORMAL, "child_gitlink": CHILD,
             "watched_and_extra_bindings": bindings, "actual_import_origin": origins})
        save("os_summary.json", {"synthetic_CPU_only": True, "runs": summaries,
             "store_concurrency_fault_uuids": [body(p)["id"] for p in store_faults]})
        save("handoff.json", {"role": "AUTHOR_CPU, not independent DS", "formal_root": FORMAL,
             "child_gitlink": CHILD, "status": "PASS", "junit": gate["junit"],
             "groups": {group: gate[group] for group in GROUPS}, "source_unchanged": True,
             "original_source_fingerprints": len(watched), "total_source_bindings": len(bindings),
             "shell_exit": 0, "gate_syntax_files": gate.get("syntax_files"),
             "copy_policy": "Exact bytes of explicitly allowlisted originals; not all temporary/cache artifacts.",
             "privacy": {"generated_test_server_capabilities_scanned": len(private_files),
                         "private_values_or_hashes_published": False, "public_recursive_field_check": "PASS"},
             "excluded": ["all caches", "whole *_tmp trees", "server capability files",
                          "actor/assignment configs", "runtime proofs", "fake checkpoint containers"],
             "limits": "Synthetic CPU fixtures including the synthetic900 scheduling regression. No native GPU/Cosmos weights/RoboCasa/EGL/real DCP/formal900 benchmark/training execution. Foreign survival and completed Resume are carried by passed original test assertions, not fabricated standalone raw artifacts.",
             "independent_DS": "NOT_RUN by this author archive; no Evidence Gate closure inferred.",
             "next_step": "Owner/GPT review and separately authorized independent DS unified Gate; no automatic dispatch or V3 merge."})
        for p in stage.rglob("*"):
            if p.is_file():
                privacy_check(p, secrets)
        save("artifact_sha256.json", {str(p.relative_to(stage)): sha(p.read_bytes())
             for p in sorted(stage.rglob("*")) if p.is_file()})
        require(all(sha(Path(row["original"]).read_bytes()) == row["sha256"] for row in mappings),
                "Original evidence changed during archival")
        require(read_json(evidence / "gate.json")["status"] == "PASS" and
                exit_file.read_text().strip() == "0", "Original completion receipts changed during archival")
        require(all(sha((source / name).read_bytes()) == digest for name, digest in watched.items()) and
                not git(source, "status", "--porcelain=v1").strip() and
                not git(source / "cosmos-framework", "status", "--porcelain=v1").strip(),
                "Formal source changed during archival")
        target.parent.mkdir(parents=True, exist_ok=True)
        require(not target.exists(), "Destination appeared during archive")
        stage.rename(target)
    print(json.dumps({"destination": str(target), "formal_root": FORMAL,
                      "child_gitlink": CHILD, "junit": gate["junit"],
                      "raw_copies": len(mappings), "source_bindings": len(bindings),
                      "capability_leak_check": "PASS"}, indent=2))


if __name__ == "__main__":
    main()
