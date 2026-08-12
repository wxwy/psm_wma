# PSM-WMA G0 Runtime Execution Plan v0.6
## Cosmos3 Native World-Action-Reasoner Route

**日期**：2026-08-12  
**上游**：Static Audit v0.6、Detailed Design v2.1  
**原则**：先建立 `Cosmos3-Edge-Policy-DROID → LIBERO` 无 PSM baseline，再加入 Memory；G0 smoke 不计正式实验预算。

---

# 0. 通用输出规范

所有 Gate 输出 JSON 到：

```text
artifacts/g0/<gate_name>.json
```

统一字段：

```json
{
  "repo_commit": "...",
  "model_path": "...",
  "gpu": "...",
  "dtype": "bfloat16",
  "peak_vram_gb": 0.0,
  "latency_ms": 0.0,
  "finite": true,
  "status": "PASS|FAIL"
}
```

FAIL 必须记录 exception、shape、config diff，不允许只写“跑不通”。

---

# 1. G0-R01 Edge-Policy-DROID 官方能力 Smoke

## 目的

确认同一官方 checkpoint 在本机至少能独立运行：
1. Reasoner；
2. Policy/Action；
3. World/Video generator 或官方 policy rollout。

## 输入

```text
models/Cosmos3-Edge-Policy-DROID
```

使用官方 `cosmos-framework` / model card 的原生 inference，不先改 PSM。

## 检查
- load 成功；
- reasoner text finite；
- action shape 与 released contract 一致（典型 `[16,8]`）；
- generated rollout/latent finite；
- peak VRAM；
- warmup/steady latency。

## PASS
三条 pathway 至少 Reasoner + Policy 均可运行；World output 若 serving 模式不直接 decode，也必须确认 shared Generator 正常。

输出：`R01_edge_policy_droid_smoke.json`。

---

# 2. G0-R02 Edge vs Edge-Policy-DROID Checkpoint Audit

## 目的

回答 DROID post-training 到底改了什么，指导 LIBERO 继承/冻结。

## 比较

当前不要求为了 R02 立即重新下载 bare `Cosmos3-Edge`。优先做 source/config/export mapping 审计；只有确实需要 tensor-by-tensor diff 时再补回 checkpoint：

```text
Cosmos3-Edge source/config reference
vs
Cosmos3-Edge-Policy-DROID checkpoint
```

至少比较：
- root / transformer config diff；
- parameter key set；
- vision encoder / VAE 是否 byte/hash identical；
- shared generator layers 的 L2/relative diff；
- action projection keys/diff；
- reasoner/und pathway keys/diff；
- `cosmos_framework_model.safetensors` 与 diffusers export 的映射。

## 输出

```json
{
  "same_config_core": true,
  "changed_parameter_groups": {},
  "reasoner_changed_ratio": 0.0,
  "generator_changed_ratio": 0.0,
  "action_proj_changed_ratio": 0.0,
  "vae_identical": true,
  "vision_encoder_identical": true
}
```

## PASS
能明确划分：继承 shared generator、Reasoner、action-domain projection 的策略；不要求两 checkpoint 大部分权重 identical。

---

# 3. G0-R03 Cosmos Action Pipeline / Domain Audit

## 目的

把 Action 数据流从 dataset 到 env 输出完整打印：

```text
raw action
→ ActionProcessor/transform
→ normalized/padded action
→ raw_action_dim/domain_id
→ pack_action_tokens
→ action2llm
→ shared MoT
→ llm2action
→ mask/denormalize
```

## DROID 检查
- 8D raw action；
- absolute joint position + gripper；
- domain name/id；
- chunk 语义；
- state/proprio contract。

## LIBERO reference 检查
读取 official Nano recipe：
- 10D；
- frame_wise_relative；
- rot6d；
- concat_view；
- quantile_rot；
- chunk 16。

## PASS
能生成一张 exact shape/semantic 表，且确认代码没有全局硬编码 DROID 8D。

额外必须确认：
- LIBERO gripper mapping 的实际代码；
- simulation frame / image rotation（包括 180° 变换）实际位置；
- `quantile_rot` normalization 是否显式启用；
- `chunk_size / max_action_dim / hidden_size / SequencePlan/PackedSequence` 的源码路径 + config key + runtime shape；
- Edge formal SFT `requires_grad` group、trainable parameter count；目标是验证约 1.423B official-style Generator+Action selective update，而不是 whole-checkpoint full-parameter。

输出：`R03_action_contract.json`。

---

# 4. G0-R04 Edge-Policy-DROID × LIBERO Forward/Loss Smoke

## 目的

验证“把官方 Nano LIBERO data/action recipe 迁到 Edge-Policy-DROID”在结构上可运行。

## 禁止
- 不加 PSM；
- 不改 Agent；
- 不换 benchmark；
- 不做长训练。

## 最小改动
建立新的 experiment/config（命名示意）：

```text
action_policy_libero_edge_warmstart.py
```

warm start：`Cosmos3-Edge-Policy-DROID`。

## 检查
- LIBERO sample → `GenerationDataClean`；
- SequencePlan Vision/Action target 正确；
- raw action 10D，padding 到 model max dim 正确；
- action domain id 正确；
- vision/action flow loss finite；
- backward finite；
- Reasoner 参数默认不训练；
- no unexpected 8D assert；
- EMA **off**；
- 记录 FSDP2/AC config，但 smoke 优先正确性；
- 用一个 batch 做 online vision VAE encode vs proposed offline-cache latent parity；未通过前训练仍使用官方 online path。

## PASS
连续 20–50 steps 无 NaN/OOM/shape mismatch。

输出：`R04_edge_libero_forward_loss.json`。

---

# 5. G0-R05 LIBERO Tiny Overfit

## 数据
1 个 task，少量 episode/固定 batch；100–500 optimizer steps。

## 目的
EMA off。不是追 SR，只验证：
- action flow loss 明显下降；
- generated action 从纯 noise 向 GT 靠近；
- vision flow 同时稳定；
- checkpoint save/load 后输出一致。

## PASS
loss 有清晰下降趋势且 held-out forward finite。

输出：`R05_libero_tiny_overfit.json`。

---

# 6. G0-R06 LIBERO Closed-loop Baseline

## 目的

得到 PSM 之前唯一合法的 baseline：

```text
Cosmos3-Edge-Policy-DROID
→ LIBERO adaptation
→ Edge-Policy-LIBERO
```

## 协议
- 先单个易 task/suite；
- 记录 prediction horizon / execution horizon / query stride；
- 初始建议 chunk 16、execute 1；
- 不用 memory/agent/RL；
- formal SFT 默认 Reasoner frozen，Generator+Action selective update；
- FSDP2：parameter/gradient/optimizer state shard；AC 先 selective；
- EMA 默认 **on** 对齐官方 recipe；若因 VRAM/throughput 关闭，必须记录并在后续所有 matched Memory 实验保持一致；
- 若显存有明显余量而 all-gather 吞吐差，单独 profile `reshard_after_forward=False`，不与算法变量混跑。

## PASS
最低：SR > 0 且不同 seed 可重复。  
推荐：达到“可用于比较 +PSM”的 usable baseline；若明显低于同规模成熟 policy，要先定位 action/camera/state contract。

输出：`R06_libero_closed_loop.json`。

**R06 FAIL 时禁止正式 PSM 实验。**

---

# 7. G0-R07 Local / Global Optional-Modality Packing / Attention Smoke

## 目的
在不实现真实 Memory 算法前，用 dummy Local / Global tensors 验证 Cosmos3 能把二者作为独立、可选、always-clean modality。

## 运行路径前置核对

先记录当前 submodule commit，并从真实调用点确认 `sequence_packing` import/runtime 链。对当前固定 commit `5d6dedc7...`，package-level export 为 `__init__.py → packers.py / sequence.py / modality.py`；仓库中并存的 `types.py` 不得未经 import 追踪就作为修改目标。R07 实现前必须输出实际 class/function 的 `__module__`、源码路径与 import trace，并把 `packers.py`、position/mRoPE、attention mask 与 FSDP graph 一并纳入 smoke。

## 最小对象

```text
SequencePlan.has_local_memory
SequencePlan.has_global_memory
PackedSequence.local_memory
PackedSequence.global_memory
local_memory2llm + local_memory_modality_embed
global_spatial2llm + global_memory_modality_embed
```

## 四种构造

```text
A: Vision + Action/Future, no memory
B: +Local only
C: +Global only
D: +Local +Global
```

## 检查
- absent modality 不 pack，不补固定 zero tokens；
- Local/Global sequence indexes 独立；
- 两者无 mse indexes / noise timestep / decoder；
- noisy Action/Vision 能 attend Local/Global；
- Local/Global 不读取同一步 noisy targets；
- Local / Global position/type embedding 独立；
- Zero/Shuffle content 不改变 shape/index contract；
- `has_* = false` 与 `has_* = true + zero content` 可区分；
- forward/backward/FSDP finite。

## PASS
A/B/C/D 全部 finite；attention leakage assertion=0；optional-modality contract 可进入真实 Local/Global 实现。

输出：`R07_memory_modalities_packing_attention.json`.

# 8. G0-R08 Temporal Multi-Sensor / History Replay Gate

## 目的
把 episode history 变成 causal Local evidence，并确认 main RGB / depth / pose / robot state / wrist RGB / executed action 使用同一 source timeline。

每个 sample 输出：

```json
{
  "episode_id": 1,
  "anchor_source_index": 100,
  "history_source_indices": [84,88,92,96],
  "history_rgb_timestamps": [],
  "history_depth_source_indices": [],
  "history_pose_source_indices": [],
  "history_state_source_indices": [],
  "history_wrist_source_indices": [],
  "history_executed_action_ranges": [[84,88],[88,92],[92,96],[96,100]],
  "target_action_range": [100,116]
}
```

## Assertions
- 不跨 episode；
- RGB/depth/pose/state/wrist 的 source-index/timestamp 映射显式可追溯；
- depth 必须对齐对应 RGB，而不是按缓存数组 index 猜测；
- Local update 不看 target/future action；
- 只写 executed action；
- prediction chunk suffix 不写入；
- VAE latent step / raw frame / policy step 显式映射；
- offline replay 与 online step 语义一致。

## PASS
LIBERO sampled anchors 全通过；输出 `R08_temporal_multisensor_alignment.json`.

# 9. G0-R09 Local PSM Backend Selection / Forward-Backward Smoke

> **前置硬条件**：R06 Edge-Policy-LIBERO closed-loop baseline PASS。R06 之前不允许通过 TTT 或任何 Local Memory 改造“救 baseline”。

共享链路：

```text
history main/wrist RGB + depth + pose + state + executed action
→ Temporal Alignment
→ LocalEvidenceEncoder
→ temporal compressor backend
→ Local state/readout
→ local_memory2llm
→ Cosmos3 PackedSequence
→ native vision/action loss
```

## R09-A — `recurrent_latent` baseline

```text
aligned E_t
→ recurrent query / gated latent compressor
→ M_t / K_local tokens
```

目标是得到最简单、fixed-budget 的 learned Local baseline，作为“有 learned temporal memory”对照。

## R09-B — `ttt_fast_weight` primary candidate

参考 RoboTTT（arXiv:2607.15275）的原则，但保持 PSM-WMA Local optional-modality 接口：

```text
aligned E_t
→ per-step summary/register tokens
→ TTT-KVB fast-weight state W_t
→ Local readout
→ K_local tokens
```

首期 TTT 作为独立 Local temporal compressor，不直接插入 Cosmos3 shared MoT。训练允许 segment 内梯度，segment 边界携带但 detach fast-weight state；推理持续更新 fast weights。

## 两个 backend 都必须检查
- M_local / backend state / Z_local shape 可追踪；
- all finite；
- Local evidence/write/read/adapter grads nonzero；
- state detach/TBPTT 边界可打印；
- episode reset 正确；
- vectorized / multi-env state 无串扰；
- frozen Cosmos groups grad zero；
- Normal/Zero/Shuffle/Stale/Truncated 全能 forward；
- intervention 保持 token/index/SequencePlan shape；
- **future world 与 action output** 都记录 sensitivity；
- 记录 peak VRAM、step latency、state bytes、save/load/reset 成本。

TTT 额外检查：
- fast weights 在同 episode 内实际发生有限更新；
- segment boundary 后数值 state 连续、autograd graph 已 detach；
- 新 episode从规定的 W0/reset state 开始；
- fast weights 不误入模型慢权重 checkpoint/optimizer state 的生命周期；
- FSDP 多 rank 下 fast-state ownership/shape 一致。

## Backend Freeze Rule
R09 smoke 不以短跑 SR 决定胜负。先要求两者工程正确，再比较：
1. future/action sensitivity；
2. 训练稳定性；
3. 长状态保持能力；
4. VRAM/latency；
5. batching/reset/FSDP 复杂度。

`ttt_fast_weight` 是第一优先候选，但只有综合收益明确时才冻结；否则使用 `recurrent_latent` baseline 进入 E002。

## PASS
至少 `recurrent_latent` 连续 100 steps 无 leakage/NaN 且 intervention contract 全通；`ttt_fast_weight` 若进入正式候选，必须通过同等 contract + TTT 专项 state assertions。最终输出 backend decision。

输出：`R09_local_backend_selection_smoke.json`。

---

# 10. G0-R10 RoboCasa365 Schema / Action Domain Gate

## 目的

从真实 dataset dump：
- native fps；
- camera keys/shape；
- raw/post-transform state；
- raw/post-transform action；
- action controller semantics；
- intrinsics/extrinsics/pose availability；
- language/episode/task fields。

## 实现
建立 `robocasa` ActionProcessor/domain，不硬转 DROID 8D。

## smoke
- 20–50 steps forward/loss；
- tiny overfit；
- 再做 closed-loop baseline。

## PASS
无 Memory RoboCasa baseline 非零且可重复后，才进入 E006 +Local。

输出：`R10_robocasa_domain.json`。

---

# 11. G0-R11 Planner / Reasoner MemoryRequest Smoke

## 目的
验证 Agent 以后不需要改 Memory 底层接口，只通过 routing/query 决定 optional modality presence。

```text
Goal + current observation summary + memory metadata
→ Cosmos3 Reasoner / Planner
→ MemoryRequest
   ├─ local.enabled + budget/horizon
   └─ global.enabled + semantic/spatial/time query + top_k
→ dataset/runtime builder
→ SequencePlan.has_local_memory / has_global_memory
```

## 检查
- structured output parseable；
- local-only / global-only / both / neither 都能构造合法 request；
- Global query 可带 semantic query / spatial region / temporal range / top-k；
- Planner 不直接操作 Memory tensor；
- event-trigger API；
- Reasoner 输出可作为下一次 Generator instruction / memory routing；
- 不需要每 control step 调 reasoner。

Goal Memory 若后续启用，只作为额外 Target，不阻断本 Gate。

## PASS
至少跑通一条：subgoal→MemoryRequest→Local/Global read→Generator action→new obs→verifier。

输出：`R11_planner_memory_request.json`.

# 12. G0-R12 oVDA / Vision-VAE Cache Alignment & Throughput Gate

## oVDA
- official checkpoint；
- offline sequential cache；
- online causal step；
- RGB↔depth source-index/timestamp alignment；
- fps/VRAM profile。

## Vision VAE cache
在 exact official policy temporal sample 上比较：

```text
online official VAE encode → latent A
offline proposed cache     → latent B
```

要求 shape/temporal metadata 一致并数值在预期误差内。未经验证禁止逐帧独立 VAE encode 替代 clip encode。

R12 不阻断 E001–E004；一旦启动 Spatial Global Memory，R12 中所选 geometry/source path 成为对应 Global 实验的前置 Gate。

输出：`R12_ovda_vae_cache_profile.json`.

# 13. G0-R13 Spatial Global Store / Retrieval / Modality Smoke

## 目的
不追求完整 Region/Place map，先证明单一 persistent spatial store 能构建、检索并通过 Global modality 影响 native world/action。

## Store 最小字段

```text
visual/semantic feature
geometry/depth feature
camera/world pose
view direction
timestamp
confidence/freshness
source frame/key-view reference
```

## Retrieval
输入 current pose / current visual / optional semantic query，输出 Top-K records；记录 retrieval score、spatial distance、timestamp、source ids。

## Global adapter

```text
Top-K records
→ GlobalSpatialEncoder / compressor
→ global_spatial2llm
→ PackedSequence.global_memory
→ native vision/action loss
```

## 检查
- store 不跨 episode；
- source/provenance 可回溯；
- Top-K 有界；
- Normal/Zero/Shuffle/Wrong-view/Stale shape invariant；
- Global grads 只进入 trainable encoder/retrieval/adapter，oVDA/map deterministic 部分可 frozen；
- Global-only 与 no-memory action/world output 有可测 sensitivity；
- forward/backward/FSDP finite。

## PASS
连续 100 steps finite，intervention contract 全通，才允许 E005+。

输出：`R13_global_spatial_memory_smoke.json`.

---
# 14. 决策树

```text
R01 FAIL
→ 修官方环境/checkpoint，不做项目代码

R01 PASS
→ R02/R03

R04 FAIL
→ 修 Edge×LIBERO action/data contract
→ 若结构性不可用，切 Predict2-2B fallback

R05 PASS
→ R06 closed-loop

R06 FAIL
→ stop PSM
→ 禁止 RL/Agent rescue

R06 PASS
→ R07/R08/R09
→ E001–E004 Local

R12 + R13 PASS
→ Spatial Global E005–E007

R10 PASS
→ RoboCasa E008–E011

R11 PASS
→ Planner/Reasoner E013/E014

Goal Memory conditional
→ only if planner/query cannot represent task progress
```

---

# 15. 运行时必须回填到 Detailed Design 的字段

```text
Edge peak VRAM / latency
Reasoner latency
Action sampler steps
LIBERO query/execution cadence
Edge→LIBERO trainable parameter groups
new domain initialization strategy
K_local / K_global and readout budgets
Local multi-sensor alignment / selected backend / history TBPTT-detach or TTT fast-weight policy
Local/Global packed positions / attention mask
Global store representation / retrieval top-k / provenance
RoboCasa exact D_action/D_state
λ_action / λ_vision
EMA choice
FSDP2 AC/reshard profile
VAE cache parity metrics
```

这些字段 Runtime 前不得在主文档写成伪精确常量。  
