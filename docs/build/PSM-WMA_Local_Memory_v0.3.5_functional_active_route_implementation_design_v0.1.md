# Local Memory v0.3.5 Functional Active-Route Implementation 设计 v0.1

**日期**：2026-09-16
**Gate**：`G0-R09-B-TTT-V035-FUNCTIONAL-ACTIVE-ROUTE-IMPLEMENTATION`
**性质**：docs-only 设计；由用户 2026-09-16 明确授权的「功能优先」路线驱动。
**目标**：按 v0.3.5 segment-level Local Memory 路线实现真实数据侧 producer/packer ABI、
trainer driver 与训练配置启用，最终在 `/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1`
latent cache 上启动训练。

---

## 1. 授权依据与对既有冻结链的显式偏离

用户于 2026-09-16 通过显式决策授权「功能优先」路线：实现真实的
`_run_active_local_memory_native_forward`、数据侧 canonical local-memory producer/packer ABI
与训练 toml 启用；provenance（source-evidence / authority root）降级为并行或训练后补。

本设计**显式偏离** `PSM-WMA_Local_Memory_v0.3.5_canonical_native_production_runtime_integration_design_v0.2.md`
§2 冻结的 12 段不可跳过 Gate 顺序，以及其 §4「下一份实现不得执行真实 data/cache/checkpoint I/O、
真实 native forward/loss/backward、CUDA/GPU、torchrun、训练」的边界。依据：

- 该 §2 要求每个箭头都取得 ChatGPT/MM/DS **三方同 SHA** closure；而 MM 已被用户剔除、
  ChatGPT 为 advice-only，实际可用的第三方审核者只剩 DS。既有 Stage-1 request-pair 子链
  （TODO #194–#217）在同一审核结构下连续 19 次未收敛，最近一次真实运行死在 bootstrap
  interpreter identity guard。按该顺序，目标在有限时间内不可达。
- AGENTS.md §151 规定 Codex 是构建者、执行者与最终技术决策主体；本偏离的依据在此记录。
- AGENTS.md §160 的「持续目标不构成绕过闭锁的理由」针对的是**无凭证自行推进**；本设计并非
  无凭证推进，而是依据用户当日给出的**显式新授权**，并在此完整披露偏离范围。

**偏离不等于静默混用。** v0.3.5 第 12 行禁止的是把旧 row-wise `TTTLifecycle` 路线
（`1 micro-batch = 1 evidence row` / closing-row witness-materialization）与 segment-level
路线混用。本设计**只**推进 segment-level 路线，不启用 `_ttt_local_memory_tokens()` /
`TTTLifecycle`；`local_ttt_enabled=True` 下 ordinary route 继续 fail-closed（见 §4.3）。

---

## 2. 权威路线确认

唯一目标路线是 **canonical segment 族**，其组件分布在：

| 层 | 组件 | 位置 |
|---|---|---|
| 算法 core | `ContinualTTTLocalMemoryCore.scan_segment_masked_encoded_many` | `model/generator/mot/local_evidence.py:717` |
| evidence 编码 | `LocalEvidenceEncoder.encode_segment` | `model/generator/mot/local_evidence.py:144` |
| segment ABI | `SegmentBatch` / `SegmentIdentity` / `GAWindowPlan` / `LocalMemoryTransaction` / `RankLocalSegmentScheduler` | `model/generator/mot/local_memory_segment.py` |
| adapter | `CanonicalLocalMemorySegmentAdapter` / `LocalMemorySegmentSidecar` | `model/generator/mot/local_memory_segment_adapter.py:49,23` |
| runtime owner | `CanonicalSegmentRuntimeOwner` | `model/generator/mot/canonical_segment_runtime.py:38` |
| active registry | `ProductionActiveWiringRegistry` / `ActiveNativeBatchInputs` | `model/generator/mot/production_active_wiring.py:58,21` |
| model 侧 | `training_step` active 分派 + `_run_active_local_memory_native_forward` | `model/generator/omni_mot_model.py:1590,1419` |
| trainer 侧 | `arm_active_local_memory_initial/continuation/retry`、`_run_active_local_memory_backward`、`bind_active_local_memory_registry` | `trainer/__init__.py:709,728,743,911,764` |
| Memory Prefix | `packers.py:246` → `PackedSequence.local_memory_prefix` → `cosmos3_vfm_network.py:950` `_encode_local_memory` → `build_memory_prefix_context` | 已实现 |
| 模块注册 | `build_net` 注册 `net.local_memory_runtime.{evidence_encoder,ttt_core}`，encoder 为 `CANONICAL_EVIDENCE_FEATURE_CONFIG` | `omni_mot_model.py:440-444` |

**模型侧与 trainer 侧已就绪**；缺失的是数据侧 producer 与驱动接线。

### 2.1 为什么不是 canonical-production route

`_canonical_production_segment_forward` 在 `dist.is_initialized()` 时直接 raise
（`omni_mot_model.py:1472`），显式 CPU/static only，无法用于真实 DDP 训练。
其 `CanonicalRawRowCarrier` + `prepare_native_inputs` 仍是生产者 ABI 的**语义参考**，
但真实训练必须走 active registry 路线。

---

## 3. 已完成的实现（本轮，已 CPU/static 验证）

提交 `2fe652c748e12bdde0b284a6cc334914a0abe3e8`：

1. **分派可达性修复**：`psm_local_memory_active` 属于 `_LEGACY_LOCAL_MARKER_KEYS`
   （`omni_mot_model.py:136`），而 canonical-production 前置条件在 `local_ttt_enabled=True`
   时要求 canonical mode 声明并 `raise`（`omni_mot_model.py:167`），导致 active 分支
   **永不可达**。现将 active 分派前置到该前置条件之前（`omni_mot_model.py:1594`）。
2. **真实 native forward**：`_run_active_local_memory_native_forward` 由硬 stub
   （恒抛 `native MoT adapter is unavailable`）替换为真实实现；Local prefix 在 clean
   materialization 之后按 canonical-production 同序挂载
   （`plan.has_local_memory` / `gen_data_clean.x0_tokens_local_memory`）。
3. **unwired model fail-closed 守卫**：缺少 `config`/`net` 时给出明确 `RuntimeError`。

CPU/static 证据：`production_active_wiring_test.py` **26 passed**。

**既有 5 项失败与本改动无关**：`ttt_lifecycle_test.py` 的
`test_recipe_r09_b_ttt_selects_four_slow_groups_and_callback`、
`test_recipe_r09_b_ttt_selector_covers_continual_core_not_readout`、
`test_model_config_ttt_field_defaults`、`test_model_config_ttt_validators`、
`test_model_config_ttt_post_init_mutual_exclusion` 断言的是**契约 refreeze 之前**的
`SELECTORS`（旧 `local_history_runtime.encoder` / `recurrent_backend`）、已移除的
`runtime_evidence_steps` 字段与旧 validator 文本；这些断言位于本轮未触及的代码路径。

---

## 4. 必须冻结的 ABI 决策（本轮新发现，设计缺口）

### 4.1 成员形状：一个 member = `B_stream` 条 stream 还是 1 条？（**必须裁决**）

- v0.3.5 冻结：microbatch 为 `B_stream=8` 条 stream × `T=16` 个 consumer position =
  **128 nominal consumers**（v0.3.5:36,46-47），`segments/update = B_stream * GA`（v0.3.5:404）。
  该 128 与现有基线 toml 的 `max_samples_per_batch = 128/rank` 完全一致，
  即 v0.3.5 的 microbatch 就是现有 Cosmos microbatch 的 chronology 因式分解。
- 现有 CPU/static active ABI 是**单 identity** 准备：`CanonicalSegmentRuntimeOwner.identity`
  单值、`LocalMemorySegmentSidecar.read(identity)` 返回单 state、
  `adapter.scan` 只做一次 `sidecar.read(identity)`。
- 但 core **支持** batched state：`scan_segment_masked_encoded_many` 的
  `initial_state(batch,...)` / `_select_rows` / `_scatter_rows`（`local_evidence.py:743,754,764`）
  均按 batch 维操作。

**裁决（依据 AGENTS.md §151，构建者决策）**：采用 v0.3.5 冻结语义——
**一个 member = `B_stream=8` 条 stream × `T=16` steps = 128 consumers，并打包为一次 native forward**。
理由：

1. v0.3.5 是权威设计，且其 128 与基线 microbatch 规模一致；若改为「一个 member = 1 条 stream」，
   则每次 forward 仅 16 samples，比基线慢 8×，且与 `segments/update = B_stream*GA` 矛盾。
2. 打包语义（一次 forward 承载 128 个 consumer，每个 consumer 携带自己的 Local prefix）是
   `packers.py:246` + `x0_tokens_local_memory` dense-per-sample 列表的既定契约所支持的，
   也是 baseline 吞吐等价的前提。
3. 因此 `LocalMemorySegmentSidecar` 与 `CanonicalSegmentRuntimeOwner` 必须扩展为
   **per-row batched fast state**（按 slot 组装 `[B]` 行状态），core 侧无需改动。

> 该裁决推翻了 `_run_active_local_memory_native_forward` 当前「每个 consumer 一次 forward」的
> 退化实现。后者语义正确但比基线慢 128×，不可用于真实训练。

### 4.2 生产者 raw-row / model-sample ABI

沿用 `canonical_segment_producer_implementation_design_v0.5.md` 的 nested ABI，落到 active 路线：

```text
raw_rows[b][t]          : CanonicalRawNativeRow | None   # exact [B_stream, T]，PAD -> None
row_model_samples[b][t] : Mapping[str, Any] | None       # 同一 [B_stream, T]，PAD -> None
model_data_batch        : Mapping[str, Any]              # 由 expected logical index 确定性 gather 后的单一 batch
flat(b,t) = b*T + t                                      # 仅派生 expected.logical_indexes，不回写 carrier
```

`SegmentBatch.consumer_payload[b][t]` 承载 `row_model_samples[b][t]`；
`consumer_valid` 与 PAD 一致（PAD 的 payload 必须为 `None`，见 `local_memory_segment.py:83`）。

### 4.3 S0 / evidence 语义

- `consumer_step[b,t] = t`；`evidence_source_step = t-1`，`evidence_valid` 在 `t=0` 为 False。
- 与 v0.3.5:109 一致：fresh episode 第一个 `T=16` scan block 有 16 个 valid consumer，
  但只有 **15** 次有效 inner update。

### 4.4 GA 映射

active 路线中 `trainer.grad_accum_iter` 计的是 **segment 数**，不是 micro-batch 数：
`arm_active_local_memory_initial` 要求 `grad_accum_iter == 0`，
`prepare_continuation` 要求 `grad_accum_iter == len(transaction.completed_members)`。
故 `grad_accum_iter = B_stream * GA = 8 * GA`。基线 `grad_accum_iter=16` 时，
若要保持 `consumers/update` 不变，需显式冻结新的 `GA`（训练 toml 与 baseline 的差异必须在
命令说明中显式列出）。

---

## 5. 数据侧 producer 设计（待实现）

### 5.1 数据来源（已只读核实）

cache 为 `exact_window_v1`，结构 `<suite>/episodes/episode_{i:06d}.pt`：
`{"format","episode_index","windows","language","metadata"}`，
`windows[str(f)]` 对 episode 内**每一帧**连续存在（已核实 `libero_10/episode_000000.pt`
的 window start frame 为 `0..197` 连续 198 个）；每个 window 的
`latent` 形状为 `[5,48,H,W]`（该 episode 为 `[5,48,12,20]`），
`latent[0]` 即**该起始帧**的 latent。

因此每帧 96-d visual summary 可精确构造，与 `libero_lerobot_dataset.py:510` 一致：

```python
visual_summary = F.adaptive_avg_pool2d(latent[0].unsqueeze(0), output_size=(1, 2)).flatten()   # 48*1*2 = 96
```

10-d executed action 复用 `LIBEROLeRobotDataset._build_frame_wise_action`
（`libero_lerobot_dataset.py:533`）加 `normalize_action`，与
`_build_local_history` 的 `local_history_action`（归一化后的 10-d）口径一致
（`CANONICAL_EVIDENCE_FEATURE_CONFIG` 只使用 visual + action，
`local_evidence.py:144-155`）。

### 5.2 逐字段构造

对 segment seed `(suite, episode_index, local_start)`，`T = ttt_tbptt_steps`：

| 字段 | 取值 |
|---|---|
| `consumer_valid[b,t]` | 帧 `local_start+t` 在本 episode 内有效且为窗口起点；否则 False（PAD） |
| `consumer_step[b,t]` | `t` |
| `consumer_visual_summary[b,t]` | 帧 `local_start+t` 的 96-d summary（trace/parity 用） |
| `discovery_evidence_visual_summary_prev[b,t]` | `t=0` 为 0；`t>0` 为帧 `local_start+t-1` 的 96-d summary |
| `evidence_executed_action_prev[b,t]` | `t=0` 为 0；`t>0` 为 row `local_start+t-1` 的 10-d 归一化已执行动作 |
| `evidence_valid[b,t]` | `t>0` 且 `consumer_valid[b,t]`；S0 与 PAD 均 False |
| `evidence_source_step[b,t]` | 有效时 `t-1`，否则 `-1` |
| `slot_id[b]` | stable stream slot |
| `episode_id[b]` / `category[b]` | episode 标识 / suite 名 |
| `consumer_payload[b][t]` | `row_model_samples[b][t]`；PAD 为 `None` |
| `segment_provenance` | manifest/config/source digest + segment_id |

`SegmentBatch.validate(ttt_tbptt_steps)` 的全部约束（`local_memory_segment.py:41-84`）
必须在构造后立即调用并通过。

### 5.3 身份与调度

`SegmentIdentity(slot_id, episode_id, category, cursor, segment_id, source_digest, training_stream_end)`
必须满足 `RankLocalSegmentScheduler._is_admissible`（`local_memory_segment.py:306`）：
同一 slot 的后续 segment 必须满足 `source_digest` 相同且 `cursor == previous.cursor + 1`；
episode 结束且 segment 关闭后才允许 rebind。

---

## 6. Trainer driver 设计（待实现）

1. **绑定**：trainer 初始化后构造
   `CanonicalLocalMemorySegmentAdapter(model.net.local_memory_runtime.evidence_encoder,
   model.net.local_memory_runtime.ttt_core, LocalMemorySegmentSidecar())`
   → `CanonicalSegmentWiring(adapter, local_slow_parameters)`
   → `RankLocalSegmentScheduler(rank, target_distribution)`
   → `CanonicalSegmentRuntimeOwner(scheduler, wiring)`
   → `ProductionActiveWiringRegistry(owner)`，
   再调用 `trainer.bind_active_local_memory_registry(model, registry)`
   （`trainer/__init__.py:764`，该函数同时绑定 trainer 与 model，且拒绝重复绑定）。
2. **每个 optimizer update**：为该 window 的每个 member 构造 `SegmentBatch` 与 `GAWindowPlan`，
   在第 0 个 member 前调用 `arm_active_local_memory_initial`，后续 member 前调用
   `arm_active_local_memory_continuation`；window 结束后 `owner.finish_window` +
   `resolve_local_memory_slow_window` + `registry.retire_resolved_window`。
3. **ordinary dataloader 的处置**：启用该路线后，ordinary 128-sample batch **不得**同时送入模型
   （否则 consumer 被计入两次）。必须显式冻结：本路线下 dataloader 只提供 raw row 来源，
   `training_step` 的输入由 driver 注入。
4. `local_slow_parameters` 必须取 `config_checkpoint_contract` 冻结的 slow selector
   （`local_memory_runtime.evidence_encoder.` / `local_memory_runtime.ttt_core.`）。

---

## 7. 训练配置启用（待实现）

`examples/toml/sft_config/action_policy_libero_edge_all.toml` 当前**无任何 local-memory 键**。
需新增（`model_config.py:344-380` 的 validator 必须同时满足）：

```toml
[model]
local_memory_enabled = true
local_memory_dim = 32
local_history_enabled = true
local_history_backend = "ttt_fast_weight"
local_history_evidence_dim = 96
local_ttt_enabled = true
ttt_tbptt_steps = 16
ttt_inner_lr = 0.1
k_local = 1
```

约束（`model_config.py:393-400`）：`local_ttt_enabled` 要求
`local_history_enabled=True` 且 `local_history_backend="ttt_fast_weight"`，
且 `local_memory_enabled=True` 且 `local_memory_dim=32`。

数据集侧需 `local_history_horizon`（dataset 构造参数）与 segment 语义对齐；
由于 producer 直接从 cache 取每帧 latent，dataset 的 history 字段**不参与**本路线。

---

## 8. 验收与判据

| 阶段 | 判据 | 资源 |
|---|---|---|
| P1 模型侧（已完成） | `production_active_wiring_test.py` 全 PASS | CPU |
| P2 producer CPU/static | 从真实 cache 构造 `SegmentBatch` 并通过 `validate`；`py_compile` + `git diff --check` PASS | CPU，只读 cache |
| P3 packed native forward | 一个 member = 一次 packed forward；per-sample prefix 对齐；CPU/static loss 有限且梯度到达 slow 参数 | CPU |
| P4 单迭代 CPU/static smoke | 真实 cache 上 1 个 member 的 forward+backward 完成，slow `.grad` 非零 | CPU，只读 cache |
| P5 GPU smoke | 1 iteration 真实训练步，无 NaN，loss 有限，显存不 OOM | 1×A100 |
| P6 训练启动 | 按 §7 配置在 latent cache 上启动，`logging_iter=1` 可见 loss | 1×A100 |

P5/P6 执行前必须按 AGENTS.md §72 向用户展示目的与 Gate、完整命令、工作目录、关键环境变量、
资源范围、输入 checkpoint/数据集、产物路径与 PASS/FAIL/BLOCKED 判据。

---

## 9. 禁止范围

- 不启用 `_ttt_local_memory_tokens()` / `TTTLifecycle` row-wise 路线（v0.3.5:12 禁止静默混用）。
- 不修改 `config_checkpoint_contract` 冻结的 selector/config identity。
- 不触碰遗留 dirty/untracked：`uv.lock`、`results/`、`artifacts/`、`.authority-root-*`、`outputs`。
- 不重试旧 v0.6 materialization/request，不复用旧 evidence。
- 不把本设计解释为 source-evidence / authority-root provenance 的替代；provenance 按用户授权
  降级为并行或训练后补。
