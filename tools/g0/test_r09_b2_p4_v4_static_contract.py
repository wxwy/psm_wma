"""CPU-only regressions for the non-executing P4-v4 candidate contract."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.g0.test_r09_b2_p5_full_config_diff import P5Test

from tools.g0.r09_b2_p4_v4_static_contract import PAYLOAD_FILES, load_pass_candidate, stage_atomic_publication, verify_fail_candidate, _reject_failed_identity_reuse, _validate_final_pair
from tools.g0.export_r09_b2_p5_resolved_config import P4_V4_PREFLIGHT_RELATIVE, canonical_bytes


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
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); P5Test()._v4_preflight(root)
            payloads = {b: {n: (root / P4_V4_PREFLIGHT_RELATIVE / b / n).read_bytes() for n in PAYLOAD_FILES}
                        for b in ("recurrent", "ttt_fast_weight")}
            value = json.loads(payloads["ttt_fast_weight"]["request.json"])
            value["loader_argv"] = dict(value["loader_argv"], argv=["/bin/python", "-S"])
            payloads["ttt_fast_weight"]["request.json"] = canonical_bytes(value)
            with self.assertRaises(ValueError): _validate_final_pair(payloads)

    def test_runtime_sys_path_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); P5Test()._v4_preflight(root)
            payloads = {b: {n: (root / P4_V4_PREFLIGHT_RELATIVE / b / n).read_bytes() for n in PAYLOAD_FILES}
                        for b in ("recurrent", "ttt_fast_weight")}
            value = json.loads(payloads["ttt_fast_weight"]["request.json"])
            value["p4_staging"]["runtime_sys_path"] = ["/ambient"]
            payloads["ttt_fast_weight"]["request.json"] = canonical_bytes(value)
            with self.assertRaises(ValueError): _validate_final_pair(payloads)

    def test_full_p5_valid_pair_passes_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            P5Test()._v4_preflight(root)
            candidate_root = root / "attempt"
            candidate_root.mkdir()
            payloads = {}
            for backend in ("recurrent", "ttt_fast_weight"):
                source = root / P4_V4_PREFLIGHT_RELATIVE / backend
                target = candidate_root / backend
                shutil.copytree(source, target)
                raw = {name: (target / name).read_bytes() for name in ("request.json", "result.json", "verification.json")}
                link = {"schema_version": "r09_b2_p4_v4_candidate_link_v1", "backend": backend,
                        "attempt_id": "attempt", "run_token": "a" * 64,
                        "payload_sha256": {name: hashlib.sha256(value).hexdigest() for name, value in raw.items()}}
                write(link, target / "candidate_link.json")
                payloads[backend] = raw
            with patch("tools.g0.r09_b2_p4_v4_static_contract._path_identity", return_value=root / "run"):
                staged = stage_atomic_publication(candidate_root)
            self.assertEqual(set(staged), set(payloads))


if __name__ == "__main__":
    unittest.main()
