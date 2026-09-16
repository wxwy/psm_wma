import json
import unittest

from tools.psm_wma.build_source_evidence_closure_request_instance import (
    TOP_LEVEL_KEYS, SCHEMA, build_request_instance, verify_instance_bytes,
)


def bundle():
    return {key: ({"value": key} if key not in ("schema", "sha256") else (SCHEMA if key == "schema" else ""))
            for key in TOP_LEVEL_KEYS}


class ConstructionTests(unittest.TestCase):
    def test_build_is_canonical_and_self_bound(self):
        raw = build_request_instance(bundle())
        self.assertEqual(raw, raw.decode().encode())
        self.assertEqual(verify_instance_bytes(raw), json.loads(raw)["sha256"])

    def test_rejects_unknown_top_level_key(self):
        value = bundle()
        value["unknown"] = 1
        with self.assertRaises(ValueError):
            build_request_instance(value)

    def test_rejects_modified_digest(self):
        raw = build_request_instance(bundle())
        value = json.loads(raw)
        value["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            verify_instance_bytes(json.dumps(value, separators=(",", ":"), sort_keys=True).encode() + b"\n")


if __name__ == "__main__":
    unittest.main()
