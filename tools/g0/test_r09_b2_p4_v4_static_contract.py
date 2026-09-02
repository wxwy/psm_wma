"""CPU-only regressions for the non-executing P4-v4 candidate contract."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.g0.r09_b2_p4_v4_static_contract import load_pass_candidate, stage_atomic_publication, verify_fail_candidate


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


if __name__ == "__main__":
    unittest.main()
