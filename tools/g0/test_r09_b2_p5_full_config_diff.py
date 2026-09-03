"""CPU-only P5 v4 static-contract tests; never compose a Cosmos config."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.g0.export_r09_b2_p5_resolved_config import (
    P4_V4_PREFLIGHT_RELATIVE, P5_FORBIDDEN_ENVIRONMENT, P5_P3_BACKEND_ENVIRONMENT, PYTHON_CHILD_LOCALE,
    build_v4_pair_requests, canonical_bytes, derive_v2_roster_entries, load_p4_v4_preflight,
    p5_effective_environment, sha256_json,
)
from tools.g0.r09_b2_p4_v4_execution_preflight import _planned_projection
from tools.g0.verify_r09_b2_p5_full_config_diff import _authorized_p4_v4_evidence, _exporter_source, verify_pair
from tools.g0.verify_r09_b2_p4_d005 import P3_ARTIFACT_SHA256, P3_VERIFIER_SHA256


class P5Test(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

    def test_v2_roster_derivation_is_nested_closed_and_p4_semantically_identical(self):
        token = "a" * 64
        manifest_core = {"entries": [
            {"path": f"import_staging/{token}/pkg/sub/module.py", "type": "regular", "sha256": "b" * 64},
            {"path": "top.py", "type": "regular", "sha256": "c" * 64},
        ]}
        manifest = {**manifest_core, "sha256": sha256_json(manifest_core)}
        entries = derive_v2_roster_entries(manifest, token)
        self.assertEqual([item["path"] for item in entries], [
            "import_staging", f"import_staging/{token}", f"import_staging/{token}/pkg",
            f"import_staging/{token}/pkg/sub", f"import_staging/{token}/pkg/sub/module.py", "top.py",
        ])
        projection = _planned_projection(manifest, token)
        self.assertEqual(set(projection), {"entries", "projection_sha256"})
        self.assertEqual(projection["entries"], entries)
        self.assertEqual(projection["projection_sha256"], sha256_json({"entries": entries}))
        for path in ("preflight.json", "request.json", "result.json", "verification.json", "candidate_link.json", "import_staging", f"import_staging/{token}"):
            bad_core = {"entries": [{"path": path, "type": "regular", "sha256": "d" * 64}]}
            with self.assertRaises(ValueError):
                derive_v2_roster_entries({**bad_core, "sha256": sha256_json(bad_core)}, token)
        collision_core = {"entries": [
            {"path": "pkg", "type": "regular", "sha256": "d" * 64},
            {"path": "pkg/module.py", "type": "regular", "sha256": "e" * 64},
        ]}
        with self.assertRaises(ValueError):
            derive_v2_roster_entries({**collision_core, "sha256": sha256_json(collision_core)}, token)
        for path in ("preflight.json/x", "request.json/x", "result.json/x", "verification.json/x", "candidate_link.json/x"):
            bad_core = {"entries": [{"path": path, "type": "regular", "sha256": "d" * 64}]}
            with self.assertRaises(ValueError):
                derive_v2_roster_entries({**bad_core, "sha256": sha256_json(bad_core)}, token)
        unicode_core = {"entries": [{"path": "pkg/é.py", "type": "regular", "sha256": "e" * 64}]}
        p4_raw = (json.dumps(unicode_core, sort_keys=True, separators=(",", ":")) + "\n").encode()
        unicode_manifest = {**unicode_core, "sha256": hashlib.sha256(p4_raw).hexdigest()}
        self.assertNotEqual(unicode_manifest["sha256"], sha256_json(unicode_core))
        unicode_entries = derive_v2_roster_entries(unicode_manifest, token)
        unicode_projection = _planned_projection(unicode_manifest, token)
        self.assertEqual(unicode_projection["entries"], unicode_entries)
        self.assertEqual(unicode_projection["projection_sha256"], sha256_json({"entries": unicode_entries}))

    def _v4_preflight(self, root: Path) -> None:
        subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "p5@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "P5 fixture"], check=True)
        root_framework = root / "cosmos-framework"; root_framework.mkdir()
        subprocess.run(["git", "-C", str(root_framework), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(root_framework), "config", "user.email", "p5@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root_framework), "config", "user.name", "P5 fixture"], check=True)
        (root_framework / "module.py").write_text("x = 1\n")
        subprocess.run(["git", "-C", str(root_framework), "add", "module.py"], check=True)
        subprocess.run(["git", "-C", str(root_framework), "commit", "-qm", "fixture"], check=True)
        source = root / "source"; source.mkdir()
        framework = source / "cosmos-framework"; framework.mkdir()
        for repository in (source, framework):
            subprocess.run(["git", "-C", str(repository), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(repository), "config", "user.email", "p5@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repository), "config", "user.name", "P5 fixture"], check=True)
        (framework / "module.py").write_text("x = 1\n")
        subprocess.run(["git", "-C", str(framework), "add", "module.py"], check=True)
        subprocess.run(["git", "-C", str(framework), "commit", "-qm", "fixture"], check=True)
        (source / "recipe.toml").write_text("x = 1\n")
        (source / "p4_producer.py").write_text("producer = True\n")
        (source / "p4_verifier.py").write_text("verifier = True\n")
        (source / "tools/g0").mkdir(parents=True)
        (source / "tools/g0/export_r09_b2_p5_resolved_config.py").write_text("bootstrap = True\n")
        subprocess.run(["git", "-C", str(source), "add", "recipe.toml", "p4_producer.py", "p4_verifier.py", "tools/g0/export_r09_b2_p5_resolved_config.py", "cosmos-framework"], check=True)
        subprocess.run(["git", "-C", str(source), "commit", "-qm", "fixture"], check=True)
        run = root / "run"; run.mkdir(); token = "a" * 64
        staging = run / "import_staging" / token; staging.mkdir(parents=True)
        payload = staging / "payload.py"; payload.write_text("x = 1\n"); payload.chmod(0o444)
        (run / "import_staging").chmod(0o555); staging.chmod(0o555); run.chmod(0o555)

        def identity(path: Path, kind: str) -> dict[str, str]:
            core = {"root": str(path), "resolved_root": str(path), "kind": kind}
            return {**core, "identity_sha256": sha256_json(core)}

        toml = {"path": "recipe.toml", "git_blob_sha256": hashlib.sha256(subprocess.check_output(["git", "-C", str(source), "show", "HEAD:recipe.toml"])).hexdigest(), "current_sha256": hashlib.sha256((source / "recipe.toml").read_bytes()).hexdigest()}
        source_record = {"identity": identity(source, "git_source"), "revision": self._git(source, "rev-parse", "HEAD"), "gitlink": self._git(source, "ls-tree", "HEAD", "cosmos-framework").split()[2], "submodule_revision": self._git(framework, "rev-parse", "HEAD"), "toml": toml}
        manifest_entries = [{"path": f"import_staging/{token}/payload.py", "type": "regular", "sha256": hashlib.sha256(payload.read_bytes()).hexdigest()}]
        manifest_core = {"entries": manifest_entries}; manifest = {**manifest_core, "sha256": sha256_json(manifest_core)}
        roster_entries = [
            {"path": "import_staging", "type": "directory", "mode": "0555", "sha256": ""},
            {"path": f"import_staging/{token}", "type": "directory", "mode": "0555", "sha256": ""},
            {"path": f"import_staging/{token}/payload.py", "type": "regular", "mode": "0444", "sha256": manifest_entries[0]["sha256"]},
        ]
        roster_core = {"entries": roster_entries}; roster = {**roster_core, "sha256": sha256_json(roster_core)}
        for backend in ("recurrent", "ttt_fast_weight"):
            directory = root / P4_V4_PREFLIGHT_RELATIVE / backend; directory.mkdir(parents=True)
            env_core = {"set": {"A": "1", "PSM_R09_B1_TTT_ENABLED": P5_P3_BACKEND_ENVIRONMENT["PSM_R09_B1_TTT_ENABLED"][backend]}, "unset": list(P5_FORBIDDEN_ENVIRONMENT), "inherit_allowlist": []}
            environment = {**env_core, "sha256": sha256_json(env_core)}
            native_core = {"set": {}, "unset": list(P5_FORBIDDEN_ENVIRONMENT), "inherit_allowlist": []}
            native = {**native_core, "sha256": sha256_json(native_core)}
            defaults_core = {"toml": toml, "ordered_overrides": ["trainer.max_iter=100", "trainer.save_zero_checkpoint=true"]}
            defaults = {**defaults_core, "canonical_sha256": sha256_json(defaults_core)}
            interpreter_core = {"lexical_launcher": "/bin/python", "base_executable": "/bin/python", "stdlib": "/lib", "lib_dynload": "/lib"}
            interpreter = {**interpreter_core, "identity_sha256": sha256_json(interpreter_core)}
            def tool_identity(path: str) -> dict[str, str]:
                core = {"root_revision": self._git(source, "rev-parse", "HEAD"), "tool_path": path, "git_blob_sha256": hashlib.sha256(subprocess.check_output(["git", "-C", str(source), "show", f"HEAD:{path}"])).hexdigest(), "current_sha256": hashlib.sha256((source / path).read_bytes()).hexdigest()}
                return {**core, "sha256": sha256_json(core)}
            producer = tool_identity("p4_producer.py")
            bootstrap_sha = hashlib.sha256((source / "tools/g0/export_r09_b2_p5_resolved_config.py").read_bytes()).hexdigest()
            request = {"schema_version": "v4", "backend": backend, "production_source": source_record, "p4_run": {"identity": identity(run, "run_root"), "run_token": token, "roster_sha256": roster["sha256"]}, "p4_staging": {"identity": identity(staging, "staging_root"), "relative_path": f"import_staging/{token}", "readonly": True, "manifest_sha256": manifest["sha256"], "payload_import_roots": [{"relative_root": ".", "subtree_manifest_sha256": manifest["sha256"]}], "runtime_sys_path": [str(staging)]}, "request_defaults": defaults, "interpreter": interpreter, "loader_argv": {"argv": ["/bin/python", "-I", "-S", "-B", "-c", "verified-loader"], "request_token_index": 0, "loader_literal_sha256": "0" * 64, "bootstrap_git_blob_sha256": bootstrap_sha, "bootstrap_current_sha256": bootstrap_sha}, "effective_environment": environment, "native_loader_environment": native, "payload_manifest": manifest, "producer": producer}
            request_sha = sha256_json(request)
            outcome = {**request, "status": "PASS", "request_sha256": request_sha, "native_closure": [], "pre_p5_run_root_roster": roster}
            outcome_sha = sha256_json(outcome)
            checks = [{"name": name, "passed": True} for name in ("request_schema", "result_schema", "paths", "source", "staging_manifest", "staging_readonly", "runtime_sys_path", "environment", "native_closure", "run_root_roster", "producer")]
            verification_core = {"schema_version": "v4", "status": "PASS", "backend": backend, "request_sha256": request_sha, "result_sha256": outcome_sha, "checks": checks, "verifier": tool_identity("p4_verifier.py")}
            verification = {**verification_core, "verification_sha256": sha256_json(verification_core)}
            (directory / "request.json").write_bytes(canonical_bytes(request))
            (directory / "result.json").write_bytes(canonical_bytes(outcome))
            (directory / "verification.json").write_bytes(canonical_bytes(verification))
        (run / "import_staging").chmod(0o755); staging.chmod(0o755); run.chmod(0o755)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        (run / "import_staging").chmod(0o555); staging.chmod(0o555); run.chmod(0o555)

    def _authority(self, root: Path) -> dict[str, object]:
        commit = self._git(root, "rev-parse", "HEAD")
        tree_sha = hashlib.sha256(subprocess.check_output(["git", "-C", str(root), "cat-file", "tree", commit])).hexdigest()
        gitlink = self._git(root, "ls-tree", commit, "cosmos-framework").split()[2]
        blobs: dict[str, dict[str, str]] = {}
        for backend in ("recurrent", "ttt_fast_weight"):
            blobs[backend] = {}
            for filename in ("request.json", "result.json", "verification.json"):
                relative = f"artifacts/g0/r09/b2/p4_execution_preflight_v4/{backend}/{filename}"
                blobs[backend][filename] = hashlib.sha256(subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{relative}"])).hexdigest()
        return {"commit": commit, "tree_sha256": tree_sha, "gitlink": gitlink, "blobs": blobs}

    def _exporter_worktree(self, root: Path, temporary: Path) -> Path:
        exporter = temporary / "exporter"
        subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach", str(exporter), "HEAD"], check=True, stdout=subprocess.DEVNULL)
        self.addCleanup(lambda: subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force", str(exporter)], check=False, stdout=subprocess.DEVNULL))
        return exporter

    def test_v4_preflight_and_pair_are_historical_p4_v2_independent(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "evidence"; evidence.mkdir(); self._v4_preflight(evidence)
            loaded = load_p4_v4_preflight(evidence)
            self.assertEqual(p5_effective_environment(loaded["recurrent"]["request"], loaded["ttt_fast_weight"]["request"], backend="recurrent"), {"A": "1", "PSM_R09_B1_TTT_ENABLED": "0", **PYTHON_CHILD_LOCALE})
            requests = build_v4_pair_requests(evidence)
            self.assertEqual(requests["recurrent"]["cwd"], str(evidence / "source" / "cosmos-framework"))
            exporter = self._exporter_worktree(root, Path(temp)); source = _exporter_source(exporter)
            def envelope(backend: str) -> dict[str, object]:
                request = requests[backend]
                contract = contracts[backend]
                return {"schema_version": "r09_b2_p5_full_config_diff_v4", "backend": backend, "provenance": {"p4_v4_request_sha256": request["p4_request_sha256"], "p4_v4_result_sha256": request["p4_result_sha256"], "p4_v4_verification_sha256": request["p4_verification_sha256"], "exporter_source": source, "p3_contract": {"artifact_sha256": P3_ARTIFACT_SHA256, "verifier_sha256": P3_VERIFIER_SHA256, "backend_contract": contract}}, "effective_launch": {key: request[key] for key in ("cwd", "toml", "overrides", "interpreter", "loader_argv", "environment", "runtime_sys_path")}, "resolved_config": {"model": {"config": {"local_history_backend": backend}}, "optimizer": {"keys_to_select": [backend]}}}
            contracts = {"recurrent": {"selector_keys": ["recurrent"], "optimizer_membership_sha256": "a" * 64}, "ttt_fast_weight": {"selector_keys": ["ttt_fast_weight"], "optimizer_membership_sha256": "b" * 64}}
            recurrent, ttt = envelope("recurrent"), envelope("ttt_fast_weight")
            with patch("tools.g0.verify_r09_b2_p5_full_config_diff.AUTHORIZED_P4_V4_EVIDENCE", self._authority(evidence)), patch("tools.g0.verify_r09_b2_p5_full_config_diff._p3_contracts", return_value=contracts):
                self.assertEqual(verify_pair(recurrent, ttt, evidence, exporter)["status"], "PASS")
                self.assertEqual(verify_pair(recurrent, ttt, evidence, evidence)["status"], "FAIL")
                bad = json.loads(json.dumps(ttt)); bad["provenance"]["p4_v4_result_sha256"] = "0" * 64
                self.assertEqual(verify_pair(recurrent, bad, evidence, exporter)["status"], "FAIL")
                bad = json.loads(json.dumps(ttt)); bad["effective_launch"]["runtime_sys_path"].append("/ambient")
                self.assertEqual(verify_pair(recurrent, bad, evidence, exporter)["status"], "FAIL")
                bad = json.loads(json.dumps(ttt)); bad["effective_launch"]["environment"]["PSM_R09_B1_TTT_ENABLED"] = "0"
                self.assertEqual(verify_pair(recurrent, bad, evidence, exporter)["status"], "FAIL")
                bad = json.loads(json.dumps(ttt)); bad["resolved_config"]["optimizer"]["keys_to_select"] = ["recurrent"]
                self.assertEqual(verify_pair(recurrent, bad, evidence, exporter)["status"], "FAIL")
                for value in ("recurrent", "ttt_fast_weight"):
                    left, right = json.loads(json.dumps(recurrent)), json.loads(json.dumps(ttt))
                    left["resolved_config"]["model"]["config"]["local_history_backend"] = value
                    right["resolved_config"]["model"]["config"]["local_history_backend"] = value
                    self.assertEqual(verify_pair(left, right, evidence, exporter)["status"], "FAIL")
                left, right = json.loads(json.dumps(recurrent)), json.loads(json.dumps(ttt))
                del left["resolved_config"]["model"]["config"]["local_history_backend"]
                del right["resolved_config"]["model"]["config"]["local_history_backend"]
                self.assertEqual(verify_pair(left, right, evidence, exporter)["status"], "FAIL")
                bad = json.loads(json.dumps(ttt)); bad["resolved_config"]["unexpected"] = True
                self.assertEqual(verify_pair(recurrent, bad, evidence, exporter)["status"], "FAIL")

    def test_v4_evidence_authority_rejects_clean_replacement_descendant_and_gitlink_drift(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "evidence"; evidence.mkdir(); self._v4_preflight(evidence)
            authority = self._authority(evidence)
            exporter = self._exporter_worktree(root, Path(temp))
            with patch("tools.g0.verify_r09_b2_p5_full_config_diff.AUTHORIZED_P4_V4_EVIDENCE", authority):
                _authorized_p4_v4_evidence(evidence)
                for backend in ("recurrent", "ttt_fast_weight"):
                    for filename in ("request.json", "result.json", "verification.json"):
                        path = evidence / P4_V4_PREFLIGHT_RELATIVE / backend / filename
                        path.write_bytes(path.read_bytes() + b" ")
                subprocess.run(["git", "-C", str(evidence), "add", "."], check=True)
                subprocess.run(["git", "-C", str(evidence), "commit", "-qm", "joint replacement"], check=True)
                self.assertEqual(verify_pair({}, {}, evidence, exporter)["error"], "P4 v4 evidence HEAD is not the authorized exact commit")

        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "evidence"; evidence.mkdir(); self._v4_preflight(evidence)
            authority = self._authority(evidence)
            with patch("tools.g0.verify_r09_b2_p5_full_config_diff.AUTHORIZED_P4_V4_EVIDENCE", authority):
                subprocess.run(["git", "-C", str(evidence), "commit", "--allow-empty", "-qm", "descendant"], check=True)
                with self.assertRaisesRegex(ValueError, "authorized exact commit"):
                    _authorized_p4_v4_evidence(evidence)

        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "evidence"; evidence.mkdir(); self._v4_preflight(evidence)
            authority = self._authority(evidence)
            framework = evidence / "cosmos-framework"
            with patch("tools.g0.verify_r09_b2_p5_full_config_diff.AUTHORIZED_P4_V4_EVIDENCE", authority):
                subprocess.run(["git", "-C", str(framework), "commit", "--allow-empty", "-qm", "gitlink drift"], check=True)
                with self.assertRaisesRegex(ValueError, "submodule HEAD"):
                    _authorized_p4_v4_evidence(evidence)

        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "evidence"; evidence.mkdir(); self._v4_preflight(evidence)
            authority = self._authority(evidence)
            target = evidence / P4_V4_PREFLIGHT_RELATIVE / "recurrent" / "request.json"
            with patch("tools.g0.verify_r09_b2_p5_full_config_diff.AUTHORIZED_P4_V4_EVIDENCE", authority):
                target.write_bytes(target.read_bytes() + b" ")
                with self.assertRaisesRegex(ValueError, "blob does not match"):
                    _authorized_p4_v4_evidence(evidence)

        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "evidence"; evidence.mkdir(); self._v4_preflight(evidence)
            authority = self._authority(evidence)
            target = evidence / P4_V4_PREFLIGHT_RELATIVE / "recurrent" / "request.json"
            with patch("tools.g0.verify_r09_b2_p5_full_config_diff.AUTHORIZED_P4_V4_EVIDENCE", authority):
                target.unlink(); target.symlink_to("result.json")
                with self.assertRaisesRegex(ValueError, "current regular file"):
                    _authorized_p4_v4_evidence(evidence)

        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "evidence"; evidence.mkdir(); self._v4_preflight(evidence)
            authority = self._authority(evidence)
            exporter = self._exporter_worktree(root, Path(temp))
            (evidence / "untracked.txt").write_text("forbidden\n")
            with patch("tools.g0.verify_r09_b2_p5_full_config_diff.AUTHORIZED_P4_V4_EVIDENCE", authority):
                self.assertEqual(verify_pair({}, {}, evidence, exporter)["error"], "evidence_root and its cosmos-framework submodule must be full-clean")

    def test_v4_preflight_mutation_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp); self._v4_preflight(evidence)
            request = evidence / P4_V4_PREFLIGHT_RELATIVE / "recurrent" / "request.json"
            forged = json.loads(request.read_text()); forged["backend"] = "ttt_fast_weight"; request.write_bytes(canonical_bytes(forged))
            with self.assertRaises(ValueError):
                load_p4_v4_preflight(evidence)

    def test_v4_roster_rejects_unlisted_path(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp); self._v4_preflight(evidence)
            run = evidence / "run"; run.chmod(0o755)
            (run / "unexpected").write_text("forbidden\n")
            with self.assertRaises(ValueError):
                load_p4_v4_preflight(evidence)

    def test_v4_roster_rejects_missing_payload_path(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp); self._v4_preflight(evidence)
            run = evidence / "run"; run.chmod(0o755)
            staging = run / "import_staging" / ("a" * 64)
            staging.chmod(0o755)
            (staging / "payload.py").unlink()
            staging.chmod(0o555)
            self.assertEqual(staging.stat().st_mode & 0o777, 0o555)
            self.assertFalse((staging / "payload.py").exists())
            with self.assertRaisesRegex(ValueError, "roster-unlisted path"):
                load_p4_v4_preflight(evidence)


if __name__ == "__main__":
    unittest.main()
