import os
import tempfile
import unittest
from pathlib import Path

from tools.psm_wma.observe_source_evidence_bundle import (
    BLOCKED_AUTHORITY_NOT_CLOSED, OBSERVATION_SECTIONS, ObservationError,
    build_observation_bundle, observe_bundle,
)


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

    def test_requires_all_ten_sections_and_metadata(self):
        sections = {name: {} for name in OBSERVATION_SECTIONS}
        metadata = {"head_revision": "a" * 40, "index_tree_native_oid": "b" * 40,
                    "formal_root": "c" * 40, "child_gitlink": "d" * 40, "cwd": "/tmp",
                    "interpreter": "/usr/bin/python", "git": {},
                    "sanitized_env_sha256": "e" * 64, "argv": []}
        result = build_observation_bundle(sections=sections, metadata=metadata)
        self.assertEqual(tuple(result["sections"]), OBSERVATION_SECTIONS)

    def test_missing_section_is_blocked(self):
        with self.assertRaisesRegex(ObservationError, BLOCKED_AUTHORITY_NOT_CLOSED):
            build_observation_bundle(sections={}, metadata={})


if __name__ == "__main__":
    unittest.main()
