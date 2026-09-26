# PSM-WMA V3 Upstream Bootstrap

Date: 2026-09-26

Status: BOOTSTRAPPED / upstream-native validation pending

## 2026-09-26 Stage A 显式 override

用户明确取消下面的 Nano P1 → Edge P2 顺序。当前 Stage A 是 **Cosmos3-Edge-Policy-DROID + upstream RoboCasa raw15 native baseline**。旧 Nano 描述仅保留为历史，不是当前启动依据。

- root：`/disk/rl/worktrees/psm_wma-v3`；child：`/disk/rl/worktrees/cosmos-framework-v3`，两者下的 child checkout 不同，运行必须使用后者；本轮不改 Gitlink、不提交。
- recipe：`action_policy_robocasa_edge`，基于 `EDGE_MODEL_CONFIG`，复用 upstream RoboCasa 数据/训练骨架，整体替换 Nano 模型配置。旧 smoke wrapper/TOML 原位替换，不增设第二套 launcher。
- 合同：`use_base_action=True / base_encoding=raw / raw_action_dim=15 / camera_set=left_wrist / use_state=True / fps=20 / chunk_length=32 / encode_exact_durations=[33] / action_normalization=None`。保留 64 维动作宽度、32 domains、ego20；不新增 head。
- DCP API 核对：`checkpoint/dcp.py` 的 warm-start 分支才传递 skip list；`CustomLoadPlanner` 在缺失键/尺寸校验之前按子串剔除 skip 项。因此 `strict_resume=True` 配合 `['net_ema.']` 保留并要求完整加载常规模型动作头，不沿用 Nano 的四项 action skips。当前 DCP 无 `action_pos_embed` 参数；不新增或跳过该参数。
- `net.action2llm.fc.weight / net.llm2action.fc.weight` 为 `[32,131072]`，对应 2048×64；bias 为 `[32,2048] / [32,64]`；动作 modality 为 `[2048]`。DROID policy 元信息维持 32chunk/15fps/droid_lerobot，fine-tune 数据为20fps。
- AdamW 通过当前 `weight_decay_skip_patterns` API 保护两组 action projections：RoboCasa domain30 之外的行不会因 weight decay 改变。其余优化器配置继承 upstream。
- WAM 视觉条件使用本地 Wan2.2 VAE，生成器投影从 DCP 加载，关闭 understanding→generation pretrained 覆盖。VLM tokenizer 经 `EDGE_POLICY_CHECKPOINT` 注入，`repository/revision=None`，本地 native Edge processor，不回退 Hub。此路线不启用 reasoner 的 SigLIP 理解视觉塔，不改框架视觉加载机制。
- launcher 不注入/清除 `HF_HUB_OFFLINE` 或 `TRANSFORMERS_OFFLINE`，完全继承调用方；本次 CPU 验证由调用方显式离线。
- 职责：ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。本轮不运行 GPU、不提交，不派发真实执行。

### 启动合同（命令供后续执行，本轮仅运行 config/CPU 检查）

```bash
cd /disk/rl/worktrees/cosmos-framework-v3
export EDGE_POLICY_CHECKPOINT=/disk/rl/models/Cosmos3-Edge-Policy-DROID
export BASE_CHECKPOINT_PATH=/disk/rl/models/Cosmos3-Edge-Policy-DROID-dcp
export WAN_VAE_PATH=/disk/rl/models/wan22_vae/Wan2.2_VAE.pth
export ROBOCASA_ROOT=/disk/rl/data/robocasa_v30
# 评测使用原始 v2.1，每个任务选定一份带 extras/dataset_meta.json 的 lerobot。
export ROBOCASA_EVAL_DATASET=/disk/rl/datasets/robocasa365/v1.0/target/atomic/CloseFridge/20250816/lerobot
# python 使用已具备 Cosmos 依赖的环境；SIM_PYTHON 使用仿真环境。
python examples/psm_wma_robocasa_native.py config --output-root outputs/psm_wma_v3_edge
python examples/psm_wma_robocasa_native.py train --steps 3 --output-root outputs/psm_wma_v3_edge
python examples/psm_wma_robocasa_native.py server --steps 3 --output-root outputs/psm_wma_v3_edge
python examples/psm_wma_robocasa_native.py eval --task CloseFridge --output-root outputs/psm_wma_v3_edge
```

`train --steps` 仅接受 1/2/3，GA=1、单 rank、batch=1；server 指向对应 DCP 与训练 `config.yaml`，raw15/20fps/chunk32；eval 固定 1ep/left_wrist/state/raw base。所有 stage 支持 `--print-command`，只预检和展示命令。输出：`<output-root>/psm_wma_v3/edge_robocasa/smoke/{config.yaml,checkpoints/iter_*}`、`<output-root>/server`、`<output-root>/eval/CloseFridge`。

CPU PASS 只证明配置、入口和合同，不能替代运行验证：训练需有限 loss、完成选定 step、生成可重载 DCP；server 需成功载入并返回有限的32×15动作；CloseFridge 需完成1ep并留存结果（success 单独记录，不将1ep视为统计验收）。缺资产/环境为 BLOCKED，合同、加载、非有限值或异常退出为 FAIL。

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
