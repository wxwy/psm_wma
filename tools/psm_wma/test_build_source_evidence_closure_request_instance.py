import json
import unittest

from tools.psm_wma.build_source_evidence_closure_request_instance import (
    TOP_LEVEL_KEYS, SCHEMA, SECTION_KEYS, RECORD_KEYS, RECEIPT_KEYS,
    build_request_instance, verify_instance_bytes,
)


def bundle():
    result = {"schema": SCHEMA, "formal_root": "a" * 40,
              "child_gitlink": "b" * 40, "sha256": ""}
    for name, keys in SECTION_KEYS.items():
        result[name] = {key: (["collection", "producer", "record", "receipt", "root_audit"] if name == "execution" and key == "order" else [] if key in ("keys", "callables", "argv", "order", "absent_paths", "absent_refs", "selected_paths", "package_keys", "witness_keys")
                        else False if key in ("zero_mutation", "one_shot", "no_retry", "pass_hard_stop")
                        else {} if key == "source_digest_receipt_mapping" else ("a" * 64 if "sha256" in key else "b" * 40 if key in ("module_blob_native_oid", "selection_blob_native_oid", "candidate_revision", "parent_root_revision", "child_gitlink") else key))
                           for key in keys}
    result["record"]["keys"] = list(RECORD_KEYS)
    result["record"]["source_digest_receipt_mapping"] = {key: key for key in RECORD_KEYS[2:]}
    result["receipt"]["keys"] = list(RECEIPT_KEYS)
    result["publication"]["package_keys"] = list(__import__("tools.psm_wma.immutable_source_collection", fromlist=["SOURCE_PACKAGE_KEYS"]).SOURCE_PACKAGE_KEYS)
    result["publication"]["witness_keys"] = list(__import__("tools.psm_wma.immutable_source_collection", fromlist=["SOURCE_WITNESS_KEYS"]).SOURCE_WITNESS_KEYS)
    return result


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
