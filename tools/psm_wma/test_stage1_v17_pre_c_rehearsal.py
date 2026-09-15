import copy
import hashlib
import json
import pickle
import unittest
from dataclasses import replace

from tools.psm_wma.stage1_v17_pre_c_rehearsal import (
    AUTHORITY_ARGV, AuthorityAbsenceV1, AbsenceObservationV1, ClosureV1,
    DESIGNATED_ABSENCES, DescriptorV1, ENV, FROZEN_TARGETS, FrozenTargetV1,
    OpaquePatchCapabilityV1, P0_OBJECTS, P1_OBJECT_NAMES, PreCRehearsalError,
    QueryFactV1, ReadbackV1, RehearsalInputV1, consume_once_v05, rehearse_v05,
    RawFactV1, ReplayBindingV1, SourceObjectV1,
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
        p0 = tuple(SourceObjectV1(name, root, path, blob, raw_fact(name, name.encode()))
                   for name, root, path, blob in P0_OBJECTS)
        p1 = tuple(raw_fact(name, name.encode()) for name in P1_OBJECT_NAMES)
        binding = ReplayBindingV1(P0_OBJECTS[0][1], P0_OBJECTS[0][2], P0_OBJECTS[0][3],
            "a" * 64, 18966, "--bootstrap-owner-root-fd", 8,
            tuple((f"--key-{index}", f"old-{index}", f"new-{index}") for index in range(8)),
            tuple((f"old-{index}", f"new-{index}") for index in range(8)))
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
        value, calls = self.fixture(); plan = rehearse_v05(value)
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
                      "owner_fd_flag", "owner_fd_value", "parser_rows", "source_rows"):
            mutation = replace(value.closure.replay_binding, **{
                field: (("x", "y", "z"),) if field == "parser_rows" else (("x", "y"),)
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


if __name__ == "__main__": unittest.main()
