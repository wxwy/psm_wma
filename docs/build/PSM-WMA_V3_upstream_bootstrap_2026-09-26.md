# PSM-WMA V3 Upstream Bootstrap

Date: 2026-09-26

Status: BOOTSTRAPPED / upstream-native validation pending

## Frozen branches

Historical baseline remains frozen:

- root: `V2`
- child: `wxwy/cosmos-framework:v2`

V3 work must not modify either branch.

## V3 branches

Root:

- `wxwy/psm_wma:V3`

Child:

- `wxwy/cosmos-framework:v3-local-ttt`

The child branch was created directly from NVIDIA upstream and initially contains no V2 Local-TTT changes.

## Pinned upstream baseline

Repository:

`NVIDIA/cosmos-framework`

Pinned release:

`release/2026-09-25-358182a3`

Pinned commit:

`850fdbeacddabad138ed56df39cd6fb96e975078`

The first V3 root Gitlink points exactly to that commit.

This commit already contains NVIDIA's RoboCasa support, including:

- RoboCasa LeRobot dataset;
- raw15 and ego20 action contracts;
- official RoboCasa post-training config;
- closed-loop RoboCasa evaluator;
- 10D/15D/20D env-action decoders.

## V3 construction order

P0. Upstream bootstrap and provenance lock.

P1. Run upstream-native RoboCasa raw15 smoke with no Local-TTT modifications.

P2. Establish Edge raw15 Native baseline on the upstream framework.

P3. Port Local-TTT algorithm core with action-dimension-agnostic interfaces.

P4. Add raw15 Local-TTT evidence (`visual96 + executed_action15`).

P5. Port online Local-TTT session / fast-state lifecycle.

P6. Integrate Local-TTT into the official RoboCasa closed-loop path without replacing official simulation semantics.

P7. Reintroduce selected V2 engineering capabilities only after Native and Local-TTT regressions are clean: latent cache, resume, parallel eval, video/profiling/diagnostics.

## RGB / state contract

The current upstream RoboCasa recipe already matches the main V2 visual contract:

- `camera_set=left_wrist`;
- `agentview_left | eye_in_hand`;
- source composite `256x512`;
- `resolution=None` auto-transform to the 256-tier wide bucket;
- `use_state=True`, EEF 10D state conditioning padded to the action width.

Multi-camera variants are not a V3 bootstrap priority.

## GPU smoke rule

The connected validation host currently reports an A100 80GB, but the user explicitly fixed the V3 smoke budget to `GA=1`.

Any V3 training smoke must therefore set gradient accumulation to 1 (`GA=1`) regardless of detected GPU capacity unless the user explicitly changes this constraint.

A smoke may reduce batch size, action/video decode, number of steps, and dataset coverage, but it must not silently change the action contract being validated.

## Assistant roles

The tmux `ds` session is an execution/validation assistant only.

Allowed:

- inspect environment and dependencies;
- clone/fetch/checkout the formal V3 branches;
- run static tests and smoke jobs;
- collect logs, JSON, profiler output, and artifacts;
- report failures and evidence.

Forbidden:

- edit or commit production source;
- modify root Gitlink;
- patch launchers/configs/tests in place;
- merge or rebase V3.

All production code changes are owned by GPT/ChatGPT.

The tmux `cx` session is an independent reviewer only. It reviews GPT/ChatGPT formal diffs and tests, and cross-checks ds runtime evidence. It must not edit or commit production files, move branches/Gitlinks, or launch training.
