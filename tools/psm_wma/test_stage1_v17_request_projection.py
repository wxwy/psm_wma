import ast
import base64
import dataclasses
import gzip
import hashlib
import json
import unittest
from unittest.mock import patch

from tools.psm_wma import stage1_v17_request_projection as projection

OUTER_GZIP_B64 = (
    "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"
)

ADAPTER_GZIP_B64 = (
    "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"
)

OUTER_RAW = gzip.decompress(base64.b64decode(OUTER_GZIP_B64))
ADAPTER_RAW = gzip.decompress(base64.b64decode(ADAPTER_GZIP_B64))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob_oid(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def replace_once(raw, old, new):
    if raw.count(old) != 1:
        raise AssertionError("fixture target is not unique")
    return raw.replace(old, new, 1)


def replace_after(raw, marker, old, new):
    offset = raw.index(marker)
    before, after = raw[:offset], raw[offset:]
    return before + after.replace(old, new, 1)


class ProjectionTest(unittest.TestCase):
    def assert_projection_fails(self, outer, adapter, category, **values):
        expected_outer = (len(outer), sha(outer))
        expected_adapter = (blob_oid(adapter), sha(adapter))
        with patch.multiple(projection, OUTER=expected_outer, ADAPTER=expected_adapter, **values):
            with self.assertRaisesRegex(projection.AuthorityReplayError, "projection_" + category):
                projection.project_request_closure(outer, adapter)

    def test_frozen_fixture_identity_and_canonical_projection(self):
        self.assertEqual((len(OUTER_RAW), sha(OUTER_RAW)), projection.OUTER)
        self.assertEqual((blob_oid(ADAPTER_RAW), sha(ADAPTER_RAW)), projection.ADAPTER)
        result = projection.project_request_closure(OUTER_RAW, ADAPTER_RAW)
        self.assertEqual(tuple(field.name for field in dataclasses.fields(result)), (
            "selection", "config", "parser_argv", "parser_argv_items", "bootstrap_argv",
            "bootstrap", "bootstrap_contract", "outer", "adapter_source"))
        self.assertEqual((result.parser_argv.byte_length, result.parser_argv.sha256), projection.PARSER_ARGV)
        self.assertEqual((result.bootstrap_argv.byte_length, result.bootstrap_argv.sha256), projection.BOOTSTRAP_ARGV)
        self.assertEqual((result.bootstrap_contract.byte_length, result.bootstrap_contract.sha256), projection.BOOTSTRAP_CONTRACT)
        self.assertEqual(result.parser_argv.raw, json.dumps(list(result.parser_argv_items), separators=(",", ":"), ensure_ascii=False).encode())
        self.assertEqual(tuple(zip(result.parser_argv_items[::2], result.parser_argv_items[1::2])), projection.FLAG_VALUES)
        self.assertEqual(result.bootstrap_argv.raw, json.dumps(["--", *result.parser_argv_items], separators=(",", ":"), ensure_ascii=False).encode())
        self.assertEqual(result.bootstrap_contract.raw, json.dumps(
            {"bootstrap_argv_sha256": result.bootstrap_argv.sha256,
             "bootstrap_raw_sha256": result.bootstrap.sha256}, sort_keys=True, separators=(",", ":")).encode())

    def test_input_identities_fail_before_projection(self):
        with self.assertRaisesRegex(projection.AuthorityReplayError, "projection_input_identity"):
            projection.project_request_closure(OUTER_RAW + b"# drift", ADAPTER_RAW)
        with self.assertRaisesRegex(projection.AuthorityReplayError, "projection_input_identity"):
            projection.project_request_closure(OUTER_RAW, ADAPTER_RAW + b"# drift")

    def test_raw_shape_and_base64_target_fail_closed(self):
        self.assert_projection_fails(replace_once(OUTER_RAW, b"RAW =", b"BROKEN ="), ADAPTER_RAW, "raw_shape")
        self.assert_projection_fails(OUTER_RAW.replace(b"base64.b64decode", b"base64.decode", 1), ADAPTER_RAW, "raw_target")
        self.assert_projection_fails(replace_once(OUTER_RAW, b"RAW = (", b"RAW = (b'', "), ADAPTER_RAW, "raw_shape")

    def test_parser_canonical_order_and_adjacency_fail_closed(self):
        result = projection.project_request_closure(OUTER_RAW, ADAPTER_RAW)
        raw = result.parser_argv.raw
        reordered = json.dumps([*result.parser_argv_items[2:4], *result.parser_argv_items[:2], *result.parser_argv_items[4:]], separators=(",", ":")).encode()
        self.assert_projection_fails(replace_once(OUTER_RAW, raw, reordered), ADAPTER_RAW, "argv")
        self.assert_projection_fails(replace_once(OUTER_RAW, raw, raw.replace(b",", b", ", 1)), ADAPTER_RAW, "argv")
        duplicate = json.dumps([*result.parser_argv_items, "--cwd", "/proc/self/fd/8"], separators=(",", ":")).encode()
        self.assert_projection_fails(replace_once(OUTER_RAW, raw, duplicate), ADAPTER_RAW, "argv")
        missing = json.dumps(result.parser_argv_items[:-2], separators=(",", ":")).encode()
        self.assert_projection_fails(replace_once(OUTER_RAW, raw, missing), ADAPTER_RAW, "argv")

    def test_bootstrap_signature_return_and_raw_drift_fail_closed(self):
        self.assert_projection_fails(OUTER_RAW, replace_once(ADAPTER_RAW, b"def bootstrap_payload()", b"def bootstrap_payload(value)"), "bootstrap")
        self.assert_projection_fails(OUTER_RAW, replace_after(ADAPTER_RAW, b"def bootstrap_payload()", b"return (", b"return value #"), "parse")
        self.assert_projection_fails(OUTER_RAW, replace_once(ADAPTER_RAW, b"import hashlib,json", b"import hashes,json"), "identity")

    def test_literal_rejects_name_and_call(self):
        for expression in ("value", "f()"):
            with self.assertRaisesRegex(projection.AuthorityReplayError, "projection_literal"):
                projection._literal(ast.parse(expression, mode="eval").body)


if __name__ == "__main__":
    unittest.main()
