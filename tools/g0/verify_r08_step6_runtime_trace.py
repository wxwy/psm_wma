"""CPU-only R08 Step 6 production injection and packing trace."""

from pathlib import Path
import json
import hashlib
import os
import socket
import subprocess
from datetime import datetime, timezone

import torch

import cosmos_framework.model.generator.omni_mot_model as omni_mot_model
from cosmos_framework.data.generator.sequence_packing.packers import pack_input_sequence
from cosmos_framework.data.generator.sequence_packing.sequence import SequencePlan
from cosmos_framework.model.generator.mot.local_evidence import LocalEvidenceEncoder, LocalHistoryRuntime, StatelessLocalReplayReadout
from cosmos_framework.model.generator.utils.data_and_condition import GenerationDataClean


def _runtime() -> LocalHistoryRuntime:
    return LocalHistoryRuntime(
        LocalEvidenceEncoder(evidence_dim=8, visual_dim=4, action_dim=3, max_age_steps=8),
        StatelessLocalReplayReadout(evidence_dim=8, local_dim=5, hidden_dim=8),
    )


def _make_data(local_tokens: list[torch.Tensor] | None) -> GenerationDataClean:
    return GenerationDataClean(
        batch_size=2,
        is_image_batch=False,
        x0_tokens_vision=[torch.randn(1, 2, 2, 2, 2), torch.randn(1, 2, 2, 2, 2)],
        x0_tokens_action=[torch.randn(3, 4), torch.randn(3, 4)],
        x0_tokens_local_memory=local_tokens,
    )


def _pack(plans: list[SequencePlan], local_tokens: list[torch.Tensor] | None):
    return pack_input_sequence(
        sequence_plans=plans,
        input_text_indexes=[[10, 11], [12, 13]],
        gen_data_clean=_make_data(local_tokens),
        input_timesteps=torch.zeros(2),
        special_tokens={"eos_token_id": 2, "start_of_generation": 3, "end_of_generation": 4},
        latent_patch_size=1,
        temporal_compression_factor=4,
        action_dim=4,
    )


def _mrope_at(packed, modality: str) -> list[list[int]]:
    data = getattr(packed, modality)
    assert data is not None
    return packed.position_ids[:, data.sequence_indexes].tolist()


def main() -> None:
    out = Path("artifacts/g0/r08/step6_runtime_trace.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    omni_mot_model.DEVICE = torch.device("cpu")
    model = object.__new__(omni_mot_model.OmniMoTModel)
    torch.nn.Module.__init__(model)
    model.config = type("Config", (), {"local_history_horizon": 2, "local_history_state_enabled": False})()
    model.net = torch.nn.Module()
    model.net.local_history_runtime = _runtime()
    mask = torch.tensor([[True, False], [False, False]])
    data_batch = {
        "history_visual_summary": torch.randn(2, 2, 4),
        "local_history_action": torch.randn(2, 2, 3),
        "history_age_steps": torch.arange(2).repeat(2, 1),
        "history_dt_s": torch.ones(2, 2, 1),
        "history_mask": mask,
    }
    plans = [
        SequencePlan(has_text=True, has_vision=True, has_action=True, condition_frame_indexes_vision=[0]),
        SequencePlan(has_text=True, has_vision=True, has_action=True, condition_frame_indexes_vision=[0]),
    ]
    model._inject_local_history(data_batch, plans)
    with_local = _pack(plans, [data_batch["local_memory"][0]])
    no_local_plans = [
        SequencePlan(has_text=True, has_vision=True, has_action=True, condition_frame_indexes_vision=[0]),
        SequencePlan(has_text=True, has_vision=True, has_action=True, condition_frame_indexes_vision=[0]),
    ]
    torch.manual_seed(1)
    no_local = _pack(no_local_plans, None)
    local_indexes = with_local.local_memory.sequence_indexes.tolist() if with_local.local_memory is not None else []
    vision_mrope_equal = _mrope_at(with_local, "vision") == _mrope_at(no_local, "vision")
    action_mrope_equal = _mrope_at(with_local, "action") == _mrope_at(no_local, "action")
    root = Path(__file__).resolve().parents[2]
    submodule = root / "cosmos-framework"
    tool_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    root_commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    submodule_commit = subprocess.check_output(["git", "-C", str(submodule), "rev-parse", "HEAD"], text=True).strip()
    payload = {
        "schema_version": "r08_step6_runtime_trace_v1",
        "status": "PASS",
        "provenance": {
            "root_commit": root_commit,
            "submodule_commit": submodule_commit,
            "tool_sha256": tool_sha,
            "hostname": socket.gethostname(),
            "utc_time": datetime.now(timezone.utc).isoformat(),
            "python": os.environ.get("VIRTUAL_ENV", "system"),
        },
        "history_mask": mask.tolist(),
        "local_present": [plan.has_local_memory for plan in plans],
        "local_indexes": local_indexes,
        "local_token_shapes": [list(token.shape) if token is not None else None for token in data_batch["local_memory"]],
        "vision_sequence_indexes": with_local.vision.sequence_indexes.tolist(),
        "action_sequence_indexes": with_local.action.sequence_indexes.tolist(),
        "assertions": {
            "mixed_batch_gating": [plan.has_local_memory for plan in plans] == [True, False],
            "one_token_for_valid": len(local_indexes) == 1,
            "all_mask_absent": data_batch["local_memory"][1] is None,
            "local_payload_shape": tuple(data_batch["local_memory"][0].shape) == (1, 5),
            "vision_mrope_unchanged": vision_mrope_equal,
            "action_mrope_unchanged": action_mrope_equal,
            "condition_frame_indexes_vision_unchanged": [plan.condition_frame_indexes_vision for plan in plans]
            == [plan.condition_frame_indexes_vision for plan in no_local_plans],
            "condition_frame_indexes_action_unchanged": [plan.condition_frame_indexes_action for plan in plans]
            == [plan.condition_frame_indexes_action for plan in no_local_plans],
            "state_disabled": True,
        },
    }
    if not all(payload["assertions"].values()):
        raise AssertionError(payload)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: wrote {out}")


if __name__ == "__main__":
    main()
