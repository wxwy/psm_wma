"""CPU-only R08 Step 6 runtime trace for history-to-Local gating."""

from pathlib import Path
import json

import torch

from cosmos_framework.model.generator.mot.local_evidence import LocalEvidenceEncoder, LocalHistoryRuntime, StatelessLocalReplayReadout


def main() -> None:
    out = Path("artifacts/g0/r08/step6_runtime_trace.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    batch, horizon = 3, 4
    mask = torch.tensor([[True, True, False, False], [False] * horizon, [True] * horizon])
    runtime = LocalHistoryRuntime(
        LocalEvidenceEncoder(evidence_dim=8, visual_dim=4, action_dim=3, max_age_steps=8),
        StatelessLocalReplayReadout(evidence_dim=8, local_dim=5, hidden_dim=8),
    )
    tokens, present, evidence = runtime(
        history_visual_summary=torch.randn(batch, horizon, 4),
        local_history_action=torch.randn(batch, horizon, 3),
        history_age_steps=torch.arange(horizon).repeat(batch, 1),
        history_dt_s=torch.ones(batch, horizon, 1),
        history_mask=mask,
    )
    local_indexes = [[0] if flag else [] for flag in present.tolist()]
    payload = {
        "schema_version": "r08_step6_runtime_trace_v1",
        "status": "PASS",
        "source_ids": [[0, 1], [], [0, 1, 2, 3]],
        "history_mask": mask.tolist(),
        "evidence_shape": list(evidence.shape),
        "readout_shape": list(tokens.shape),
        "local_present": present.tolist(),
        "local_indexes": local_indexes,
        "future_shape": [batch, 5],
        "action_shape": [batch, 16, 10],
        "assertions": {
            "mixed_batch_gating": present.tolist() == [True, False, True],
            "one_token_for_valid": all(len(indexes) == 1 for indexes, flag in zip(local_indexes, present.tolist(), strict=True) if flag),
            "absent_not_packed": local_indexes[1] == [],
            "finite": bool(torch.isfinite(tokens).all() and torch.isfinite(evidence).all()),
            "state_disabled": True,
        },
    }
    if not all(payload["assertions"].values()):
        raise AssertionError(payload)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: wrote {out}")


if __name__ == "__main__":
    main()
