"""PASS-only F5 evidence packager. Does not import/execute project code or tests.

Original evidence and the clean Formal Pair remain read-only. Root must approve
running this script; writing the script does not trigger publication.
"""

from __future__ import annotations

import ast
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

BASE = Path("/workspace/work/runtime-probe-evidence")
SOURCE = Path("/workspace/work/psm-wma-runtime-evidence-formal")
TARGET = Path("/workspace/work/psm-wma-runtime-evidence/docs/collab/codex/evidence/2026-10-30_eval_v2_runtime_probe_F5")
FORMAL = "7c74dc26ac4837f193727ecf847b9b64554c18b2"
CHILD = "53c3c95202e14d3b72d236eee6899a80acf82989"
OLD_ROOT = "427b4d09cdd8070820a39b93ebf2ff832a23e359"
OLD_CHILD = "0ae313e329d290fc6b8a50fda1112820fb7ac485"
TEST = "tools/v3/eval_v2_production_tests/runtime_evidence_test.py"
STORE = "cosmos_framework/evaluation/robocasa_v2/store.py"
MIB = 1024 * 1024
RAW_NAMES = ("before.json", "execution.json", "console.log", "junit.xml", "shell-exit.txt")
SMALL_PATTERNS = (
    "manifest.json", "summary.json", "episodes.jsonl", "tasks/*/summary.json",
    "_internal/run_inputs.json", "_internal/verification_cache.json",
    "_internal/coordination_metrics.json", "_internal/invocations/*.json",
    "_internal/tasks/*/streams/*.json", "_internal/tasks/*/cleanup/*.json",
    "_internal/tasks/*/environments/*.json",
    "_internal/tasks/*/slots/*/attempts/*.json",
    "_internal/tasks/*/slots/*/events/*/*.json",
    *["tasks/*/episodes/*/" + leaf for leaf in (
        "actions.jsonl", "core_inventory.json", "local_memory.json",
        "predictions.jsonl", "result.json", "scene_provenance.json")],
)


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def original(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.resolve() == path.absolute(),
            "Missing ordinary non-symlink original: " + str(path))
    return path.read_bytes()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return sha(canonical(value))


def document(path):
    return json.loads(original(path))


def body(path):
    value = document(path)
    if isinstance(value, dict) and set(value) == {"body", "sha256"}:
        require(value["sha256"] == digest(value["body"]), "Corrupt sealed original record")
        return value["body"]
    return value


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def junit(path):
    tree = ET.fromstring(original(path))
    suites = list(tree.iter("testsuite"))
    counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites)
              for key in ("tests", "failures", "errors", "skipped")}
    return tree, counts


def reject_private(value):
    if isinstance(value, dict):
        for key, item in value.items():
            key = str(key).lower().replace("-", "_")
            if key in {"capability", "capabilities", "owner_token", "owner_capability"} or key.endswith("_owner_token"):
                require(item in (None, "", False, [], {}), "Nonempty private field in publication candidate")
            reject_private(item)
    elif isinstance(value, list):
        for item in value:
            reject_private(item)


def safe_public(path, raw):
    # These are synthetic vendor fixtures, not credential-bearing OS fixtures.
    # Still reject any unexpected capability/owner-token fields before copying.
    if path.suffix == ".json":
        reject_private(json.loads(raw))
    elif path.suffix == ".jsonl":
        for line in raw.splitlines():
            if line.strip():
                reject_private(json.loads(line))


def verify_run(label, expected):
    directory = BASE / label
    require(directory.is_dir() and not directory.is_symlink(), "Missing original run " + label)
    require({p.name for p in directory.iterdir() if p.is_file()} == set(RAW_NAMES),
            "Unexpected/missing top-level raw original in " + label)
    metadata = document(directory / "execution.json")
    before = document(directory / "before.json")
    require(all(metadata[key] == before[key] for key in before), "Before/metadata mismatch: " + label)
    require(metadata["source_unchanged"] is True and
            metadata["source_before"] == metadata["source_after"], "Source drift recorded: " + label)
    require(original(directory / "shell-exit.txt").decode().strip() == str(metadata["shell_exit"]),
            "Raw shell exit mismatch: " + label)
    tree, counts = junit(directory / "junit.xml")
    require(counts == expected, "Unexpected JUnit counts: " + label)
    require(metadata["shell_exit"] == (1 if label == "red" else 0), "Unexpected run exit: " + label)
    env = metadata["environment_overrides"]
    require(env["CUDA_VISIBLE_DEVICES"] == "" and env["COSMOS_DEVICE"] == "cpu" and
            env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1", "CPU-only environment record mismatch")
    observed = metadata["source_before"]
    require(observed["child"] == observed["gitlink"], "Child/Gitlink mismatch in raw metadata")
    require(len(observed["source_sha256"]) == 10, "Expected ten watched source originals")
    if label == "red":
        require(observed["root"] == OLD_ROOT and observed["child"] == OLD_CHILD and
                observed["child_status"] == "" and observed["root_status"] == "?? " + TEST,
                "RED must retain the exact old Pair plus only the untracked same new test")
        failures = [failure for case in tree.iter("testcase") for failure in case.findall("failure")]
        require(len(failures) == 1 and "oversized JSON" in (failures[0].text or "") and
                "store.py" in (failures[0].text or ""), "RED is not the original oversized Store failure")
    else:
        groups = Counter(case.attrib["classname"].split(".")[-1] for case in tree.iter("testcase"))
        require(groups == {"runtime_evidence_test": 21, "entry_test": 15, "store_test": 49},
                "85 must be21 new+15 existing entry+49 Store; do not add run totals")
        if label.startswith("final"):
            require(observed["root_status"] == observed["child_status"] == "",
                    "Final/preformat runs must have been clean exact Pairs")
    return metadata, counts


def main():
    require(not TARGET.exists(), "Publication destination must be NEW")
    require(SOURCE.is_dir() and BASE.is_dir(), "Missing source/evidence roots")
    expected_pass = {"tests": 85, "failures": 0, "errors": 0, "skipped": 0}
    runs = {}
    for label in ("red", "working", "final", "final-formatted"):
        wanted = {"tests": 1, "failures": 1, "errors": 0, "skipped": 0} if label == "red" else expected_pass
        metadata, counts = verify_run(label, wanted)
        runs[label] = {"metadata": metadata, "counts": counts}
    final = runs["final-formatted"]["metadata"]
    require(final["source_before"]["root"] == FORMAL and
            final["source_before"]["child"] == CHILD, "Actual final formatted Pair mismatch")
    require(git(SOURCE, "rev-parse", "HEAD").decode().strip() == FORMAL and
            git(SOURCE / "cosmos-framework", "rev-parse", "HEAD").decode().strip() == CHILD and
            git(SOURCE, "rev-parse", "HEAD:cosmos-framework").decode().strip() == CHILD,
            "Current clean Formal Pair mismatch")
    require(not git(SOURCE, "status", "--porcelain=v1").strip() and
            not git(SOURCE / "cosmos-framework", "status", "--porcelain=v1").strip(),
            "Formal source must remain clean")
    hashes = final["source_before"]["source_sha256"]
    require(all(sha(original(SOURCE / name)) == expected for name, expected in hashes.items()),
            "Final source fingerprints no longer match original execution")
    test_sha = hashes[TEST]
    require(all(run["metadata"]["source_before"]["source_sha256"][TEST] == test_sha for run in runs.values()),
            "RED and every GREEN must use exactly the same test hash")
    red_bindings = {}
    for name, expected in runs["red"]["metadata"]["source_before"]["source_sha256"].items():
        if name == TEST:
            red_bindings[name] = {"sha256": expected, "provenance": "untracked copy identical to final test GitBlob"}
            continue
        is_child = name.startswith("cosmos-framework/")
        repo, commit = (SOURCE / "cosmos-framework", OLD_CHILD) if is_child else (SOURCE, OLD_ROOT)
        relative = name.removeprefix("cosmos-framework/") if is_child else name
        blob = git(repo, "rev-parse", commit + ":" + relative).decode().strip()
        require(sha(git(repo, "cat-file", "blob", blob)) == expected,
                "RED recorded production fingerprint differs from its old exact GitBlob")
        red_bindings[name] = {"commit": commit, "git_blob": blob, "sha256": expected}
    proof = document(BASE / "static-final/proof.json")
    require(proof["formal_root"] == FORMAL and proof["child"] == CHILD and
            proof["parent_root"] == OLD_ROOT and proof["parent_child"] == OLD_CHILD,
            "Final static scope proof Pair mismatch")
    require(len(proof["checks"]) == 5 and all(c["exit_code"] == 0 for c in proof["checks"]) and
            proof["syntax_files"] == 4, "Final static checks must all have passed")
    require(set(proof["ordinary_store_AST_unchanged_except"]) == {"MAX_RUNTIME_PROBE", "write_runtime_probe"} and
            set(proof["entry_AST_unchanged_except_fake_prepare_fixture_fields"]) == {"runtime", "runtime_probe_evidence"},
            "Unexpected scope exception in static proof")
    require(proof["actual_unmodified_verify_source_and_import"] == {
        "source": [FORMAL, CHILD, FORMAL],
        "store_import": str(SOURCE / "cosmos-framework" / STORE)},
        "Actual unmodified verify_source/import observation mismatch")
    bindings = {}
    for name in sorted(set(hashes) | set(proof["bindings"])):
        is_child = name.startswith("cosmos-framework/")
        repo, commit = (SOURCE / "cosmos-framework", CHILD) if is_child else (SOURCE, FORMAL)
        relative = name.removeprefix("cosmos-framework/") if is_child else name
        blob = git(repo, "rev-parse", commit + ":" + relative).decode().strip()
        raw = original(SOURCE / name)
        require(raw == git(repo, "cat-file", "blob", blob), "Formal source/GitBlob mismatch")
        bindings[name] = {"commit": commit, "git_blob": blob, "sha256": sha(raw), "watched_in_final": name in hashes}
        if name in proof["bindings"]:
            require({key: bindings[name][key] for key in ("commit", "git_blob", "sha256")} == proof["bindings"][name],
                    "Raw final static proof source binding mismatch")
    for name in proof["protected_Root_blobs_unchanged"]:
        require(git(SOURCE, "rev-parse", OLD_ROOT + ":" + name) == git(SOURCE, "rev-parse", FORMAL + ":" + name),
                "Protected production Root source changed")
    old_store = ast.parse(git(SOURCE / "cosmos-framework", "show", OLD_CHILD + ":" + STORE))
    new_store = ast.parse(git(SOURCE / "cosmos-framework", "show", CHILD + ":" + STORE))
    new_store.body = [node for node in new_store.body if not
        (isinstance(node, ast.FunctionDef) and node.name == "write_runtime_probe") and not
        (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MAX_RUNTIME_PROBE" for t in node.targets))]
    require(ast.dump(new_store) == ast.dump(old_store), "Ordinary Store AST changed")
    require(b"Would reformat:" in original(BASE / "static/check_1.log") and
            b"write_runtime_probe" in original(BASE / "static/store_format_diff.txt"),
            "Initial format-check debug failure originals missing")
    case = BASE / "final-formatted/tmp/test_public_large_runtime_evid0/out"
    require(case.is_dir() and not case.is_symlink(), "Original public large case output missing")
    manifest = document(case / "manifest.json")
    anchor_path = case / "_internal/run_inputs.json"
    anchor_raw, anchor = original(anchor_path), document(anchor_path)
    require(len(anchor_raw) < 256 * 1024 and "runtime_probe_evidence" not in anchor and
            set(anchor["runtime"]) == {"digest"}, "Run anchor is not compact")
    cache = document(case / "_internal/verification_cache.json")
    require(cache["anchor_sha256"] == digest(anchor), "Model verification cache anchor binding mismatch")
    invocation_paths = sorted((case / "_internal/invocations").glob("*.json"))
    invocations = [body(p) for p in invocation_paths]
    require(len(invocations) == 2 and {row["mode"] for row in invocations} == {"fresh", "resume"},
            "Need one original Fresh and one Resume invocation")
    references = []
    for invocation in invocations:
        reference = invocation["runtime_probe"]
        require(set(reference) == {"path", "canonical_sha256"}, "Unexpected invocation sidecar reference schema")
        path = Path(reference["path"])
        if not path.is_absolute():
            path = case / path
        require(path.parent == case / "_internal/runtime_probe" and
                re.fullmatch(r"[0-9a-f]{32}\.json", path.name), "Invalid original sidecar path")
        references.append((invocation["mode"], path, reference))
    require({path for _, path, _ in references} == set((case / "_internal/runtime_probe").glob("*.json")) and
            len({path for _, path, _ in references}) == 2, "Sidecar set/reference mismatch")
    witnesses = [json.loads(line[len("V2_RUNTIME_EVIDENCE_WITNESS "):])
                 for line in original(BASE / "final-formatted/console.log").decode().splitlines()
                 if line.startswith("V2_RUNTIME_EVIDENCE_WITNESS ")]
    require(len(witnesses) == 1, "Original final runtime evidence witness missing")
    witness = witnesses[0]
    require(witness["anchor_bytes_unchanged"] is True and witness["Core_bytes_unchanged"] is True and
            witness["stdout_warning_only_changed"] is True and witness["fresh_evidence_count"] == 1 and
            witness["resume_evidence_count"] == 2 and witness["synthetic_asset_SHA_entries"] == 150_000 and
            witness["anchor_canonical_sha256_before"] == witness["anchor_canonical_sha256_after"] == digest(anchor),
            "Original passed test witness does not prove immutable anchor/Core or append-only evidence")
    selected = [(BASE / label / name, Path("raw") / label / name)
                for label in runs for name in RAW_NAMES]
    selected += [(BASE / "static-final" / name, Path("raw/static-final") / name)
                 for name in ("proof.json", "root.diff", "child.diff", *[f"check_{i}.log" for i in range(5)])]
    selected += [(BASE / "static" / name, Path("debug/initial-format-failure") / name)
                 for name in ("check_0.log", "check_1.log", "store_format_diff.txt")]
    selected += [(BASE / name, Path("helpers") / name) for name in ("run_focused.py", "check_static.py", "archive.py")]
    selected += [(p, Path("large_case") / p.relative_to(case))
                 for pattern in SMALL_PATTERNS for p in sorted(case.glob(pattern))]
    require(len({str(dest) for _, dest in selected}) == len(selected), "Duplicate explicit archive path")
    core = sorted(case.glob("tasks/*/episodes/*/result.json"))
    require(len(core) == 2, "Original two admitted Core results missing")
    mappings, compressed_records = [], []
    with tempfile.TemporaryDirectory(prefix="f5-publication-", dir=BASE) as scratch:
        stage = Path(scratch) / "publication"
        stage.mkdir()
        def save(name, value):
            (stage / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
        for source, relative in selected:
            raw = original(source)
            safe_public(source, raw)
            output = stage / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(raw)
            require(original(output) == raw, "Original byte copy mismatch")
            mappings.append({"original": str(source), "published": str(relative), "encoding": "original_bytes",
                             "original_sha256": sha(raw), "original_bytes": len(raw),
                             "published_sha256": sha(raw), "published_bytes": len(raw)})
        for mode, source, reference in references:
            raw = original(source)
            require(16 * MIB < len(raw) <= 64 * MIB, "Full sidecar must exceed the old report limit and obey the private limit")
            record = json.loads(raw)
            reject_private(record)
            require(set(record) == {"manifest_digest", "evaluation_runtime", "runtime_probe_evidence"} and
                    record["manifest_digest"] == manifest["digest"] and digest(record) == reference["canonical_sha256"],
                    "Original sidecar/canonical invocation binding mismatch")
            runtime, probe = record["evaluation_runtime"], record["runtime_probe_evidence"]
            assets = runtime["packages"]["robocasa"]["untracked_asset_sha256"]
            require(len(assets) == 150_000 and all(re.fullmatch(r"[0-9a-f]{64}", value) for value in assets.values()),
                    "Full synthetic asset SHA table missing")
            require(runtime["digest"] == digest({k: v for k, v in runtime.items() if k != "digest"}) == anchor["runtime"]["digest"],
                    "Stable runtime digest binding mismatch")
            lines = probe["stdout"].splitlines()
            require(len(lines) == 2 and lines[1].startswith("PSM_RUNTIME ") and
                    json.loads(lines[1][len("PSM_RUNTIME "):]) == runtime,
                    "Raw probe stdout does not retain the complete runtime JSON")
            buffer = io.BytesIO()
            with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, compresslevel=9, mtime=0) as stream:
                stream.write(raw)
            compressed = buffer.getvalue()
            require(compressed[:3] == b"\x1f\x8b\x08" and compressed[4:8] == b"\0" * 4 and
                    compressed[3] & 8 == 0, "Gzip must retain mtime0 and omit the source filename")
            restored = gzip.decompress(compressed)
            require(restored == raw and json.loads(restored) == record and
                    digest(json.loads(restored)) == reference["canonical_sha256"],
                    "Lossless gzip bytes/JSON/canonical verification failed")
            relative = Path("large_case/_internal/runtime_probe") / (source.name + ".gz")
            output = stage / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(compressed)
            require(gzip.decompress(original(output)) == raw, "Published gzip byte verification failed")
            item = {"mode": mode, "original": str(source), "published": str(relative),
                    "encoding": "gzip_mtime0_no_filename", "original_sha256": sha(raw),
                    "original_bytes": len(raw), "published_sha256": sha(compressed),
                    "published_bytes": len(compressed), "canonical_sha256": reference["canonical_sha256"],
                    "decompressed_bytes_JSON_canonical_verified": True,
                    "runtime_digest": runtime["digest"], "asset_SHA_entries": len(assets),
                    "asset_table_canonical_sha256": digest(assets), "stdout_sha256": sha(probe["stdout"].encode()),
                    "stdout_warning": lines[0], "stdout_body_sha256": sha(lines[1].encode())}
            mappings.append(item)
            compressed_records.append(item)
        require(len({item["runtime_digest"] for item in compressed_records}) == 1 and
                len({item["asset_table_canonical_sha256"] for item in compressed_records}) == 1 and
                len({item["stdout_body_sha256"] for item in compressed_records}) == 1 and
                len({item["stdout_warning"] for item in compressed_records}) == 2,
                "Fresh/Resume must differ only in the probe stdout warning")
        require(sorted(item["original_bytes"] for item in compressed_records) == sorted(witness["sidecar_bytes"]) and
                len(anchor_raw) == witness["run_inputs_bytes"], "Actual original byte sizes disagree with the original witness")
        save("source_gitblob_bindings.json", {"formal_root": FORMAL, "child_gitlink": CHILD,
             "watched_source_fingerprints": hashes, "bindings": bindings,
             "red_source_GitBlob_bindings": red_bindings,
             "red_new_test_untracked_but_same_sha256": test_sha})
        save("sidecar_lossless_gzip.json", compressed_records)
        save("original_to_published.json", mappings)
        save("handoff.json", {"formal_root": FORMAL, "child_gitlink": CHILD,
             "role": "AUTHOR focused CPU/static; not DS", "final": {"label": "final-formatted", "counts": expected_pass,
             "groups": {"new_runtime_evidence": 21, "existing_entry": 15, "existing_store": 49},
             "source_unchanged": True, "clean": True, "shell_exit": 0},
             "red": {"pair": [OLD_ROOT, OLD_CHILD], "counts": runs["red"]["counts"], "shell_exit": 1,
             "scope": "Same new test copied untracked into clean old production Pair; original oversized JSON failure retained as FAIL."},
             "intermediate_only": {label: {"counts": runs[label]["counts"],
                 "original_source": runs[label]["metadata"]["source_before"]} for label in ("working", "final")},
             "debug": "Initial static format check failed; unchanged original logs/diff retained, final static checks separately PASS.",
             "static_final": {"checks": 5, "exit_codes": [0] * 5, "syntax_files": 4,
                 "actual_unmodified_verify_source": proof["actual_unmodified_verify_source_and_import"],
                 "ordinary_Store_AST_unchanged_except": proof["ordinary_store_AST_unchanged_except"]},
             "large_case": {"original_test_witness": witness, "sidecars": 2, "asset_entries_each": 150_000,
                 "compression": "Complete raw original bytes preserved losslessly in deterministic gzip; no plain oversized sidecars committed.",
                 "Core_before_after_equality": "Carried by passed original test and raw witness; only the surviving Core originals are archived, no separate before snapshot was produced."},
             "not_additive": "Repeated working/preformat/final runs are separate evidence, not an aggregate test total.",
             "excluded": ["whole tmp/cache trees", "miniGit repositories", "fake checkpoint containers", "real assets"],
             "limits": "Synthetic vendor/interpreter/model-execution boundaries with real prepare/verify_source/Git/model identity/Store. No real assets/GPU/Canary/900/full unified Gate or training execution in this focused archive.",
             "independent_DS": "Not performed or approved by this author evidence.",
             "next_step": "Root/Owner review; no automatic Gate replay, DS dispatch or V3 merge."})
        save("artifact_sha256.json", {str(path.relative_to(stage)): sha(original(path))
             for path in sorted(stage.rglob("*")) if path.is_file()})
        require(all(sha(original(Path(item["original"]))) == item["original_sha256"] for item in mappings),
                "Original evidence changed during archive")
        require(all(sha(original(SOURCE / name)) == expected for name, expected in hashes.items()) and
                not git(SOURCE, "status", "--porcelain=v1").strip() and
                not git(SOURCE / "cosmos-framework", "status", "--porcelain=v1").strip(),
                "Formal source changed during archive")
        require(not TARGET.exists(), "Destination appeared during archive")
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        stage.rename(TARGET)
    print(json.dumps({"published": str(TARGET), "formal_root": FORMAL, "child_gitlink": CHILD,
                      "final_focused": expected_pass, "separate_original_runs": list(runs),
                      "lossless_compressed_sidecars": len(compressed_records), "original_copies": len(mappings)}, indent=2))


if __name__ == "__main__":
    main()
