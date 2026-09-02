"""CPU-only regression tests for the non-executing P4-v4 entry foundation."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.g0.r09_b2_p4_v4_execution_preflight import main


class EntryFoundationTest(unittest.TestCase):
    def test_requires_matching_regular_request_and_never_executes(self):
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "request.json"
            request.write_bytes(b"{}\n")
            digest = hashlib.sha256(request.read_bytes()).hexdigest()
            with self.assertRaisesRegex(RuntimeError, "separately reviewed"):
                main(["--request", str(request), "--request-sha256", digest])
            with self.assertRaises(ValueError):
                main(["--request", str(request), "--request-sha256", "0" * 64])


if __name__ == "__main__":
    unittest.main()
