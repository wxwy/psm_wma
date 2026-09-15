import copy
import base64
import gzip
import hashlib
import json
import pickle
import unittest
from dataclasses import replace

from tools.psm_wma import stage1_v17_request_projection as projection
from tools.psm_wma.stage1_v17_pre_c_rehearsal import (
    AUTHORITY_ARGV, AuthorityAbsenceV1, AbsenceObservationV1, ClosureV1, ContractV05,
    DESIGNATED_ABSENCES, DescriptorV1, ENV, FROZEN_TARGETS, FrozenTargetV1,
    OpaquePatchCapabilityV1, P0_OBJECTS, P1_OBJECT_NAMES, PreCRehearsalError,
    QueryFactV1, ReadbackV1, RehearsalInputV1, consume_once_v05, rehearse_v05,
    RawFactV1, ReplayBindingV1, SourceObjectV1,
)
from tools.psm_wma.test_stage1_v17_launcher_replay import CANONICAL_BASE_GZIP_B64
from tools.psm_wma.test_stage1_v17_request_projection import ADAPTER_RAW, OUTER_RAW


REPLAY_HELPER_GZIP_B64 = (
    "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"
)


class PreCRehearsalTest(unittest.TestCase):
    def fixture(self, outcome="APPLIED", verify=True):
        calls = []
        def apply(descriptor, patch_text):
            calls.append((descriptor, patch_text)); return outcome
        cap = OpaquePatchCapabilityV1("host", "host.patch", "host/patch.py", "a" * 64,
            f"{apply.__module__}.{apply.__qualname__}", "psm.stage1.request-patch-consumer/v1",
            "opaque-patch-text-handoff/v1", apply)
        raw = json.dumps({"a": 1}, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        md = ("json_filename: docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.json\n"
              f"json_bytes: {len(raw)}\njson_sha256: {hashlib.sha256(raw).hexdigest()}\n"
              "canonicalization: utf-8; recursive sorted keys; compact separators; exactly one terminal LF\n"
              f"json_git_blob_oid: {blob}\n").encode()
        def add(payload): return b"".join(b"+" + line for line in payload.splitlines(keepends=True))
        patch = (b"--- /dev/null\n+++ b/docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.json\n" + add(raw) +
                 b"--- /dev/null\n+++ b/docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.md\n" + add(md))
        def query(argv, stdout, predicate, advertised=b""):
            return QueryFactV1(argv, 30, 0, stdout, b"", predicate, advertised,
                len(stdout), hashlib.sha256(stdout).hexdigest(), 0,
                hashlib.sha256(b"").hexdigest(), len(advertised),
                hashlib.sha256(advertised).hexdigest())
        def absence(path):
            raw_observation = json.dumps(
                {"lexists": False, "path": path, "predicate": "lexists_false"},
                sort_keys=True, separators=(",", ":")).encode() + b"\n"
            return AbsenceObservationV1(path, False, raw_observation, "lexists_false",
                len(raw_observation), hashlib.sha256(raw_observation).hexdigest())
        def raw_fact(name, raw):
            return RawFactV1(name, raw, len(raw), hashlib.sha256(raw).hexdigest())
        base_source = gzip.decompress(base64.b64decode(CANONICAL_BASE_GZIP_B64))
        replay_helper = gzip.decompress(base64.b64decode(REPLAY_HELPER_GZIP_B64))
        p0_raw = (base_source, replay_helper, ADAPTER_RAW)
        p0 = tuple(SourceObjectV1(name, root, path, blob, raw_fact(name, source))
                   for (name, root, path, blob), source in zip(P0_OBJECTS, p0_raw, strict=True))
        projected = projection.project_request_closure(OUTER_RAW, ADAPTER_RAW)
        p1 = tuple(raw_fact(name, getattr(projected, name).raw) for name in P1_OBJECT_NAMES)
        binding = ReplayBindingV1(P0_OBJECTS[0][1], P0_OBJECTS[0][2], P0_OBJECTS[0][3],
            hashlib.sha256(base_source).hexdigest(), 18966, "--bootstrap-owner-root-fd", 8,
            tuple(projected.parser_argv_items),
            (
                ("--formal-root", "9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5", "08d5828cdb4c12afa3b798ff01826c91ceb8755a"),
                ("--cwd", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8", "/proc/self/fd/8"),
                ("--index", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.index", "/proc/self/fd/8/.authority-root.index"),
                ("--bootstrap-project-root", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8", "/proc/self/fd/8"),
                ("--adapter-blob-oid", "da782754b8e8efa0f3cae973aa68602dcda1c237", "4a51bddd15ec9a88883e3071cc550de85721599b"),
                ("--adapter-raw-sha256", "091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9", "87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816"),
                ("--collection-module-blob-oid", "eefde4e5b5a0965bbdcaa5390b9286a4c77f2665", "4e9f51a52e822e7e57b67aa6ff5eaab8613566c1"),
                ("--collection-module-raw-sha256", "1b3353b0bd1342f1685062f962a7cbc1ba0dbf699bdc72c099ca470cb09cc340", "89eb3ee194f16665aea76ed4dcbaba803fc944d1e0b889d25be69d0831e68c67"),
            ),
            (
                ("9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5", "08d5828cdb4c12afa3b798ff01826c91ceb8755a"),
                (".authority-root-materialization-9dd2fb8", ".authority-root-materialization-08d5828"),
                ("da782754b8e8efa0f3cae973aa68602dcda1c237", "4a51bddd15ec9a88883e3071cc550de85721599b"),
                ("62a7bbf5fcb609e52931639001e6db01df81f0de2a33afd41c0080eb8e903f68", "bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702"),
                ("7538", "9406"),
                ("7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8", "ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097"),
                ("2427", "2336"),
                ("72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2", "1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333"),
            ))
        targets = tuple(FrozenTargetV1(name, path) for name, path in FROZEN_TARGETS)
        closure = ClosureV1(raw_fact("git_directory", b"git"), raw_fact("git_config", b"config"),
            raw_fact("local_v2", b"V2"),
            query(("git", "ls-remote", "origin", "refs/heads/V2"), b"v2", "remote_v2_ancestor", b"V2"),
            query(AUTHORITY_ARGV, b"", "authority_absent"),
            AuthorityAbsenceV1("refs/local-authority", b"local-absent", "authority_absent", 12, hashlib.sha256(b"local-absent").hexdigest()),
            AuthorityAbsenceV1("refs/remote-authority", b"remote-absent", "authority_absent", 13, hashlib.sha256(b"remote-absent").hexdigest()),
            tuple(absence(path) for path in DescriptorV1().paths),
            tuple(absence(path) for path in DESIGNATED_ABSENCES), p0, p1, binding, targets)
        def verifier(json_raw, markdown_raw, paths):
            return ReadbackV1(json_raw, markdown_raw) if verify else ReadbackV1(b"bad\n", markdown_raw)
        return RehearsalInputV1(cap, DescriptorV1(), raw, md, patch, ENV, closure,
            verifier, f"{verifier.__module__}.{verifier.__qualname__}"), calls

    def test_success_is_exactly_once(self):
        value, calls = self.fixture(); self.assertIsInstance(value, ContractV05); plan = rehearse_v05(value)
        self.assertEqual(consume_once_v05(plan, value.closure), "HARD_STOP_PENDING_INDEPENDENT_REVIEW")
        with self.assertRaisesRegex(PreCRehearsalError, "already_consumed"): consume_once_v05(plan, value.closure)
        self.assertEqual(len(calls), 1)

    def test_every_terminal_result_consumes_plan(self):
        for outcome in ("REJECTED_NO_WRITE", "PARTIAL_OR_UNKNOWN", "OTHER"):
            value, calls = self.fixture(outcome); plan = rehearse_v05(value)
            with self.assertRaises(PreCRehearsalError): consume_once_v05(plan, value.closure)
            with self.assertRaisesRegex(PreCRehearsalError, "already_consumed"): consume_once_v05(plan, value.closure)
            self.assertEqual(len(calls), 1)

    def test_copy_and_pickle_are_rejected(self):
        value, _ = self.fixture(); plan = rehearse_v05(value)
        for thing in (value.capability, plan):
            with self.assertRaises(PreCRehearsalError): copy.copy(thing)
            with self.assertRaises(PreCRehearsalError): pickle.dumps(thing)

    def test_environment_and_closure_are_exact(self):
        value, _ = self.fixture()
        with self.assertRaisesRegex(PreCRehearsalError, "six_key_environment"):
            rehearse_v05(RehearsalInputV1(value.capability, value.descriptor, value.json_raw, value.markdown_raw,
                value.patch_raw, ENV[:-1], value.closure, value.post_write_verify, value.post_write_qualname))
        foreign = replace(value.closure,
            output_absences=tuple(replace(item, path="foo") for item in value.closure.output_absences))
        with self.assertRaisesRegex(PreCRehearsalError, "closure_absence"):
            rehearse_v05(RehearsalInputV1(value.capability, value.descriptor, value.json_raw, value.markdown_raw,
                value.patch_raw, ENV, foreign, value.post_write_verify, value.post_write_qualname))

    def test_canonical_witnesses_and_forbidden_values_fail_closed(self):
        value, _ = self.fixture()
        for field, raw in (("json_raw", b'{"a":1}'), ("markdown_raw", b"bad\n"), ("patch_raw", b"v0.4\n")):
            values = dict(value.__dict__); values[field] = raw
            with self.assertRaises(PreCRehearsalError): rehearse_v05(RehearsalInputV1(**values))

    def test_post_write_failure_is_terminal(self):
        value, calls = self.fixture(verify=False); plan = rehearse_v05(value)
        with self.assertRaisesRegex(PreCRehearsalError, "post_write"): consume_once_v05(plan, value.closure)
        with self.assertRaisesRegex(PreCRehearsalError, "already_consumed"): consume_once_v05(plan, value.closure)
        self.assertEqual(len(calls), 1)

    def test_query_and_absence_identity_drifts_fail_closed(self):
        value, _ = self.fixture()
        for field in ("stdout_length", "stdout_sha256", "stderr_length", "stderr_sha256",
                      "advertised_length", "advertised_sha256"):
            foreign_query = replace(value.closure.remote_v2, **{
                field: 1 if field.endswith("length") else "0" * 64})
            foreign_closure = replace(value.closure, remote_v2=foreign_query)
            with self.assertRaisesRegex(PreCRehearsalError, "closure_query"):
                rehearse_v05(replace(value, closure=foreign_closure))
        for observations_field in ("output_absences", "designated_absences"):
            observations = getattr(value.closure, observations_field)
            for field in ("lexists", "raw", "predicate", "byte_length", "sha256"):
                mutation = {field: (True if field == "lexists" else b"foreign" if field == "raw"
                                    else "foreign" if field in ("predicate", "sha256") else 1)}
                foreign = (replace(observations[0], **mutation),) + observations[1:]
                foreign_closure = replace(value.closure, **{observations_field: foreign})
                with self.assertRaisesRegex(PreCRehearsalError, "closure_absence"):
                    rehearse_v05(replace(value, closure=foreign_closure))

    def test_inherited_closure_identity_drifts_fail_closed(self):
        value, _ = self.fixture()
        for field in ("git_identity", "config_raw", "local_v2_raw"):
            foreign = replace(value.closure, **{field: replace(getattr(value.closure, field), sha256="0" * 64)})
            with self.assertRaisesRegex(PreCRehearsalError, "closure_empty"):
                rehearse_v05(replace(value, closure=foreign))
        for field in ("root", "path", "blob_oid", "raw"):
            mutation = replace(value.closure.p0_objects[0], **{
                field: replace(value.closure.p0_objects[0].raw, sha256="0" * 64)
                if field == "raw" else "foreign"})
            foreign = replace(value.closure, p0_objects=(mutation,) + value.closure.p0_objects[1:])
            with self.assertRaisesRegex(PreCRehearsalError, "closure_inherited"):
                rehearse_v05(replace(value, closure=foreign))
        for field in ("name", "raw", "byte_length", "sha256"):
            mutation = replace(value.closure.p1_objects[0], **{
                field: b"foreign" if field == "raw" else 1
                if field == "byte_length" else "foreign"})
            foreign = replace(value.closure, p1_objects=(mutation,) + value.closure.p1_objects[1:])
            with self.assertRaisesRegex(PreCRehearsalError, "closure_inherited"):
                rehearse_v05(replace(value, closure=foreign))
        for field in ("formal_parent", "base_path", "base_blob_oid", "base_raw_sha256", "base_bytes",
                      "owner_fd_flag", "owner_fd_value", "parser_argv_items", "parser_rows", "source_rows"):
            mutation = replace(value.closure.replay_binding, **{
                field: ("foreign",) if field == "parser_argv_items" else (("x", "y", "z"),) if field == "parser_rows" else (("x", "y"),)
                if field == "source_rows" else 1 if field in ("base_bytes", "owner_fd_value") else "foreign"})
            foreign = replace(value.closure, replay_binding=mutation)
            with self.assertRaisesRegex(PreCRehearsalError, "closure_inherited"):
                rehearse_v05(replace(value, closure=foreign))
        for field in ("name", "path"):
            mutation = replace(value.closure.targets[0], **{field: "foreign"})
            foreign = replace(value.closure, targets=(mutation,) + value.closure.targets[1:])
            with self.assertRaisesRegex(PreCRehearsalError, "closure_inherited"):
                rehearse_v05(replace(value, closure=foreign))
        for field, value_to_mutate in (("p0_objects", tuple(reversed(value.closure.p0_objects))),
                                       ("p1_objects", tuple(reversed(value.closure.p1_objects))),
                                       ("replay_binding", replace(value.closure.replay_binding, owner_fd_value=9)),
                                       ("targets", tuple(reversed(value.closure.targets)))):
            foreign = replace(value.closure, **{field: value_to_mutate})
            with self.assertRaisesRegex(PreCRehearsalError, "closure_inherited"):
                rehearse_v05(replace(value, closure=foreign))

    def test_foreign_self_consistent_sources_and_literals_fail_before_consumer(self):
        value, calls = self.fixture()
        for index, item in enumerate(value.closure.p0_objects):
            foreign_raw = RawFactV1(item.name, b"foreign", 7, hashlib.sha256(b"foreign").hexdigest())
            p0 = list(value.closure.p0_objects)
            p0[index] = replace(item, raw=foreign_raw)
            with self.assertRaisesRegex(PreCRehearsalError, "closure_inherited"):
                rehearse_v05(replace(value, closure=replace(value.closure, p0_objects=tuple(p0))))
        for index, item in enumerate(value.closure.p1_objects):
            foreign = RawFactV1(item.name, b"foreign", 7, hashlib.sha256(b"foreign").hexdigest())
            p1 = list(value.closure.p1_objects); p1[index] = foreign
            with self.assertRaisesRegex(PreCRehearsalError, "closure_inherited"):
                rehearse_v05(replace(value, closure=replace(value.closure, p1_objects=tuple(p1))))
        for field, foreign_value in (("base_raw_sha256", "0" * 64),
                                     ("parser_argv_items", ("foreign",)),
                                     ("parser_rows", value.closure.replay_binding.parser_rows[::-1]),
                                     ("source_rows", value.closure.replay_binding.source_rows[::-1])):
            binding = replace(value.closure.replay_binding, **{field: foreign_value})
            with self.assertRaisesRegex(PreCRehearsalError, "closure_inherited"):
                rehearse_v05(replace(value, closure=replace(value.closure, replay_binding=binding)))
        self.assertEqual(calls, [])

    def test_sealed_observation_identity_drifts_fail_before_consumer(self):
        value, calls = self.fixture()
        def foreign_raw(name):
            return RawFactV1(name, b"foreign", 7, hashlib.sha256(b"foreign").hexdigest())
        remote = replace(value.closure.remote_v2, stdout=b"foreign", advertised_v2=b"foreign",
                         stdout_length=7, stdout_sha256=hashlib.sha256(b"foreign").hexdigest(),
                         advertised_length=7, advertised_sha256=hashlib.sha256(b"foreign").hexdigest())
        p0 = replace(value.closure.p0_objects[0], raw=foreign_raw("base_source"))
        p1 = foreign_raw("selection")
        cases = (
            replace(value.closure, git_identity=foreign_raw("git_directory")),
            replace(value.closure, config_raw=foreign_raw("git_config")),
            replace(value.closure, local_v2_raw=foreign_raw("local_v2")),
            replace(value.closure, remote_v2=remote),
            replace(value.closure, p0_objects=(p0,) + value.closure.p0_objects[1:]),
            replace(value.closure, p1_objects=(p1,) + value.closure.p1_objects[1:]),
            replace(value.closure, replay_binding=replace(value.closure.replay_binding, owner_fd_value=9)),
            replace(value.closure, targets=tuple(reversed(value.closure.targets))),
        )
        for current in cases:
            plan = rehearse_v05(value)
            with self.assertRaisesRegex(PreCRehearsalError, "freshness"):
                consume_once_v05(plan, current)
            self.assertEqual(calls, [])


if __name__ == "__main__": unittest.main()
