#!/usr/bin/env python3
"""P3 provenance verifier 的冻结 Python recipe source 回归测试。"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
VERIFY_PATH = ROOT / "tools/g0/verify_r09_b2_p3_gpu_inventory.py"
SPEC = importlib.util.spec_from_file_location("verify_r09_b2_p3_gpu_inventory", VERIFY_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)
COLLECT_SPEC = importlib.util.spec_from_file_location(
    "collect_r09_b2_p3_gpu_inventory", ROOT / "tools/g0/collect_r09_b2_p3_gpu_inventory.py"
)
assert COLLECT_SPEC is not None and COLLECT_SPEC.loader is not None
COLLECT = importlib.util.module_from_spec(COLLECT_SPEC)
COLLECT_SPEC.loader.exec_module(COLLECT)


def _git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FrozenPythonRecipeSourceRegressionTest(unittest.TestCase):
    """Python recipe/config 当前字节偏离审核 commit blob 时必须 fail-closed。"""

    def _passing_artifact(self, d005_path: Path) -> dict[str, object]:
        root_revision = _git("rev-parse", "HEAD")
        submodule_root = ROOT / "cosmos-framework"
        gitlink_revision = _git("ls-tree", root_revision, "cosmos-framework").split()[2]
        submodule_revision = _git("rev-parse", "HEAD", cwd=submodule_root)
        command_argv = ["fixture", "--no-gpu"]
        environment = {"FIXTURE": "1"}
        provenance: dict[str, object] = {
            "root_revision": root_revision,
            "submodule_revision": submodule_revision,
            "gitlink_revision": gitlink_revision,
            "command_argv": command_argv,
            "cwd": str(ROOT),
            "environment": environment,
            "gpu_uuid": "fixture-gpu-uuid",
            "approved_run_token": VERIFY.RUN_TOKEN,
        }
        for field, relative in VERIFY.FROZEN_SOURCE_PATHS.items():
            provenance[field] = _sha256(ROOT / relative)

        d005 = {
            "root_revision": root_revision,
            "submodule_revision": submodule_revision,
            "gitlink_revision": gitlink_revision,
            "command_argv": command_argv,
            "cwd": str(ROOT),
            "environment": environment,
            "gpu_uuid": "fixture-gpu-uuid",
            "world_size": 1,
            "max_peak_gib": 24,
            "approved_run_token": VERIFY.RUN_TOKEN,
        }
        d005_path.parent.mkdir(parents=True, exist_ok=True)
        d005_path.write_text(json.dumps(d005, sort_keys=True) + "\n")
        provenance["d005_record"] = {
            "path": str(d005_path.relative_to(ROOT)),
            "sha256": _sha256(d005_path),
        }
        assets = {
            name: {"exists": True, "sha256": "fixture", "size_bytes": 1}
            for name in VERIFY.REQUIRED_PROCESSOR_ASSETS
        }
        processor = {
            "canonical_path": str(ROOT),
            "is_local_directory": True,
            "required_assets": assets,
            "offline_environment": {
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "HUGGINGFACE_HUB_CACHE": str(ROOT),
            },
            "observed_offline_environment": {
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "HUGGINGFACE_HUB_CACHE": str(ROOT),
            },
            "before_assets": assets,
            "after_assets": assets,
            "resolved_tokenizer_binding": {
                "repository": None,
                "revision": None,
                "tokenizer_type": str(ROOT),
            },
        }
        recurrent_name = "local_history_runtime.recurrent_backend.fixture"
        recurrent = {
            "status": "PASS",
            "inventory": {
                "model_parameters": [{"name": recurrent_name, "selected_by_optimizer": True, "selected_by_resolved_selector": True}],
                "named_buffers": [],
                "optimizer_param_groups": [{"parameters": [{"name": recurrent_name}]}],
                "optimizer_state": {"eligible_parameter_names": [recurrent_name], "not_materialized": True, "entries": []},
                "dcp_state": {"inspected": True, "persistent_keys": [], "production_binding": {"symbol": "ModelWrapper.state_dict/OptimizersContainer.state_dict"}},
                "selector_optimizer_exclusions": [],
            },
        }
        ttt = {
            "status": "PASS",
            "inventory": {
                "model_parameters": [], "named_buffers": [], "optimizer_param_groups": [],
                "optimizer_state": {"eligible_parameter_names": [], "not_materialized": True, "entries": []},
                "dcp_state": {"inspected": True, "persistent_keys": [], "production_binding": {"symbol": "ModelWrapper.state_dict/OptimizersContainer.state_dict"}},
                "selector_optimizer_exclusions": [],
            },
        }
        return {
            "schema_version": "r09_b2_p3_gpu_inventory_v1",
            "status": "PASS",
            "execution": {"world_size": 1, "distributed_initialized": False, "weights_loaded": False, "checkpoint_loaded": False, "forward_executed": False, "backward_executed": False, "optimizer_step_executed": False, "scheduler_step_executed": False, "checkpoint_saved": False, "peak_allocated_bytes": 0, "peak_reserved_bytes": 0},
            "local_processor": processor,
            "provenance": provenance,
            "recurrent": recurrent,
            "ttt_fast_weight": ttt,
            "matched_diff": {
                "allowed_backend_specific_prefixes": list(VERIFY.ALLOWED_RECURRENT_ONLY_PREFIXES),
                "recurrent_only_resolved_selector": [recurrent_name],
                "ttt_only_resolved_selector": [],
                "recurrent_only_optimizer": [recurrent_name],
                "ttt_only_optimizer": [],
            },
        }

    def test_python_recipe_source_mutation_fails_closed(self) -> None:
        d005_path = ROOT / "artifacts/g0/r09/b2/p3_source_hash_regression_test_d005.json"
        source = ROOT / VERIFY.FROZEN_SOURCE_PATHS["production_recipe_source_sha256"]
        original = source.read_bytes()
        try:
            artifact = self._passing_artifact(d005_path)
            # 本测试工作树自身含未提交测试文件；隔离 cleanliness，专测冻结源身份。
            frozen_recipe_only = {
                "production_recipe_source_sha256": VERIFY.FROZEN_SOURCE_PATHS[
                    "production_recipe_source_sha256"
                ]
            }
            with mock.patch.object(VERIFY, "_tracked_clean", return_value=True), mock.patch.object(
                VERIFY, "FROZEN_SOURCE_PATHS", frozen_recipe_only
            ):
                self.assertEqual(VERIFY.verify(artifact, ROOT)["status"], "PASS")
                source.write_bytes(original + b"\n# p3 source-hash regression fixture\n")
                result = VERIFY.verify(artifact, ROOT)
                self.assertFalse(result["checks"]["source_hashes_valid"])
                self.assertEqual(result["status"], "FAIL")
        finally:
            source.write_bytes(original)
            d005_path.unlink(missing_ok=True)

    def test_isolated_worker_rejects_remote_tokenizer_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in COLLECT.REQUIRED_PROCESSOR_ASSETS:
                (root / name).write_text("fixture\n")
            record = COLLECT.prepare_isolated_worker(
                root, {"repository": None, "revision": None, "tokenizer_type": str(root.resolve())}
            )
            self.assertEqual(record["observed_offline_environment"], record["offline_environment"])
            d005_path = ROOT / "artifacts/g0/r09/b2/p3_worker_embedding_test_d005.json"
            try:
                artifact = self._passing_artifact(d005_path)
                artifact["local_processor"] = record
                with mock.patch.object(VERIFY, "_tracked_clean", return_value=True), mock.patch.object(
                    VERIFY, "FROZEN_SOURCE_PATHS", {}
                ):
                    self.assertEqual(VERIFY.verify(artifact, ROOT)["status"], "PASS")
            finally:
                d005_path.unlink(missing_ok=True)
            with self.assertRaisesRegex(ValueError, "remote repository"):
                COLLECT.prepare_isolated_worker(
                    root, {"repository": "nvidia/Cosmos3-Edge", "revision": "main", "tokenizer_type": str(root.resolve())}
                )


if __name__ == "__main__":
    unittest.main()
