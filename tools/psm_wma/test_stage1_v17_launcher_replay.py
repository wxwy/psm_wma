import hashlib
import unittest

from tools.psm_wma.stage1_v17_launcher_replay import AuthorityReplayError, ReplayBinding, replay_outer_payload


def sha(raw): return hashlib.sha256(raw).hexdigest()


class ReplayTest(unittest.TestCase):
    def binding(self, source, parser, outer, replacements=(("--cwd", "/old", "/new"),)):
        return ReplayBinding("p", "x", "o", sha(source), len(source), replacements,
            (("FORMAL=old", "FORMAL=new"),), "--bootstrap-owner-root-fd", "8",
            len(parser), sha(parser), len(outer), sha(outer))

    def fixture(self):
        base = b'FORMAL=old\nRAW=(b\'\'\'["--cwd","/old","--bootstrap-project-root","/old"]\'\'\',)\n'
        parser = b'["--cwd","/new","--bootstrap-project-root","/old","--bootstrap-owner-root-fd","8"]'
        outer = b'FORMAL=new\nRAW=(b\'\'\'["--cwd","/new","--bootstrap-project-root","/old","--bootstrap-owner-root-fd","8"]\'\'\',)\n'
        return base, parser, outer

    def test_round_trip(self):
        base, parser, outer = self.fixture()
        result = replay_outer_payload(base_source=base, binding=self.binding(base, parser, outer))
        self.assertEqual(result.outer_payload_bytes, outer)

    def test_wrong_adjacent_value_fails(self):
        base, parser, outer = self.fixture()
        binding = self.binding(base, parser, outer, (("--cwd", "/wrong", "/new"),))
        with self.assertRaisesRegex(AuthorityReplayError, "parser_target"):
            replay_outer_payload(base_source=base, binding=binding)

    def test_duplicate_old_values_are_flag_addressed(self):
        base, _, _ = self.fixture()
        parser = b'["--cwd","/new","--bootstrap-project-root","/new","--bootstrap-owner-root-fd","8"]'
        outer = b'FORMAL=new\nRAW=(b\'\'\'["--cwd","/new","--bootstrap-project-root","/new","--bootstrap-owner-root-fd","8"]\'\'\',)\n'
        binding = self.binding(base, parser, outer, (("--cwd", "/old", "/new"), ("--bootstrap-project-root", "/old", "/new")))
        self.assertEqual(replay_outer_payload(base_source=base, binding=binding).parser_argv_bytes, parser)

    def test_source_drift_fails(self):
        base, parser, outer = self.fixture()
        binding = self.binding(base, parser, outer)
        # Replace the sole source target with one absent from the frozen base.
        binding = ReplayBinding(binding.formal_parent, binding.base_path, binding.base_blob_oid,
            binding.base_raw_sha256, binding.base_bytes, binding.parser_replacements,
            (("MISSING=old", "FORMAL=new"),), binding.owner_fd_flag, binding.owner_fd_value,
            binding.expected_parser_bytes, binding.expected_parser_sha256,
            binding.expected_outer_bytes, binding.expected_outer_sha256)
        with self.assertRaisesRegex(AuthorityReplayError, "source_target"):
            replay_outer_payload(base_source=base, binding=binding)

    def test_existing_owner_fd_fails(self):
        base, parser, outer = self.fixture()
        base = base.replace(b'"--cwd"', b'"--bootstrap-owner-root-fd"', 1)
        binding = self.binding(base, parser, outer)
        with self.assertRaisesRegex(AuthorityReplayError, "owner_fd"):
            replay_outer_payload(base_source=base, binding=binding)
