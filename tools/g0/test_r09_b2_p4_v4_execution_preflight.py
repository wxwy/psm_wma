"""CPU-only regression tests for the non-executing P4-v4 entry foundation."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.g0.r09_b2_p4_v4_execution_preflight import EXECUTION_CONTRACT, main


class EntryFoundationTest(unittest.TestCase):
    def _request(self) -> bytes:
        return (json.dumps({"schema_version": "r09_b2_p4_v4_execution_request_v1",
                            **{key: {} for key in ("entry", "source", "interpreter", "environment", "run", "candidates", "backends", "authorities")},
                            "execution_contract": EXECUTION_CONTRACT},
                           sort_keys=True, separators=(",", ":")) + "\n").encode()

    def test_requires_matching_regular_request_and_never_executes(self):
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "request.json"
            request.write_bytes(self._request())
            digest = hashlib.sha256(request.read_bytes()).hexdigest()
            with self.assertRaisesRegex(RuntimeError, "separately reviewed"):
                main(["--request", str(request), "--request-sha256", digest])
            with self.assertRaises(ValueError):
                main(["--request", str(request), "--request-sha256", "0" * 64])

    def test_rejects_unknown_execution_request_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "request.json"
            value = json.loads(self._request())
            value["ambient"] = {}
            request.write_bytes((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
            with self.assertRaisesRegex(ValueError, "schema differs"):
                main(["--request", str(request), "--request-sha256", hashlib.sha256(request.read_bytes()).hexdigest()])


if __name__ == "__main__":
    unittest.main()
