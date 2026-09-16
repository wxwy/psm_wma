import json
import tempfile
import unittest
from pathlib import Path

from tools.psm_wma.write_source_evidence_closure_request_instance import (
    APPROVED_JSON_NAME, APPROVED_MARKDOWN_NAME, write_approved_request_pair, write_request_pair,
)
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

    def test_fixed_path_publisher_uses_versioned_siblings(self):
        raw = build_request_instance(bundle())
        digest = json.loads(raw)["sha256"]
        markdown = f"# detached\nsha256: {digest}\n".encode()
        with tempfile.TemporaryDirectory() as root:
            result = write_approved_request_pair(raw, markdown, Path(root),
                                                 expected_formal_root="a" * 40,
                                                 expected_child_gitlink="b" * 40,
                                                 expected_instance_sha256=digest)
            self.assertEqual(result["terminal"], "PASS")
            self.assertTrue((Path(root) / APPROVED_JSON_NAME).is_file())
            self.assertTrue((Path(root) / APPROVED_MARKDOWN_NAME).is_file())
            self.assertFalse((Path(root) / ".request_instance_stage").exists())


if __name__ == "__main__":
    unittest.main()
