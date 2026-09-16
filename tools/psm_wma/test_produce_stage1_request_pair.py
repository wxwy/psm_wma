from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.psm_wma.produce_stage1_request_pair import (
    PairPublicationError,
    produce_pair,
    publish_verified_pair,
    validate_pair_environment,
)


class PairPublicationTest(unittest.TestCase):
    def test_produce_pair_reuses_canonical_builder(self) -> None:
        environment = {key: "1" for key in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_SYSTEM", "GIT_NO_REPLACE_OBJECTS", "LANG", "LC_ALL")}
        environment.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "credential.https://github.com.helper", "GIT_CONFIG_VALUE_0": "!/usr/bin/gh auth git-credential"})
        payload = {"environment": environment, "schema": "test"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw, markdown = produce_pair(root / "pair.json", root / "pair.md", payload)
            self.assertEqual((root / "pair.json").read_bytes(), raw)
            self.assertEqual((root / "pair.md").read_bytes(), markdown)

    def test_environment_allowlist_accepts_helper_without_secrets(self) -> None:
        base = {key: "1" for key in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_SYSTEM", "GIT_NO_REPLACE_OBJECTS", "LANG", "LC_ALL")}
        validate_pair_environment({**base, "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "credential.https://github.com.helper", "GIT_CONFIG_VALUE_0": "!/usr/bin/gh auth git-credential"})
        with self.assertRaises(PairPublicationError):
            validate_pair_environment({**base, "GH_TOKEN": "secret"})

    def test_publish_and_idempotent_replay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = (root / "pair.json", root / "pair.md")
            raw = (b'{"ok":true}\n', b"pair\n")
            publish_verified_pair(*paths, *raw)
            publish_verified_pair(*paths, *raw)
            self.assertEqual(paths[0].read_bytes(), raw[0])
            self.assertEqual(paths[1].read_bytes(), raw[1])

    def test_divergent_existing_pair_is_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            json_path, markdown_path = root / "pair.json", root / "pair.md"
            json_path.write_bytes(b"old\n")
            markdown_path.write_bytes(b"old\n")
            with self.assertRaises(PairPublicationError):
                publish_verified_pair(json_path, markdown_path, b"new\n", b"new\n")
            self.assertEqual(json_path.read_bytes(), b"old\n")
            self.assertEqual(markdown_path.read_bytes(), b"old\n")

    def test_symlink_destination_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_bytes(b"outside\n")
            (root / "pair.json").symlink_to(target)
            with self.assertRaises(PairPublicationError):
                publish_verified_pair(root / "pair.json", root / "pair.md", b"x\n", b"y\n")
            self.assertEqual(target.read_bytes(), b"outside\n")


if __name__ == "__main__":
    unittest.main()
