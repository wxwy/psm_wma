"""CPU-only permanent P5 static-contract tests; never compose a Cosmos config."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.g0.export_r09_b2_p5_resolved_config import CanonicalizationError, PYTHON_CHILD_LOCALE, bound_exporter_source, build_pair_requests, canonicalize, parse_d005_command, run_parent_export, sanitized_environment, validate_production_root, validate_root_isolation
from tools.g0.verify_r09_b2_p5_full_config_diff import P4_RECORD_SHA256, _expected, _exporter_source, verify_pair
from tools.g0.verify_r09_b2_p4_d005 import P3_VERIFIER_SHA256


def target_a() -> None: pass
def target_b() -> None: pass


class P5Test(unittest.TestCase):
    def _exporter_worktree(self, root: Path, temporary: Path) -> Path:
        exporter = temporary / "exporter"
        subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach", str(exporter), "HEAD"], check=True, stdout=subprocess.DEVNULL)
        self.addCleanup(lambda: subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force", str(exporter)], check=False, stdout=subprocess.DEVNULL))
        return exporter

    def _pair(self):
        root = Path(__file__).resolve().parents[2]; records, contracts, record_sha256, verification_sha256 = _expected(root)
        def envelope(backend):
            record = records[backend]; p3 = record["inputs"]["p3_inventory"]
            return {"schema_version": "r09_b2_p5_full_config_diff_v2", "backend": backend,
                    "provenance": {"production_source": record["source"], "exporter_source": None, "inputs": {"p4_record_sha256": record_sha256[backend], "p4_d005_sha256": record["d005_sha256"], "p4_verification_sha256": verification_sha256, "p3_inventory_path": p3["path"], "p3_inventory_sha256": p3["sha256"], "p3_verifier_sha256": P3_VERIFIER_SHA256}},
                    "effective_launch": {"command": {"argv": record["command"]["argv"], "cwd": record["command"]["cwd"], "interpreter": record["command"]["interpreter"], "toml": "examples/toml/sft_config/action_policy_libero_edge_all.toml", "trailing_overrides": ["trainer.max_iter=100", "trainer.save_zero_checkpoint=true"]}, "environment": {"set": record["environment"]["set"], "unset": record["environment"]["unset"], "inherit_allowlist": record["environment"]["inherit_allowlist"], "effective": record["environment"]["set"]}, "world_size": record["budget"]["world_size"], "budget": record["budget"], "p1_p3_d005_bindings": {"p1_manifest": record["inputs"]["p1_manifest"], "p3_inventory": p3}, "derived_job_path_local": record["outputs"]["run_root"]},
                    "resolved_config": {"model": {"config": {"local_history_backend": "ttt_fast_weight" if backend == "ttt_fast_weight" else "recurrent"}}, "optimizer": {"keys_to_select": contracts[backend]["selector_keys"]}}}
        return root, envelope("recurrent"), envelope("ttt_fast_weight"), contracts

    def test_real_p4_shape_p3_contract_passes_and_mutations_fail(self):
        root, recurrent, ttt, contracts = self._pair()
        with tempfile.TemporaryDirectory() as temp:
            exporter = self._exporter_worktree(root, Path(temp))
            source = _exporter_source(exporter)
            recurrent["provenance"]["exporter_source"] = source; ttt["provenance"]["exporter_source"] = source
            self.assertEqual(verify_pair(recurrent, ttt, root, exporter)["status"], "PASS")
            self.assertEqual(verify_pair(recurrent, ttt, root, root)["status"], "FAIL")
            bad = {**ttt, "provenance": {**ttt["provenance"], "inputs": {**ttt["provenance"]["inputs"], "p3_inventory_sha256": "bad"}}}; self.assertEqual(verify_pair(recurrent, bad, root, exporter)["status"], "FAIL")
            bad = {**ttt, "provenance": {**ttt["provenance"], "inputs": {**ttt["provenance"]["inputs"], "p3_inventory_path": "other.json"}}}; self.assertEqual(verify_pair(recurrent, bad, root, exporter)["status"], "FAIL")
            fake_inputs = {**recurrent["provenance"]["inputs"], "p3_verifier_sha256": "bogus"}
            bad_recurrent = {**recurrent, "provenance": {**recurrent["provenance"], "inputs": fake_inputs}}
            bad_ttt = {**ttt, "provenance": {**ttt["provenance"], "inputs": {**ttt["provenance"]["inputs"], "p3_verifier_sha256": "bogus"}}}
            self.assertEqual(verify_pair(bad_recurrent, bad_ttt, root, exporter)["status"], "FAIL")
            bad = {**ttt, "effective_launch": {**ttt["effective_launch"], "p1_p3_d005_bindings": {"p3_inventory": {**ttt["effective_launch"]["p1_p3_d005_bindings"]["p3_inventory"], "backend_contract": contracts["recurrent"]}}}}; self.assertEqual(verify_pair(recurrent, bad, root, exporter)["status"], "FAIL")
            arbitrary = {"selector_keys": ["arbitrary"], "optimizer_membership_sha256": "bad"}
            bad = {**ttt, "effective_launch": {**ttt["effective_launch"], "p1_p3_d005_bindings": {"p3_inventory": {**ttt["effective_launch"]["p1_p3_d005_bindings"]["p3_inventory"], "backend_contract": arbitrary}}}}; self.assertEqual(verify_pair(recurrent, bad, root, exporter)["status"], "FAIL")
            extra = {**contracts["ttt_fast_weight"], "unexpected": True}
            bad = {**ttt, "effective_launch": {**ttt["effective_launch"], "p1_p3_d005_bindings": {"p3_inventory": {**ttt["effective_launch"]["p1_p3_d005_bindings"]["p3_inventory"], "backend_contract": extra}}}}; self.assertEqual(verify_pair(recurrent, bad, root, exporter)["status"], "FAIL")
            bad = {**ttt, "resolved_config": {"model": {"config": {"local_history_backend": "arbitrary"}}, "optimizer": ttt["resolved_config"]["optimizer"]}}; self.assertEqual(verify_pair(recurrent, bad, root, exporter)["status"], "FAIL")
            for path in (("provenance",), ("provenance", "inputs"), ("effective_launch",),
                         ("effective_launch", "command"), ("effective_launch", "environment"),
                         ("effective_launch", "p1_p3_d005_bindings")):
                bad_recurrent, bad_ttt = json.loads(json.dumps(recurrent)), json.loads(json.dumps(ttt))
                for envelope in (bad_recurrent, bad_ttt):
                    node = envelope
                    for key in path:
                        node = node[key]
                    node["unknown"] = True
                self.assertEqual(verify_pair(bad_recurrent, bad_ttt, root, exporter)["status"], "FAIL")
            forged = {**P4_RECORD_SHA256, "recurrent": "0" * 64}
            with patch("tools.g0.verify_r09_b2_p5_full_config_diff.P4_RECORD_SHA256", forged):
                self.assertEqual(verify_pair(recurrent, ttt, root, exporter)["status"], "FAIL")

    def test_canonicalization_and_d005_contract_are_fail_closed(self):
        self.assertNotEqual(canonicalize(target_a), canonicalize(target_b))
        with self.assertRaises(CanonicalizationError): canonicalize(float("nan"))
        record = {"command": {"executable": False, "argv": ["python", "--sft-toml=r.toml", "trainer.max_iter=100", "trainer.save_zero_checkpoint=true"]}}
        self.assertEqual(parse_d005_command(record), ("r.toml", ["trainer.max_iter=100", "trainer.save_zero_checkpoint=true"]))
        record["command"]["argv"].reverse()
        with self.assertRaises(ValueError): parse_d005_command(record)
        self.assertEqual(sanitized_environment({"set": {"B": "2"}, "unset": ["X"], "inherit_allowlist": ["A"]}, {"A": "1", "X": "x", "LEAK": "z"}), {"A": "1", "B": "2", **PYTHON_CHILD_LOCALE})
        with self.assertRaises(ValueError):
            sanitized_environment({"set": {}, "unset": ["LC_CTYPE"], "inherit_allowlist": []}, {})

    def test_d005_absolute_production_root_rejects_relocated_checkout(self):
        root = Path(__file__).resolve().parents[2]; records, _, _, _ = _expected(root)
        self.assertEqual(validate_production_root(records["recurrent"], records["ttt_fast_weight"], Path("/disk/rl/psm_wma_p4_d005_retry")), Path("/disk/rl/psm_wma_p4_d005_retry"))
        with self.assertRaises(ValueError):
            validate_production_root(records["recurrent"], records["ttt_fast_weight"], root)
        with patch("tools.g0.export_r09_b2_p5_resolved_config._git_clean", return_value=False):
            with self.assertRaises(ValueError):
                validate_production_root(records["recurrent"], records["ttt_fast_weight"], Path("/disk/rl/psm_wma_p4_d005_retry"))

    def test_root_isolation_rejects_equal_and_symlink_equivalent_paths(self):
        root = Path(__file__).resolve().parents[2]
        with self.assertRaises(ValueError):
            validate_root_isolation(root, root)
        with tempfile.TemporaryDirectory() as temp:
            alias = Path(temp) / "root-alias"; alias.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                validate_root_isolation(root, alias)

    def test_execution_identity_and_failed_attempt_are_fail_closed(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            temporary = Path(temp); exporter = self._exporter_worktree(root, temporary)
            with self.assertRaises(ValueError):
                bound_exporter_source(exporter)
            output = temporary / "canonical-output"
            request = {"interpreter": {"realpath": "/bin/false"}, "cwd": str(root), "environment": {"effective": {}}, "backend": "recurrent"}
            with (patch("tools.g0.export_r09_b2_p5_resolved_config.build_pair_requests", return_value={"recurrent": request}),
                  patch("tools.g0.export_r09_b2_p5_resolved_config.bound_exporter_source", return_value=({}, lambda *_: {"status": "PASS"})),
                  patch("tools.g0.export_r09_b2_p5_resolved_config.subprocess.run", side_effect=subprocess.CalledProcessError(7, "child"))):
                with self.assertRaises(subprocess.CalledProcessError):
                    run_parent_export({}, {}, production_root=Path("/disk/rl/psm_wma_p4_d005_retry"), evidence_root=root, exporter_root=exporter, output_dir=output)
            attempts = list(temporary.glob(".canonical-output.attempt-*"))
            self.assertEqual(len(attempts), 1)
            self.assertEqual(json.loads((attempts[0] / "failure.json").read_text())["status"], "FAIL")
            self.assertFalse(output.exists())

    def test_child_bootstrap_reaches_precompose_guard_under_d005_env(self):
        root = Path(__file__).resolve().parents[2]; records, _, _, _ = _expected(root); record = records["recurrent"]
        with tempfile.TemporaryDirectory() as temp:
            request = {"cwd": record["command"]["cwd"], "interpreter": {"realpath": "/bin/false"}, "environment": {"effective": record["environment"]["set"]}}
            path = Path(temp) / "request.json"; path.write_text(json.dumps(request))
            result = subprocess.run([record["command"]["interpreter"]["realpath"], str(root / "tools/g0/export_r09_b2_p5_resolved_config.py"), "--child-request", str(path), "--child-output", str(Path(temp) / "tree.json")], cwd=record["command"]["cwd"], env=record["environment"]["set"], text=True, capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("request schema/backend is not verifier-owned", result.stderr)

    def test_arbitrary_consistent_child_request_is_rejected_before_compose(self):
        root = Path(__file__).resolve().parents[2]; records, _, _, _ = _expected(root); record = records["recurrent"]
        requests = build_pair_requests(records["recurrent"], records["ttt_fast_weight"], production_root=Path("/disk/rl/psm_wma_p4_d005_retry"), evidence_root=root)
        forged = json.loads(json.dumps(requests["recurrent"])); forged["toml"] = "examples/toml/attacker.toml"
        forged["command_argv"] = ["--sft-toml=examples/toml/attacker.toml" if token.startswith("--sft-toml=") else token for token in forged["command_argv"]]
        with tempfile.TemporaryDirectory() as temp:
            path, output = Path(temp) / "forged.json", Path(temp) / "tree.json"; path.write_text(json.dumps(forged))
            result = subprocess.run([record["command"]["interpreter"]["realpath"], str(root / "tools/g0/export_r09_b2_p5_resolved_config.py"), "--child-request", str(path), "--child-output", str(output)], cwd=record["command"]["cwd"], env=record["environment"]["set"], text=True, capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not a frozen D005-bound identity", result.stderr)
            self.assertFalse(output.exists())
