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

P1 初审数据入口澄清：训练使用 `/disk/rl/data/robocasa_v30`；closed-loop eval 必须使用原始 v2.1 `/data/rl/datasets/robocasa365/v1.0/target/atomic/<task>/<date>/lerobot`，并包含 `extras/dataset_meta.json`，不得使用训练 v3.0 副本。

Nano tokenizer 来自 `Qwen/Qwen3-VL-8B-Instruct`，当前未证明缓存完整。glue 继承调用方环境，不强制设置 `HF_HUB_OFFLINE`/`TRANSFORMERS_OFFLINE`；ds 在获准联网时预热并验证缓存后，可以显式开启 offline。

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

用户 2026-09-26 最新角色 override：ChatGPT 负责设计、总体规划和审核；用户为项目 owner/最终裁决；tmux `cx`/Codex 负责生产代码实现及静态/CPU 检查；tmux `ds` 负责执行/测试。此条显式取代旧 GPT implement / cx reviewer 分工，cx 不启动训练/GPU。技术顺序保持 P1 upstream-native raw15 → P2 Edge raw15 Native → P3+ Local-TTT。
