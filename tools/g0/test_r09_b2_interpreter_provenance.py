"""CPU-only permanent regressions for P4 native-load provenance primitives."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.g0.r09_b2_interpreter_provenance import (
    ProvenanceError,
    analyse_all_staged_python,
    analyse_elf_loader_symbols,
    analyse_wrapper_contract,
    analyse_python_contract,
    verify_native_load_contract,
    exact_allowlist,
    lexical_interpreter,
)


class InterpreterProvenanceTest(unittest.TestCase):
    def _python(self, root: Path, relative: str, content: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_all_source_classes_and_exact_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._python(root, "editable/app.py", "import ctypes\nctypes.CDLL('editable.so')\n")
            self._python(root, "registry/torch_helper.py", "import torch\ntorch.ops.load_library('registry.so')\n")
            self._python(root, "vcs/helper.py", "from ctypes import PyDLL\nPyDLL('vcs.so')\n")
            rows = analyse_all_staged_python(root, ["editable/app.py", "registry/torch_helper.py", "vcs/helper.py"])
            self.assertEqual(len(rows), 3)
            self.assertTrue(exact_allowlist(rows, rows))
            self.assertFalse(exact_allowlist(rows, rows[:-1]))

    def test_registry_shared_forgery_and_excluded_python_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._python(root, "registry/torch_helper.py", "import ctypes\nctypes.CDLL('one.so')\nctypes.CDLL('two.so')\n")
            rows = analyse_all_staged_python(root, ["registry/torch_helper.py"])
            self.assertFalse(exact_allowlist(rows, rows[:1]))
            self._python(root, "editable/missing.py", "pass\n")
            with self.assertRaises(ProvenanceError):
                analyse_all_staged_python(root, ["registry/torch_helper.py"])

    def test_indirect_and_nonliteral_python_native_load_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._python(root, "x.py", "import ctypes\nloader = ctypes.CDLL\nloader('x.so')\n")
            with self.assertRaises(ProvenanceError):
                analyse_all_staged_python(root, ["x.py"])

    def test_dynamic_constructor_alias_and_reassignment_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._python(root, "x.py", "from builtins import getattr as g\ng(ctypes, 'CDLL')('x.so')\n")
            with self.assertRaises(ProvenanceError):
                analyse_all_staged_python(root, ["x.py"])
            self._python(root, "x.py", "import ctypes\nloader = getattr\nloader(ctypes, 'CDLL')('x.so')\n")
            with self.assertRaises(ProvenanceError):
                analyse_all_staged_python(root, ["x.py"])

    def test_parameterized_wrapper_requires_literal_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._python(root, "torch/classes.py", "import ctypes\ndef load_library(path):\n    ctypes.CDLL(path)\nload_library('fixed.so')\n")
            definitions, invocations = analyse_wrapper_contract(root, ["torch/classes.py"])
            self.assertEqual(len(definitions), 1); self.assertEqual(len(invocations), 1)
            self._python(root, "torch/classes.py", "import ctypes\ndef load_library(path):\n    ctypes.CDLL(path)\nload_library(dynamic_path)\n")
            with self.assertRaises(ProvenanceError):
                analyse_wrapper_contract(root, ["torch/classes.py"])

    def test_wrapper_chain_expands_to_native_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._python(root, "torch/_ops.py", "import ctypes\ndef load_library(path):\n    ctypes.CDLL(path)\n")
            self._python(root, "torch/classes.py", "from torch._ops import load_library\ndef classes_load(path):\n    load_library(path)\nclasses_load('fixed.so')\n")
            definitions, invocations = analyse_wrapper_contract(root, ["torch/_ops.py", "torch/classes.py"])
            self.assertEqual(len(definitions), 2)
            self.assertEqual(invocations[0]["final_fqn"], "ctypes.CDLL")

    def test_combined_contract_uses_only_runtime_load_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._python(root, "x.py", "import ctypes\ndef load(path):\n    ctypes.CDLL(path)\nload('wrapper.so')\nctypes.CDLL('direct.so')\n")
            contract = analyse_python_contract(root, ["x.py"])
            self.assertEqual(len(contract["direct_python"]), 1)
            self.assertEqual(len(contract["wrapper_invocations"]), 1)
            self.assertTrue(exact_allowlist(contract["native_runtime_allowlist"], contract["native_runtime_allowlist"]))

    def test_contract_recomputes_candidate_sets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self._python(root, "x.py", "import ctypes\nctypes.CDLL('x.so')\n")
            python = analyse_python_contract(root, ["x.py"])
            contract = {"staging_root": str(root), "python_payloads": ["x.py"], "closure_objects": [], "elf_loader_records": [], **python}
            self.assertTrue(verify_native_load_contract(contract))
            contract["native_runtime_allowlist"] = []
            self.assertFalse(verify_native_load_contract(contract))
            self._python(root, "x.py", "import ctypes\nctypes.CDLL(name)\n")
            with self.assertRaises(ProvenanceError):
                analyse_all_staged_python(root, ["x.py"])

    def test_full_elf_closure_and_second_site_omission(self) -> None:
        objects = [
            {"canonical_path": "/seed.so", "undefined_symbols": []},
            {"canonical_path": "/closure.so", "undefined_symbols": ["dlopen"]},
        ]
        records = [{"component_path": "/closure.so", "symbol": "dlopen", "target_rule": "origin_literal", "target": "/closure-plugin.so", "target_sha256": "a" * 64}]
        rows = analyse_elf_loader_symbols(objects, records)
        self.assertEqual(rows[0]["component_path"], "/closure.so")
        with self.assertRaises(ProvenanceError):
            analyse_elf_loader_symbols(objects, [])

    def test_dlsym_and_unpaired_elf_record_fail(self) -> None:
        with self.assertRaises(ProvenanceError):
            analyse_elf_loader_symbols([{"canonical_path": "/closure.so", "undefined_symbols": ["dlsym"]}], [])
        with self.assertRaises(ProvenanceError):
            analyse_elf_loader_symbols([{"canonical_path": "/plain.so", "undefined_symbols": []}], [{"component_path": "/plain.so", "symbol": "dlopen", "target_rule": "literal", "target": "/x.so", "target_sha256": "a" * 64}])

    def test_lexical_launcher_is_not_replaced_by_realpath(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); target = root / "base-python"; launcher = root / "venv-python"
            target.write_text("base"); launcher.symlink_to(target)
            record = lexical_interpreter(launcher)
            self.assertEqual(record["path"], str(launcher))
            self.assertEqual(record["realpath"], str(target))
            self.assertNotEqual(record["path"], record["realpath"])


if __name__ == "__main__":
    unittest.main()
