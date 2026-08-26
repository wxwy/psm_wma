# PSM-WMA Temporal Local Memory 详细设计补充 v0.1

**日期**：2026-08-26  
**状态**：implementation addendum / 待 R07-R09 实测冻结  
**上游冻结文档**：`docs/build/PSM-WMA_02_detailed_design_v2.1_frozen.md`  
**执行计划**：`docs/build/PSM-WMA_G0_runtime_execution_plan_v0.6_aligned.md`  
**长期决策**：`MEMORY/DECISIONS.md` D014 / D015  
**工程母体**：`cosmos-framework`  

> 本文件是 v2.1 frozen 详细设计中 **Temporal Local Memory** 的版本化实现补充，不覆盖 frozen 主文档。  
> 本文件负责把 R07–R09 从“模块级设计”细化为 Codex 可直接审计和实现的 dataflow / tensor / causality / state-management contract。  
> 标记为 **[FROZEN]** 的内容继承现有项目决策；**[V0 DEFAULT]** 是当前推荐的最小实现；**[TBD/GATE]** 必须由 R08/R09 实测后才能冻结。

---

# 0. 执行摘要

## 0.1 Local Memory 的唯一研究问题

Temporal Local Memory 解决：

> **当前观测不足以表达“刚刚发生过什么”时，如何以固定预算保存近期时序状态，并让这些历史证据真实进入 Cosmos3 的 native future-world / action path。**

它不是 Global Spatial Memory 的缩小版，也不负责长期地图、目标位置、跨房间空间检索。

首期主链：

```text
historical observations / state / executed actions
                    │
                    ▼
          Temporal Alignment
                    │
                    ▼
           Local Evidence Encoder
                    │
                    ▼
      Temporal Compressor / State
                    │
                    ▼
             Local Readout
                    │
                    ▼
             local_memory2llm
                    │
                    ▼
     Local clean optional-modality tokens
                    │
                    ▼
            Cosmos3 Generator
              ┌─────┴─────┐
              ▼           ▼
         Future Vision   Action
```

## 0.2 首期推荐路线

```text
R07  dummy Local clean modality
  ↓
R08  causal history replay + timeline alignment
  ↓
     history prime z0 + robot state + executed action
  ↓
R09-A recurrent_latent baseline
  ↓
Normal / Zero / Shuffle / Stale / Truncated intervention
  ↓
No-Memory vs +Local matched experiment
  ↓
R09-B 仅替换 temporal compressor 为 TTT fast-weight
```

**[FROZEN]** Local/Global 必须独立；首期只做 Local。  
**[FROZEN]** Local 是 always-clean condition，不是 flow/diffusion target。  
**[V0 DEFAULT]** Local visual evidence 优先尝试已有 Cosmos native prime `z0`，不先建立 MoWA-style whole-episode Policy latent。  
**[V0 DEFAULT]** 第一版 evidence 只使用 `historical z0 + historical robot state + executed action interval`。Depth/pose 留给后续，不与 Local v0 同时引入。  
**[V0 DEFAULT]** 第一版 temporal compressor 先做简单 recurrent baseline；TTT 只替换 compressor，不改变 evidence / Local modality contract。  

---

# 1. 范围与非目标

## 1.1 本补充负责

- R07 Local optional clean modality 的接入合同；
- R08 episode-prefix / history replay / source-index 对齐；
- Local v0 visual/state/action evidence representation；
- LocalEvidenceEncoder 的输入输出 contract；
- recurrent Local state / readout / reset / detach 语义；
- TTT backend 的接口边界；
- train vs inference state lifecycle；
- Local intervention / attribution；
- tensor shape、日志和 Gate artifact。

## 1.2 首期明确不做

- Global store / spatial retrieval / oVDA geometry；
- Planner / Reasoner / Agent routing；
- RL / online policy optimization；
- MoWA whole-episode latent 替换 Policy native latent；
- current robot state 直接加入原 Policy 输入（这是独立变量，不能和 Local 主实验混跑）；
- Local reconstruction auxiliary loss；
- 从零训练新的视觉 backbone；
- 一开始就把 TTT 插入 Cosmos shared MoT。

---

# 2. R06 依赖与 matched baseline 原则

Local 正式实验只能从项目冻结的 No-Memory baseline 继续。用户在 2026-08-26 已明确倾向直接使用现有 `iter_000002800` 结果作为 R06 baseline；R06 的最终状态由 `SESSION.md` / `TODO.md` / `MEMORY/DECISIONS.md` 另行收口，本文件不修改 R06 记录。

后续 `No Memory` vs `+Local` 必须匹配：

```text
base checkpoint / initialization
LIBERO dataset + task set
guidance
sampler / denoise steps
max episode steps
prediction horizon
execution horizon
policy re-query cadence
eval seeds / initial states（能固定时必须固定）
EMA / precision / action normalization
```

Local 实验中不得顺便加入 current-state-to-policy、CFG tuning、RL、Agent 或新的视觉 backbone。

---

# 3. 时间与因果合同

## 3.1 当前 policy anchor

对当前决策 anchor `t`：

```text
f0 ... f(t-H) ... f(t-2) f(t-1) | ft | f(t+1) ... f(t+16)
└──────────── Local history ───────┘ now └── native future target ──┘
```

**[FROZEN]** 决策 `t` 使用的 Local state 只能由 `<= t-1` 的证据构造：

```text
M_local(t) = F(history <= t-1)
```

`ft` 属于当前 Policy observation，不属于本次决策的历史写入；完成本次决策/观察后，`ft` 才可用于下一次 memory update。

## 3.2 Executed Action 语义

Local 只记录**实际执行**的动作：

```text
obs_i
+ actions actually executed after obs_i
+ obs_(i+1)
→ memory update
```

禁止：
- predicted but unexecuted action chunk suffix；
- target future action；
- future demonstration action 被提前写入 Local。

离线 replay 与在线执行必须使用同一语义。

## 3.3 三条时间轴必须显式保存

每个 Local sample 至少可追溯：

```text
raw frame/source index
VAE latent source index
policy anchor / executed-action range
```

不得通过“数组位置碰巧相同”推断多源对齐。

---

# 4. R08 Local History Schema

建议新增/构造独立的 `LocalHistoryEvidence`，不要把所有字段永久塞进基础 LIBERO sample contract。

```python
LocalHistoryEvidence = {
    "episode_id": int,
    "anchor_source_index": int,          # current policy anchor t

    "history_source_indices": Tensor[H],
    "history_timestamps": Tensor[H],
    "history_valid_mask": Tensor[H],

    # visual candidate v0
    "history_prime_latent": Tensor[H, 48, 16, 32],

    # actual dims must be audited, not guessed
    "history_robot_state": Tensor[H, D_state],

    # ragged intervals may be padded
    "history_action_intervals": Tensor[H, L_max, 10],
    "history_action_mask": Tensor[H, L_max],
    "history_action_ranges": Tensor[H, 2],

    # audit
    "policy_window_frame_indices": Tensor[17],
    "policy_latent_source_frame_indices": Tensor[5],
    "target_action_range": Tensor[2],
}
```

### 4.1 `D_state` 不允许预设

`D_state` 必须由 R08 从当前 LIBERO parquet/schema/runtime dump 得到。不要因为 DROID、RoboCasa 或历史项目里的 state 维度而写死 LIBERO state shape。

### 4.2 action interval v0 canonical representation

**[V0 DEFAULT]** 使用与 LIBERO Policy 相同的 post-transform / normalized 10D action 语义：

```text
[dpos(3), rot6d(6), gripper(1)]
```

但只保存真正执行过的 action。在线时应从“实际被选中并执行的 model-space action”形成相同 representation；必要时同时记录 env-space action 作为 audit，不把 env-space 与 model-space 混为一谈。

---

# 5. Local visual evidence v0：historical prime `z0`

## 5.1 为什么优先用现有 prime `z0`

当前 exact-window cache 已按 stride=1 保存每个合法 policy window：

```text
window @ i : [z0_i, z1_i, z2_i, z3_i, z4_i]
shape      : [5, 48, 16, 32]
```

其中当前 Policy 仍保持 Cosmos native fresh-window contract。Local v0 可以仅抽取每个历史 window 的 `z0_i`：

```text
history visual evidence
= z0_(t-H), ..., z0_(t-1)
```

优点：
- 不新增视觉 backbone；
- 不改变 Policy representation；
- 直接复用已经验证过 parity 的 cache；
- 将实验变量集中在“是否有 learned temporal state”。

## 5.2 **硬 Gate：prime z0 future-suffix invariance**

这是 Local v0 使用 exact-window cache 的前置条件。

虽然 Wan VAE 设计为 causal，仍不得仅凭架构假设“17-frame window 的 `z0` 绝不受后续 16 帧影响”。因为对历史时刻 `i<t`，cache window `i:i+16` 可能包含决策时刻 `t` 之后的离线 future frame。

R08 必须做以下实证：

```text
same first frame f_i
suffix A = real future frames
suffix B = shuffled / replaced / synthetic different future frames

encode [f_i + suffix A] -> z0_A
encode [f_i + suffix B] -> z0_B

assert z0_A ≈ z0_B within strict numerical tolerance
```

至少覆盖：
- 多个 episode；
- 多个 `start_frame % 4`；
- concat_view；
- 当前正式 VAE/runtime precision contract。

只有 PASS 后，`history_prime_latent` 才允许直接来自 exact-window cache。

**FAIL 分流**：
1. 建立独立 causal prime cache（只产生当前 prime representation，并验证与 Policy z0 distribution 的关系）；或
2. 改用独立 RGB/VLM evidence encoder；
3. 不允许用带 future leakage 的 cached `z0` 继续训练 Local。

## 5.3 cache I/O

R08/R09 smoke 先复用已有 episode-sharded exact-window cache，只读取每个历史 window 的 `latent[0]`。

若 profiling 发现 episode `.pt` 中重复 future latents 导致 Local replay I/O/RAM 成为瓶颈，可派生一个只包含：

```text
episode_id
start_frame
prime_z0
source metadata
```

的 compact prime cache。它只是已有 verified latent 的派生索引/存储优化，不改变 representation，不应和算法实验一起统计为新变量。

---

# 6. Per-step LocalEvidenceEncoder v0

目标：把每个历史时刻的视觉、state、executed action 压成固定宽度 evidence：

```text
(z0_i, state_i, executed_action_interval_i)
→ e_i ∈ R[D_local]
```

首期不把完整 `[48,16,32]` 当 512 个 token 直接送入 temporal compressor。

## 6.1 Visual summary

**[V0 DEFAULT]** 对 concat-view prime latent 做轻量 view-aware pooling：

```text
z0_i [48,16,32]
    ↓ adaptive pool spatial H, preserve two width halves
v_i [2,48]
    ↓ shared VisualMLP / Linear
v_i [2,D_v]
```

等价实现可以用 `AdaptiveAvgPool2d((1,2))`，使两个输出 token 大致对应 third-person / wrist 两个 concat 区域。

说明：
- 这是 smoke/default，不是最终视觉表征冻结；
- 若实际 VAE receptive field 使中心边界混合，该方案仍只是低成本 summary，不宣称严格 camera disentanglement；
- R09 若发现明显信息不足，再比较 2×2 pooling、learned query pooling 或少量 register tokens；不要首版直接复制全 spatial grid。

## 6.2 State encoder

```text
state_i [D_state]
→ LayerNorm / normalization according to audited stats
→ MLP
→ s_i [D_s]
```

当前 robot state 直接进入 Policy 是另一个独立研究变量；Local v0 只允许 state 经历史 Local path 进入模型。

## 6.3 Executed ActionIntervalEncoder

对每个 history step 的已执行 interval：

```text
a_i [L_i,10] + mask
→ masked mean
+ last valid action
→ concat [20]
→ MLP
a_i_summary [D_a]
```

当 execution horizon=1 时 mean 与 last 相同，但保留 interval contract，方便后续 q>1 不改 schema。

## 6.4 Fusion

**[V0 DEFAULT]** 简单、可审计的 late fusion：

```text
flatten/project(v_i)
+ state embedding s_i
+ action interval embedding a_i
(+ optional delta-time scalar/embedding)
→ concat
→ FusionMLP + LayerNorm
→ e_i [D_local]
```

首期不做 cross-modal Transformer，不引入新的 attention stack。

输出：

```text
E_history [B,H,D_local]
```

`D_local` 在 R09 profile 前保持可配置。

---

# 7. R09-A：recurrent Local baseline

## 7.1 backend contract

**[V0 DEFAULT]** 第一版使用简单 gated recurrent state（优先 `GRUCell` 或等价最小 gated recurrent block）：

```text
M_0 = zeros
for i in chronological history:
    M_i = GRUCell(e_i, M_(i-1))

M_local = M_last
```

目的不是证明 GRU 是最终最优，而是得到最小 learned causal temporal baseline。

## 7.2 state shape

```text
E_history : [B,H,D_local]
M_i       : [B,D_mem]
```

初始可令 `D_mem == D_local` 简化实现；两者都保持 config-driven。

## 7.3 LocalReadout

```text
M_local [B,D_mem]
→ Linear/MLP
→ [B,K_local,D_local]
→ local_memory2llm
→ [B,K_local,D_cosmos]
→ + local_memory_modality_embed
```

`K_local` 是 token budget，不在本文件冻结。R07 smoke 可用一个很小的固定值（例如 1–4）验证接口，但正式值由 R09 VRAM/latency/sensitivity 决定。

## 7.4 Local token position semantics

Local readout token 已经是历史压缩结果，不再逐 token 对应原始 frame。

**[V0 DEFAULT]**：
- 历史先后顺序由 recurrent update 保留；
- historical age / Δt 如有需要编码进 evidence content；
- Local readout 在 Cosmos packing 中使用独立 modality/type embedding；
- 首期不要直接发明负时间 mRoPE 或把 Local token 假装成 Vision H/W patch；
- 具体 position id 必须在 R07 根据当前真实 `SequencePlan/PackedSequence` runtime 入口核验后实现。

---

# 8. R07：Local optional clean modality contract

R07 不读取真实 history，只先实现 Local 的“插座”。

必须支持：

```text
A. has_local_memory = false
   → Local 完全不 pack

B. has_local_memory = true + Normal dummy content

C. has_local_memory = true + Zero content

D. has_local_memory = true + Shuffle content
```

A 与 C 必须语义不同。

Local modality **[FROZEN]**：
- always clean；
- no noise timestep；
- no RF/FM interpolation；
- no `mse_loss_indexes`；
- no Local decoder；
- native action / future vision 可以 attend Local；
- Local 不读取同 sample 的 noisy/future target 形成泄漏。

### 8.1 No-Memory parity

`has_local_memory=false` 必须保持现有 baseline path 无回归。固定 seed 下至少检查：
- packed token/index contract；
- action/future output；
- native loss。

### 8.2 zero-init 与 sensitivity 的判定

v2.1 config 保留 `condition_zero_init`。如果正式实现采用 zero-init，为避免“结构正确但初始 sensitivity=0”产生假 FAIL：
- R07 首次结构测试只要求 clean/index/loss contract 正确；
- 可在 1–10 个最小 optimizer steps 后再测 Normal/Zero/Shuffle sensitivity；
- 不要为了 sensitivity 人为破坏 function-preserving init。

---

# 9. R08：history replay 与 causality Gate

R08 的任务不是训练 Memory，而是证明输入历史是真的历史。

每个抽样 anchor 必须断言：

1. history 不跨 episode；
2. `history_source_indices < anchor_source_index`；
3. visual/state/action 都能回溯到同 source timeline；
4. action range 只覆盖已执行动作；
5. target action range 与 history action range 无交集；
6. current/future Policy window 不被误写入 Local；
7. `prime z0 future-suffix invariance` PASS；
8. offline replay 与 online update 的 state transition 语义一致；
9. padding/mask 不把无效 history 当真 evidence；
10. episode reset 后 state 清零/初始化正确。

建议 artifact：

```text
artifacts/g0/r08/R08_temporal_local_history_alignment.json
```

至少记录：
- sampled episode/anchor ids；
- history source indexes；
- action ranges；
- target range；
- z0 suffix-invariance max/mean error；
- cross-episode violation count；
- future-leakage violation count；
- status PASS/FAIL。

---

# 10. Train / Inference state lifecycle

## 10.1 R09 smoke：window replay

为了先验证机制，允许固定历史窗口：

```text
history = [max(0,t-H), ..., t-1]
M_start = zeros
replay history
→ M_local(t)
→ supervise current Policy sample
```

这是 **Local-v0 windowed learned memory**，不能宣称已经证明“整 episode persistent training”。

## 10.2 Formal persistent Local：segment TBPTT

只有 R09-A 证明 Local path 正确且有 sensitivity 后，再进入 persistent state 训练。候选：

```text
episode segment 0
→ M_S
→ detach
segment 1
→ M_2S
→ detach
...
```

要求：
- segment 按 episode chronological order；
- state 可以跨 segment 携带，但 autograd graph 在边界 detach；
- 不跨 episode；
- multi-worker / multi-env state key 必须至少包含 episode/env identity；
- learned model weights 进入 checkpoint；runtime recurrent state 不进入 optimizer state；
- inference 可以在整个 episode 持续更新，不受 TBPTT segment 长度限制。

如果当前 `IterableDataset` / shuffle 机制不适合 stateful segment carry，R09 先保持 sample-internal replay，不允许为了“持久化”暗中依赖 batch 顺序。

---

# 11. R09-B：TTT fast-weight 替换边界

TTT 不是第二套 Local 系统，只替换 temporal compressor：

```text
相同 History Schema
相同 LocalEvidenceEncoder
相同 evidence token budget
        │
        ├─ A: recurrent_latent
        └─ B: ttt_fast_weight

相同 LocalReadout
相同 local_memory2llm
相同 Cosmos optional-modality contract
相同 native vision/action losses
```

比较必须尽量 matched：
- evidence representation；
- history sampling；
- Local output token budget；
- training steps；
- backbone trainable scope；
- eval protocol。

TTT 额外 Gate：
- fast weights 同 episode 内真的更新；
- segment detach 后数值 state 连续而 autograd graph 不连续；
- episode reset 正确；
- fast-state 不误入 slow-weight optimizer/checkpoint lifecycle；
- multi-rank state ownership 明确。

R09-B 前不得直接把 RoboTTT 原结构插入 shared Cosmos MoT。

---

# 12. Loss 与 trainable scope

第一版不增加 Local reconstruction loss：

```text
L_total = λ_v * L_vision_flow + λ_a * L_action_flow
```

梯度链：

```text
native action/future loss
→ Cosmos shared attention
→ Local clean tokens
→ local_memory2llm
→ LocalReadout
→ recurrent/TTT compressor
→ LocalEvidenceEncoder
```

Local 模块必须观测到 finite/nonzero grad；若 zero-init 导致首步 upstream grad 为 0，应记录 init 语义并在后续最小 step 验证梯度开始流动，不能误判结构断路。

首期建议训练：
- LocalEvidenceEncoder；
- recurrent/TTT backend；
- LocalReadout；
- `local_memory2llm` / modality embedding；
- Cosmos 其余 trainable scope必须与 matched baseline 约定一致，不在 Local 实验中随意扩大/缩小。

---

# 13. 推荐 tensor dataflow（v0）

以下维度中仅 Cosmos/cache 已知维度可视为当前事实；`H/D_state/D_local/K_local` 必须 runtime/config 驱动。

```text
Policy exact-window cached latent
[B,5,48,16,32]
        │
        └─ Policy native path unchanged

Historical windows @ i<t
[B,H,5,48,16,32]
        │ select latent[:, :, 0]
        ▼
history prime z0
[B,H,48,16,32]
        │
        ▼
view-aware spatial pooling
[B,H,2,48]
        │
        ▼
VisualMLP
[B,H,2,D_v]

history state
[B,H,D_state]
        │ StateMLP
        ▼
[B,H,D_s]

executed action intervals
[B,H,L_max,10] + mask
        │ mean + last + MLP
        ▼
[B,H,D_a]

visual + state + action
        │ FusionMLP
        ▼
E_history
[B,H,D_local]
        │
        ▼
Recurrent / TTT compressor
        ▼
M_local
[B,D_mem]
        │
        ▼
LocalReadout
[B,K_local,D_local]
        │
        ▼
local_memory2llm + modality embed
[B,K_local,2048]
        │ clean optional modality
        ▼
Cosmos PackedSequence
        │
        ├─ future vision flow
        └─ action flow
```

### 13.1 dtype

- exact-window cache 当前存储/runtime dtype 以实际 manifest/loader 为准；不要从 `vae compute_dtype=bf16` 推断磁盘 tensor dtype；
- LocalEvidenceEncoder 可以在读取后 cast 到训练 precision；
- normalization / pooling / recurrent numerical precision应通过 R09 smoke 记录，不在设计阶段硬写。

---

# 14. Intervention 与归因

Local 必须至少支持：

```text
Absent     : has_local_memory=false
Normal     : 正常历史
Zero       : same shape/index, content=0
Shuffle    : 同 batch/episode 内打乱内容，保持 shape/index
Stale      : 使用更旧 state/readout
Truncated  : 减少有效 history
```

可选 diagnostic：
- state-only；
- visual-only；
- action-only；
- wrong action interval；
- history temporal permutation。

主指标：
- action output delta；
- future/world output delta；
- native losses；
- closed-loop SR（正式 experiment 才看）；
- peak VRAM / latency / state bytes。

**不能只凭训练 loss 下降证明模型使用了 Local。** Normal vs Zero/Shuffle/Stale 必须产生可解释 sensitivity，最终还要看 matched closed-loop。

---

# 15. R07-R09 Gate 顺序与 PASS

## R07 — Local optional modality plumbing

PASS：
- No-Memory path 无回归；
- absent 与 present+zero 可区分；
- Local 独立 pack；
- clean-only / no-loss-index；
- forward/backward finite；
- Local adapter/embed 有梯度；
- 最小训练后 Normal/Zero/Shuffle 对 action 或 future 有非零 sensitivity。

## R08 — causal history replay

PASS：
- timeline/source-index assertions 全过；
- no cross-episode；
- no future action/observation leakage；
- executed-action contract 正确；
- prime z0 future-suffix invariance PASS，或启用无泄漏 fallback representation；
- offline replay 与 online state update 语义一致。

## R09-A — recurrent baseline

PASS：
- 至少 100 optimizer steps finite；
- Local evidence/write/read/adapter grads nonzero；
- episode reset / batch isolation 正确；
- Normal/Zero/Shuffle/Stale/Truncated 全能 forward；
- action/future sensitivity 可测；
- VRAM/latency/state bytes 可接受。

## R09-B — TTT candidate

在 A PASS 后才开始。除复用 A 的全部 Gate 外，还必须通过 fast-weight state 专项 assertions。

---

# 16. 与“更长 raw history”的必要对照

正式 Local 主实验不能只比较：

```text
No Memory vs +Local
```

还必须保留 v2.1 E003 的逻辑：

```text
A. No Memory / native current observation
B. longer raw/recent history without learned persistent compressor
C. + learned Local Memory
```

目的：区分提升来自：
- 单纯给模型更多帧；还是
- learned compression / recurrent state 本身。

如果 B≈C，则不能把收益包装成 persistent memory 算法优势。

---

# 17. 建议代码边界（实现前必须 runtime audit）

以下仅为职责建议，不是未经审计的强制文件路径：

```text
cosmos_framework/model/generator/psm/
├── local_evidence.py
├── local_memory.py
├── local_memory_adapter.py
└── temporal_alignment.py
```

可能需要的最小 upstream core patch：
- `SequencePlan.has_local_memory`；
- `PackedSequence.local_memory`；
- packer/index/attention 支持；
- Generator `local_memory2llm` / modality embedding 注册。

R07 编码前 Codex 必须从当前 `cosmos-framework/v2` HEAD 输出真实：
- `SequencePlan` class/module/file；
- `PackedSequence` class/module/file；
- packer；
- position/mRoPE；
- attention mask；
- mse/noise index；
- FSDP/AC parameter registration；
- 实际 import trace。

不要照旧文档文件名盲改。

---

# 18. Config 建议

```yaml
psm:
  local:
    enabled: false
    optional: true

    # representation
    visual_source: prime_z0          # v0 candidate; R08 causality gate required
    use_robot_state: true
    use_executed_action: true
    use_depth: false                 # Local v0 off
    use_pose: false                  # Local v0 off

    # evidence
    visual_pool: view_avg_1x2        # v0 smoke default
    evidence_dim: TBD

    # history
    history_steps: TBD
    history_stride: TBD

    # backend
    backend: recurrent_latent        # R09-A first
    state_dim: TBD
    token_budget: TBD
    tbptt_steps: TBD

    # optional later
    ttt_inner_update: TBD
    ttt_segment_steps: TBD

    # intervention/debug
    mode: normal                     # normal|zero|shuffle|stale|truncated
```

所有 `TBD` 禁止在实现前变成“项目已冻结常量”。R07/R08 smoke 可以给 CLI/config 临时默认值，但 artifact 必须记录实际值。

---

# 19. Codex 执行清单

Codex 读取本文件后不要一次实现 R07-R09。

## Step 1 — R07 source audit

只读当前 runtime，输出 file:line/import trace 和最小 patch 设计。

## Step 2 — R07 implementation

实现 dummy Local clean modality + unit/forward/backward/sensitivity smoke；生成 R07 JSON；独立审查后再关 Gate。

## Step 3 — R08 history builder

实现 source-index/time/action alignment；首先做 `prime z0 future-suffix invariance` Gate；未 PASS 禁止将 cached prime z0 用作 Local history。

## Step 4 — R09-A recurrent

实现 LocalEvidenceEncoder + recurrent state + LocalReadout；先 window replay smoke，再做 intervention / gradient / state reset。

## Step 5 — matched Local experiment

R09-A 工程 Gate PASS 后才跑 No-Memory vs +Local；保持 R06 contract matched。

## Step 6 — R09-B TTT

只有 recurrent baseline 已正确且值得继续时，才替换 compressor 为 TTT fast-weight。

---

# 20. 本补充的冻结边界总结

## 已冻结 / 不应再讨论

- Policy/WAM 继续 Cosmos native exact-window visual contract；
- Memory representation 与 Policy representation 解耦；
- Local/Global 是独立 optional clean modalities；
- Local 不作为 FM target；
- Local 只读 causal history + executed action；
- Local 必须进入 native Action/Future path；
- recurrent 与 TTT 通过同一 Local interface 比较；
- no-memory baseline 失败时不能靠 Memory/RL/Agent rescue。

## 当前推荐但待 Gate

- historical prime `z0` 作为 Local visual v0；
- 1×2 view-aware pooling；
- historical state + executed action interval；
- late fusion MLP；
- GRU-style recurrent baseline；
- fixed small Local token readout；
- window replay → persistent TBPTT 分阶段实现。

## 必须由实验冻结

- `H / history_stride`；
- `D_local / D_mem`；
- `K_local`；
- visual pooling/token 数；
- state normalization；
- action interval encoder细节；
- recurrent具体 hidden size / layer 数；
- TBPTT segment；
- TTT update rule；
- continuous Wan regular latent 是否优于 prime z0；
- Local 是否需要 depth/pose；
- formal persistent state training sampler。

---

# 21. 一句话 implementation contract

```text
past-only verified visual/state/executed-action evidence
→ aligned per-step E_t
→ smallest correct recurrent Local state first
→ fixed-budget clean Local tokens
→ native Cosmos3 future/action losses
→ intervention proves the model actually uses history
→ only then replace compressor with TTT or enlarge representation
```
