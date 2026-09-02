"""CPU-only regressions for the non-executing P4-v4 candidate contract."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.g0.r09_b2_p4_v4_static_contract import load_pass_candidate, stage_atomic_publication, verify_fail_candidate, _reject_failed_identity_reuse, _validate_final_pair


def write(value: object, path: Path) -> bytes:
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(raw)
    return raw


class CandidateContractTest(unittest.TestCase):
    def _pass(self, root: Path, backend: str, token: str = "a" * 64) -> None:
        folder = root / "attempt" / backend
        folder.mkdir(parents=True)
        payload = {
            "request.json": {"backend": backend, "p4_run": {"run_token": token}},
            "result.json": {"backend": backend, "status": "PASS"},
            "verification.json": {"backend": backend, "status": "PASS"},
        }
        bytes_ = {name: write(value, folder / name) for name, value in payload.items()}
        write({"schema_version": "r09_b2_p4_v4_candidate_link_v1", "backend": backend,
               "attempt_id": "attempt", "run_token": token,
               "payload_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in bytes_.items()}},
              folder / "candidate_link.json")

    def test_pass_payload_is_byte_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._pass(root, "recurrent")
            self._pass(root, "ttt_fast_weight")
            with patch("tools.g0.r09_b2_p4_v4_static_contract._validate_final_pair"), patch(
                "tools.g0.r09_b2_p4_v4_static_contract._reject_failed_identity_reuse"
            ):
                staged = stage_atomic_publication(root / "attempt")
            self.assertIn("request.json", staged["recurrent"])
            (root / "attempt/recurrent/request.json").write_bytes(
                (root / "attempt/recurrent/request.json").read_bytes() + b" "
            )
            with self.assertRaises(ValueError):
                load_pass_candidate(root / "attempt/recurrent", "recurrent")

    def test_rejects_extra_payload_key_and_fail_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._pass(root, "recurrent")
            self._pass(root, "ttt_fast_weight")
            request = root / "attempt/recurrent/request.json"
            value = json.loads(request.read_text())
            value["attempt_id"] = "bad"
            write(value, request)
            link = root / "attempt/recurrent/candidate_link.json"
            link_value = json.loads(link.read_text())
            link_value["payload_sha256"]["request.json"] = hashlib.sha256(request.read_bytes()).hexdigest()
            write(link_value, link)
            with patch("tools.g0.r09_b2_p4_v4_static_contract._validate_final_pair"), patch(
                "tools.g0.r09_b2_p4_v4_static_contract._reject_failed_identity_reuse"
            ):
                with self.assertRaises(ValueError):
                    stage_atomic_publication(root / "attempt")
            failure = root / "fail/recurrent"
            failure.mkdir(parents=True)
            write({"backend": "recurrent"}, failure / "request.json")
            write({"schema_version": "r09_b2_p4_v4_candidate_link_v1", "backend": "recurrent",
                   "attempt_id": "fail", "run_token": "a" * 64, "status": "FAIL",
                   "stage": "admission", "error_type": "ValueError", "error": "x"}, failure / "failure.json")
            with self.assertRaises(ValueError):
                verify_fail_candidate(failure, "recurrent")

    def test_poison_rejects_token_or_run_root_reuse(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); attempt = root / "attempt"; attempt.mkdir()
            old = root / "old" / "recurrent"; old.mkdir(parents=True)
            (old / "failure.json").write_text("{}")
            payload = {"request.json": json.dumps({"p4_run": {"run_token": "b" * 64, "identity": {}}}).encode()}
            with patch("tools.g0.r09_b2_p4_v4_static_contract.verify_fail_candidate", return_value=("a" * 64, "/run")), patch(
                "tools.g0.r09_b2_p4_v4_static_contract._path_identity", return_value=Path("/run")
            ):
                with self.assertRaises(ValueError):
                    _reject_failed_identity_reuse(attempt, {"recurrent": payload})

    def test_effective_launch_drift_is_rejected(self):
        request = {"production_source": {}, "request_defaults": {}, "interpreter": {},
                   "effective_launch": {"cwd": "/x", "toml": "a", "overrides": [],
                                        "interpreter": "i", "loader_argv": ["-I"], "runtime_sys_path": []}}
        raw_request = (json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n").encode()
        payloads = {backend: {"request.json": raw_request, "result.json": b"{}\n", "verification.json": b"{}\n"}
                    for backend in ("recurrent", "ttt_fast_weight")}
        loaded = {backend: {"request": dict(request), "result": {}, "verification": {}}
                  for backend in payloads}
        loaded["ttt_fast_weight"]["request"]["effective_launch"] = dict(request["effective_launch"], loader_argv=["-S"])
        with patch("tools.g0.r09_b2_p4_v4_static_contract.load_p4_v4_preflight", return_value=loaded):
            with self.assertRaises(ValueError):
                _validate_final_pair(payloads)

    def test_runtime_sys_path_drift_is_rejected(self):
        request = {"production_source": {}, "request_defaults": {}, "interpreter": {},
                   "effective_launch": {"cwd": "/x", "toml": "a", "overrides": [],
                                        "interpreter": "i", "loader_argv": ["-I"],
                                        "runtime_sys_path": ["/staging"]}}
        raw_request = (json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n").encode()
        payloads = {backend: {"request.json": raw_request, "result.json": b"{}\n", "verification.json": b"{}\n"}
                    for backend in ("recurrent", "ttt_fast_weight")}
        loaded = {backend: {"request": dict(request), "result": {}, "verification": {}}
                  for backend in payloads}
        loaded["ttt_fast_weight"]["request"]["effective_launch"] = dict(
            request["effective_launch"], runtime_sys_path=["/ambient"]
        )
        with patch("tools.g0.r09_b2_p4_v4_static_contract.load_p4_v4_preflight", return_value=loaded):
            with self.assertRaises(ValueError):
                _validate_final_pair(payloads)

    def test_valid_pair_passes_admission_with_verifier_loader(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._pass(root, "recurrent")
            self._pass(root, "ttt_fast_weight", token="b" * 64)
            loaded = {
                backend: {
                    "request": {"backend": backend, "p4_run": {"run_token": token}},
                    "result": {"backend": backend, "status": "PASS"},
                    "verification": {"backend": backend, "status": "PASS"},
                }
                for backend, token in (("recurrent", "a" * 64), ("ttt_fast_weight", "b" * 64))
            }
            with patch("tools.g0.r09_b2_p4_v4_static_contract.load_p4_v4_preflight", return_value=loaded):
                staged = stage_atomic_publication(root / "attempt")
            self.assertEqual(set(staged), {"recurrent", "ttt_fast_weight"})


if __name__ == "__main__":
    unittest.main()
