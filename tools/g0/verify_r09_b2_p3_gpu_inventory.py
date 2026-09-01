#!/usr/bin/env python3
"""Fail-closed verifier for the approved GPU-only P3 inventory schema."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


ALLOWED_RECURRENT_ONLY_PREFIXES = ("local_history_runtime.recurrent_backend.",)
TTT_RUNTIME_NAMES = {"W", "pending_evidence", "last_evidence", "initialized", "segment_progress"}
NO_EXECUTION_FIELDS = (
    "weights_loaded", "checkpoint_loaded", "forward_executed", "backward_executed",
    "optimizer_step_executed", "scheduler_step_executed", "checkpoint_saved",
)
REQUIRED_PROCESSOR_ASSETS = {
    "tokenizer.json",
    "tokenizer_config.json",
    "chat_template.jinja",
    "special_tokens_map.json",
    "preprocessor_config.json",
    "video_preprocessor_config.json",
}
PASS_PROVENANCE_KEYS = {
    "root_revision",
    "submodule_revision",
    "gitlink_revision",
    "recipe_sha256",
    "production_recipe_source_sha256",
    "edge_model_config_source_sha256",
    "inherited_recipe_source_sha256",
    "collector_sha256",
    "verifier_sha256",
    "model_source_sha256",
    "optimizer_source_sha256",
    "dcp_source_sha256",
    "command_argv",
    "cwd",
    "environment",
    "gpu_uuid",
    "d005_record",
    "approved_run_token",
}
FROZEN_SOURCE_PATHS = {
    "recipe_sha256": "cosmos-framework/examples/toml/sft_config/action_policy_libero_edge_all.toml",
    "production_recipe_source_sha256": "cosmos-framework/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py",
    "edge_model_config_source_sha256": "cosmos-framework/cosmos_framework/configs/base/experiment/sft/models/edge_model_config.py",
    "inherited_recipe_source_sha256": "cosmos-framework/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_all_nano.py",
    "collector_sha256": "tools/g0/collect_r09_b2_p3_gpu_inventory.py",
    "verifier_sha256": "tools/g0/verify_r09_b2_p3_gpu_inventory.py",
    "model_source_sha256": "cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py",
    "optimizer_source_sha256": "cosmos-framework/cosmos_framework/utils/generator/optimizer.py",
    "dcp_source_sha256": "cosmos-framework/cosmos_framework/checkpoint/dcp.py",
}
RUN_TOKEN = "APPROVE_TO_RUN_GPU_ONLY_P3_GATE"
APPROVED_MAX_PEAK_GIB = 28
INVENTORY_MODEL_OVERRIDES = {"load_vision_tokenizer": {"before": True, "after": False}}
MODEL_DCP_SYMBOL = "cosmos_framework.checkpoint.dcp.ModelWrapper.state_dict"
OPTIMIZER_DCP_SYMBOL = "cosmos_framework.utils.generator.optimizer.OptimizersContainer.state_dict"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL
    ).strip()


def _git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)


def _tracked_clean(root: Path, revision: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", revision, "--"],
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _contained(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def provenance_checks(artifact: dict[str, object], root: Path | None) -> dict[str, bool]:
    """仅对 PASS 独立绑定本地 checkout、冻结源文件和 D005 record。"""
    keys = ("root_gitlink_valid", "root_tracked_clean", "submodule_head_valid", "submodule_tracked_clean", "source_hashes_valid", "d005_identity_valid", "command_binding_valid", "gpu_binding_valid", "run_token_valid")
    if artifact.get("status") != "PASS":
        return {key: True for key in keys}
    if root is None:
        return {key: False for key in keys}
    provenance = artifact.get("provenance", {})
    try:
        root = root.resolve()
        root_revision = provenance["root_revision"]
        submodule_root = root / "cosmos-framework"
        gitlink = _git(root, "ls-tree", root_revision, "cosmos-framework").split()[2]
        root_gitlink_valid = (
            root_revision == _git(root, "rev-parse", "HEAD")
            and gitlink == provenance.get("gitlink_revision")
        )
        root_tracked_clean = _tracked_clean(root, root_revision)
        submodule_head_valid = _git(submodule_root, "rev-parse", "HEAD") == gitlink == provenance.get("submodule_revision")
        submodule_tracked_clean = _tracked_clean(submodule_root, gitlink)
        source_hashes_valid = True
        for field, relative in FROZEN_SOURCE_PATHS.items():
            source_root = root if relative.startswith("tools/") else submodule_root
            source_revision = root_revision if source_root == root else gitlink
            source_relative = relative if source_root == root else relative.removeprefix("cosmos-framework/")
            blob = _git_bytes(source_root, "show", f"{source_revision}:{source_relative}")
            source_hashes_valid = source_hashes_valid and provenance.get(field) == _sha256_bytes(blob) and (source_root / source_relative).read_bytes() == blob
        d005_ref = provenance.get("d005_record", {})
        d005_relative = Path(d005_ref["path"])
        if d005_relative.is_absolute() or ".." in d005_relative.parts:
            raise ValueError("D005 path must be relative to the verified root")
        d005_path = root / d005_relative
        if not _contained(root, d005_path):
            raise ValueError("D005 path escapes the verified root")
        d005 = json.loads(d005_path.read_text())
        d005_identity_valid = (
            d005_ref.get("sha256") == _sha256(d005_path)
            and all(d005.get(key) == provenance.get(key) for key in ("root_revision", "submodule_revision", "gitlink_revision"))
        )
        command_binding_valid = (
            d005.get("command_argv") == provenance.get("command_argv")
            and d005.get("cwd") == provenance.get("cwd")
            and d005.get("environment") == provenance.get("environment")
        )
        gpu_binding_valid = (
            d005.get("gpu_uuid") == provenance.get("gpu_uuid")
            and d005.get("world_size") == artifact.get("execution", {}).get("world_size") == 1
            and d005.get("max_peak_gib") == APPROVED_MAX_PEAK_GIB
        )
        run_token_valid = provenance.get("approved_run_token") == RUN_TOKEN and d005.get("approved_run_token") == RUN_TOKEN
    except (IndexError, KeyError, OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError):
        return {key: False for key in keys}
    return {
        "root_gitlink_valid": root_gitlink_valid,
        "root_tracked_clean": root_tracked_clean,
        "submodule_head_valid": submodule_head_valid,
        "submodule_tracked_clean": submodule_tracked_clean,
        "source_hashes_valid": source_hashes_valid,
        "d005_identity_valid": d005_identity_valid,
        "command_binding_valid": command_binding_valid,
        "gpu_binding_valid": gpu_binding_valid,
        "run_token_valid": run_token_valid,
    }


def _selected(inventory: dict[str, object], field: str) -> set[str]:
    return {row["name"] for row in inventory.get("model_parameters", []) if row.get(field)}


def _forbidden(keys: list[str]) -> bool:
    return not any(key.split(".")[-1] in TTT_RUNTIME_NAMES for key in keys)


def backend_checks(record: dict[str, object]) -> dict[str, bool]:
    inventory = record.get("inventory", {})
    rows = inventory.get("model_parameters", [])
    names = [row.get("name") for row in rows]
    groups = inventory.get("optimizer_param_groups", [])
    entries = [entry for group in groups for entry in group.get("parameters", [])]
    grouped = [entry.get("name") for entry in entries]
    selected = _selected(inventory, "selected_by_optimizer")
    selector = _selected(inventory, "selected_by_resolved_selector")
    state = inventory.get("optimizer_state", {})
    eligible = set(state.get("eligible_parameter_names", []))
    state_entries = state.get("entries", [])
    dcp = inventory.get("dcp_state", {})
    persistent_keys = dcp.get("persistent_keys", [])
    binding = dcp.get("production_binding", {})
    selected_model_keys = dcp.get("selected_model_parameter_keys", {})
    optimizer_references = set(dcp.get("optimizer_parameter_references", []))
    optimizer_schema = dcp.get("optimizer_state_schema", [])
    rows_by_name = {row.get("name"): row for row in rows}
    schema_owners = {row.get("owner") for row in optimizer_schema}
    schema_identities = {
        (row.get("owner"), row.get("owner_fqn"), row.get("namespace"), row.get("suffix"))
        for row in optimizer_schema
    }
    return {
        "inventory_override_exact": record.get("inventory_model_overrides") == INVENTORY_MODEL_OVERRIDES,
        "selector_exclusions_empty": not inventory.get("selector_optimizer_exclusions", []),
        "selector_equals_optimizer": selector == selected,
        "model_names_unique": len(names) == len(set(names)),
        "optimizer_reverse_map": all(name in set(names) for name in grouped),
        "optimizer_no_duplicates": len(grouped) == len(set(grouped)),
        "optimizer_equals_selected": selected == set(grouped),
        "state_eligibility": eligible == selected,
        "unmaterialized_state_empty": not state.get("not_materialized") or not state_entries,
        "materialized_state_reverse_map": state.get("not_materialized") or all(entry.get("parameter_name") in eligible and isinstance(entry.get("state_keys"), list) for entry in state_entries),
        "dcp_inspected": dcp.get("inspected") is True,
        "dcp_production_binding": (
            binding.get("model_symbol") == MODEL_DCP_SYMBOL
            and binding.get("optimizer_symbol") == OPTIMIZER_DCP_SYMBOL
            and binding.get("model_invoked") is True
            and binding.get("optimizer_invoked") is True
        ),
        "dcp_selected_model_membership": (
            set(selected_model_keys) == selected
            and all(key in dcp.get("model_state_keys", []) for key in selected_model_keys.values())
        ),
        "dcp_optimizer_membership": optimizer_references == selected,
        "dcp_optimizer_schema_valid": (
            schema_owners == optimizer_references
            and len(schema_identities) == len(optimizer_schema)
            and all(
                row.get("owner") in set(names)
                and isinstance(row.get("owner_fqn"), str)
                and row.get("owner_fqn", "").startswith("net.")
                and row.get("namespace") in {"state", "param_groups"}
                and isinstance(row.get("suffix"), str)
                and bool(row.get("suffix"))
                and row.get("flat_key") == f"{row.get('namespace')}.{row.get('owner_fqn')}.{row.get('suffix')}"
                for row in optimizer_schema
            )
        ),
        "group_metadata_matches_model": all(
            entry.get("name") in rows_by_name
            and entry.get("numel") == rows_by_name[entry.get("name")].get("numel")
            and entry.get("dtype") == rows_by_name[entry.get("name")].get("dtype")
            for entry in entries
        ),
        "ttt_excluded_everywhere": _forbidden(names + [row.get("name", "") for row in inventory.get("named_buffers", [])] + grouped + persistent_keys),
    }


def diff_checks(artifact: dict[str, object]) -> dict[str, bool]:
    declared = artifact.get("matched_diff", {})
    recurrent = artifact["recurrent"].get("inventory", {})
    ttt = artifact["ttt_fast_weight"].get("inventory", {})
    checks = {"policy_declared_exact": tuple(declared.get("allowed_backend_specific_prefixes", [])) == ALLOWED_RECURRENT_ONLY_PREFIXES}
    for field, label in (("selected_by_resolved_selector", "resolved_selector"), ("selected_by_optimizer", "optimizer")):
        recurrent_only = sorted(_selected(recurrent, field) - _selected(ttt, field))
        ttt_only = sorted(_selected(ttt, field) - _selected(recurrent, field))
        checks[f"declared_{label}"] = declared.get(f"recurrent_only_{label}") == recurrent_only and declared.get(f"ttt_only_{label}") == ttt_only
        checks[f"only_allowed_{label}"] = not ttt_only and all(name.startswith(ALLOWED_RECURRENT_ONLY_PREFIXES) for name in recurrent_only)
    for collection, label in (("model_parameters", "model_parameters"), ("named_buffers", "buffers")):
        recurrent_rows = {row["name"]: row for row in recurrent.get(collection, [])}
        ttt_rows = {row["name"]: row for row in ttt.get(collection, [])}
        recurrent_only = set(recurrent_rows) - set(ttt_rows)
        ttt_only = set(ttt_rows) - set(recurrent_rows)
        shared = set(recurrent_rows) & set(ttt_rows)
        checks[f"only_allowed_{label}"] = (
            not ttt_only
            and all(name.startswith(ALLOWED_RECURRENT_ONLY_PREFIXES) for name in recurrent_only)
        )
        checks[f"shared_{label}_metadata"] = all(
            recurrent_rows[name].get("numel") == ttt_rows[name].get("numel")
            and recurrent_rows[name].get("dtype") == ttt_rows[name].get("dtype")
            and recurrent_rows[name].get("shape") == ttt_rows[name].get("shape")
            for name in shared
        )

    def normalized_model_dcp_keys(inventory: dict[str, object]) -> set[str]:
        return {
            key.removeprefix("net.")
            for key in inventory.get("dcp_state", {}).get("model_state_keys", [])
        }

    recurrent_dcp = normalized_model_dcp_keys(recurrent)
    ttt_dcp = normalized_model_dcp_keys(ttt)
    checks["only_allowed_dcp_model_keys"] = (
        not (ttt_dcp - recurrent_dcp)
        and all(key.startswith(ALLOWED_RECURRENT_ONLY_PREFIXES) for key in recurrent_dcp - ttt_dcp)
    )

    def optimizer_schema(inventory: dict[str, object]) -> dict[tuple[str, str, str, str], dict[str, object]]:
        rows = inventory.get("dcp_state", {}).get("optimizer_state_schema", [])
        schema = {}
        for row in rows:
            identity = (row.get("owner"), row.get("owner_fqn"), row.get("namespace"), row.get("suffix"))
            schema[identity] = row
        return schema

    recurrent_schema = optimizer_schema(recurrent)
    ttt_schema = optimizer_schema(ttt)
    recurrent_only = set(recurrent_schema) - set(ttt_schema)
    ttt_only = set(ttt_schema) - set(recurrent_schema)
    shared = set(recurrent_schema) & set(ttt_schema)
    checks["only_allowed_dcp_optimizer_schema"] = (
        not ttt_only
        and all(
            isinstance(identity[0], str) and identity[0].startswith(ALLOWED_RECURRENT_ONLY_PREFIXES)
            for identity in recurrent_only
        )
    )
    checks["shared_dcp_optimizer_schema_metadata"] = all(
        all(
            recurrent_schema[identity].get(field) == ttt_schema[identity].get(field)
            for field in ("kind", "shape", "dtype", "numel", "value", "items")
        )
        for identity in shared
    )
    return checks


def verify(artifact: dict[str, object], root: Path | None = None) -> dict[str, object]:
    execution = artifact.get("execution", {})
    processor = artifact.get("local_processor", {})
    assets = processor.get("required_assets", {})
    offline = processor.get("offline_environment", {})
    binding = processor.get("resolved_tokenizer_binding", {})
    binding_sha256 = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    provenance = artifact.get("provenance", {})
    backends = {name: artifact.get(name, {}) for name in ("recurrent", "ttt_fast_weight")}
    pass_claimed = artifact.get("status") == "PASS"
    backend_execution_valid = True
    backend_processor_valid = True
    if pass_claimed:
        common_environment = provenance.get("environment", {})
        for name, record in backends.items():
            observed = record.get("execution", {}).get("observed_environment", {})
            backend_execution_valid = backend_execution_valid and (
                record.get("execution", {}).get("distributed_initialized") is False
                and record.get("execution", {}).get("peak_allocated_bytes", 1 << 60) <= APPROVED_MAX_PEAK_GIB * 1024**3
                and record.get("execution", {}).get("peak_reserved_bytes", 1 << 60) <= APPROVED_MAX_PEAK_GIB * 1024**3
                and observed.get("PSM_R08_LOCAL_HISTORY_ENABLED") == "1"
                and observed.get("PSM_LOCAL_DUMMY_ENABLED") == "0"
                and observed.get("PSM_R09_A1_ENABLED") == "0"
                and observed.get("PSM_R09_B1_TTT_ENABLED") == ("1" if name == "ttt_fast_weight" else "0")
                and all(observed.get(key) == common_environment.get(key) for key in common_environment)
            )
            backend_processor_valid = backend_processor_valid and record.get("local_processor") == processor
    checks = {
        "schema": artifact.get("schema_version") == "r09_b2_p3_gpu_inventory_v1",
        "single_process": execution.get("world_size") == 1 and execution.get("distributed_initialized") is False,
        "no_execution": all(execution.get(key) is False for key in NO_EXECUTION_FIELDS),
        "peak_under_limit": (
            execution.get("peak_allocated_bytes", 1 << 60) <= APPROVED_MAX_PEAK_GIB * 1024**3
            and execution.get("peak_reserved_bytes", 1 << 60) <= APPROVED_MAX_PEAK_GIB * 1024**3
        ),
        "backend_status": (all(record.get("status") == "PASS" for record in backends.values()) if pass_claimed else True),
        "backend_execution_binding": backend_execution_valid,
        "backend_processor_binding": backend_processor_valid,
        "local_processor_path": processor.get("is_local_directory") is True and bool(processor.get("canonical_path")),
        "offline_environment": offline.get("HF_HUB_OFFLINE") == "1" and offline.get("TRANSFORMERS_OFFLINE") == "1" and offline.get("HUGGINGFACE_HUB_CACHE") == processor.get("canonical_path"),
        "local_processor_assets": set(assets) == REQUIRED_PROCESSOR_ASSETS and all(asset.get("exists") is True and asset.get("sha256") for asset in assets.values()),
        "observed_offline_environment": (
            processor.get("observed_offline_environment") == offline
            if pass_claimed
            else True
        ),
        "processor_package_read_only": (
            processor.get("phase_trace") == ["offline_env_applied", "binding_validated", "processor_constructed", "post_snapshot_taken"]
            and processor.get("construction_witness", {}).get("constructor_identity") == "cosmos_framework.model.generator.omni_mot_model.build_vlm_processor"
            and processor.get("construction_witness", {}).get("binding_sha256") == binding_sha256
            and bool(processor.get("construction_witness", {}).get("processor_type"))
            and processor.get("before_assets") == processor.get("after_assets") == processor.get("worker_final_assets") == assets
            if pass_claimed
            else True
        ),
        "resolved_local_tokenizer_binding": (
            binding.get("repository") is None
            and binding.get("revision") is None
            and binding.get("tokenizer_type") == processor.get("canonical_path")
            if pass_claimed
            else True
        ),
        "pass_provenance_fields": all(provenance.get(key) for key in PASS_PROVENANCE_KEYS) if pass_claimed else True,
    }
    provenance = provenance_checks(artifact, root)
    checks.update(provenance)
    backend = {name: backend_checks(record) for name, record in backends.items()} if pass_claimed else {}
    diff = diff_checks(artifact) if pass_claimed and all(name in artifact for name in backends) else {}
    pass_ready = all(checks.values()) and all(all(item.values()) for item in backend.values()) and all(diff.values())
    blocked_checks = {
        key: value
        for key, value in checks.items()
        if key not in {"local_processor_path", "local_processor_assets"}
    }
    status = "PASS" if pass_claimed and pass_ready else "BLOCKED" if artifact.get("status") == "BLOCKED" and all(blocked_checks.values()) else "FAIL"
    return {"status": status, "record_valid": pass_ready if pass_claimed else all(blocked_checks.values()), "checks": checks, "backend_checks": backend, "matched_diff_checks": diff}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    result = verify(json.loads(args.artifact.read_text()), args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["status"] == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
