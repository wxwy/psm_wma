# PSM-WMA G0 工程核验报告
## Static Audit v0.6 — Cosmos3 Native World-Action-Reasoner Route Locked

**日期**：2026-08-12  
**上游**：技术调研 v1.7、详细设计 v2.1  
**目的**：冻结“哪些官方 Cosmos3 资产已存在、哪些扩展点可用、哪些仍必须 Runtime 验证”。

---

# 1. 静态结论

**v0.6 新增结论（2026-08-12）**：PSM 不再实现成单一 `psm` field，而是两个独立 optional clean modalities：`local_memory` 与 `global_memory`。Local 由时间对齐的多源近期 evidence 经 learned compression 产生；Global 由 persistent spatial store 检索/压缩产生。二者分别 mapper 到 Cosmos hidden space；无 decoder/noise/loss target；presence 由 `SequencePlan` 明确声明，后续 Planner 可动态路由。

1. **PSM-WMA 主工程母体改为 NVIDIA `cosmos-framework`。** StarVLA 不再是主训练/模型框架，只保留 baseline/fallback 参考。  
2. **主初始化 checkpoint 改为 `Cosmos3-Edge-Policy-DROID` 4B。** 裸 `Cosmos3-Edge` 是 foundation/reference。  
3. Cosmos3 Generator 原生包含 Vision/Action/Sound continuous modality adapter；Action 通过 `action2llm/llm2action + action_modality_embed` 进入 shared MoT。  
4. `SequencePlan/PackedSequence` 原生支持 modality presence 与 clean/noisy target 路由；缺失 modality 可以为 `None`。  
5. Action 使用 `DomainAwareLinear` + `domain_id/raw_action_dim`，因此架构不是固定 8D；DROID 8D 只是已发布 policy checkpoint 的 embodiment。  
6. 官方公开 Action SFT stack 完整；当前显式 DROID/LIBERO exact recipe 以 Cosmos3-Nano 为主。LIBERO recipe 已冻结 10D `frame_wise_relative` + rot6d、chunk16 等 contract。  
7. `Cosmos3-Edge-Policy-DROID` 同 checkpoint 保留 Reasoner；Reasoner 与 Generator 是两条 inference pathway，不是同一次 decode。  
8. Memory 第一版最小改动是：新增 `local_memory` 与 `global_memory` 两个独立 optional clean condition modalities，而不是统一 `psm` span，也不增加独立 WorldStateAdapter、FutureHead 或 LayerwiseFM bridge。  
9. Reasoner 不直接经过 VFM modality embedder；首期通过 compact memory metadata/summary 生成 `MemoryRequest`，由 Planner 决定 Local/Global presence/query，再把连续 Memory token 送入 Generator。  
10. oVDA 路线保持不变：learned depth 唯一 provider，且为 conditional。

# 2. 静态 Gate 状态

| Gate | 项目 | 状态 | 静态结论 |
|---|---|---|---|
| S01 | cosmos-framework 可作为训练/推理母体 | PASS | Generator/Reasoner/SFT/serving/checkpoint 均在同仓 |
| S02 | Edge-Policy-DROID 官方 checkpoint | PASS | 4B policy checkpoint 已发布 |
| S03 | Reasoner 能力存在 | PASS | model/reasoner path 保留；Runtime 性能仍需测 |
| S04 | Native Action modality | PASS | `action2llm/llm2action/action_modality_embed` |
| S05 | Multi-domain action abstraction | PASS | `DomainAwareLinear`, `domain_id`, `raw_action_dim` |
| S06 | SequencePlan variable modality | PASS | `vision/action/sound` 可为 None；clean/noisy 分离 |
| S07 | LIBERO Action SFT contract | PASS | official Nano recipe 存在 |
| S08 | Edge exact LIBERO recipe | NOT-PASS | 未见独立 Edge-LIBERO official recipe；需本项目 adaptation |
| S09 | Local/Global clean modality insertion | PASS-DESIGN | packing/data结构允许扩展；Runtime attention/shape 需验证 |
| S10 | Reasoner continuous Memory direct injection | NOT-PASS | reasoner path bypass VFM embedder；首期用 compact summary→MemoryRequest routing |
| S11 | RoboCasa action domain | PENDING | 需 schema/runtime dump |
| S12 | BEHAVIOR whole-body domain | DEFERRED | Stage5 后冻结 |
| S13 | oVDA | PASS-EXTERNAL | official code/weights；Runtime profile conditional |

# 3. 关键源码锚点

## 3.1 `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py`

静态确认：

```text
Vision:
vae2llm / llm2vae

Action:
action2llm / llm2action
+ action_modality_embed
+ DomainAwareLinear

Sound:
sound2llm / llm2sound
```

`action_gen=True` 时要求 `vision_gen=True`，说明 Action generation 被设计为 world/visual generation 体系的一部分，而非 action-only standalone model。

## 3.2 `sequence_packing/types.py` / `modality.py` / `sequence.py`

静态确认：
- `SequencePlan.has_vision/has_action/has_sound`；
- `condition_frame_indexes_*`；
- `ModalityData.sequence_indexes`；
- `mse_loss_indexes`；
- `condition_mask`；
- `noisy_frame_indexes`；
- Action `domain_id/raw_action_dim`。

因此“一次 forward 输出什么”由数据/plan 显式定义，不是模型根据输入自动 router。

## 3.3 Reasoner

`generate_reasoner_text()` 只走 reasoner/und pathway，并明确绕过 VFM-level generation embedders/head。因此：
- 同 checkpoint 可以 Reasoning 和 Action；
- 但首期不是一次 joint decode；
- PSM Generator condition 与 Reasoner context 必须分开 readout。

# 4. DROID / LIBERO Action Contract

## 4.1 DROID released Edge policy

```text
raw action dim = 8
absolute joint position
7 arm joints + gripper
canonical released action chunk = 16×8
```

## 4.2 LIBERO official Cosmos3 recipe

```text
raw action dim = 10
frame_wise_relative
rotation = rot6d
chunk_length = 16
20 Hz dataset contract
third-person + wrist concat view
normalization = quantile_rot
```

结论：DROID→LIBERO 不是 reshape，而是新 embodiment/action-domain adaptation。

# 5. Local / Global Memory 扩展点静态设计

新增最小对象：

```text
SequencePlan.has_local_memory
SequencePlan.has_global_memory

PackedSequence.local_memory
PackedSequence.global_memory

local_memory2llm
local_memory_modality_embed

global_spatial2llm
global_memory_modality_embed
```

共同 contract：
- always clean；
- no noise timestep；
- no `mse_loss_indexes`；
- no output decoder；
- absent modality 不 pack；
- noisy Vision/Action 可 attend；
- Memory 不能读取同一步 noisy target。

不同 contract：
- Local position/evidence 以 timestamp / temporal order / sensor alignment 为中心；
- Global position/evidence 以 world/relative pose / camera view / historical time / retrieval provenance 为中心；
- 两者不得先 concat 后共用同一个 mapper。

源码事实：当前 `PackedSequence` 仍只原生列出 vision/action/sound，因此新增 Local/Global 需要扩展 dataclass、packer、scatter/encode 与 attention/position audit；`SequencePlan` 本身是显式 modality-presence 路由，适合 optional Memory。

Global 强备选：利用 Cosmos3 已有 control-style multi-vision path，将 spatial store 查询/重投影成 aligned depth/semantic reference；该路线不等于现成 Global checkpoint 能力，只复用 conditioning topology。

静态风险：mRoPE / attention split / FSDP graph 一致性必须由 R07/R13 runtime smoke 验证。

# 6. 旧主线废止项

以下 v0.4 Static 结论不再有效：
- “StarVLA 继续作为工程母体”；
- “LayerwiseFM 是主 Action consumer”；
- “Cosmos3-Edge 只能 World/Feature Host”；
- “不直接复用 Edge-Policy-DROID action capability”；
- `WorldStateAdapter/ActionBridge/ActionConditionedFutureHead` 作为 Must-have。

这些保留为历史记录，不再约束 v2.0。

# 6A. Foundation 训练 / 并行静态事实补充

- Official-style Edge→LIBERO adaptation 默认选择 Generator pathway + action interface，Reasoner frozen；按当前 Edge 源码维度估算约 **1.423B** trainable，R03/R04 runtime dump 确认；
- Action Policy native supervision = Vision flow + Action flow；Memory 第一版无 reconstruction loss；condition_mask 只在 noised target 位置产生 FM supervision，Action 只监督 `raw_action_dim`；
- cosmos-framework 当前使用 FSDP2 `fully_shard`；默认多卡应分片 parameter / gradient / optimizer state。activation 由 AC 单独处理，先 selective；
- official LIBERO Action recipe 使用 Power EMA；R04/R05 admission smoke 关闭，R06 baseline 默认先开启以减少 recipe drift；
- vision VAE 可做 offline cache，但必须先验证 official temporal clip encode 与 cache latent parity，不能默认逐帧独立 encode 等价；
- oVDA 作为 Global geometry source 时同样必须保存 RGB/depth/pose source-index/timestamp 对齐。

# 7. Runtime 前不得硬冻结的项

- Edge-Policy-DROID 实际 VRAM/latency；
- Edge→LIBERO config 最小差分；
- DROID policy checkpoint 中 shared generator 与 action projection 的权重变化范围；
- new LIBERO domain slot 是否 fresh init / partial reuse；
- `K_local/K_goal/K_psm`；
- PSM mRoPE/position implementation；
- shared generator 解冻范围；
- RoboCasa exact action/state schema；
- Reasoner 在目标 agent task 的实际质量。

# 8. Static → Runtime 交接

Runtime Gate 顺序：

```text
R01 official Edge-Policy-DROID smoke
→ R02 Edge vs Policy-DROID checkpoint audit
→ R03 action pipeline/domain audit
→ R04 Edge×LIBERO forward/loss
→ R05 tiny overfit
→ R06 closed-loop baseline
→ R07 Local/Global optional-modality packing/attention
→ R08 temporal multi-sensor/history alignment
→ R09 Local fwd/bwd/intervention
→ R10 RoboCasa domain
→ R11 Planner/Reasoner MemoryRequest
→ R12 oVDA/VAE cache parity
→ R13 Global store/retrieval/modality
```

只有 R06 PASS 后才允许把 PSM 算法实验结果归因给 Memory。  
