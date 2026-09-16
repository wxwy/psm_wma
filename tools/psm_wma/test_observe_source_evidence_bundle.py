import os
import tempfile
import unittest
from pathlib import Path

from tools.psm_wma.observe_source_evidence_bundle import (
    BLOCKED_AUTHORITY_NOT_CLOSED, OBSERVATION_SECTIONS, ObservationError,
    assemble_constructor_bundle, build_observation_bundle, observation_to_bundle,
    observe_and_assemble, observe_bundle,
)
from tools.psm_wma.test_build_source_evidence_closure_request_instance import bundle


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

    def test_reads_git_metadata_through_observe_bundle(self):
        root = Path.cwd()
        result = observe_bundle(root=root, files={"module": root / "AGENTS.md"}, target_paths=[],
                                argv=[], env={}, env_allowlist=[], git_repo=root,
                                git_paths=["AGENTS.md"])
        self.assertEqual(len(result["git"]["head_revision"]), 40)
        self.assertEqual(len(result["git"]["blob_oids"]["AGENTS.md"]), 40)

    def test_assembles_flat_constructor_bundle(self):
        result = assemble_constructor_bundle(bundle())
        self.assertEqual(result["schema"], "root_source_evidence_closure_request_instance_v1")
        self.assertEqual(len(result["sha256"]), 64)

    def test_flat_bundle_missing_field_is_blocked(self):
        value = bundle()
        value.pop("executor")
        with self.assertRaisesRegex(ObservationError, BLOCKED_AUTHORITY_NOT_CLOSED):
            assemble_constructor_bundle(value)

    def test_observe_and_assemble_end_to_end(self):
        root = Path.cwd()
        result = observe_and_assemble(
            root=root, files={"module": root / "AGENTS.md"}, target_paths=[], argv=[], env={},
            env_allowlist=[], git_repo=root, git_ref="HEAD", git_paths=["AGENTS.md"],
            bundle_template=bundle(), formal_root="a" * 40, child_gitlink="b" * 40)
        self.assertEqual(result["schema"], "root_source_evidence_closure_request_instance_v1")
        self.assertEqual(result["executor"]["module_path"], str(root / "AGENTS.md"))
        self.assertEqual(result["producer"]["module_path"], str(root / "AGENTS.md"))
        self.assertEqual(result["root_audit"]["module_path"], str(root / "AGENTS.md"))
        self.assertEqual(result["executor"]["cwd"], str(root))

    def test_observe_and_assemble_requires_git_observation(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ObservationError, BLOCKED_AUTHORITY_NOT_CLOSED):
                observe_and_assemble(root=Path(root), files={}, target_paths=[], argv=[], env={},
                                     env_allowlist=[], git_repo=Path(root), git_ref="HEAD",
                                     git_paths=[], bundle_template=bundle(), formal_root="a" * 40,
                                     child_gitlink="b" * 40)

    def test_real_observation_binds_available_file_identities(self):
        root = Path.cwd()
        names = {"module": "AGENTS.md", "selection": "AGENTS.md", "config": "AGENTS.md",
                 "interpreter": "AGENTS.md", "git": "AGENTS.md"}
        observation = observe_bundle(
            root=root, files={name: root / path for name, path in names.items()}, target_paths=[],
            argv=["python", "-m", "x"], env={}, env_allowlist=[], git_repo=root,
            git_ref="HEAD", git_paths=["AGENTS.md"])
        result = observation_to_bundle(bundle(), observation,
                                       formal_root="c" * 40, child_gitlink="d" * 40)
        self.assertEqual(result["authority"]["selection_path"], str(root / "AGENTS.md"))
        self.assertEqual(result["authority"]["config_path"], str(root / "AGENTS.md"))
        self.assertEqual(result["executor"]["interpreter_path"], str(root / "AGENTS.md"))
        self.assertEqual(result["executor"]["git_path"], str(root / "AGENTS.md"))
        self.assertEqual(result["authority"]["selection_blob_native_oid"],
                         observation["git"]["blob_oids"]["AGENTS.md"])

    def test_missing_observed_blob_fails_closed(self):
        observation = {"root": {}, "files": {"module": {"path": "module.py", "raw_sha256": "a" * 64}},
                       "target_paths": [], "argv": [], "cwd": "/tmp",
                       "sanitized_env_sha256": "b" * 64,
                       "git": {"head_revision": "c" * 40, "index_tree_native_oid": "d" * 40,
                               "ref_revision": "e" * 40, "blob_oids": {}}}
        with self.assertRaisesRegex(ObservationError, BLOCKED_AUTHORITY_NOT_CLOSED):
            observation_to_bundle(bundle(), observation, formal_root="f" * 40, child_gitlink="0" * 40)


if __name__ == "__main__":
    unittest.main()
