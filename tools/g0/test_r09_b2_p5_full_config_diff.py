"""CPU-only permanent P5 static-contract tests; never compose a Cosmos config."""

from __future__ import annotations

import dataclasses
import unittest
from pathlib import Path

from tools.g0.export_r09_b2_p5_resolved_config import CanonicalizationError, canonicalize, parse_d005_command, sanitized_environment
from tools.g0.verify_r09_b2_p5_full_config_diff import verify_pair


def target_a() -> None: pass
def target_b() -> None: pass


class P5Test(unittest.TestCase):
    def _pair(self):
        contracts = {"recurrent": {"selector_keys": ["base", "local_history_runtime"], "optimizer_membership_sha256": "r"}, "ttt_fast_weight": {"selector_keys": ["local_history_runtime.encoder"], "optimizer_membership_sha256": "t"}}
        common = {"schema_version": "r09_b2_p5_full_config_diff_v2", "provenance": {"production_source": {"gitlink": "g"}, "inputs": {"p3_inventory_path": "p3.json", "p3_inventory_sha256": "sha", "p3_verifier_sha256": "pass"}}, "effective_launch": {"environment": {"set": {}, "effective": {}}, "p1_p3_d005_bindings": {"p3_inventory": {"backend_contract": None}}, "derived_job_path_local": "out"}, "resolved_config": {"model": {"config": {"local_history_backend": "recurrent"}}, "optimizer": {"keys_to_select": ["base", "local_history_runtime"]}}}
        recurrent = {**common, "backend": "recurrent"}; recurrent["effective_launch"] = {**common["effective_launch"], "p1_p3_d005_bindings": {"p3_inventory": {"backend_contract": contracts["recurrent"]}}}
        ttt = {**common, "backend": "ttt_fast_weight"}; ttt["effective_launch"] = {**common["effective_launch"], "p1_p3_d005_bindings": {"p3_inventory": {"backend_contract": contracts["ttt_fast_weight"]}}}; ttt["resolved_config"] = {"model": {"config": {"local_history_backend": "ttt_fast_weight"}}, "optimizer": {"keys_to_select": ["local_history_runtime.encoder"]}}
        return recurrent, ttt, contracts

    def test_real_p4_shape_p3_contract_passes_and_mutations_fail(self):
        recurrent, ttt, contracts = self._pair(); self.assertEqual(verify_pair(recurrent, ttt, contracts)["status"], "PASS")
        bad = {**ttt, "provenance": {**ttt["provenance"], "inputs": {**ttt["provenance"]["inputs"], "p3_inventory_sha256": "bad"}}}; self.assertEqual(verify_pair(recurrent, bad, contracts)["status"], "FAIL")
        bad = {**ttt, "provenance": {**ttt["provenance"], "inputs": {**ttt["provenance"]["inputs"], "p3_inventory_path": "other.json"}}}; self.assertEqual(verify_pair(recurrent, bad, contracts)["status"], "FAIL")
        bad = {**ttt, "effective_launch": {**ttt["effective_launch"], "p1_p3_d005_bindings": {"p3_inventory": {"backend_contract": contracts["recurrent"]}}}}; self.assertEqual(verify_pair(recurrent, bad, contracts)["status"], "FAIL")

    def test_canonicalization_and_d005_contract_are_fail_closed(self):
        self.assertNotEqual(canonicalize(target_a), canonicalize(target_b))
        with self.assertRaises(CanonicalizationError): canonicalize(float("nan"))
        record = {"command": {"executable": False, "argv": ["python", "--sft-toml=r.toml", "trainer.max_iter=100", "trainer.save_zero_checkpoint=true"]}}
        self.assertEqual(parse_d005_command(record), ("r.toml", ["trainer.max_iter=100", "trainer.save_zero_checkpoint=true"]))
        record["command"]["argv"].reverse()
        with self.assertRaises(ValueError): parse_d005_command(record)
        self.assertEqual(sanitized_environment({"set": {"B": "2"}, "unset": ["X"], "inherit_allowlist": ["A"]}, {"A": "1", "X": "x", "LEAK": "z"}), {"A": "1", "B": "2"})
