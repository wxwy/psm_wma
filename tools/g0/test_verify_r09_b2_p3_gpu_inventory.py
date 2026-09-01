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
        environment = {
            "CUDA_VISIBLE_DEVICES": "0",
            "EDGE_POLICY_CHECKPOINT": str(ROOT),
            "WAN_VAE_PATH": "/fixture/vae",
            "BASE_CHECKPOINT_PATH": "/fixture/base",
            "LIBERO_ROOT": "/fixture/libero",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HUGGINGFACE_HUB_CACHE": str(ROOT),
        }
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
            "worker_final_assets": assets,
            "phase_trace": ["offline_env_applied", "binding_validated", "processor_constructed", "post_snapshot_taken"],
            "construction_witness": {
                "constructor_identity": "cosmos_framework.model.generator.omni_mot_model.build_vlm_processor",
                "binding_sha256": hashlib.sha256(json.dumps({"repository": None, "revision": None, "tokenizer_type": str(ROOT)}, sort_keys=True).encode()).hexdigest(),
                "processor_type": "fixture.Processor",
            },
            "resolved_tokenizer_binding": {
                "repository": None,
                "revision": None,
                "tokenizer_type": str(ROOT),
            },
        }
        recurrent_name = "local_history_runtime.recurrent_backend.fixture"
        recurrent = {
            "status": "PASS",
            "local_processor": processor,
            "inventory_model_overrides": VERIFY.INVENTORY_MODEL_OVERRIDES,
            "execution": {
                "distributed_initialized": False,
                "peak_allocated_bytes": 0,
                "peak_reserved_bytes": 0,
                "observed_environment": environment | {
                    "PSM_R08_LOCAL_HISTORY_ENABLED": "1",
                    "PSM_LOCAL_DUMMY_ENABLED": "0",
                    "PSM_R09_A1_ENABLED": "0",
                    "PSM_R09_B1_TTT_ENABLED": "0",
                },
            },
            "inventory": {
                "model_parameters": [{"name": recurrent_name, "numel": 1, "dtype": "float32", "selected_by_optimizer": True, "selected_by_resolved_selector": True}],
                "named_buffers": [],
                "optimizer_param_groups": [{"parameters": [{"name": recurrent_name, "numel": 1, "dtype": "float32"}]}],
                "optimizer_state": {"eligible_parameter_names": [recurrent_name], "not_materialized": True, "entries": []},
                "dcp_state": {
                    "inspected": True,
                    "persistent_keys": [f"net.{recurrent_name}"],
                    "model_state_keys": [f"net.{recurrent_name}"],
                    "selected_model_parameter_keys": {recurrent_name: f"net.{recurrent_name}"},
                    "optimizer_parameter_references": [recurrent_name],
                    "optimizer_state_schema": [{
                        "flat_key": f"param_groups.net.{recurrent_name}.lr",
                        "owner": recurrent_name,
                        "namespace": "param_groups",
                        "suffix": "lr",
                        "kind": "float",
                        "value": 0.1,
                    }],
                    "production_binding": {
                        "model_symbol": VERIFY.MODEL_DCP_SYMBOL,
                        "optimizer_symbol": VERIFY.OPTIMIZER_DCP_SYMBOL,
                        "model_invoked": True,
                        "optimizer_invoked": True,
                    },
                },
                "selector_optimizer_exclusions": [],
            },
        }
        ttt = {
            "status": "PASS",
            "local_processor": processor,
            "inventory_model_overrides": VERIFY.INVENTORY_MODEL_OVERRIDES,
            "execution": {
                "distributed_initialized": False,
                "peak_allocated_bytes": 0,
                "peak_reserved_bytes": 0,
                "observed_environment": environment | {
                    "PSM_R08_LOCAL_HISTORY_ENABLED": "1",
                    "PSM_LOCAL_DUMMY_ENABLED": "0",
                    "PSM_R09_A1_ENABLED": "0",
                    "PSM_R09_B1_TTT_ENABLED": "1",
                },
            },
            "inventory": {
                "model_parameters": [], "named_buffers": [], "optimizer_param_groups": [],
                "optimizer_state": {"eligible_parameter_names": [], "not_materialized": True, "entries": []},
                "dcp_state": {
                    "inspected": True,
                    "persistent_keys": [],
                    "model_state_keys": [],
                    "selected_model_parameter_keys": {},
                    "optimizer_parameter_references": [],
                    "optimizer_state_schema": [],
                    "production_binding": {
                        "model_symbol": VERIFY.MODEL_DCP_SYMBOL,
                        "optimizer_symbol": VERIFY.OPTIMIZER_DCP_SYMBOL,
                        "model_invoked": True,
                        "optimizer_invoked": True,
                    },
                },
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
                root, {"tokenizer": {"repository": None, "revision": None, "tokenizer_type": str(root.resolve())}}
            )
            self.assertEqual(record["observed_offline_environment"], record["offline_environment"])
            d005_path = ROOT / "artifacts/g0/r09/b2/p3_worker_embedding_test_d005.json"
            try:
                artifact = self._passing_artifact(d005_path)
                artifact["local_processor"] = record
                with mock.patch.object(VERIFY, "_tracked_clean", return_value=True), mock.patch.object(
                    VERIFY, "FROZEN_SOURCE_PATHS", {}
                ):
                    self.assertEqual(VERIFY.verify(artifact, ROOT)["status"], "FAIL")
                    record["after_assets"] = record["required_assets"]
                    record["phase_trace"] = ["offline_env_applied", "binding_validated", "processor_constructed", "post_snapshot_taken"]
                    record["construction_witness"] = {"constructor_identity": "arbitrary_callable", "binding_sha256": hashlib.sha256(json.dumps(record["resolved_tokenizer_binding"], sort_keys=True).encode()).hexdigest(), "processor_type": "builtins.object"}
                    self.assertEqual(VERIFY.verify(artifact, ROOT)["status"], "FAIL")
            finally:
                d005_path.unlink(missing_ok=True)
            with self.assertRaisesRegex(ValueError, "remote repository"):
                COLLECT.prepare_isolated_worker(
                    root, {"tokenizer": {"repository": "nvidia/Cosmos3-Edge", "revision": "main", "tokenizer_type": str(root.resolve())}}
                )
            with self.assertRaisesRegex(ValueError, "differs from validated binding"):
                COLLECT.run_production_processor_construction(
                    record,
                    {"tokenizer": {"repository": None, "revision": None, "tokenizer_type": str(root / "different")}},
                )
            with self.assertRaisesRegex(ValueError, "differs from validated binding"):
                COLLECT.run_production_processor_construction(
                    record,
                    {"tokenizer": {"repository": "nvidia/Cosmos3-Edge", "revision": "main", "tokenizer_type": str(root.resolve())}},
                )

    def test_production_dcp_membership_is_not_symbolic_only(self) -> None:
        d005_path = ROOT / "artifacts/g0/r09/b2/p3_dcp_membership_test_d005.json"
        try:
            artifact = self._passing_artifact(d005_path)
            with mock.patch.object(VERIFY, "_tracked_clean", return_value=True), mock.patch.object(
                VERIFY, "FROZEN_SOURCE_PATHS", {}
            ):
                self.assertEqual(VERIFY.verify(artifact, ROOT)["status"], "PASS")
                artifact["recurrent"]["inventory"]["dcp_state"]["optimizer_parameter_references"] = []
                result = VERIFY.verify(artifact, ROOT)
                self.assertFalse(result["backend_checks"]["recurrent"]["dcp_optimizer_membership"])
                self.assertEqual(result["status"], "FAIL")
        finally:
            d005_path.unlink(missing_ok=True)

    def test_state_schema_helpers_preserve_names_and_tensor_metadata(self) -> None:
        class TensorFixture:
            shape = (2, 3)
            dtype = "torch.float32"

            @staticmethod
            def numel() -> int:
                return 6

        state = {
            "param_groups.net.a.lr": 0.1,
            "param_groups.net.a.betas": (0.9, 0.95),
            "param_groups.net.b.lr": 0.1,
            "state.net.a.exp_avg": TensorFixture(),
        }
        rows = COLLECT._flattened_optimizer_schema(state, {"a", "b"})
        self.assertEqual({row["owner"] for row in rows}, {"a", "b"})
        tensor_rows = [row for row in rows if row["kind"] == "tensor"]
        self.assertEqual(tensor_rows, [{
            "flat_key": "state.net.a.exp_avg", "owner": "a", "namespace": "state",
            "suffix": "exp_avg", "kind": "tensor", "shape": [2, 3], "dtype": "float32", "numel": 6,
        }])
        self.assertEqual(
            next(row for row in rows if row["flat_key"] == "param_groups.net.a.betas"),
            {
                "flat_key": "param_groups.net.a.betas", "owner": "a", "namespace": "param_groups",
                "suffix": "betas", "kind": "tuple",
                "items": [{"kind": "float", "value": 0.9}, {"kind": "float", "value": 0.95}],
            },
        )
        self.assertNotEqual({row["owner"] for row in rows}, {"a", "b", "missing"})
        with self.assertRaisesRegex(RuntimeError, "unmapped"):
            COLLECT._flattened_optimizer_schema({"param_groups.net.a_extra.lr": 0.1}, {"a"})
        with self.assertRaisesRegex(RuntimeError, "unmapped"):
            COLLECT._flattened_optimizer_schema({"param_groups.net.extra.lr": 0.1}, {"a"})

    def test_backend_orchestration_stops_after_nonzero_recurrent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            calls = []

            def run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                backend_output = Path(command[command.index("--output") + 1])
                backend_output.write_text(json.dumps({"status": "BLOCKED", "partial": True}))
                return subprocess.CompletedProcess(command, 9, "worker stdout", "worker stderr")

            with mock.patch.object(COLLECT.subprocess, "run", side_effect=run):
                backends = COLLECT._run_backend_workers(["collector"], output, ROOT, {})
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][calls[0].index("--worker-backend") + 1], "recurrent")
            self.assertEqual(backends["recurrent"]["returncode"], 9)
            self.assertEqual(backends["recurrent"]["stdout"], "worker stdout")
            self.assertEqual(backends["recurrent"]["stderr"], "worker stderr")
            self.assertEqual(backends["recurrent"]["partial_backend_json"], {"status": "BLOCKED", "partial": True})
            self.assertNotIn("ttt_fast_weight", backends)

    def test_backend_orchestration_stops_after_launch_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            with mock.patch.object(
                COLLECT.subprocess, "run", side_effect=PermissionError(13, "Permission denied", "collector")
            ) as run:
                backends = COLLECT._run_backend_workers(["collector"], output, ROOT, {})
            self.assertEqual(run.call_count, 1)
            self.assertEqual(backends["recurrent"]["status"], "BLOCKED")
            self.assertIn("PermissionError", backends["recurrent"]["launch_error"])
            self.assertNotIn("ttt_fast_weight", backends)

    def test_nonexecutable_collector_script_launches_through_interpreter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "collector.py"
            script.write_text("print('worker launched')\n")
            script.chmod(0o644)
            command = COLLECT._worker_command_argv(script, [])
            self.assertEqual(command[:2], [COLLECT.sys.executable, str(script.resolve())])
            completed = subprocess.run(command, text=True, capture_output=True, check=True)
            self.assertEqual(completed.stdout, "worker launched\n")

    def test_worker_uses_framework_cwd_for_production_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            framework = root / "cosmos-framework"
            framework.mkdir()
            with mock.patch.object(COLLECT.os, "chdir") as chdir:
                self.assertEqual(COLLECT._set_worker_production_cwd(root), framework)
            chdir.assert_called_once_with(framework)
        with self.assertRaisesRegex(RuntimeError, "framework directory is missing"):
            COLLECT._set_worker_production_cwd(Path("/missing/p3-framework-root"))

    def test_attempt3_output_paths_are_fresh_and_prior_attempt_evidence_is_unchanged(self) -> None:
        output = ROOT / "artifacts/g0/r09/b2/p3_gpu_inventory_attempt3/p3_gpu_inventory.json"
        d005 = output.with_name("p3_gpu_inventory_d005.json")
        attempt_one = ROOT / "artifacts/g0/r09/b2/p3_gpu_inventory/p3_gpu_inventory_attempt1_d005.json"
        attempt_two = ROOT / "artifacts/g0/r09/b2/p3_gpu_inventory/p3_gpu_inventory.json"
        before = {path: _sha256(path) for path in (attempt_one, attempt_two)}
        COLLECT._assert_fresh_output_paths(ROOT, output, d005)
        self.assertEqual(before, {path: _sha256(path) for path in before})
        with self.assertRaisesRegex(ValueError, "fresh and untracked"):
            COLLECT._assert_fresh_output_paths(ROOT, attempt_two, d005)

    def test_backend_orchestration_stops_after_zero_exit_blocked_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            calls = []

            def run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                Path(command[command.index("--output") + 1]).write_text(json.dumps({"status": "BLOCKED"}))
                return subprocess.CompletedProcess(command, 0, "", "")

            with mock.patch.object(COLLECT.subprocess, "run", side_effect=run):
                backends = COLLECT._run_backend_workers(["collector"], output, ROOT, {})
            self.assertEqual(len(calls), 1)
            self.assertEqual(backends, {"recurrent": {"status": "BLOCKED"}})

    def test_backend_orchestration_launches_ttt_only_after_recurrent_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            calls = []

            def run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                Path(command[command.index("--output") + 1]).write_text(json.dumps({"status": "PASS"}))
                return subprocess.CompletedProcess(command, 0, "", "")

            with mock.patch.object(COLLECT.subprocess, "run", side_effect=run):
                backends = COLLECT._run_backend_workers(["collector"], output, ROOT, {})
            self.assertEqual(
                [command[command.index("--worker-backend") + 1] for command in calls],
                ["recurrent", "ttt_fast_weight"],
            )
            self.assertEqual({name: record["status"] for name, record in backends.items()}, {
                "recurrent": "PASS", "ttt_fast_weight": "PASS",
            })

    def test_backend_diff_rejects_ttt_only_persistent_key(self) -> None:
        d005_path = ROOT / "artifacts/g0/r09/b2/p3_dcp_diff_test_d005.json"
        try:
            artifact = self._passing_artifact(d005_path)
            artifact["ttt_fast_weight"]["inventory"]["dcp_state"]["model_state_keys"] = ["net.unexpected"]
            with mock.patch.object(VERIFY, "_tracked_clean", return_value=True), mock.patch.object(
                VERIFY, "FROZEN_SOURCE_PATHS", {}
            ):
                result = VERIFY.verify(artifact, ROOT)
                self.assertFalse(result["matched_diff_checks"]["only_allowed_dcp_model_keys"])
                self.assertEqual(result["status"], "FAIL")
        finally:
            d005_path.unlink(missing_ok=True)

    def test_backend_diff_rejects_ttt_only_optimizer_dcp_schema(self) -> None:
        d005_path = ROOT / "artifacts/g0/r09/b2/p3_optimizer_dcp_diff_test_d005.json"
        try:
            artifact = self._passing_artifact(d005_path)
            artifact["ttt_fast_weight"]["inventory"]["dcp_state"]["optimizer_state_schema"] = [{
                "flat_key": "param_groups.net.unexpected.lr",
                "owner": "unexpected",
                "namespace": "param_groups",
                "suffix": "lr",
                "kind": "float",
                "value": 0.1,
            }]
            with mock.patch.object(VERIFY, "_tracked_clean", return_value=True), mock.patch.object(
                VERIFY, "FROZEN_SOURCE_PATHS", {}
            ):
                result = VERIFY.verify(artifact, ROOT)
                self.assertFalse(result["matched_diff_checks"]["only_allowed_dcp_optimizer_schema"])
                self.assertEqual(result["status"], "FAIL")
        finally:
            d005_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
