"""Public CLI Fresh/Resume, real input/source identity and native CPU Slot loop."""
# ruff: noqa: F811 -- pytest resolves imported fixture names.

import json

import pytest
import yaml
from robocasa_eval_v2 import identity
from tools.v3.eval_v2_production_tests.runtime_evidence_test import (
    real_prepare as real_prepare,
    public,
    core_bytes,
)
from tools.v3.eval_v2_streaming_tests.capacity_test import streaming_config
from tools.v3.eval_v2_streaming_tests.pipeline_test import Pipeline, Router
from tools.v3.eval_v2_production_tests.native_test import native
from cosmos_framework.inference.robocasa_session_transactions_test import (
    clock_kernel as clock_kernel,
)  # noqa: F401


def test_public_streaming_cli_fresh_resume_and_protocol_change_rejected(
    real_prepare, monkeypatch
):
    case = real_prepare
    case.cfg.update(
        streaming_config(gpu_ids=[6], sims_per_gpu=2, max_infer_batch_size=2),
        local_memory_mode="off",
        render_backend="osmesa",
        render_gpu_ids=[],
        save_rollout_mp4=False,
        save_generated_video="none",
    )
    case.path.write_text(yaml.safe_dump(case.cfg))
    monkeypatch.setattr(native, "build_state_token", lambda _: [0.0] * 15)
    monkeypatch.setattr(
        "robocasa_eval_v2.runtime.group_members", lambda pgid: {pgid: "S"}
    )
    monkeypatch.setattr(
        identity, "clock_environment", lambda *a: {"domain": "CPU-double"}
    )

    class NativeRuntime(Pipeline):
        def __init__(self, store, cfg, inputs, environment):
            super().__init__(store, cfg, monkeypatch, inputs, environment)
            monkeypatch.setattr("requests.Session", lambda: Router(self))

    case.Runtime = NativeRuntime
    assert public(case, "fresh") == 0
    manifest = json.loads((case.root / "manifest.json").read_bytes())
    assert manifest["protocol"]["schedule"] == case.cfg["scheduling_protocol"]
    original = core_bytes(case.root)
    assert len(list(case.root.glob("tasks/*/episodes/*/result.json"))) == 2
    assert public(case, "resume") == 0
    assert core_bytes(case.root) == original
    case.cfg["sims_per_gpu"] = 4
    case.path.write_text(yaml.safe_dump(case.cfg))
    with pytest.raises(ValueError, match="immutable"):
        public(case, "resume")
    assert core_bytes(case.root) == original
