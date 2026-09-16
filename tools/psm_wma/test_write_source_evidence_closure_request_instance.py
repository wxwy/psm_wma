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
                write_request_pair(b"{}\n", b"# detached\n", target,
                                   expected_formal_root="a" * 40,
                                   expected_child_gitlink="b" * 40,
                                   expected_instance_sha256="0" * 64)
            self.assertFalse(target.exists())

    def test_publishes_valid_pair_in_fixture(self):
        raw = build_request_instance(bundle())
        with tempfile.TemporaryDirectory() as root:
            digest = __import__("json").loads(raw)["sha256"]
            result = write_request_pair(raw, f"# detached\nsha256: {digest}\n".encode(), Path(root) / "fixture",
                                        expected_formal_root="a" * 40,
                                        expected_child_gitlink="b" * 40,
                                        expected_instance_sha256=digest)
            self.assertEqual(result["terminal"], "PASS")

    def test_existing_directory_returns_residue(self):
        raw = build_request_instance(bundle())
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "fixture"
            target.mkdir()
            result = write_request_pair(raw, f"# detached\nsha256: {json.loads(raw)['sha256']}\n".encode(), target,
                                        expected_formal_root="a" * 40,
                                        expected_child_gitlink="b" * 40,
                                        expected_instance_sha256=json.loads(raw)["sha256"])
            self.assertEqual(result["terminal"], "REAL_OUTPUT_WRITE_FAILED")
            self.assertIn("published_side", result)


if __name__ == "__main__":
    unittest.main()
