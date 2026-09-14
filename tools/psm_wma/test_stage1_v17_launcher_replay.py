import hashlib
import subprocess
import unittest

from tools.psm_wma.stage1_v17_launcher_replay import AuthorityReplayError, ReplayBinding, replay_outer_payload


def sha(raw): return hashlib.sha256(raw).hexdigest()


class ReplayTest(unittest.TestCase):
    def canonical(self):
        source = subprocess.run(
            ["git", "show", "08d5828cdb4c12afa3b798ff01826c91ceb8755a:docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py"],
            check=True, capture_output=True, cwd="/disk/rl/psm_wma").stdout
        parser_rows = (
            ("--formal-root", "9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5", "08d5828cdb4c12afa3b798ff01826c91ceb8755a"),
            ("--cwd", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8", "/proc/self/fd/8"),
            ("--index", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.index", "/proc/self/fd/8/.authority-root.index"),
            ("--bootstrap-project-root", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8", "/proc/self/fd/8"),
            ("--adapter-blob-oid", "da782754b8e8efa0f3cae973aa68602dcda1c237", "4a51bddd15ec9a88883e3071cc550de85721599b"),
            ("--adapter-raw-sha256", "091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9", "87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816"),
            ("--collection-module-blob-oid", "eefde4e5b5a0965bbdcaa5390b9286a4c77f2665", "4e9f51a52e822e7e57b67aa6ff5eaab8613566c1"),
            ("--collection-module-raw-sha256", "1b3353b0bd1342f1685062f962a7cbc1ba0dbf699bdc72c099ca470cb09cc340", "89eb3ee194f16665aea76ed4dcbaba803fc944d1e0b889d25be69d0831e68c67"))
        source_rows = (("9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5", "08d5828cdb4c12afa3b798ff01826c91ceb8755a"), (".authority-root-materialization-9dd2fb8", ".authority-root-materialization-08d5828"), ("da782754b8e8efa0f3cae973aa68602dcda1c237", "4a51bddd15ec9a88883e3071cc550de85721599b"), ("62a7bbf5fcb609e52931639001e6db01df81f0de2a33afd41c0080eb8e903f68", "bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702"), ("7538", "9406"), ("7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8", "ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097"), ("2427", "2336"), ("72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2", "1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333"))
        return source, ReplayBinding("08d5828cdb4c12afa3b798ff01826c91ceb8755a", "docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py", "af19a9eb66ecaf8bd0b92a48ab1867f105026658", sha(source), len(source), parser_rows, source_rows, "--bootstrap-owner-root-fd", "8", 2336, "1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333", 18875, "658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8")

    def test_canonical_v16_replay(self):
        source, binding = self.canonical()
        result = replay_outer_payload(base_source=source, binding=binding)
        self.assertEqual((len(result.parser_argv_bytes), result.parser_argv_sha256), (2336, binding.expected_parser_sha256))
        self.assertEqual((len(result.outer_payload_bytes), result.outer_payload_sha256), (18875, binding.expected_outer_sha256))

    def test_canonical_self_check_drifts_fail(self):
        source, binding = self.canonical()
        for offset in range(4, 8):
            rows = list(binding.source_replacements)
            old, new = rows[offset]
            rows[offset] = ("missing-" + old, new)
            changed = ReplayBinding(binding.formal_parent, binding.base_path, binding.base_blob_oid,
                binding.base_raw_sha256, binding.base_bytes, binding.parser_replacements, tuple(rows),
                binding.owner_fd_flag, binding.owner_fd_value, binding.expected_parser_bytes,
                binding.expected_parser_sha256, binding.expected_outer_bytes, binding.expected_outer_sha256)
            with self.assertRaisesRegex(AuthorityReplayError, "source_target"):
                replay_outer_payload(base_source=source, binding=changed)
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

    def test_reordered_targets_fail(self):
        base, parser, outer = self.fixture()
        binding = self.binding(base, parser, outer, (("--bootstrap-project-root", "/old", "/new"), ("--cwd", "/old", "/new")))
        with self.assertRaisesRegex(AuthorityReplayError, "parser_target"):
            replay_outer_payload(base_source=base, binding=binding)

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
