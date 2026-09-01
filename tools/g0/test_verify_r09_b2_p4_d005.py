"""CPU-only permanent regressions for the P4 non-executable D005 verifier."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.g0.verify_r09_b2_p4_d005 import REQUIRED_ENV, RANK_ENV, _sha256_tree, verify_pair
from tools.g0.write_r09_b2_p4_d005 import finalize, membership_sha256, sha256_json


class P4D005Test(unittest.TestCase):
    def _git(self, cwd: Path, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()

    def _setup(self, root: Path) -> tuple[dict[str, object], dict[str, object]]:
        framework = root / "cosmos-framework"
        (framework / ".venv/bin").mkdir(parents=True)
        python = framework / ".venv/bin/python"; python.write_text("python"); python.chmod(0o755)
        (framework / "examples/toml/sft_config").mkdir(parents=True)
        (framework / "examples/toml/sft_config/action_policy_libero_edge_all.toml").write_text("x")
        for repo, message in ((framework, "sub"), (root, "root")):
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "test"], check=True)
        subprocess.run(["git", "-C", str(framework), "add", "."], check=True); subprocess.run(["git", "-C", str(framework), "commit", "-qm", "sub"], check=True)
        (root / "README").write_text("root")
        subprocess.run(["git", "-C", str(root), "add", "README"], check=True)
        subprocess.run(["git", "-C", str(root), "update-index", "--add", "--cacheinfo", f"160000,{self._git(framework, 'rev-parse', 'HEAD')},cosmos-framework"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "root"], check=True)
        for name in ("base", "edge", "vae", "libero", "stream", "cache"):
            (root / "assets" / name).mkdir(parents=True); (root / "assets" / name / "data").write_text(name)
        p1 = {"schema_version": "p1", "status": "PASS", "tiny_cpu_build": {"record_count": 1}}
        p3 = {
            "recurrent": {"inventory": {"selector": {"keys_to_select": ["net"]}, "model_parameters": [{"name": "net.a", "selected_by_optimizer": True}]}},
            "ttt_fast_weight": {"inventory": {"selector": {"keys_to_select": ["ttt"]}, "model_parameters": [{"name": "ttt.a", "selected_by_optimizer": True}]}},
        }
        return p1, p3

    def _asset(self, path: Path) -> dict[str, str]:
        return {"path": str(path), "realpath": str(path.resolve()), "sha256": _sha256_tree(path.resolve())}

    def _record(self, root: Path, p1: dict[str, object], p3: dict[str, object], backend: str) -> dict[str, object]:
        framework = root / "cosmos-framework"; python = framework / ".venv/bin/python"; output = root / "future" / backend
        source = {"root_revision": self._git(root, "rev-parse", "HEAD"), "root_clean": True, "submodule_revision": self._git(framework, "rev-parse", "HEAD"), "submodule_clean": True, "gitlink_revision": self._git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2]}
        paths = {"PSM_R09_B2_STREAM_MANIFEST_ROOT": "stream", "LIBERO_LATENT_CACHE_ROOT": "cache", "LIBERO_ROOT": "libero", "BASE_CHECKPOINT_PATH": "base", "EDGE_POLICY_CHECKPOINT": "edge", "WAN_VAE_PATH": "vae", "PYTHONPATH": "cosmos-framework", "IMAGINAIRE_OUTPUT_ROOT": f"future/{backend}"}
        values = {key: value if value is not None else str(root / "assets" / paths[key]) if key in paths else str(root / paths[key]) for key, value in REQUIRED_ENV.items()}
        values["PYTHONPATH"] = str(framework); values["IMAGINAIRE_OUTPUT_ROOT"] = str(output); values["PSM_R09_B1_TTT_ENABLED"] = "1" if backend == "ttt_fast_weight" else "0"
        env = {"set": values, "unset": sorted(RANK_ENV), "inherit_allowlist": []}; env["sha256"] = sha256_json(env)
        assets = {"base_checkpoint": self._asset(root / "assets/base"), "edge_processor": self._asset(root / "assets/edge"), "wan_vae": self._asset(root / "assets/vae"), "libero_root": self._asset(root / "assets/libero"), "stream_manifest": self._asset(root / "assets/stream"), "latent_cache": self._asset(root / "assets/cache"), "interpreter": self._asset(python)}
        inputs = {"p1_manifest": {"sha256": sha256_json(p1), "record_count": 1}, "p3_inventory": {"sha256": sha256_json(p3), "backend_contract": {"selector_keys": p3[backend]["inventory"]["selector"]["keys_to_select"], "optimizer_membership_sha256": membership_sha256(p3, backend)}}, "external_assets": assets}
        command = {"cwd": str(framework.resolve()), "interpreter": {"realpath": str(python.resolve()), "sha256": _sha256_tree(python)}, "argv": [str(python.resolve()), "-m", "torch.distributed.run", "--standalone", "--nnodes=1", "--nproc-per-node=1", "-m", "cosmos_framework.scripts.train", "--sft-toml=examples/toml/sft_config/action_policy_libero_edge_all.toml", "trainer.max_iter=100", "trainer.save_zero_checkpoint=true"], "executable": False, "launcher": {"kind": "python_module", "module": "torch.distributed.run"}}
        command["sha256"] = sha256_json(command)
        identity = {"project": "p", "group": "g", "name": backend}; run_root = output / "p/g" / backend
        return finalize({"schema_version": "r09_b2_p4_launch_d005_v1", "status": "FROZEN_NOT_EXECUTED", "backend": backend, "source": source, "command": command, "environment": env, "budget": {"world_size": 1, "micro_batch_size": 1, "grad_accum_steps": 1, "global_batch_size": 1, "samples_per_update": 1, "optimizer_updates": 100}, "inputs": inputs, "outputs": {"job_identity": identity, "run_root": str(run_root), "checkpoint_step0": str(run_root / "checkpoints/iter_000000000"), "checkpoint_step100": str(run_root / "checkpoints/iter_000000100"), "stdout_log": str(run_root / "stdout.log"), "capture_dir": str(run_root / "capture"), "fresh": True}})

    def _pair(self, root: Path):
        p1, p3 = self._setup(root)
        return self._record(root, p1, p3, "recurrent"), self._record(root, p1, p3, "ttt_fast_weight"), p1, p3

    def test_valid_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, p1, p3 = self._pair(root)
            self.assertEqual(verify_pair(recurrent, ttt, root, p1, p3)["status"], "PASS")

    def test_rejects_argv_and_interpreter_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, p1, p3 = self._pair(root)
            recurrent["command"]["argv"].append("trainer.max_iter=5000")
            self.assertEqual(verify_pair(finalize(recurrent), ttt, root, p1, p3)["status"], "FAIL")
            recurrent, ttt, p1, p3 = self._pair(root / "two")
            recurrent["command"]["interpreter"]["realpath"] = "/bin/sh"
            self.assertEqual(verify_pair(finalize(recurrent), ttt, root / "two", p1, p3)["status"], "FAIL")

    def test_rejects_env_p3_provenance_and_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, p1, p3 = self._pair(root)
            del recurrent["environment"]["set"]["LIBERO_LATENT_CACHE_ROOT"]
            self.assertEqual(verify_pair(finalize(recurrent), ttt, root, p1, p3)["status"], "FAIL")
            recurrent, ttt, p1, p3 = self._pair(root / "two")
            p3["recurrent"]["inventory"]["model_parameters"][0]["selected_by_optimizer"] = False
            self.assertEqual(verify_pair(recurrent, ttt, root / "two", p1, p3)["status"], "FAIL")
            recurrent, ttt, p1, p3 = self._pair(root / "three")
            recurrent["source"]["gitlink_revision"] = "bad"
            self.assertEqual(verify_pair(finalize(recurrent), ttt, root / "three", p1, p3)["status"], "FAIL")
            recurrent, ttt, p1, p3 = self._pair(root / "four")
            Path(recurrent["outputs"]["run_root"]).mkdir(parents=True)
            self.assertEqual(verify_pair(recurrent, ttt, root / "four", p1, p3)["status"], "FAIL")

    def test_rejects_disallowed_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); recurrent, ttt, p1, p3 = self._pair(root)
            recurrent["environment"]["set"]["IMAGINAIRE_OUTPUT_ROOT"] = "/tmp/not_allowlisted"
            recurrent["environment"]["sha256"] = sha256_json({key: recurrent["environment"][key] for key in ("set", "unset", "inherit_allowlist")})
            self.assertEqual(verify_pair(finalize(recurrent), ttt, root, p1, p3)["status"], "FAIL")
