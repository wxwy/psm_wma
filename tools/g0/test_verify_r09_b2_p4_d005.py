"""CPU-only permanent regressions for the P4 non-executable D005 verifier."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.g0.verify_r09_b2_p4_d005 import verify_pair
from tools.g0.write_r09_b2_p4_d005 import finalize


class P4D005Test(unittest.TestCase):
    def _record(self, root: Path, backend: str) -> dict[str, object]:
        framework = root / "cosmos-framework"
        (framework / "examples/toml/sft_config").mkdir(parents=True, exist_ok=True)
        (framework / "examples/toml/sft_config/action_policy_libero_edge_all.toml").write_text("x")
        python = framework / "python"
        python.write_text("python")
        output = root / "future" / backend
        identity = {"project": "p", "group": "g", "name": "n"}
        return finalize({"schema_version": "r09_b2_p4_launch_d005_v1", "status": "FROZEN_NOT_EXECUTED", "backend": backend, "source": {"x": 1}, "command": {"cwd": str(framework.resolve()), "interpreter": {"realpath": str(python)}, "argv": [str(python), "-m", "torch.distributed.run", "--standalone", "--nnodes=1", "--nproc-per-node=1", "-m", "cosmos_framework.scripts.train", "--sft-toml=examples/toml/sft_config/action_policy_libero_edge_all.toml", "trainer.max_iter=100", "trainer.save_zero_checkpoint=true"], "executable": False, "launcher": {"kind": "python_module"}}, "environment": {"set": {"PSM_R09_B1_TTT_ENABLED": "1" if backend == "ttt_fast_weight" else "0", "LIBERO_NUM_WORKERS": "0", "CUDA_VISIBLE_DEVICES": "0", "IMAGINAIRE_OUTPUT_ROOT": str(output)}, "unset": [], "inherit_allowlist": []}, "budget": {"world_size": 1, "optimizer_updates": 100}, "inputs": {"x": 1}, "outputs": {"job_identity": identity, "run_root": str(output / "p/g/n"), "checkpoint_step0": str(output / "p/g/n/checkpoints/iter_000000000"), "checkpoint_step100": str(output / "p/g/n/checkpoints/iter_000000100")}})

    def test_valid_and_negative_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            recurrent, ttt = self._record(root, "recurrent"), self._record(root, "ttt_fast_weight")
            self.assertEqual(verify_pair(recurrent, ttt, root)["status"], "PASS")
            ttt["command"]["cwd"] = str(root)
            self.assertEqual(verify_pair(recurrent, finalize(ttt), root)["status"], "FAIL")

    def test_rejects_bare_launcher_and_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            recurrent, ttt = self._record(root, "recurrent"), self._record(root, "ttt_fast_weight")
            recurrent["command"]["argv"][0] = "torchrun"
            self.assertEqual(verify_pair(finalize(recurrent), ttt, root)["status"], "FAIL")
            recurrent = self._record(root, "recurrent")
            Path(recurrent["outputs"]["run_root"]).mkdir(parents=True)
            self.assertEqual(verify_pair(recurrent, ttt, root)["status"], "FAIL")
