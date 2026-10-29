#!/usr/bin/env python3
"""Read frozen Git objects with git/stdlib AST; do not import project code.

This is an internal author-side read-only static audit, NOT a GPT Code Gate,
independent DS execution, GPU performance test or native DCP Resume test.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_ROOT = "3d5806a2b702b42d3f24e7645aa7cec9cd70b0c7"
FORMAL_ROOT = "e0fe911dfb9fd34957234828195cf051713f6c3d"
BASE_CHILD = "746c5cf2f2324104a62fb71510343aa40d3976c5"
FORMAL_CHILD = "f6a92d47b6dac7998ddc58b3da26ef93f8068dc7"
LAST_PRODUCTION_CHILD = "d64e5c1d8541341b26f6ef0557822fe76d8dd52d"
TRAINER = "cosmos_framework/trainer/matched_no_ttt.py"
PROFILE = "cosmos_framework/utils/no_ttt_loader_profile.py"
RESUME_TEST = "cosmos_framework/trainer/no_ttt_cpu_loader_resume_test.py"
EXAMPLE_TEST = "examples/psm_wma_robocasa_matched_no_ttt_test.py"
WORKER_ENTRY_TEST = "tools/v3/no_ttt_workers_entry_test.py"
ASYNC_PRODUCTION_FILES = (
    "cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py",
    "cosmos_framework/trainer/matched_no_ttt.py",
    "cosmos_framework/trainer/no_ttt_async_loader.py",
    "cosmos_framework/trainer/no_ttt_async_recipe.py",
    "cosmos_framework/utils/no_ttt_loader_profile.py",
)

CHILD_PROTECTED_FILES = (
    "cosmos_framework/trainer/no_ttt_cpu_loader.py",
    "cosmos_framework/model/generator/mot/robocasa_exact_window_local.py",
    "cosmos_framework/checkpoint/dcp.py",
    "cosmos_framework/trainer/__init__.py",
    "cosmos_framework/trainer/local_memory_grouped.py",
    "cosmos_framework/data/generator/action/utils/transforms.py",
    "cosmos_framework/data/generator/augmentors/text_tokenizer.py",
    "cosmos_framework/data/generator/action/utils/transform_random.py",
    "cosmos_framework/utils/generator/optimizer.py",
    "examples/psm_wma_robocasa_matched_no_ttt.py",
    "cosmos_framework/trainer/no_ttt_cpu_loader_test.py",
    "cosmos_framework/trainer/matched_no_ttt_test.py",
    "cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py",
    "cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py",
)
ROOT_PROTECTED_FILES = (
    "scripts/train_v3_matched_no_ttt.sh",
    "scripts/train_v3_matched_no_ttt_4gpu.sh",
    "scripts/serve_v3_matched_no_ttt.py",
    "configs/eval/robocasa_matched_no_ttt.example.yaml",
    "tools/v3/matched_no_ttt_entry_test.py",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str, binary: bool = False):
    data = subprocess.check_output(["git", "-C", str(repo), *args])
    return data if binary else data.decode().strip()


def content(repo: Path, revision: str, path: str) -> bytes:
    return git(repo, "show", f"{revision}:{path}", binary=True)


def tree(repo: Path, revision: str, path: str) -> ast.Module:
    return ast.parse(content(repo, revision, path).decode(), filename=f"{revision}:{path}")


def ast_bytes(value: ast.AST) -> bytes:
    return ast.dump(value, include_attributes=False).encode()


def named(module: ast.AST, trail: str) -> ast.AST:
    value = module
    for name in trail.split("."):
        found = [part for part in value.body if getattr(part, "name", None) == name]
        if len(found) != 1:
            raise ValueError(f"expected exactly one AST node for {trail}: {name}")
        value = found[0]
    return value


def equality_record(label: str, old: ast.AST, new: ast.AST) -> dict:
    left, right = ast_bytes(old), ast_bytes(new)
    return {"scope": label, "baseline_ast_sha256": sha256(left), "formal_ast_sha256": sha256(right), "equal": left == right}


def byte_records(repo: Path, baseline: str, formal: str, paths: tuple[str, ...]) -> list[dict]:
    records = []
    for path in paths:
        old, new = content(repo, baseline, path), content(repo, formal, path)
        records.append({
            "path": path,
            "baseline_blob": git(repo, "rev-parse", f"{baseline}:{path}"),
            "formal_blob": git(repo, "rev-parse", f"{formal}:{path}"),
            "baseline_sha256": sha256(old), "formal_sha256": sha256(new),
            "baseline_bytes": len(old), "formal_bytes": len(new), "equal": old == new,
        })
    return records


def top_level_tests(module: ast.Module) -> dict[str, ast.AST]:
    return {part.name: part for part in module.body if isinstance(part, (ast.FunctionDef, ast.AsyncFunctionDef)) and part.name.startswith("test_")}


def assertions(node: ast.AST) -> list[str]:
    return [sha256(ast_bytes(part)) for part in ast.walk(node) if isinstance(part, ast.Assert)]


def remove_exact_statement(body: list[ast.stmt], text: str) -> ast.stmt:
    expected = ast.parse(text).body[0]
    found = [index for index, part in enumerate(body) if ast_bytes(part) == ast_bytes(expected)]
    if len(found) != 1:
        raise ValueError(f"did not find exactly one permitted fixture addition: {text}")
    return body.pop(found[0])


def fixture_module_audit(repo: Path, baseline: str, formal: str, path: str, normalizer) -> dict:
    old_module, new_module = tree(repo, baseline, path), tree(repo, formal, path)
    old_tests, new_tests = top_level_tests(old_module), top_level_tests(new_module)
    if old_tests.keys() != new_tests.keys():
        raise ValueError(f"test functions added/removed/renamed: {path}")
    function_checks = []
    for name in old_tests:
        before, after = assertions(old_tests[name]), assertions(new_tests[name])
        if before != after:
            raise ValueError(f"old assertion AST changed: {path}:{name}")
        function_checks.append({
            "test_function": name,
            "baseline_full_function_ast_sha256": sha256(ast_bytes(old_tests[name])),
            "formal_full_function_ast_sha256": sha256(ast_bytes(new_tests[name])),
            "full_function_ast_equal_before_normalization": ast_bytes(old_tests[name]) == ast_bytes(new_tests[name]),
            "baseline_assertion_ast_sha256": before,
            "formal_assertion_ast_sha256": after,
            "assertion_ast_equal": True,
        })
    global_before, global_after = assertions(old_module), assertions(new_module)
    if global_before != global_after:
        raise ValueError(f"assert AST changed outside test functions: {path}")
    changes = normalizer(new_module)
    normalized = equality_record(f"whole_module_after_exact_fixture_normalization:{path}", old_module, new_module)
    if not normalized["equal"]:
        raise ValueError(f"fixture-only normalized module AST differs: {path}")
    for entry in function_checks:
        name = entry["test_function"]
        entry["normalized_function_ast_equal"] = ast_bytes(old_tests[name]) == ast_bytes(named(new_module, name))
        if not entry["normalized_function_ast_equal"]:
            raise ValueError(f"normalized existing test function differs: {path}:{name}")
    return {
        "path": path,
        "source_bytes": byte_records(repo, baseline, formal, (path,))[0],
        "test_functions": function_checks,
        "assertion_count_entire_module": len(global_before),
        "all_old_assertion_ast_equal": True,
        "all_untouched_function_ast_equal": all(item["full_function_ast_equal_before_normalization"] for item in function_checks if item["test_function"] not in changes["fixture_modified_test_functions"]),
        "normalization": changes,
        "normalized_whole_module": normalized,
    }


def normalize_example_fixture(module: ast.Module) -> dict:
    import_node = remove_exact_statement(module.body, "from dataclasses import make_dataclass")
    helper_text = '''def _structured_identity_fixture(value):
    """Use supported structured config records; never relax production identity."""
    if isinstance(value, SimpleNamespace):
        values = {key: _structured_identity_fixture(item) for key, item in vars(value).items()}
        record = make_dataclass("IdentityConfigFixture", [(key, object) for key in values])
        return record(**values)
    if isinstance(value, dict):
        return {key: _structured_identity_fixture(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_structured_identity_fixture(item) for item in value)
    return value
'''
    helper = remove_exact_statement(module.body, helper_text)
    target = "test_all_worker_counts_share_strict_training_and_config_identity"
    function = named(module, target)
    additions = (
        "config = _structured_identity_fixture(config)",
        "args.dataset_index_root.mkdir(parents=True)",
        '(args.dataset_index_root / "receipt.json").write_text("{}")',
    )
    removed = [ast.unparse(remove_exact_statement(function.body, statement)) for statement in additions]
    return {
        "fixture_modified_test_functions": [target],
        "removed_exact_import": ast.unparse(import_node),
        "removed_exact_helper": ast.unparse(helper),
        "removed_helper_ast_sha256": sha256(ast_bytes(helper)),
        "removed_exact_fixture_statements": removed,
        "assertions_modified": False,
    }


def normalize_worker_job_fixture(module: ast.Module) -> dict:
    target = "test_same_job_identity_ignores_loader_runtime_changes_but_still_checks_semantics"
    function = named(module, target)
    expected_args = ast.parse('args = _args(tmp_path, "--no-ttt", "--world-size", "4", "--ga", "4", "--job-name", "no_ttt_worker_runtime_contract_world4_ga4")').body[0]
    matches = [statement for statement in function.body if ast_bytes(statement) == ast_bytes(expected_args)]
    if len(matches) != 1:
        raise ValueError("did not find the exact ordinary strict-Job fixture assignment")
    call = matches[0].value
    if not isinstance(call, ast.Call) or call.args[-1].value != "no_ttt_worker_runtime_contract_world4_ga4":
        raise ValueError("strict-Job fixture AST changed unexpectedly")
    call.args[-1].value = "no_ttt_packed128_droid_fresh_30k_world4_ga4"
    return {
        "fixture_modified_test_functions": [target],
        "permitted_literal_change": {
            "baseline": "no_ttt_packed128_droid_fresh_30k_world4_ga4",
            "formal": "no_ttt_worker_runtime_contract_world4_ga4",
            "count": 1,
            "purpose": "exercise ordinary strict namespace rather than the existing Owner-exempt formal Job",
        },
        "assertions_modified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-worktree", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("audit.json"))
    args = parser.parse_args()
    root, child = args.root_worktree.resolve(), args.root_worktree.resolve() / "cosmos-framework"
    state = {
        "schema": "nottt_async_protected_static_audit_v2",
        "audit_kind": "INTERNAL_AUTHOR_READONLY_STATIC_AUDIT_NOT_GPT_CODE_GATE",
        "status": "FAIL_STATIC_SCOPE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline": {"root": BASE_ROOT, "child": BASE_CHILD},
        "formal": {"root": FORMAL_ROOT, "child": FORMAL_CHILD},
        "last_production_child_before_fixture_only_fix": LAST_PRODUCTION_CHILD,
        "probe_sha256": sha256(Path(__file__).read_bytes()),
        "command": [sys.executable, str(Path(__file__).resolve()), "--root-worktree", str(root), "--output", str(args.output.resolve())],
        "limitations": [
            "Static Git-object/AST checks only; no project modules imported or project code executed.",
            "No independent GPT/DS verdict, actual GPU overlap, CUDA RNG restoration or native DCP Resume qualification.",
            "The old reduced-B1 arbitrary-stochastic-transform Resume fixture explicitly injects the legacy RAW backend; its unchanged assertions do not prove the new async backend.",
            "Functions with permitted additions are compared only after the exact documented normalization; originals remain bound by Git Blob and SHA256.",
        ],
    }
    try:
        for repo, revision in ((root, BASE_ROOT), (root, FORMAL_ROOT), (child, BASE_CHILD), (child, FORMAL_CHILD), (child, LAST_PRODUCTION_CHILD)):
            if git(repo, "rev-parse", f"{revision}^{{commit}}") != revision:
                raise ValueError(f"commit object mismatch: {revision}")
        state["formal"]["gitlink"] = git(root, "rev-parse", f"{FORMAL_ROOT}:cosmos-framework")
        state["baseline"]["gitlink"] = git(root, "rev-parse", f"{BASE_ROOT}:cosmos-framework")
        if state["formal"]["gitlink"] != FORMAL_CHILD:
            raise ValueError("formal Root Gitlink mismatch")
        if state["baseline"]["gitlink"] != BASE_CHILD:
            raise ValueError("baseline Root Gitlink mismatch")
        state["working_tree_observation_before"] = {"root": git(root, "status", "--porcelain"), "child": git(child, "status", "--porcelain")}

        old, new = tree(child, BASE_CHILD, TRAINER), tree(child, FORMAL_CHILD, TRAINER)
        state["trainer_source"] = byte_records(child, BASE_CHILD, FORMAL_CHILD, (TRAINER,))
        exact_functions = ("FrontierState", "MatchedNoTTTWindow", "_binding", "restore_no_ttt_frontier", "MatchedNoTTTTrainer.training_step", "MatchedNoTTTTrainer.train", "NoTTTFrontierCallback.load_state_dict")
        checks = [equality_record(name, named(old, name), named(new, name)) for name in exact_functions]

        # The new hook is exactly one additional RNG-neutral statement. Compare
        # the full original callback after deleting only this precise addition.
        a, b = copy.deepcopy(named(old, "NoTTTFrontierCallback.state_dict")), copy.deepcopy(named(new, "NoTTTFrontierCallback.state_dict"))
        checks.append(equality_record("frontier_callback_return_schema", next(part for part in a.body if isinstance(part, ast.Return)), next(part for part in b.body if isinstance(part, ast.Return))))
        expected_hook = ast.parse('if loader is not None and hasattr(loader, "checkpoint_boundary"):\n    loader.checkpoint_boundary()').body[0]
        matches = [index for index, part in enumerate(b.body) if ast_bytes(part) == ast_bytes(expected_hook)]
        if len(matches) != 1:
            raise ValueError("callback normalization did not find the exact permitted hook")
        removed_hook = b.body.pop(matches[0])
        state["callback_normalization"] = {"removed_statement": ast.unparse(removed_hook), "removed_count": 1}
        checks.append(equality_record("frontier_callback_all_old_guards_and_validation", a, b))

        # workers=0 takes neither old nor new positive-worker branch. Delete
        # exactly that one branch from each function, retaining every guard,
        # default, assignment, callback registration and function argument.
        a, b = copy.deepcopy(named(old, "MatchedNoTTTTrainer.bind_grouped_stream")), copy.deepcopy(named(new, "MatchedNoTTTTrainer.bind_grouped_stream"))
        selector = ast.parse("loader_profile is not None and loader_profile.workers", mode="eval").body
        removed = []
        for value in (a, b):
            indices = [index for index, part in enumerate(value.body) if isinstance(part, ast.If) and ast_bytes(part.test) == ast_bytes(selector)]
            if len(indices) != 1:
                raise ValueError("bind normalization did not find one positive-worker branch")
            removed.append(ast.unparse(value.body.pop(indices[0])))
        state["worker_zero_normalization"] = {"removed_baseline_positive_branch": removed[0], "removed_formal_positive_branch": removed[1], "removed_count_each": 1}
        checks.append(equality_record("worker_zero_bind_all_other_code", a, b))

        old_profile, new_profile = tree(child, BASE_CHILD, PROFILE), tree(child, FORMAL_CHILD, PROFILE)
        for name in ("LoaderProfile.__post_init__", "LoaderProfile.identity", "profile_from_args"):
            checks.append(equality_record(name, named(old_profile, name), named(new_profile, name)))
        state["exact_and_normalized_ast_checks"] = checks
        state["protected_child_bytes"] = byte_records(child, BASE_CHILD, FORMAL_CHILD, CHILD_PROTECTED_FILES)
        state["protected_root_bytes"] = byte_records(root, BASE_ROOT, FORMAL_ROOT, ROOT_PROTECTED_FILES)
        state["protected_subtrees"] = [
            {"repository": kind, "path": path, "baseline_tree": git(repo, "rev-parse", f"{baseline}:{path}"), "formal_tree": git(repo, "rev-parse", f"{formal}:{path}"), "equal": git(repo, "rev-parse", f"{baseline}:{path}") == git(repo, "rev-parse", f"{formal}:{path}")}
            for kind, repo, baseline, formal, paths in (
                ("root", root, BASE_ROOT, FORMAL_ROOT, ("scripts", "configs", "third_party")),
                ("child", child, BASE_CHILD, FORMAL_CHILD, ("cosmos_framework/model", "cosmos_framework/checkpoint", "cosmos_framework/callbacks", "cosmos_framework/configs")),
            ) for path in paths
        ]

        old_tests, new_tests = tree(child, BASE_CHILD, RESUME_TEST), tree(child, FORMAL_CHILD, RESUME_TEST)
        baseline_tests, formal_tests = top_level_tests(old_tests), top_level_tests(new_tests)
        if baseline_tests.keys() != formal_tests.keys():
            raise ValueError("old Resume test functions were added/removed/renamed")
        test_checks = []
        for name in baseline_tests:
            record = equality_record(name, baseline_tests[name], formal_tests[name])
            record.update(baseline_assertion_ast_sha256=assertions(baseline_tests[name]), formal_assertion_ast_sha256=assertions(formal_tests[name]))
            test_checks.append(record)
        state["old_resume_test_functions"] = test_checks
        state["old_resume_test_file"] = byte_records(child, BASE_CHILD, FORMAL_CHILD, (RESUME_TEST,))[0]
        state["old_resume_test_file"]["byte_difference_expected"] = "exact fixture backend injection plus formatter-only whitespace; normalized whole-module AST checked below"
        fixture = named(new_tests, "cpu_boundaries")
        expected_injection = ast.parse('monkeypatch.setattr(trainer_module, "NoTTTAsyncLoader", lambda producer, profile, planner: loader_module.NoTTTCpuLoader(producer, profile))').body[0]
        indices = [index for index, part in enumerate(fixture.body) if ast_bytes(part) == ast_bytes(expected_injection)]
        if len(indices) != 1:
            raise ValueError("Resume fixture normalization did not find the exact RAW-backend injection")
        injection = fixture.body.pop(indices[0])
        state["old_resume_fixture_normalization"] = {"removed_statement": ast.unparse(injection), "removed_count": 1}
        state["old_resume_normalized_whole_module"] = equality_record("old_resume_module_excluding_exact_fixture_injection", old_tests, new_tests)

        state["corrected_old_fixture_modules"] = [
            fixture_module_audit(child, BASE_CHILD, FORMAL_CHILD, EXAMPLE_TEST, normalize_example_fixture),
            fixture_module_audit(root, BASE_ROOT, FORMAL_ROOT, WORKER_ENTRY_TEST, normalize_worker_job_fixture),
        ]

        # f6a92d4's only change after the last production commit is the exact
        # Example-test fixture above. Compare every OTHER Git object, and also
        # give direct byte/SHA256 witnesses for all new/modified production files.
        state["production_release_bytes"] = byte_records(child, LAST_PRODUCTION_CHILD, FORMAL_CHILD, ASYNC_PRODUCTION_FILES)
        def object_map(revision):
            rows = git(child, "ls-tree", "-r", "-z", revision, binary=True).split(b"\0")
            result = {}
            for row in rows:
                if row:
                    header, path = row.split(b"\t", 1)
                    result[path.decode()] = header.decode()
            return result

        previous_objects, release_objects = object_map(LAST_PRODUCTION_CHILD), object_map(FORMAL_CHILD)
        expected_changed_file = EXAMPLE_TEST
        removed_previous = previous_objects.pop(expected_changed_file)
        removed_release = release_objects.pop(expected_changed_file)
        release_nonfixture_equal = previous_objects == release_objects
        state["release_only_fixture_delta"] = {
            "baseline": LAST_PRODUCTION_CHILD,
            "formal": FORMAL_CHILD,
            "formal_parent": git(child, "rev-parse", f"{FORMAL_CHILD}^"),
            "excluded_exact_fixture_file": expected_changed_file,
            "excluded_baseline_object": removed_previous,
            "excluded_formal_object": removed_release,
            "other_git_object_count": len(previous_objects),
            "baseline_other_objects_sha256": sha256(json.dumps(previous_objects, sort_keys=True).encode()),
            "formal_other_objects_sha256": sha256(json.dumps(release_objects, sort_keys=True).encode()),
            "equal": release_nonfixture_equal,
        }
        if git(child, "rev-parse", f"{FORMAL_CHILD}^") != LAST_PRODUCTION_CHILD:
            raise ValueError("fixture release parent differs from frozen production commit")
        if git(child, "diff", "--name-only", LAST_PRODUCTION_CHILD, FORMAL_CHILD).splitlines() != [expected_changed_file]:
            raise ValueError("release includes changes beyond the exact Example fixture")

        # Keep scientific-asset exclusion separate from assertion preservation:
        # the original optional real-data test remains byte-identical in Git.
        gate_source = content(root, FORMAL_ROOT, "tools/v3/run_no_ttt_async_cpu_gate.py")
        optional = "cosmos-framework/cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py::test_optional_real_data_debug_smoke"
        gate_ast = ast.parse(gate_source.decode())
        selections = []
        for item in ast.walk(gate_ast):
            if isinstance(item, ast.JoinedStr):
                parts = []
                for part in item.values:
                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                        parts.append(part.value)
                    elif isinstance(part, ast.FormattedValue) and isinstance(part.value, ast.Name) and part.value.id == "CHILD":
                        parts.append("cosmos-framework")
                    else:
                        break
                else:
                    text = "".join(parts)
                    if text.startswith("--deselect="):
                        selections.append(text)
        if selections != [f"--deselect={optional}"]:
            raise ValueError("unexpected scientific-asset deselection in final CPU runner")
        state["optional_real_data_selection"] = {
            "gate_blob": git(root, "rev-parse", f"{FORMAL_ROOT}:tools/v3/run_no_ttt_async_cpu_gate.py"),
            "gate_sha256": sha256(gate_source),
            "explicit_deselected_node": optional,
            "deselection_count": 1,
            "reason": "current task forbids real scientific assets; this optional pre-existing test is retained unchanged, not counted as an executed PASS",
            "original_source_file_byte_equal": next(record["equal"] for record in state["protected_child_bytes"] if record["path"] == "cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py"),
        }

        all_checks = [*checks, *state["protected_child_bytes"], *state["protected_root_bytes"], *state["protected_subtrees"], *test_checks, state["old_resume_normalized_whole_module"], *(record["normalized_whole_module"] for record in state["corrected_old_fixture_modules"]), *state["production_release_bytes"], state["release_only_fixture_delta"]]
        if not all(record["equal"] for record in all_checks):
            raise ValueError("one or more protected equality checks failed")
        state["working_tree_observation_after"] = {"root": git(root, "status", "--porcelain"), "child": git(child, "status", "--porcelain")}
        state["working_tree_status_unchanged"] = state["working_tree_observation_after"] == state["working_tree_observation_before"]
        if not state["working_tree_status_unchanged"]:
            raise ValueError("working-tree status changed during read-only audit")
        fixture_records = state["corrected_old_fixture_modules"]
        state["summary"] = {
            "equality_checks": len(all_checks),
            "protected_child_files": len(CHILD_PROTECTED_FILES),
            "protected_root_files": len(ROOT_PROTECTED_FILES),
            "unchanged_old_resume_test_functions": len(test_checks),
            "unchanged_old_resume_assert_statements": sum(len(record["baseline_assertion_ast_sha256"]) for record in test_checks),
            "fixture_corrected_old_modules": len(fixture_records),
            "fixture_corrected_modules_old_test_functions": sum(len(record["test_functions"]) for record in fixture_records),
            "fixture_corrected_modules_unchanged_old_assert_statements": sum(record["assertion_count_entire_module"] for record in fixture_records),
            "production_files_byte_identical_d64_to_release": len(ASYNC_PRODUCTION_FILES),
            "all_other_child_git_objects_identical_d64_to_release": len(previous_objects),
        }
        state["status"] = "PASS_STATIC_SCOPE"
    except Exception as error:
        state["error"] = {"type": type(error).__name__, "message": str(error)}
    args.output.write_text(json.dumps(state, indent=2) + "\n")
    print(json.dumps({"status": state["status"], "output": str(args.output.resolve()), "summary": state.get("summary"), "error": state.get("error")}, indent=2))
    return 0 if state["status"] == "PASS_STATIC_SCOPE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
