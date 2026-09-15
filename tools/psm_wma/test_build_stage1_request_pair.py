import hashlib
import json
import unittest
from pathlib import Path

from tools.psm_wma import build_stage1_request_pair as builder


def _adapter(raw: str) -> bytes:
    return f"def bootstrap_payload():\n    return {raw!r}\n".encode()


def _launcher() -> bytes:
    items = [
        "--formal-root", "a" * 40, "--child-gitlink", "b" * 40,
        "--cwd", "/disk/rl/psm_wma/.authority-root-materialization-aaaaaaa",
        "--index", "/disk/rl/psm_wma/.authority-root-materialization-aaaaaaa/.authority-root.index",
        "--bootstrap-project-root", "/disk/rl/psm_wma/.authority-root-materialization-aaaaaaa",
        "--adapter-path", "tools/adapter.py", "--adapter-blob-oid", "c" * 40,
        "--adapter-raw-sha256", "d" * 64, "--authority-module-path", "tools/auth.py",
        "--authority-module-blob-oid", "e" * 40, "--authority-module-raw-sha256", "f" * 64,
        "--collection-module-path", "tools/collection.py", "--collection-module-blob-oid", "1" * 40,
        "--collection-module-raw-sha256", "2" * 64, "--audit-module-path", "tools/audit.py",
        "--audit-module-blob-oid", "3" * 40, "--audit-module-raw-sha256", "4" * 64,
    ]
    parser = json.dumps(items, separators=(",", ":"))
    digest = hashlib.sha256(parser.encode()).hexdigest()
    return ("FORMAL = \"" + "a" * 40 + "\"\n"
            "CLEAN = ROOT + \"/.authority-root-materialization-aaaaaaa\"\n"
            "ADAPTER = (\"tools/adapter.py\",\n           \"" + "c" * 40 + "\")\n"
            "def add_and_capture():\n    require_closed(GIT_TARGET_FD,PARENT_OWNER_FD,BOOTSTRAP_FD,CLEAN_OWNER_FD)\n"
            "RAW = (b\"x\", b\"y\", b'''" + parser + "''')\n"
            "EXPECTED = ((\".authority-root.selection.json\", 3, \"x\"), (\".authority-root.config.json\", 4, \"y\"), (\".authority-root.bootstrap-contract.json\", 5, \"" + "0" * 64 + "\"))\n"
            "def boot():\n    raw=b\"bootstrap\"\n    if len(raw)!=7538 or digest(raw)!=\"" + "5" * 64 + "\": fail(\"bootstrap identity\")\n"
            "def main():\n    if len(RAW[0])!=516 or len(RAW[1])!=508 or len(RAW[2])!=2427 or tuple(digest(x) for x in RAW)!=EXPECTED[0][2:]+EXPECTED[1][2:]+(\"" + digest + "\",): fail(\"embedded authority\")\n").encode()


class BuildStage1RequestPairTest(unittest.TestCase):
    def setUp(self) -> None:
        self.inputs = builder.LauncherInputs(
            "9" * 40, "8" * 40, "9999999",
            builder.TreeBlob("tools/new_adapter.py", "7" * 40, "6" * 64),
            builder.TreeBlob("tools/new_auth.py", "5" * 40, "4" * 64),
            builder.TreeBlob("tools/new_collection.py", "3" * 40, "2" * 64),
            builder.TreeBlob("tools/new_audit.py", "1" * 40, "0" * 64),
        )

    def test_pair_and_patch_are_canonical(self) -> None:
        path = Path("docs/build/request.json")
        raw, markdown = builder.build_pair(path, {"root": "r", "nested": {"x": 1}})
        builder.verify_pair(path, raw, markdown)
        patch = builder.unified_patch(path, Path("docs/build/request.md"), raw, markdown)
        self.assertIn(b"+++ b/docs/build/request.json", patch)
        self.assertIn(b"+++ b/docs/build/request.md", patch)

    def test_rebuild_binds_every_target_and_dependent_hash(self) -> None:
        result = builder.rebuild_launcher(_launcher(), _adapter("new bootstrap"), self.inputs)
        self.assertIn(b"9" * 40, result.outer)
        self.assertIn(b".authority-root-materialization-9999999", result.outer)
        self.assertIn(b"--bootstrap-owner-root-fd\",\"8\"", result.parser_argv)
        self.assertEqual(result.parser_items.count("--bootstrap-owner-root-fd"), 1)
        self.assertIn(b'ADAPTER = ("tools/new_adapter.py",\n           "' + b"7" * 40 + b'")', result.outer)
        self.assertIn(b"require_closed(GIT_TARGET_FD,PARENT_OWNER_FD,CLEAN_OWNER_FD)", result.outer)
        self.assertIn(self.inputs.adapter.raw_sha256.encode(), result.parser_argv)
        self.assertIn(str(len(result.parser_argv)).encode(), result.outer)
        self.assertIn(builder.sha256(result.parser_argv).encode(), result.outer)
        self.assertIn(builder.sha256(result.bootstrap).encode(), result.outer)
        self.assertIn(builder.sha256(result.bootstrap_contract).encode(), result.outer)

    def test_embedded_inputs_reject_non_base64_literals(self) -> None:
        with self.assertRaises(ValueError):
            builder.embedded_input_raws(_launcher())

    def test_rebuild_rejects_existing_owner_fd(self) -> None:
        bad = _launcher().replace(b'"--adapter-path"', b'"--bootstrap-owner-root-fd","8","--adapter-path"')
        with self.assertRaises(ValueError):
            builder.rebuild_launcher(bad, _adapter("new bootstrap"), self.inputs)

    def test_payload_carries_exact_launcher_and_input_contract(self) -> None:
        base_raw = _launcher()
        adapter_raw = _adapter("new bootstrap")
        base = builder.TreeBlob("docs/base.py", builder.git_blob_oid(base_raw), builder.sha256(base_raw))
        adapter = builder.TreeBlob(self.inputs.adapter.path, builder.git_blob_oid(adapter_raw), builder.sha256(adapter_raw))
        inputs = builder.LauncherInputs(self.inputs.formal_root, self.inputs.child_gitlink, self.inputs.clean_suffix,
                                        adapter, self.inputs.authority, self.inputs.collection, self.inputs.audit)
        launcher = builder.rebuild_launcher(base_raw, adapter_raw, inputs)
        payload = builder.build_request_payload(inputs, base, base_raw, adapter_raw, launcher,
                                                b'{"selection":1}', b'{"config":1}', {"candidate_clean": True})
        raw, markdown = builder.build_pair(Path("docs/build/request.json"), payload)
        builder.verify_pair(Path("docs/build/request.json"), raw, markdown)
        self.assertEqual(payload["formal_root"], "9" * 40)
        self.assertEqual(payload["launcher"]["outer_sha256"], builder.sha256(launcher.outer))
