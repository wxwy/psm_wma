import json
import tempfile
import unittest
from pathlib import Path

from tools.psm_wma.write_source_evidence_closure_request_instance import write_request_pair
from tools.psm_wma.build_source_evidence_closure_request_instance import build_request_instance
from tools.psm_wma.test_build_source_evidence_closure_request_instance import bundle


class WriterTest(unittest.TestCase):
    def test_rejects_non_instance_before_creating_directory(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "staging"
            result = None
            with self.assertRaises(ValueError):
                write_request_pair(b"{}\n", b"# detached\n", target)
            self.assertFalse(target.exists())

    def test_publishes_valid_pair_in_fixture(self):
        raw = build_request_instance(bundle())
        with tempfile.TemporaryDirectory() as root:
            result = write_request_pair(raw, b"# detached\n", Path(root) / "fixture")
            self.assertEqual(result["terminal"], "PASS")


if __name__ == "__main__":
    unittest.main()
