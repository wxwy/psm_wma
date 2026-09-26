# V3-STAGE-A-EDGE-RAW15 closure review

- Gate: `V3-STAGE-A-EDGE-RAW15`
- Formal implementation root: `fb6a72c11aa5e7888b9425bb4a50817eab95e10c`
- Formal child/Gitlink: `196b93b70b579023ef008030b0c18a6fde353c82`
- Closure-request bookkeeping root: `8ff08edd350fc49df3d6ae60e549fa188b1928cd` (not a formal implementation target)
- Reviewer: ChatGPT
- Verdict: `APPROVE_TO_CLOSE_V3_STAGE_A_EDGE_RAW15`

## Review scope

This is the final closure review for the upstream-2026-09-25 + `nvidia/Cosmos3-Edge-Policy-DROID` + RoboCasa raw15 native integration Gate only. V2/v2 remain frozen references. No Local-TTT implementation, long-run training, benchmark capability, or task-success claim is in scope.

The new child delta relative to the previously reviewed pair is restricted to the RoboCasa action-server guardrail switch, the PSM-WMA wrapper flag, and CPU contract tests. The Edge recipe, training TOML, dataloader/action contract, raw15/ego20 semantics, checkpoint training path, and common inference implementation are unchanged.

## Contract verification

The reviewed implementation preserves the frozen RoboCasa action contract:

- `use_base_action=True`
- `base_encoding="raw"`
- `raw_action_dim=15`
- `camera_set="left_wrist"`
- `use_state=True`
- `fps=20`
- `chunk_length/action_horizon=32`
- `action_normalization=None`

The action server now exposes the already-existing common `guardrails` setup value with default `True`. The PSM-WMA action-only wrapper explicitly supplies `--no-guardrails`; common inference and its default guardrail behavior are not changed.
## Evidence

Canonical runtime evidence is recorded under:

`artifacts/v3/stage_a_edge_raw15_run02/STAGE_A_FINAL_EVIDENCE.md`

Evidence digest at review time:

`4589108cd1f761259c3650f2b6e45d79e89dad896498e4bd0f3800e9bfb1e877`

Verified evidence includes:

1. Exact pair lock: root `fb6a72c1...`, child/Gitlink `196b93b7...`, tracked production trees clean.
2. V3-environment contract tests: `26/26 PASS`, `skipped=0`, including local Edge assets, DCP planner, raw15/ego20 regression, guardrails default, and `--no-guardrails` production CLI parsing.
3. Edge raw15 one-step training evidence retained because the guardrail pair does not change the training recipe/TOML; TOML SHA-256 is unchanged.
4. One-step training completed with finite loss/gradient and a complete DCP checkpoint.
5. Formal wrapper-launched action server loaded the exact iter-1 DCP and reported `raw_action_dim=15`, `action_chunk_size=32`, `fps=20`, `requires_state=true`, and `action_stats_path=null`.
6. Formal RoboCasa closed loop used the original official v2.1 `CloseFridge` dataset and ran the full official horizon: exit code `0`, one episode, `900` simulator steps, `29` policy requests, with rollout MP4/result artifacts present.
7. All 29 action dumps have chunk length `32`, action width `15`, zero NaN/Inf, and corresponding request state width `15`.
8. The rollout result is `0/1` success. This is a capability result after only one training update, not a transport/model-I/O/action-shape/runtime failure.

## Findings

No current implementation or Evidence blocker remains for this Gate.

The `0/1` task success result is explicitly **not** approved as a task-capability claim. The Gate proves that the current Edge-Policy-DROID RoboCasa raw15 train -> checkpoint -> server -> simulator closed-loop pipeline is operational and contract-consistent. It does not prove that the policy is trained sufficiently to solve RoboCasa tasks.

Existing upstream Ruff/format debt in `action_policy_server_robocasa.py` predates this Gate and is not introduced by the reviewed delta; the reviewed change did not expand scope to reformat unrelated upstream code.
## Scope boundary

`APPROVE_TO_CLOSE_V3_STAGE_A_EDGE_RAW15`

This verdict closes only `V3-STAGE-A-EDGE-RAW15` at the exact formal pair above. It does **not** authorize or approve:

- RoboCasa task capability or non-zero SR,
- a longer native training run,
- Local-TTT / persistent-memory migration,
- checkpoint/resume semantics for Local-TTT,
- global-memory/agent/RSI work,
- any V2/v2 modification,
- any later V3 Gate.

Any later implementation/design pair requires its own Gate and fresh review.