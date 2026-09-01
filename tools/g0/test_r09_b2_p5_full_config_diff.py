"""CPU-only permanent P5 static-contract tests; never compose a Cosmos config."""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.g0.export_r09_b2_p5_resolved_config import CanonicalizationError, canonicalize, parse_d005_command, sanitized_environment, validate_production_root
from tools.g0.verify_r09_b2_p5_full_config_diff import _expected, _exporter_source, verify_pair
from tools.g0.verify_r09_b2_p4_d005 import P3_VERIFIER_SHA256, sha256_json


def target_a() -> None: pass
def target_b() -> None: pass


class P5Test(unittest.TestCase):
    def _pair(self):
        root = Path(__file__).resolve().parents[2]; records, contracts = _expected(root)
        def envelope(backend):
            record = records[backend]; p3 = record["inputs"]["p3_inventory"]
            return {"schema_version": "r09_b2_p5_full_config_diff_v2", "backend": backend,
                    "provenance": {"production_source": record["source"], "exporter_source": _exporter_source(root), "inputs": {"p4_record_sha256": sha256_json({k:v for k,v in record.items() if k != "d005_sha256"}), "p3_inventory_path": p3["path"], "p3_inventory_sha256": p3["sha256"], "p3_verifier_sha256": P3_VERIFIER_SHA256}},
                    "effective_launch": {"command": {"argv": record["command"]["argv"], "cwd": record["command"]["cwd"], "interpreter": record["command"]["interpreter"], "toml": "examples/toml/sft_config/action_policy_libero_edge_all.toml", "trailing_overrides": ["trainer.max_iter=100", "trainer.save_zero_checkpoint=true"]}, "environment": {"set": record["environment"]["set"], "unset": record["environment"]["unset"], "inherit_allowlist": record["environment"]["inherit_allowlist"], "effective": record["environment"]["set"]}, "world_size": record["budget"]["world_size"], "budget": record["budget"], "p1_p3_d005_bindings": {"p1_manifest": record["inputs"]["p1_manifest"], "p3_inventory": p3}, "derived_job_path_local": record["outputs"]["run_root"]},
                    "resolved_config": {"model": {"config": {"local_history_backend": "ttt_fast_weight" if backend == "ttt_fast_weight" else "recurrent"}}, "optimizer": {"keys_to_select": contracts[backend]["selector_keys"]}}}
        return root, envelope("recurrent"), envelope("ttt_fast_weight"), contracts

    def test_real_p4_shape_p3_contract_passes_and_mutations_fail(self):
        root, recurrent, ttt, contracts = self._pair(); self.assertEqual(verify_pair(recurrent, ttt, root, root)["status"], "PASS")
        bad = {**ttt, "provenance": {**ttt["provenance"], "inputs": {**ttt["provenance"]["inputs"], "p3_inventory_sha256": "bad"}}}; self.assertEqual(verify_pair(recurrent, bad, root, root)["status"], "FAIL")
        bad = {**ttt, "provenance": {**ttt["provenance"], "inputs": {**ttt["provenance"]["inputs"], "p3_inventory_path": "other.json"}}}; self.assertEqual(verify_pair(recurrent, bad, root, root)["status"], "FAIL")
        fake_inputs = {**recurrent["provenance"]["inputs"], "p3_verifier_sha256": "bogus"}
        bad_recurrent = {**recurrent, "provenance": {**recurrent["provenance"], "inputs": fake_inputs}}
        bad_ttt = {**ttt, "provenance": {**ttt["provenance"], "inputs": {**ttt["provenance"]["inputs"], "p3_verifier_sha256": "bogus"}}}
        self.assertEqual(verify_pair(bad_recurrent, bad_ttt, root, root)["status"], "FAIL")
        bad = {**ttt, "effective_launch": {**ttt["effective_launch"], "p1_p3_d005_bindings": {"p3_inventory": {**ttt["effective_launch"]["p1_p3_d005_bindings"]["p3_inventory"], "backend_contract": contracts["recurrent"]}}}}; self.assertEqual(verify_pair(recurrent, bad, root, root)["status"], "FAIL")
        arbitrary = {"selector_keys": ["arbitrary"], "optimizer_membership_sha256": "bad"}
        bad = {**ttt, "effective_launch": {**ttt["effective_launch"], "p1_p3_d005_bindings": {"p3_inventory": {**ttt["effective_launch"]["p1_p3_d005_bindings"]["p3_inventory"], "backend_contract": arbitrary}}}}; self.assertEqual(verify_pair(recurrent, bad, root, root)["status"], "FAIL")
        extra = {**contracts["ttt_fast_weight"], "unexpected": True}
        bad = {**ttt, "effective_launch": {**ttt["effective_launch"], "p1_p3_d005_bindings": {"p3_inventory": {**ttt["effective_launch"]["p1_p3_d005_bindings"]["p3_inventory"], "backend_contract": extra}}}}; self.assertEqual(verify_pair(recurrent, bad, root, root)["status"], "FAIL")
        bad = {**ttt, "resolved_config": {"model": {"config": {"local_history_backend": "arbitrary"}}, "optimizer": ttt["resolved_config"]["optimizer"]}}; self.assertEqual(verify_pair(recurrent, bad, root, root)["status"], "FAIL")

    def test_canonicalization_and_d005_contract_are_fail_closed(self):
        self.assertNotEqual(canonicalize(target_a), canonicalize(target_b))
        with self.assertRaises(CanonicalizationError): canonicalize(float("nan"))
        record = {"command": {"executable": False, "argv": ["python", "--sft-toml=r.toml", "trainer.max_iter=100", "trainer.save_zero_checkpoint=true"]}}
        self.assertEqual(parse_d005_command(record), ("r.toml", ["trainer.max_iter=100", "trainer.save_zero_checkpoint=true"]))
        record["command"]["argv"].reverse()
        with self.assertRaises(ValueError): parse_d005_command(record)
        self.assertEqual(sanitized_environment({"set": {"B": "2"}, "unset": ["X"], "inherit_allowlist": ["A"]}, {"A": "1", "X": "x", "LEAK": "z"}), {"A": "1", "B": "2"})

    def test_d005_absolute_production_root_rejects_relocated_checkout(self):
        root = Path(__file__).resolve().parents[2]; records, _ = _expected(root)
        self.assertEqual(validate_production_root(records["recurrent"], records["ttt_fast_weight"], Path("/disk/rl/psm_wma_p4_d005_retry")), Path("/disk/rl/psm_wma_p4_d005_retry"))
        with self.assertRaises(ValueError):
            validate_production_root(records["recurrent"], records["ttt_fast_weight"], root)

    def test_child_bootstrap_reaches_precompose_guard_under_d005_env(self):
        root = Path(__file__).resolve().parents[2]; records, _ = _expected(root); record = records["recurrent"]
        with tempfile.TemporaryDirectory() as temp:
            request = {"cwd": record["command"]["cwd"], "interpreter": {"realpath": "/bin/false"}, "environment": {"effective": record["environment"]["set"]}}
            path = Path(temp) / "request.json"; path.write_text(json.dumps(request))
            result = subprocess.run([record["command"]["interpreter"]["realpath"], str(root / "tools/g0/export_r09_b2_p5_resolved_config.py"), "--child-request", str(path), "--child-output", str(Path(temp) / "tree.json")], cwd=record["command"]["cwd"], env=record["environment"]["set"], text=True, capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cwd/interpreter differs", result.stderr)
