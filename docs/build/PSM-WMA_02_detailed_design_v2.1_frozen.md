# PSM-WMA：Persistent Spatial Memory-Augmented World-Model Agent
# 详细设计说明书 v2.1（Cosmos3 原生 World-Action-Reasoner 架构冻结版）

**日期**：2026-08-12  
**上游**：`00_project_proposal_v1.4_frozen.md`、`01_technical_survey_v1.7_frozen.md`  
**工程母体**：NVIDIA `cosmos-framework`  
**主初始化 checkpoint**：`nvidia/Cosmos3-Edge-Policy-DROID`  
**执行约束**：单人串行；1–8×A100 80GB；RTX 4090 用于开发/轻量 smoke；关键训练实验 ≤20 组

---

# 交付摘要页

## A. 一句话方案

PSM-WMA 直接扩展 Cosmos3 的原生 multimodal Generator：**Temporal Local Memory** 与 **Spatial Global Memory** 分别经独立 modality adapter 变成始终 clean、可选存在的 condition tokens，加入 `SequencePlan/PackedSequence`，与 Vision/Action 共享 Cosmos3 Generator；后续 Planner/Reasoner 决定是否请求 Local/Global、检索什么与 token budget。

## B. 主数据流

```text
                 Goal / Task
                     │
             ┌───────┴────────┐
             │ event trigger   │
             ▼                 │
      Cosmos3 Reasoner         │
             │ structured      │
             │ subgoal/status  │
             └───────┬─────────┘
                     ▼
RGB/Video ───────→ Observation Encoding
Robot State ─────→ State Encoding
Executed Actions → ActionIntervalEncoder
Spatial Cue ─────→ SpatialAdapter (optional)
                     │
              ┌──────┴──────┐
              ▼             ▼
          Local Memory    Global Spatial Memory
              │             │
              └──────┬──────┘
                     ▼
   local_memory2llm / global_spatial2llm
                     ▼
        Local clean tokens (optional)
        Global clean tokens (optional)
                     +
          SequencePlan / PackedSequence
                     ▼
             Cosmos3 Generator
              ┌──────┴───────┐
              ▼              ▼
         Future World       Action
                               │
                           Environment
                               │
                        New Observation
                               └──→ Memory update
```

## C. 架构冻结变化

**v2.1（2026-08-12）确认更新**：
- PSM 从单一 `psm` clean modality 拆成 **Local Memory modality** 与 **Global Memory modality**；二者有独立 encoder/mapper/position semantics，不能先 concat 再共用同一 adapter；
- Local = 时间对齐的多模态近期状态经 learned compression 得到；Global = 全 episode 空间结构化 store 经 retrieval/compression 得到的关键空间证据；
- 两个模态都支持 presence/absence，由 `SequencePlan` 路由；训练时人工/mode-dropout 控制，Agent 阶段由 Planner 动态控制；
- Goal Memory 保留为后续 Target，不替代 Global，也不阻断 Local→Global；Region/Place 层级 Global 仍 BEHAVIOR-only；
- R04/R05 EMA 默认关闭做 admission smoke；R06 正式 baseline 默认先对齐官方 EMA-on recipe；VAE offline cache 只有在线/离线 temporal-token parity 通过后启用；
- Edge→LIBERO 正式 SFT 采用官方风格 Generator+Action selective update，Reasoner frozen；按当前源码维度估算约 1.423B trainable，而不是 whole-checkpoint full-parameter；
- FSDP2 作为默认多卡方案，参数/梯度/optimizer state 分片；activation 不分片，AC 先 selective，显存充足但吞吐受通信影响时再 profile `reshard_after_forward=False`。

v2.0 正式删除旧主链中的：
- `WorldStateAdapter`；
- `ActionBridge`；
- `LayerwiseFM` 作为 PSM-WMA 主 Action path；
- bespoke `ActionConditionedFutureHead`；
- “Cosmos3 仅作为 Host/Teacher”假设；
- 外部 Agent LLM 作为 primary。

它们只保留在历史文档/对照方案中。

---

# 第 0 章 文档边界与设计原则

## 0.1 本文件负责什么

冻结：
- Cosmos3 原生 multimodal integration；
- PSM data schema、update/read、condition injection；
- multi-embodiment action contract；
- Reasoner/Generator runtime；
- training/loss/freeze；
- intervention、benchmark、实验矩阵；
- Runtime G0 Gate。

不冻结：
- BEHAVIOR Regional Global PSM 的 Region/Writer/Reader；
- full online RL；
- joint text/action sampler；
- 从零训练 Cosmos3。

## 0.2 核心工程原则

1. **Native-first**：优先复用 Cosmos3 原生 Vision/Action/Reasoner/SequencePlan，不再造 parallel action/world stack。  
2. **PSM-as-condition**：第一版 PSM 始终 clean，只提供上下文，不作为 diffusion target。  
3. **Action Utility First**：Memory 必须改变 native Action / closed-loop，而不是只改善 probe。  
4. **Causal memory**：Local update 只使用当前/过去 observation、state、已执行 action interval；禁止 future leakage。  
5. **One variable at a time**：先 Edge-LIBERO baseline，再 Local，再 RoboCasa，再 Goal/Reasoner。  
6. **No RL rescue**：zero-SR baseline 不进入 RL/RECAP。  

---

# 第 1 章 Cosmos3 原生结构合同

## 1.1 两条 inference pathway

同一 `Cosmos3-Edge-Policy-DROID` checkpoint 包含：

```text
Reasoner pathway
→ autoregressive text generation
→ task/subgoal/verifier

Generator pathway
→ flow-matching continuous generation
→ Vision / Action (and optional Sound)
```

两者不在首期做一次 joint decode。Reasoner 事件级调用；Generator 控制级调用。

## 1.2 Generator modality adapter

Edge hidden size 冻结为 `D_cosmos = 2048`（Runtime 仍核验 config）。原生接口：

```text
Vision latent → vae2llm   → D_cosmos
Action        → action2llm→ D_cosmos
Sound         → sound2llm → D_cosmos
Text ids      → embed_tokens → D_cosmos
```

输出：

```text
D_cosmos → llm2vae    → vision flow prediction
D_cosmos → llm2action → action flow prediction
D_cosmos → llm2sound  → sound prediction
```

Action projection 为 `DomainAwareLinear`，模型 config 支持 `max_action_dim=64`、多 embodiment domain；真实 raw action 维度由 `raw_action_dim` mask/metadata 指定。

## 1.3 SequencePlan 是任务路由，不是模型自猜

每个 sample 显式声明：

```python
SequencePlan(
    has_text,
    has_vision,
    has_action,
    has_sound,
    has_local_memory,      # new, optional clean modality
    has_global_memory,     # new, optional clean modality
    condition_frame_indexes_vision,
    condition_frame_indexes_action,
    condition_frame_indexes_sound,
)
```

语义：
- modality 不存在：不 pack；
- modality 存在且 index 在 condition 集：clean input；
- modality 存在但不在 condition 集：noised target；
- decoder 只对相应 `mse_loss_indexes` 的 target hidden 做有效输出。

## 1.4 三个关键任务模式

### Policy

```text
Text/Goal      clean
Current Vision clean
Future Vision  noisy
Action         noisy
→ Future + Action
```

### Forward Dynamics

```text
Current Vision clean
Candidate/known Action clean
Future Vision noisy
→ Future
```

### Inverse Dynamics

```text
Vision trajectory clean
Action noisy
→ Action
```

Local / Global Memory 不改变上述任务定义；它们分别作为可选 shared clean context。缺失时不 pack，不补固定零 token。

---

# 第 2 章 统一数据 Schema

## 2.1 `PSMSequenceSample`

```python
PSMSequenceSample = {
    # current Cosmos sample
    "images_or_video": ...,
    "instruction": str,
    "robot_state": Tensor,
    "action": Tensor,                 # [H_a, D_raw]
    "action_domain_name": str,
    "raw_action_dim": int,
    "sequence_plan": SequencePlan,

    # Temporal Local evidence: same source timeline
    "history_main_rgb_or_feat": ...,
    "history_depth_or_feat": optional,
    "history_camera_pose": optional,
    "history_robot_state": Tensor,
    "history_wrist_rgb_or_feat": optional,
    "history_action_intervals": Tensor,
    "history_action_mask": Tensor,
    "history_valid_mask": Tensor,
    "history_timestamps": Tensor,
    "history_source_indices": Tensor,

    # Spatial Global store / retrieval result
    "global_memory_refs": optional,       # key/record ids
    "global_patch_features": optional,
    "global_patch_xyz": optional,
    "global_camera_pose": optional,
    "global_view_direction": optional,
    "global_timestamps": optional,
    "global_confidence": optional,
    "global_retrieval_mask": optional,

    # optional planner/goal extension
    "memory_request": optional,
    "goal_id": optional,
    "subgoal_id": optional,

    # audit
    "episode_id": int,
    "anchor_index": int,
    "sample_id": str,
}
```

## 2.2 Canonical dimensions

```text
D_cosmos          = 2048      # Edge runtime verify
D_local_internal  = 1024      # initial design width; calibration allowed
K_local           = runtime calibration
K_global          = runtime/retrieval calibration
max_action_dim    = 64        # Cosmos model capacity; R03 runtime verify
```

不在设计阶段伪冻结 Global raw feature width；它取决于最终 store（RGB semantic / oVDA geometry / key-view / patch / hybrid）。Local / Global 在进入 Cosmos3 前分别投影到 `D_cosmos`。

## 2.3 Offline replay / persistent store

Local anchor `t` 按同 episode 历史顺序重放，并保持跨传感器统一 timestamp：

```text
(main RGB, depth, pose, state, wrist RGB, executed actions)_{t-H:t}
→ temporal alignment
→ local replay / compression
→ M_local_t
```

Global store 则可以 episode 级离线构建：

```text
historical RGB/semantic + oVDA depth/geometry + camera trajectory + time
→ spatial organization/fusion
→ persistent global store
→ per-anchor retrieval
```

禁止跨 episode 污染。随机 anchor 不依赖 batch 间隐式 state；Local recurrent state 可用 sample-internal replay / truncated BPTT / detached state，具体由 R08/R09 profile 冻结。

# 第 3 章 Temporal Alignment Contract

## 3.1 三条时间轴

必须区分：
1. raw environment frame/action step；
2. vision encoder/VAE latent step；
3. policy query / executed action step。

任何 host-specific compression 都不得写成全局常量。

## 3.2 Executed Action Interval

Local Memory update 只使用**已经执行**的动作区间：

```text
obs_{t-1}
+ actions actually executed between obs_{t-1} and obs_t
+ obs_t
→ M_t
```

预测但未执行的 chunk suffix 不得写入 Local。

## 3.3 Cosmos action/vision temporal alignment

Cosmos Sequence packing 中 Action 使用同一 mRoPE temporal space，默认 `action_start_frame_offset=1`，即 action[0] 与后继 vision frame 对齐。项目 adapter 必须从数据时间语义计算，而不是盲目硬编码。

## 3.4 默认 closed-loop cadence

Stage 1 默认：

```text
predict action chunk H=16 (跟随 Cosmos LIBERO recipe 起点)
execute q=1 step initially
observe new frame
update Local
re-query policy
```

若 q=1 成本不可接受，可做独立 cadence experiment，但不能和 Memory gain 混在同一组。

---

# 第 4 章 Temporal Local Observation / Alignment Adapter

## 4.1 Local evidence contract

Local 的输入不是单一视觉 latent，而是同一 source timeline 上的多模态 evidence：

```text
main RGB / visual feature
+ depth / depth feature
+ camera pose
+ robot state / proprio
+ optional wrist RGB / feature
+ executed action interval
```

任何一个来源降采样/缓存后都必须保留 `source_index/timestamp`，先对齐再压缩。特别是 oVDA depth 必须与对应 RGB frame 一一映射，不能把不同采样频率的 depth 与视觉 latent 按数组 index 直接拼接。

## 4.2 `LocalEvidenceEncoder`

候选输出：

```text
per-time evidence E_t ∈ R[B,K_e,D_local]
```

各 source 可以先独立编码再在同时间步融合，但 temporal compressor 只处理已经对齐的 evidence。第一版不要求复制全部 Cosmos visual tokens，可用 frozen/cached visual summary 控制 replay 成本。

## 4.3 Executed Action Interval

只编码已经执行的 action；未执行 chunk suffix 禁止进入 Local。每个 interval 可用 masked mean + last valid / small temporal MLP 形成 action evidence。

---

# 第 5 章 Temporal Local Memory Modality

## 5.1 定义

```text
M_local_t ∈ R[B,K_local,D_local]
```

它是 task-agnostic learned temporal state，重点保存近期世界状态变化、机器人运动/操作上下文和当前可观测信息中已经消失但仍影响决策的证据。

## 5.2 Write / compression

第一候选仍可用 recurrent query / gated cross-attention，但 v2.1 不把具体 recurrence 公式硬冻结。硬约束是：
- evidence encoder / write / compression / readout 可被 `L_vision + L_action` 优化；
- 不要求 gradient 穿过完整 episode；
- R08/R09 比较 truncated BPTT、detached recurrent state、必要时 stable/EMA update，优先保证长时持久状态与训练稳定性；
- inference persistent state 可持续更新，不因训练截断而限制实际持续时长。

## 5.3 Readout / adapter

```text
M_local_t
→ LocalReadout / compact tokens
→ local_memory2llm
→ + local_memory_modality_embed
→ Z_local [B,K_local_read,2048]
```

`local_memory2llm` 与 Global mapper 不共享。

## 5.4 Causality

允许 current/past RGB/depth/pose/state/wrist/executed actions；禁止 future observation、target action、未执行 chunk suffix。

---

# 第 6 章 Spatial Global Memory Modality

## 6.1 定义

Global 是全 episode 的 explicit / semi-explicit persistent spatial state，不是更长的 recurrent Local：

```text
GlobalRecord_i = {
  visual_or_semantic_feature,
  geometry_or_depth_feature,
  world/relative pose,
  camera pose,
  view direction,
  timestamp,
  confidence/freshness,
  optional raw/key-view reference
}
```

它用于回答“之前在什么位置、什么视角、什么时间看到了哪些与当前决策相关的内容”。

## 6.2 Store construction

第一版候选：

```text
RGB / semantic feature
+ oVDA depth or local geometry representation
+ camera trajectory / pose
+ timestamp
→ spatial lifting / structural reorganization / fusion
→ persistent global store
```

不把 oVDA 内部 feature 自动等价为完整 Global Memory；是否保存 RGB semantic feature、oVDA intermediate、3D patch、key-view 或 hybrid，由 R12/R13 专项冻结。

## 6.3 Retrieval / compression

```text
current pose + current visual + optional planner/task query
→ spatial/semantic/temporal retrieval
→ Top-K relevant records
→ GlobalSpatialEncoder / compressor
→ global_spatial2llm
→ + global_memory_modality_embed
→ Z_global [B,K_global_read,2048]
```

不允许把整张全局 map 无界塞入 Cosmos3。

## 6.4 Position semantics

Global token 应保留：world position / relative-to-current-robot pose、view direction、historical time、retrieval provenance。第一版把 metric geometry 编进 token content / Fourier pose embedding，不直接占用现有 Vision H/W mRoPE；是否需要新的 spatial RoPE 留作后续专项。

## 6.5 Regional/Place hierarchy

当前 Global 可以是单一全局 store。只有 BEHAVIOR 多房间阶段出现容量/aliasing/跨区域冲突时才增加 Region/Place hierarchy。

---

# 第 7 章 Cosmos3 Optional Memory Modalities

## 7.1 两个独立 adapter

```text
Z_local  = local_memory2llm(LocalReadout(...))   + local_memory_modality_embed
Z_global = global_spatial2llm(GlobalReadout(...)) + global_memory_modality_embed
```

不先 `[Local;Global]` concat 后共用一个 `PSMConditionAdapter`。

## 7.2 `SequencePlan` / `PackedSequence` 扩展

```python
has_local_memory: bool = False
has_global_memory: bool = False

PackedSequence.local_memory: ModalityData | None
PackedSequence.global_memory: ModalityData | None
```

二者第一版均：
- `condition_mask = all ones`；
- no noise timestep；
- no `mse_loss_indexes`；
- no decoder head；
- 不存在时不 pack；
- noisy Vision/Action 可 attend 它们；
- Memory condition 不读取同一步 noisy target。

## 7.3 Planner-facing routing

```text
MemoryRequest
├── local: enabled, horizon/budget/query_type
└── global: enabled, semantic_query, spatial_region, temporal_range, top_k
```

W4/W5 无需先实现 Agent，可由 dataset/config 直接构造 request；后续 Reasoner/Planner 接管同一接口。

## 7.4 Injection topology fallback

Primary：Native Local/Global Optional Modalities。  
Strong alternative：Global store → camera-aligned depth/semantic reference → Cosmos3 existing control-vision topology。  
Fallback：zero-gated cross-attention/residual adapter（保留 ControlNet function-preserving 思想）。  
Deferred：external memory → per-layer KV `MemoryState`。  
Full ControlNet 不作为首期实现。

# 第 8 章 Cosmos3 Generator World-Action Path

## 8.1 Policy mode

```text
Instruction clean
Current Vision clean
Local Memory clean (optional)
Global Memory clean (optional)
Future Vision noisy
Action noisy
→ shared MoT
→ native llm2vae + llm2action
```

Local / Global 对 Future 和 Action 的影响发生在共享 generator attention 中，不再通过独立 ActionBridge。

## 8.2 Forward Dynamics mode

```text
Current Vision clean
PSM clean
Candidate/known Action clean
Future Vision noisy
→ Future
```

用于 diagnostic、候选 action consequence 或后期 verifier；首期不要求 MPC/CEM。

## 8.3 是否在线 decode RGB future

不是硬要求。记录 native future latent/flow；需要可视化或 diagnostic 时再 VAE decode。Action 必须仍来自同一 PSM-conditioned Generator。

---

# 第 9 章 Planner / Reasoner Runtime

## 9.1 Agent interface 先冻结 routing，不先冻结 Agent 策略

Reasoner `generate_reasoner_text()` 走 und/reasoner pathway，不直接经过 Generator-level Local/Global mapper。因此第一版 Planner/Reasoner 不直接消费连续 Memory tensor，而通过 compact summary / metadata 做 routing/query：

```text
current goal + observation summary + memory metadata
→ Planner / Cosmos3 Reasoner
→ MemoryRequest
→ Local/Global retrieval/readout
→ Generator
```

## 9.2 Planner 决定 presence

Planner 可输出：
- `use_local_memory`；
- `use_global_memory`；
- Local horizon/token budget；
- Global semantic/spatial/temporal query + top-k；
- structured subgoal/status。

简单连续操作可以只用 Local；需要重访/out-of-view reference 时再调用 Global；两个模态都不是每个 control step 强制存在。

## 9.3 事件触发

Planner/Reasoner 优先在 episode start、subgoal complete、failure、unexpected state、memory conflict、目标长期不可见/需要历史空间证据时运行。控制频率 Generator 不等待低频 Reasoner 每步运行。

## 9.4 Goal Memory

如果后续发现仅靠 goal-conditioned retrieval 仍不足以保存任务进度，可增加独立 Goal Memory；它作为 Target，不改变 Local/Global 两个基础模态接口。

# 第 10 章 Multi-Embodiment Action Contract

## 10.1 统一原则

不把所有机器人硬转成 DROID 8D。统一的是 framework contract：

```text
raw action
→ embodiment-specific ActionProcessor
→ normalization/padding
→ domain_id + raw_action_dim
→ action2llm
→ shared Cosmos3
→ llm2action
→ mask/denormalize
→ environment action
```

## 10.2 DROID

```text
D_raw = 8
absolute joint position
7 arm joints + gripper
canonical chunk = 16 (released Edge policy request)
```

## 10.3 LIBERO

官方 Nano recipe 作为 contract reference：

```text
D_raw = 10
frame_wise_relative
rotation = rot6d
camera = third-person + wrist concat_view
chunk_length = 16
normalization = quantile_rot
```

v2.0 的第一目标是把该 data/action contract 迁到 Edge-Policy-DROID warm start。

## 10.4 RoboCasa365

不在文档里硬冻结 12D 的每一维含义；G0-R10 从实际 dataset/controller dump schema。若现有数据 transform 已定义 12D/16D state，则按其语义建立独立 `robocasa` domain，不转为 DROID joint_pos。

## 10.5 BEHAVIOR

进入 Stage 5 后根据 R1Pro/实际 robot/controller 获取 `robot.action_dim`，建立独立 whole-body domain。Action dimension 本身不是 Cosmos3 架构限制；数据语义/normalization/controller contract 才是 Gate。

---

# 第 11 章 Depth / Spatial Feature Source

learned depth provider 仍统一 oVDA。正式训练前优先离线 cache，但必须通过 exact temporal parity：

```text
同一 17-frame / recipe-defined temporal sample
├─ official online VAE/oVDA pipeline → A
└─ offline cache pipeline            → B
check A ≈ B + exact source-index mapping
```

注意：Cosmos vision VAE 是时序编码器时，不允许默认“逐 RGB frame 独立 VAE encode 后拼回去”等价于官方 clip encode；缓存粒度由 R03/R04 代码审计确认。

Global Spatial Memory 中 oVDA 首先提供 depth/geometry；还可以保留 RGB semantic feature、pose/trajectory/time。是否直接使用 oVDA intermediate feature 由 R12/R13 决定。

BEHAVIOR mechanism study 可用 simulator depth 隔离 learned-depth error。

# 第 12 章 训练阶段

## 12.1 Stage 0A：官方 checkpoint smoke
R01：Reasoner、Policy、World/Generator、VRAM/latency；不训练。

## 12.2 Stage 0B：Edge-Policy-DROID → LIBERO foundation
R03/R04/R05/R06：只改 data/action contract，PSM 关闭。先 forward/loss、tiny-overfit，再 closed-loop SR > 0。

## 12.3 Stage 1：Temporal Local Memory
R07/R08/R09 后执行 E002–E004。只增加 Local modality / encoder / update / readout；Global、Goal、Agent 关闭。

## 12.4 Stage 2：Spatial Global Memory
R12/R13 后执行 Global store/retrieval/modality 实验。先 Global-only 与 no-memory 对照，再 Local+Global；不同时引入 Goal/Agent。

## 12.5 Stage 3：RoboCasa embodiment
先无 Memory baseline，再分别 +Local、+Global、+Local+Global。RoboCasa ActionProcessor/domain 是独立变量。

## 12.6 Stage 4：Planner / Goal / Reasoner thin slice
先让 Planner 使用同一 `MemoryRequest` 决定 Local/Global presence/query；必要时再增加 Goal Memory。Reasoner 事件级、Generator 控制级。

## 12.7 Stage 5：BEHAVIOR
12 周后 Target。先 whole-body action baseline + Local/Global；只有出现真实多区域瓶颈才做 Region/Place hierarchy。

# 第 13 章 Loss

## 13.1 Native loss

```text
L_total = λ_v * L_vision_flow
        + λ_a * L_action_flow
        + λ_text * L_text(optional)
```

第一版 `λ_text=0` 于 Generator SFT；Reasoner 不和 Action SFT 同批联合训练。官方 LIBERO Action Policy recipe 当前参考 `vision loss_scale=10`、`action_loss_weight=10`，R03/R04 必须从实际 config/runtime 再确认后作为 baseline，不做随意大范围 loss-weight sweep。

## 13.2 Memory loss

第一版没有 `L_local_reconstruction` / `L_global_reconstruction`。Local write/read/compression 与 Local/Global adapters 通过 native target gradient 学习：

```text
Local / Global clean condition
→ shared hidden
→ vision flow + action flow
```

Global store 的非参数化构建部分可 stop-gradient；GlobalSpatialEncoder / retrieval scorer（若 learned）/ adapter 才进入优化链。

若后续发现 collapse，可增加轻量 diagnostic/probe，但不作为主成功指标。

## 13.3 Loss calibration

先记录无 PSM baseline 的 vision/action loss magnitude，再决定 λ 比例；最多做极短 calibration，不做大 grid sweep。

---

# 第 14 章 Freeze / Optimizer / FSDP / EMA / VAE Cache

## 14.1 Edge→LIBERO foundation trainable scope

默认不做 whole-checkpoint full-parameter SFT。沿官方 Action Policy selector 的思路，更新 Generator pathway + action interface，Reasoner/understanding 冻结。按当前 Edge 源码维度估算：

```text
moe_gen + time_embedder + vae2llm + llm2vae
+ action2llm + llm2action + action_modality_embed
≈ 1.423B trainable params
```

这是 generation-side 大规模 selective full-parameter update，不是 LoRA/head-only。R03/R04 必须 dump `requires_grad` 与实际参数量确认。

Memory 阶段新增：

```text
LocalEvidenceEncoder / Local write-read / local_memory2llm      train
GlobalSpatialEncoder / learned retrieval / global_spatial2llm    train where applicable
Reasoner                                                    frozen initially
VAE / oVDA                                                  frozen
```

## 14.2 FSDP2

8×A100 80GB 默认沿 cosmos-framework 使用 FSDP2：参数、梯度、optimizer state 分片；activation 不属于 FSDP 参数状态分片。吞吐优先：
- AC 先用 `selective`，不默认 full checkpoint；
- 若显存明显富余而 parameter all-gather 造成吞吐瓶颈，单独 profile `reshard_after_forward=False`；
- 不为追求最低显存而同时堆叠过重 AC/CP/额外分支。

## 14.3 EMA

官方 LIBERO Action Policy recipe 使用 Power EMA，但 EMA 不是数学上必须。执行口径：
- R04 forward/loss：EMA off；
- R05 tiny-overfit：EMA off；
- R06 formal baseline：默认先 EMA on 对齐官方 recipe；
- 最终 no-memory / +Local / +Global matched experiments 必须保持同一 EMA 选择。

## 14.4 VAE offline cache

可以预编码到本地以减少训练吞吐开销，但必须先验证 online encode 与 offline cache 在**官方 temporal sample contract**下等价。禁止未经验证地逐帧独立 VAE encode。缓存开启后仍需保留 packer 所需 temporal compression / shape metadata。

## 14.5 Precision

BF16 主线。Optimizer 以官方 FusedAdam/实际 recipe 为准；任何 offload/CP/compile 只在 runtime profile 证明有必要时启用。

# 第 15 章 Train / Inference 差异

| 模块 | Train | Inference |
|---|---|---|
| Local evidence alignment/compression | 有 | 有 |
| Local recurrent state | replay/TBPTT/detach | persistent update |
| Global store construction | offline/cache or online | persistent update/query |
| Global retrieval | 有/可 deterministic | 按需 |
| Local modality adapter | 有 | optional |
| Global modality adapter | 有 | optional |
| Vision flow target | 有 | 可不 decode RGB，但 shared generation path 保留 |
| Action flow | 有 | 有 |
| Planner/Reasoner | 后期独立 | 事件触发 |
| Goal Memory | Target | Target |
| oVDA | frozen/cache | optional causal |

硬约束：训练和推理都不能删除已启用 Memory→Generator condition path；Planner 不请求某模态时则该 modality 按设计不存在。

# 第 16 章 Intervention

## 16.1 Local
- Normal；Zero；Shuffle；Stale；Truncated；Sensor-drop / misalignment diagnostic（只用于排错）。

## 16.2 Global
- Normal；Zero；Shuffle；Wrong-view / Wrong-patch；Stale；Top-K truncation；location-only / content-only diagnostic。

## 16.3 Local + Global
- Local-only；Global-only；Both；Neither；保持 backbone、token budget策略、optimizer、训练步数 matched。

## 16.4 实现原则
所有 intervention 必须保持对应 modality 的 tensor shape/index contract 不变，只改变 content；“modality absent”实验则通过 `SequencePlan.has_*` 明确缺失，与“Zero content”区分。

# 第 17 章 评测指标

## 17.1 Execution
- SR；
- steps/time；
- repeated/invalid action；
- retry/re-observe count；
- action smoothness/error（如适用）。

## 17.2 Memory attribution
- Normal vs Zero/Shuffle/Stale/Truncated；
- action output delta；
- future latent/output delta；
- memory-dependent task gain。

## 17.3 World
- native vision flow / latent prediction loss；
- optional decoded future consistency；
- action-conditioned sensitivity。

## 17.4 Agent
- subgoal correctness；
- verifier accuracy；
- recovery success；
- Reasoner call count/latency。

## 17.5 Cost
- peak VRAM；
- policy latency；
- Reasoner latency；
- tokens/packed length；
- PSM memory bytes；
- preprocessing/cache cost。

---

# 第 18 章 Benchmark 分配

## 18.1 LIBERO
- Edge action-policy adaptation；
- no-regression；
- Local PSM first experiment。

## 18.2 LIBERO-Mem / RoboMME / memory-dependent controlled tasks
- 证明长期状态真实有用；
- intervention attribution。

## 18.3 RoboCasa365
- embodiment adaptation；
- state change/out-of-view/multi-stage；
- Local + Global；
- Agent thin slice。

## 18.4 BEHAVIOR-1K
- Target only；
- whole-body/mobile manipulation；
- Regional Global PSM 决策 Gate。

---

# 第 19 章 Code Structure

建议直接 fork `cosmos-framework`：

```text
cosmos-framework/
├── cosmos_framework/
│   ├── model/generator/
│   │   ├── mot/                       # upstream Cosmos3
│   │   └── psm/
│   │       ├── observation_adapter.py
│   │       ├── action_interval_encoder.py
│   │       ├── local_memory.py
│   │       ├── goal_memory.py
│   │       ├── condition_adapter.py
│   │       └── reasoner_readout.py
│   ├── data/generator/action/datasets/
│   │   ├── ... upstream ...
│   │   ├── robocasa_lerobot_dataset.py
│   │   └── behavior_dataset.py          # deferred
│   ├── data/generator/sequence_packing/
│   │   └── psm extensions
│   ├── configs/base/experiment/psm_wma/
│   └── scripts/psm_wma/
│       ├── g0_checkpoint_audit.py
│       ├── g0_action_contract.py
│       ├── g0_psm_pack_smoke.py
│       └── eval_*.py
└── docs_zh/psm_wma/
    ├── 00_project_proposal.md
    ├── 01_technical_survey.md
    └── 02_detailed_design.md
```

原则：尽量新增文件/最小 patch upstream core；对 `SequencePlan/PackedSequence` 的改动集中且有单测。

---

# 第 20 章 Config 设计

核心配置：

```yaml
psm:
  enabled: false
  internal_dim: 1024
  local_tokens: 16
  goal_tokens: 8
  read_tokens: 2
  condition_zero_init: true
  history_steps: TBD
  tbptt_steps: TBD

reasoner:
  enabled: false
  trigger_mode: event
  structured_output: true

depth:
  source: none          # none | ovda | simulator
  ovda_mode: offline_cache

action:
  domain_name: libero
  raw_action_dim: 10
  chunk_length: 16
  execution_horizon: 1
```

不得用一个 config 同时切 dataset + model + PSM + Agent。

---

# 第 21 章 Logging / Checkpoint

每个 checkpoint manifest 记录：
- base model path/hash；
- Edge vs Policy-DROID source；
- action domain/action processor stats；
- PSM K/dim/history/TBPTT；
- SequencePlan mode；
- trainable parameter groups；
- optimizer/scheduler；
- dataset commit/version；
- Runtime Gate JSON。

日志必须能还原：

```text
obs/source index
executed action range
Local update
Goal update/reset
PSM packed indexes
SequencePlan clean/noisy indexes
action/future outputs
Reasoner trigger/result
```

---

# 第 22 章 资源策略

## 22.1 RTX 4090
- config/data unit test；
- tokenizer/action processor；
- PSM modules CPU/small GPU；
- 不承诺 full Edge training。

## 22.2 A100 80GB
- official Edge inference/profile；
- frozen/partial-SFT smoke；
- LIBERO tiny-overfit；
- formal experiments 1–8 cards。

## 22.3 资源 Gate
如果 Edge-Policy-DROID 在目标 resolution/chunk 下无法以可接受成本做训练迭代，先冻结更多 shared weights；再考虑 Predict2-2B fallback，而不是缩减 PSM 归因标准。

---

# 第 23 章 实验矩阵（≤20）

| ID | 环境 | 变量 | 目的 | 状态 |
|---|---|---|---|---|
| E001 | LIBERO | Edge-Policy-LIBERO baseline | 无 Memory 基线 | Must |
| E002 | LIBERO | +Temporal Local | Local 主效果 | Must |
| E003 | LIBERO | longer raw history | Local 容量/历史对照 | Must |
| E004 | LIBERO-Mem/RoboMME | Local interventions | Local 真实使用 | Must |
| E005 | memory/spatial controlled | +Spatial Global | Global 主效果 | Must |
| E006 | same | Local-only / Global-only / Both | 互补性 | Must |
| E007 | same | Global interventions / retrieval controls | 空间证据归因 | Must |
| E008 | RoboCasa | Edge baseline | embodiment 基线 | Must |
| E009 | RoboCasa | +Local | downstream temporal gain | Must |
| E010 | RoboCasa | +Global | downstream spatial gain | Must |
| E011 | RoboCasa | +Local+Global | 组合收益 | Must/Target |
| E012 | LIBERO/RoboCasa | RGB geometry source vs +oVDA | Global construction source | Conditional |
| E013 | RoboCasa | Planner dynamic Local/Global routing | Agent interface | Target |
| E014 | RoboCasa | Cosmos Reasoner subgoal/verifier + MemoryRequest | Agent-memory coupling | Target |
| E015 | - | Goal Memory if needed | task-progress extension | Conditional |
| E016–E020 | - | reserve | 复跑/BEHAVIOR/negative | Reserve |

G0 smoke/tiny-overfit 不计正式实验预算。

---

# 第 24 章 Go / No-Go

## G0 Edge-LIBERO baseline
R01–R06 PASS：official checkpoint finite；forward/loss；tiny-overfit；closed-loop SR>0 可重复。失败不得用 RL/Agent rescue。

## G1 Temporal Local
- time alignment assertions 全通过；
- Local trainable path grads nonzero；
- Local intervention / memory-dependent task 有解释性 gap；
- 普通 fully observable task 无明显 regression。

## G2 Spatial Global
- store 中 pose/time/view/feature provenance 可追溯；
- retrieval top-k 可解释且不会无界增长；
- Global-only 相对 no-memory 有可测 action/world sensitivity；
- Wrong-view/Shuffle/Stale 能产生预期退化；
- Local+Global 至少显示互补或明确负结果。

## G3 RoboCasa
无 Memory baseline 非零稳定；Local/Global 各作为独立变量迁移；不用 Agent/RL 掩盖 zero-SR。

## G4 Planner / Agent
Planner 能通过稳定 `MemoryRequest` 决定 Local/Global presence/query；Reasoner 至少跑通一条 subgoal→memory routing→policy→verifier/reobserve。

## G5 BEHAVIOR
只有真实多房间出现容量/aliasing/跨区域冲突才启动 Region/Place hierarchy。

---

# 第 25 章 Runtime G0 回填合同

| Gate | 输出 | 决定 |
|---|---|---|
| R01 | Edge-Policy-DROID reasoner/policy/world profile | checkpoint 可用性 |
| R02 | Edge vs Policy-DROID source/config or exact checkpoint diff | 继承/冻结范围 |
| R03 | action pipeline + LIBERO parity + trainable dump | foundation contract |
| R04 | Edge×LIBERO forward/loss | adapter correctness |
| R05 | LIBERO tiny overfit | 可学习性 |
| R06 | LIBERO closed-loop baseline | PSM 准入 |
| R07 | Local/Global optional modality packing/attention dummy smoke | new modality contract |
| R08 | temporal multi-sensor alignment/history replay | Local causality |
| R09 | Local fwd/bwd/intervention | E002 准入 |
| R10 | RoboCasa schema/domain | E008 准入 |
| R11 | Planner/Reasoner MemoryRequest smoke | E013/E014 准入 |
| R12 | oVDA + VAE/cache profile/parity | Global source / throughput |
| R13 | Global store/retrieval/modality smoke | E005 准入 |

---

# 第 26 章 12 周执行

## W1：官方能力 + source/action audit
R01–R03。

## W2：LIBERO forward / tiny-overfit
R04–R05。

## W3：LIBERO closed-loop baseline
R06 + E001。

## W4：Temporal Local modality
R07–R09 + E002 smoke。

## W5：Local formal attribution
E002–E004。

## W6：Spatial Global store / retrieval / adapter
R12/R13 + E005 smoke。

## W7：Global formal + Local/Global complementarity
E005–E007。

## W8–W9：RoboCasa embodiment
R10 + E008–E011。

## W10：Planner dynamic modality routing
R11 + E013；Goal Memory only if needed。

## W11：Cosmos Reasoner Agent thin slice
E014 / failure recovery。

## W12：复跑、ablation、成本、demo、文档冻结
不强行进入 Region/Place hierarchy。

# 第 27 章 最终实现判据

PSM-WMA v2.0 的系统闭环必须能用一句数据流解释：

```text
past/current world evidence
→ persistent Local/Global state
→ clean PSM condition in Cosmos3 shared Generator
→ native future world + native robot action
→ environment feedback
→ state update

when needed:
persistent state summary
→ same checkpoint Reasoner
→ subgoal/verifier
→ next Generator query
```

如果最终实现退化为“Memory 只进 auxiliary head”“Reasoner 与 Action 完全无因果联系”“World loss 只训练时存在、Action inference 绕过 shared PSM condition”，均不满足本设计。  
