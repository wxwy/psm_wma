# R09 Local Backend Preflight Runbook v0.1

**状态**：REVIEW；仅计划，未授权实现或 GPU。  
**前置**：R08 Gate B 已三方关闭；输入仅为 R08 `LocalEvidenceBatch`，不得重读 raw RGB/parquet 或改变时间对齐。

## 固定边界

- A 先于 B：A/B 共用 `LocalMemoryBackend.step(evidence_t, state_in) -> (state_out, token, local_present)`、`reset_mask(state, done[B])`（仅 `done=true` 样本归零，其他样本逐元素不变）与全 reset；all-mask/no-valid-evidence 绝不隐式触发 reset。仅替换 temporal compressor。
- 首轮不做跨 batch/worker/episode 隐式携带；每 sample/window 从 `M_start=zeros` 开始，并在同一协议下测试两段 segment 的 state carry + graph detach。禁止每个 evidence step detach；只允许 segment 边界 detach，且只在 episode/sample reset 时 reset。
- 不改 Cosmos shared MoT、native vision/action loss、R08 encoder、Local token budget、canonical checkpoint 或训练范围。
- 禁止 GPU、长训、多卡、matched SR、backend freeze，直到本 runbook 三方审核通过。

## R09-A0：CPU contract（最小实现前）

复用 `LocalEvidenceEncoder`，新增独立 recurrent compressor 与现有 Local readout 的最小适配。输入 `evidence[B,H,D_e]`、`mask[B,H]`；输出 `tokens`（仅 `local_present=true` 的样本各一个 `[1,D_local]` token）、`local_present[B]`、可审计 state。mixed batch 必须证明有效样本恰有一个可 pack token，all-mask 样本真正 absent/not packed；masked/padded timestep 不得改变 state。断言包括 finite、固定 seed 确定性、batch permutation isolation、mixed-batch partial-reset（完成样本归零且其余不变）、full-window 与 two-segment carry+detach 数值等价。等价以 `max_abs_diff <= 1e-6`（state 与 token；carried value detach 前后 exact）判定。仅定义 Normal/Zero/Shuffle；Stale/Truncated 延后另审。

真实生产初始化也属于 A0：覆盖 meta -> `to_empty` -> 显式 fixed-seed init（或经审计的 post-materialization attach），并断言所有 Local 参数 finite 且同 seed 逐元素确定。`artifacts/g0/r09/a0_contract.json` 固定包含 schema_version、root/submodule/Gitlink、双仓 tracked-clean、backend、state shape/dtype/bytes、输入输出 shapes、trainable param count/prefixes、init seed/path/meta-init、各 assertion bool、mixed presence/partial-reset、segment state/token max_abs_diff+tolerance+PASS、tool/command hash。

## R09-A1：单卡 fwd/bwd smoke（待审核后）

固定 Gate-A canonical checkpoint、同一批次和 R08 history schema。A1 实施时唯一允许 optimizer object/prefix 为 `net.local_history_runtime.encoder.*`、`net.local_history_runtime.recurrent_backend.*`、`net.local_memory2llm.*`、`net.local_memory_modality_embed`；其中 `recurrent_backend` 是 A0 backend 接入 runtime 后的精确 production 名称。R08 `StatelessLocalReplayReadout` 在 R09 backend 启用时不在 forward/loss graph，必须冻结且不得进入 optimizer。native Vision/Action/state adapters、shared Cosmos 参数及其他所有参数均排除。probe 必须直接枚举 optimizer object IDs/names，并硬断言其精确等于 allowlist 展开集；冻结参数排除在 optimizer 外，step 前后逐参数证明未变化。记录 100 optimizer steps 的 finite loss、每个 selected Local gradient、peak VRAM、step latency、attached production backend 的 state bytes 与 segment detach/reset。FAIL：任何 NaN、跨 episode/batch 泄漏、冻结参数进入 optimizer 或变化、optimizer 集合不等于 allowlist、干预改变 packing/index，或无 nonzero future/action sensitivity。产物：`R09_local_backend_selection_smoke.json`。多卡仍由 DCP-MULTIRANK 与独立 FSDP/local-state smoke 阻塞。

## R09-B：TTT fast-weight（A 通过后另审）

仅替换 A 的 temporal compressor，保持上述 state protocol、schema、token budget、batch、checkpoint、loss 与 trainable scope 完全相同。额外断言：fast state 每 episode 实际有限更新；segment 边界数值连续而 autograd graph detach；reset 正确；fast state 不进入 slow-weight optimizer/checkpoint。不得把 RoboTTT 原结构插入 shared MoT。

## 审核/推进

本 v0.1 审核通过后只执行 A0；A0 单独送审后才执行 A1；A1 三方通过后才提出 B 的实施申请。backend 选择不得由短跑 SR 决定，比较 future/action sensitivity、稳定性、状态保持、VRAM/latency 与 state-management 成本。
