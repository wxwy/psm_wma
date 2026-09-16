import os
import tempfile
import unittest
from pathlib import Path

from tools.psm_wma.observe_source_evidence_bundle import ObservationError, observe_bundle


class ObservationTests(unittest.TestCase):
    def test_collects_identity_and_sanitized_environment(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            source = root / "module.py"
            source.write_bytes(b"print('metadata only')\n")
            result = observe_bundle(root=root, files={"module": source},
                                    target_paths=[root / "absent.json"], argv=["python", "-c"],
                                    env={"SAFE": "1", "SECRET": "hidden"}, env_allowlist=["SAFE"])
            self.assertEqual(result["files"]["module"]["size"], source.stat().st_size)
            self.assertNotIn("SECRET", str(result))

    def test_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            real = root / "real"
            real.write_bytes(b"x")
            link = root / "link"
            link.symlink_to(real)
            with self.assertRaises(ObservationError):
                observe_bundle(root=root, files={"link": link}, target_paths=[], argv=[], env={}, env_allowlist=[])

    def test_rejects_existing_target(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            target = root / "target"
            target.write_bytes(b"existing")
            with self.assertRaises(ObservationError):
                observe_bundle(root=root, files={}, target_paths=[target], argv=[], env={}, env_allowlist=[])


if __name__ == "__main__":
    unittest.main()
