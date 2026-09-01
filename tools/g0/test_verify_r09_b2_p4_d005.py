"""CPU-only permanent regressions for the P4 non-executable D005 verifier."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tools.g0.verify_r09_b2_p4_d005 as p4
from tools.g0.r09_b2_interpreter_provenance import (
    FROZEN_STDLIB_LOADER,
    LOADER_FLAGS,
    frozen_regular_python_manifest,
    lexical_interpreter,
)
from tools.g0.write_r09_b2_p4_d005 import finalize, sha256_json


class P4D005Test(unittest.TestCase):
    def _git(self, cwd: Path, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()

    def _asset(self, path: Path) -> dict[str, str]:
        return {"path": str(path), "realpath": str(path.resolve()), "sha256": p4._sha256_tree(path.resolve())}

    def _setup(self, root: Path) -> None:
        framework = root / "cosmos-framework"
        python = framework / ".venv/bin/python"
        python.parent.mkdir(parents=True); python.write_text("python"); python.chmod(0o755)
        recipe = framework / p4.TOML_RELATIVE
        recipe.parent.mkdir(parents=True)
        recipe.write_text("[job]\nproject='cosmos3_action_libero'\ngroup='action_sft'\nname='edge_libero_4in1'\n[trainer]\ngrad_accum_iter=16\n")
        for repo in (framework, root):
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "test"], check=True)
        subprocess.run(["git", "-C", str(framework), "add", "."], check=True)
        subprocess.run(["git", "-C", str(framework), "commit", "-qm", "sub"], check=True)
        (root / "README").write_text("root")
        bootstrap = root / p4.BOOTSTRAP_RELATIVE
        bootstrap.parent.mkdir(parents=True)
        bootstrap.write_text("# fixture bootstrap\n")
        for name in ("base", "edge", "vae", "libero", "cache"):
            (root / "assets" / name).mkdir(parents=True); (root / "assets" / name / "data").write_text(name)
        subprocess.run(["git", "-C", str(root), "add", "README", "assets", "tools"], check=True)
        subprocess.run(["git", "-C", str(root), "update-index", "--add", "--cacheinfo", f"160000,{self._git(framework, 'rev-parse', 'HEAD')},cosmos-framework"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "root"], check=True)

    def _frozen(self, root: Path) -> tuple[dict[str, object], dict[str, object]]:
        p1_path = root / "refs/p1/header.json"; p3_path = root / "refs/p3/inventory.json"; proof_path = root / "refs/p3/verifier.json"
        p1_path.parent.mkdir(parents=True); p3_path.parent.mkdir(parents=True)
        records = p1_path.parent / "records.jsonl"; suites_dir = p1_path.parent / "suites"; suites_dir.mkdir()
        records.write_text('{"ordinal":0}\n')
        suite_digests = {}
        for suite in ("libero_spatial", "libero_object", "libero_goal", "libero_10"):
            suite_path = suites_dir / f"{suite}.jsonl"; suite_path.write_text('{"suite":"' + suite + '"}\n'); suite_digests[suite] = p4._sha256_file(suite_path)
        p1 = {"schema_version": "r09_b2_stream_manifest_v1", **p4.PRODUCTION_P1, "records_sha256": p4._sha256_file(records), "files": {"suite_record_sha256": suite_digests}}
        def inventory(backend: str, keys: tuple[str, ...]) -> dict[str, object]:
            rows = [{"name": f"net.{key}.weight", "selected_by_optimizer": True, "selected_by_resolved_selector": True} for key in keys]
            rows.append({"name": "net.unrelated.weight", "selected_by_optimizer": False, "selected_by_resolved_selector": False})
            return {"inventory": {"selector": {"backend": backend, "keys_to_select": list(keys)}, "model_parameters": rows}}
        p3 = {"recurrent": inventory("recurrent", p4.EXPECTED_RECURRENT_SELECTOR_KEYS), "ttt_fast_weight": inventory("ttt_fast_weight", p4.EXPECTED_TTT_SELECTOR_KEYS)}
        p1_path.write_text(json.dumps(p1)); p3_path.write_text(json.dumps(p3)); proof_path.write_text(json.dumps({"status": "PASS", "record_valid": True}))
        subprocess.run(["git", "-C", str(root), "add", "refs"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "refs"], check=True)
        return p1, {"P1_HEADER_RELATIVE": "refs/p1/header.json", "P3_ARTIFACT_RELATIVE": "refs/p3/inventory.json", "P3_VERIFIER_RELATIVE": "refs/p3/verifier.json", "P1_HEADER_SHA256": p4._sha256_file(p1_path), "P3_ARTIFACT_SHA256": p4._sha256_file(p3_path), "P3_VERIFIER_SHA256": p4._sha256_file(proof_path), "FROZEN_GITLINK": self._git(root / "cosmos-framework", "rev-parse", "HEAD")}

    def _record(self, root: Path, p1: dict[str, object], backend: str, refs: dict[str, object]) -> dict[str, object]:
        framework = root / "cosmos-framework"; python = framework / ".venv/bin/python"; output = root / "future" / backend
        source = {"root_revision": self._git(root, "rev-parse", "HEAD"), "submodule_revision": self._git(framework, "rev-parse", "HEAD"), "gitlink_revision": self._git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2]}
        values = dict(p4.REQUIRED_ENV)
        values.update({"PSM_R09_B2_STREAM_MANIFEST_ROOT": str((root / refs["P1_HEADER_RELATIVE"]).parent.resolve()), "LIBERO_LATENT_CACHE_ROOT": str(root / "assets/cache"), "LIBERO_ROOT": str(root / "assets/libero"), "BASE_CHECKPOINT_PATH": str(root / "assets/base"), "EDGE_POLICY_CHECKPOINT": str(root / "assets/edge"), "WAN_VAE_PATH": str(root / "assets/vae"), "PYTHONPATH": str(framework), "IMAGINAIRE_OUTPUT_ROOT": str(output), "PSM_R09_B1_TTT_ENABLED": "1" if backend == "ttt_fast_weight" else "0"})
        env = {"set": values, "unset": sorted(p4.RANK_ENV | p4.SANITIZED_ENV), "inherit_allowlist": []}; env["sha256"] = sha256_json(env)
        assets = {"base_checkpoint": self._asset(root / "assets/base"), "edge_processor": self._asset(root / "assets/edge"), "wan_vae": self._asset(root / "assets/vae"), "libero_root": self._asset(root / "assets/libero"), "stream_manifest": self._asset((root / refs["P1_HEADER_RELATIVE"]).parent), "latent_cache": self._asset(root / "assets/cache"), "interpreter": lexical_interpreter(python)}
        keys = p4.EXPECTED_TTT_SELECTOR_KEYS if backend == "ttt_fast_weight" else p4.EXPECTED_RECURRENT_SELECTOR_KEYS
        inputs = {"p1_manifest": {"path": refs["P1_HEADER_RELATIVE"], "sha256": refs["P1_HEADER_SHA256"], "records_sha256": p1["records_sha256"], "record_count": p4.PRODUCTION_P1["record_count"]}, "p3_inventory": {"path": refs["P3_ARTIFACT_RELATIVE"], "sha256": refs["P3_ARTIFACT_SHA256"], "backend_contract": {"selector_keys": list(keys), "optimizer_membership_sha256": sha256_json(sorted(f"net.{key}.weight" for key in keys))}}, "external_assets": assets}
        interpreter = lexical_interpreter(python)
        agent = [interpreter["path"], *LOADER_FLAGS, FROZEN_STDLIB_LOADER,
                 "<request_abs>", "<request_sha256>", "<root_abs>", p4.BOOTSTRAP_RELATIVE,
                 "<bootstrap_sha256>"]
        worker = [interpreter["path"], "-m", "torch.distributed.run", "--standalone",
                  "--nnodes=1", "--nproc-per-node=1", "--no-python", *agent]
        template = {"bootstrap": {"relative_path": p4.BOOTSTRAP_RELATIVE, "sha256": p4.sha256_file(root / p4.BOOTSTRAP_RELATIVE)},
                    "request_defaults": {"toml": p4.TOML_RELATIVE, "overrides": list(p4.FROZEN_OVERRIDES)},
                    "request_schema_keys": list(p4.REQUEST_SCHEMA_KEYS),
                    "payload_manifest": frozen_regular_python_manifest(root, {"root": root, "cosmos_framework": framework}),
                    "agent_loader_argv_template": agent,
                    "worker_torchrun_argv_template": worker}
        command = {"cwd": str(framework.resolve()), "interpreter": interpreter, "argv_template": ["<agent_loader_argv_template>"], "executable": False, "launcher": {"kind": "verified_lexical_loader_template"}}
        command["sha256"] = sha256_json(command)
        identity = {"project": "cosmos3_action_libero", "group": "action_sft", "name": "edge_libero_4in1"}
        return finalize({"schema_version": p4.SCHEMA, "status": "FROZEN_NOT_EXECUTED", "backend": backend, "source": source, "command": command, "environment": env, "budget": p4.PRODUCTION_BUDGET, "inputs": inputs, "outputs": {"job_identity": identity, "fresh": True}, "interpreter_provenance_template": template})

    def _pair(self, root: Path):
        self._setup(root); p1, refs = self._frozen(root)
        return self._record(root, p1, "recurrent", refs), self._record(root, p1, "ttt_fast_weight", refs), refs

    def _patched(self, refs: dict[str, object]):
        return patch.multiple(p4, **refs)

    def test_valid_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, refs = self._pair(root)
            with self._patched(refs): self.assertEqual(p4.verify_pair(recurrent, ttt, root)["status"], "PASS")

    def test_rejects_forged_p3_even_when_self_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, refs = self._pair(root)
            path = root / refs["P3_ARTIFACT_RELATIVE"]; forged = json.loads(path.read_text())
            for row in forged["recurrent"]["inventory"]["model_parameters"]: row["selected_by_optimizer"] = row["selected_by_resolved_selector"] = False
            forged["recurrent"]["inventory"]["selector"] = {"backend": "recurrent", "keys_to_select": ["fake"]}; path.write_text(json.dumps(forged)); refs["P3_ARTIFACT_SHA256"] = p4._sha256_file(path)
            with self._patched(refs): self.assertEqual(p4.verify_pair(recurrent, ttt, root)["status"], "FAIL")

    def test_rejects_budget_env_and_template_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, refs = self._pair(root); recurrent["budget"]["micro_batch_size"] = 1
            with self._patched(refs): self.assertEqual(p4.verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")
            root = Path(tmp) / "two"; recurrent, ttt, refs = self._pair(root); recurrent["environment"]["unset"] = sorted(p4.RANK_ENV); recurrent["environment"]["sha256"] = sha256_json({key: recurrent["environment"][key] for key in ("set", "unset", "inherit_allowlist")})
            with self._patched(refs): self.assertEqual(p4.verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")
            root = Path(tmp) / "three"; recurrent, ttt, refs = self._pair(root); recurrent["interpreter_provenance_template"]["agent_loader_argv_template"][1] = "-m"
            with self._patched(refs): self.assertEqual(p4.verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")
            root = Path(tmp) / "four"; recurrent, ttt, refs = self._pair(root); recurrent["environment"]["unset"].remove("PSM_LOCAL_DUMMY_DIM"); recurrent["environment"]["sha256"] = sha256_json({key: recurrent["environment"][key] for key in ("set", "unset", "inherit_allowlist")})
            with self._patched(refs): self.assertEqual(p4.verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")

    def test_rejects_p1_and_output_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, refs = self._pair(root)
            path = root / refs["P1_HEADER_RELATIVE"]; bad = json.loads(path.read_text()); bad["record_count"] = 1; path.write_text(json.dumps(bad)); refs["P1_HEADER_SHA256"] = p4._sha256_file(path)
            with self._patched(refs): self.assertEqual(p4.verify_pair(recurrent, ttt, root)["status"], "FAIL")
            root = Path(tmp) / "two"; recurrent, ttt, refs = self._pair(root); recurrent["outputs"]["job_identity"]["name"] = "forged"
            with self._patched(refs): self.assertEqual(p4.verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")

    def test_rejects_legacy_direct_launch_and_runtime_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, refs = self._pair(root)
            recurrent["command"]["argv_template"] = [recurrent["command"]["interpreter"]["path"], "-m", "cosmos_framework.scripts.train"]
            with self._patched(refs): self.assertEqual(p4.verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")
            root = Path(tmp) / "two"; recurrent, ttt, refs = self._pair(root)
            recurrent["outputs"]["run_root"] = str(root / "forbidden-runtime-root")
            with self._patched(refs): self.assertEqual(p4.verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")

    def test_rejects_payload_manifest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, refs = self._pair(root)
            payload_roots = recurrent["interpreter_provenance_template"]["payload_manifest"]["roots"]
            next(item for item in payload_roots if item["files"])["files"][0]["sha256"] = "0" * 64
            with self._patched(refs): self.assertEqual(p4.verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")

    def test_rejects_live_gitlink_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, refs = self._pair(root)
            refs["FROZEN_GITLINK"] = "0" * 40
            with self._patched(refs): self.assertEqual(p4.verify_pair(recurrent, ttt, root)["status"], "FAIL")

    def test_rejects_schema_shape_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, refs = self._pair(root); recurrent["unexpected"] = True
            with self._patched(refs): self.assertEqual(p4.verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")

    def test_interpreter_exception_is_not_a_runtime_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, refs = self._pair(root)
            interpreter_parent = Path(recurrent["command"]["interpreter"]["realpath"]).parent
            self.assertFalse(any(interpreter_parent.is_relative_to(base) for base in p4._allowed_roots(root) if base != root.resolve()))
            recurrent["inputs"]["external_assets"]["interpreter"] = recurrent["inputs"]["external_assets"]["base_checkpoint"]
            with self._patched(refs): self.assertEqual(p4.verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")

    def test_rejects_untracked_source_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, refs = self._pair(root)
            (root / "untracked_shadow.py").write_text("pass\n")
            with self._patched(refs): self.assertEqual(p4.verify_pair(recurrent, ttt, root)["status"], "FAIL")
