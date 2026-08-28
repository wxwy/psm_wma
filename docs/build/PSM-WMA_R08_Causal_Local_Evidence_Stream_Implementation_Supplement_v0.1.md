# PSM-WMA R08 Causal Local Evidence Stream 实现补充设计 v0.1

> 状态：**R08 implementation contract / 设计补充说明**  
> 日期：2026-08-28  
> 适用分支：根仓 V2，子模块 cosmos-framework/v2  
> 上游基线：R07 runtime Gate 已关闭（root 13af0e3，submodule 10bc410）  
> 权威关系：本文件补充 PSM-WMA_02_detailed_design_v2.1_frozen.md 与 PSM-WMA_G0_runtime_execution_plan_v0.6_aligned.md 的 R08 实现细节；若与旧的“R08 直接形成最终 Local Memory”措辞冲突，以本文件的 R08/R09 分工为准。  
> 重要边界：**R08 只实现 causal local evidence stream + 最小 stateless replay readout，不实现 persistent recurrent memory；R09 才实现 recurrent latent / RoboTTT-style TTT fast-weight memory。**

---

# 0. Executive Summary

R07 已经证明：

~~~text
Local clean optional modality
→ Cosmos3 shared generator
→ Future Vision prediction
→ Action prediction
~~~

并完成：
- Local default-off old/new exact parity；
- Local clean/no-noise/no-loss contract；
- native Vision/Action mRoPE 不变；
- Local adapter / modality embedding 真实进入 optimizer；
- Local 参数真实更新；
- fixed-weight Normal / Zero / Shuffle sensitivity：Local content 改变能够可归因地改变 Future + Action。

因此 R08 不再修改 R07 的 packing / mRoPE / clean-modality 语义。R08 的任务只有一个：

> **把 R07 的 dummy Local 替换成严格因果、按真实 episode 时间轴构造的历史 evidence stream，并证明数据源、索引、动作执行边界和视觉表征不存在 future leakage。**

R08 输出的是：

~~~text
E_{t-H}, ..., E_{t-1}
~~~

即每个历史时刻的 causal evidence sequence。

R08 **不把这些 evidence token 本身定义成最终 memory state**。为了能通过 R07 Local interface 做 runtime smoke，R08 允许一个极小、无持久状态的 LocalReplayReadout：

~~~text
causal evidence sequence
→ stateless replay readout
→ K_local temporary readout token(s)
→ existing R07 Local modality
→ Cosmos
~~~

真正的 persistent temporal memory 在 R09：

~~~text
R09-A: recurrent latent / gated state
R09-B: RoboTTT-style TTT fast weights
~~~

RoboTTT 的对齐点不是“把历史 token 拼长”，而是：
- temporal stream 每步进入 memory backend；
- persistent recurrent state 固定大小；
- TTT fast weights 作为 recurrent memory state；
- 训练可用 TBPTT，state 跨 segment 保留、梯度 detach；
- 推理时持续更新 state。

PSM-WMA 不直接复制 RoboTTT 在 GR00T 主干内插 TTT layer 的 topology；当前主线保持 R07 已验证的独立 Local modality：

~~~text
evidence stream
→ LocalMemoryBackend
→ LocalReadout
→ local_memory2llm
→ Cosmos
~~~

参考：
- RoboTTT: https://arxiv.org/abs/2607.15275
- NVIDIA project: https://research.nvidia.com/labs/gear/robottt/

---

# 1. R07 → R08 Handoff Contract

## 1.1 R07 已冻结，不得在 R08 重开

以下接口视为稳定基础设施：

~~~text
Text | Local(clean) | Vision | Action
~~~

Local：
- 独立 optional modality；
- 不加 FM noise；
- 不采 Local timestep；
- 不进入 mse_loss_indexes；
- 无 Local decoder；
- 无独立 Local FM loss；
- 通过 local_memory2llm + local_memory_modality_embed 进入 Cosmos；
- Local 的加入不得推进 native Vision/Action mRoPE cursor。

R08 不重新设计：
- Local packed order；
- Local mRoPE slot strategy；
- R07 optimizer selector；
- Local decoder/loss；
- Global Memory；
- Agent / Planner / RL。

## 1.2 R07 的含义边界

R07 只证明：

~~~text
Local channel is usable.
~~~

R07 **没有证明**：

~~~text
模型已经具备真实 temporal memory。
~~~

R08/R09 才开始验证真实 history / persistent memory。

---

# 2. R08 / R09 分工冻结

## 2.1 R08 = Causal Local Evidence Stream

R08 回答：

> **“每个历史时刻，究竟把什么事实作为可写入 Local Memory 的证据？”**

负责：
1. episode 内历史索引；
2. observation / state / executed action 的时间对齐；
3. future leakage 禁止规则；
4. historical visual representation 的因果资格；
5. per-step evidence tensor；
6. episode boundary / padding / mask；
7. 一个仅用于 R08 runtime smoke 的 stateless replay readout。

不负责：
- recurrent hidden state；
- GRU；
- TTT fast weights；
- TBPTT；
- persistent inference state；
- state checkpoint/runtime serialization；
- 长上下文 scaling。

## 2.2 R09 = Persistent Temporal Local Memory

R09 回答：

> **“evidence stream 到达后，如何持续压缩成固定大小、跨时间更新的 memory state？”**

冻结两个 backend family：

### R09-A — recurrent_latent baseline

~~~text
E_t + M_{t-1}
→ gated recurrent update / GRU-like compressor
→ M_t
→ LocalReadout
~~~

### R09-B — ttt_fast_weight

~~~text
E_t + W_{t-1}
→ self-supervised TTT-KVB-style inner update
→ W_t
→ LocalReadout
~~~

RoboTTT-style 对齐的核心是 W_t 为 fast-weight recurrent state，而不是历史缓存。

R09 才允许：
- segment replay；
- TBPTT；
- state carry + detach；
- fast-weight initialization / update rule；
- context-length scaling；
- recurrent vs TTT A/B。

---

# 3. 当前 LIBERO Source Audit：R08 必须基于真实源码，不得假设字段已经可用

## 3.1 当前 loader 已存在

当前：

cosmos-framework/cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py

已经读取：

~~~text
index
episode_index
task_index
timestamp
action
~~~

当前 sample 已显式输出：

~~~text
episode_index
start_frame
task_index
window_frame_indices
latent_source_frame_indices
video_latent (cache mode)
~~~

当前 action：
- parquet raw: 7D [dpos3, axis-angle3, gripper1]
- dataset conversion: 10D [dpos3, rot6d6, gripper1]
- current policy target window: action[start : start+16]
- transform 后进入现有 ActionProcessor normalization / padding。

## 3.2 数据集有 state，但当前 loader 尚未读取

当前 NVIDIA LIBERO_LeRobot_v3 schema 有：

~~~text
observation.state: float32 [8]
~~~

但当前 LIBEROLeRobotDataset 的 parquet read columns 中没有 observation.state。

因此 R08 必须显式做 source extension，不能写：

~~~text
state 已经在 data_dict 里
~~~

R08 Step 0 必须核：
1. 四个 suite 的 meta/info.json state shape 一致；
2. parquet 中 observation.state 与 index / timestamp / episode 一一对齐；
3. state 全 finite；
4. state 语义仅按 dataset schema 记录，不自行推断重复 gripper 字段含义；
5. 再决定是否把 state 纳入 R08 v0.1 evidence。

### R08 v0.1 决策

若上述 audit PASS：

~~~text
D_state_raw = 8
~~~

将 state 纳入 R08 evidence。

若任一 suite schema 不一致或存在无法解释的异常：
- R08 不阻塞 visual + executed-action 主链；
- state 标记 optional，并单独修复，不允许错误 broadcast / truncate。

---

# 4. Canonical Time Semantics

## 4.1 当前决策 anchor

定义当前 policy query 时刻：

~~~text
anchor = t
current native Vision = obs_t
current action target = a_t, a_{t+1}, ..., a_{t+15}
~~~

当前 R08 Local history 只能来自：

~~~text
j < t
~~~

即：

~~~text
LocalHistory(t) = { E_j | max(0,t-H_hist) <= j <= t-1 }
~~~

## 4.2 action 的允许边界

按当前 LIBERO frame-wise-relative policy contract：

~~~text
obs_j -- executed a_j --> obs_{j+1}
~~~

所以在 anchor t：

允许：

~~~text
a_{t-1}
~~~

因为它已经执行，并产生了当前 obs_t。

禁止：

~~~text
a_t, a_{t+1}, ...
~~~

因为它们属于当前/未来 action target。

### R08 per-step evidence 定义

~~~text
E_j = Encode(
    visual_j,
    state_j(optional),
    executed_action_j,
    age/Δt_j
)
where j < t
~~~

注意：
- executed_action_j 必须来自 dataset 历史行；
- 不得从当前 target action chunk 的前缀/后缀“倒推历史”；
- predicted but unexecuted suffix 永远禁止进入 Local。

## 4.3 episode start

当 t < H_hist：

~~~text
valid history length = t
~~~

不得从前一个 episode 填充。

统一输出：

~~~text
history_mask [H_hist] bool
~~~

左侧 padding：
- tensor 可 zero-pad；
- history_mask=False；
- readout 必须 mask-aware。

---

# 5. R08 v0.1 History Horizon

R08 smoke 暂定：

~~~text
H_hist_smoke = 16 raw environment steps
~~~

原因：
- 与当前 action chunk=16 对齐，便于人工审计；
- 足以验证多步真实 history，不把 R08 变成长上下文性能实验；
- 20 FPS 下约 0.8 s，仅作为 plumbing/evidence smoke。

**这不是最终 Local horizon。**

最终 context scaling：
- R09 后另做；
- RoboTTT-style 1K/8K scaling 不属于 R08。

R08 至少测试：

~~~text
H=0   # no-history control
H=1   # immediate history
H=16  # R08 smoke
~~~

其中 H=0 不应产生“伪 Local history”；可通过 Local absent control 或 empty-mask contract 实现。

---

# 6. R08-Gate-0：Historical Visual Representation Causality

这是 R08 的第一个硬 Gate。

## 6.1 为什么不能直接使用 exact-window z0

现有 exact-window cache：

~~~text
17 RGB frames
→ Wan2.2 VAE
→ latent [5,48,H_lat,W_lat]
~~~

manifest / sample 记录：

~~~text
window_frame_indices = start ... start+16
latent_source_frame_indices = start, start+4, start+8, start+12, start+16
~~~

R08 候选历史视觉：

~~~text
z0(i) := latent(window_start=i)[0]
~~~

但只有在 z0(i) 不依赖 i+1... future suffix 时，才能把它当作 causal history evidence。

所以必须先做 suffix-invariance diagnostic。

## 6.2 Gate-0 test

固定第一帧：

~~~text
f_i
~~~

构造至少两种 17-frame 输入：

~~~text
A = [f_i, native_suffix_A]
B = [f_i, different_valid_suffix_B]
~~~

要求：
- index 0 的 RGB 完全相同；
- suffix 真正不同；
- 使用与当前 cache 一致的 resize / uint8 conversion / concat_view / vision_vae.py contract；
- deterministic VAE runtime；
- 只比较 temporal latent index 0。

记录：

~~~text
sha256(z0_A)
sha256(z0_B)
max_abs(z0_A-z0_B)
l2
relative_l2
~~~

### coverage

最低：

~~~text
4 suites
× 4 start_frame % 4 classes
× >=4 anchors/class
= >=64 anchors
~~~

推荐：

~~~text
>=128 anchors
~~~

必须覆盖：
- concat_view；
- 当前 bf16 compute/runtime contract；
- episode 内不同位置；
- 不同任务/episode。

可增加 repeat-first-frame suffix 作为 stress probe，但**不能只用这种 OOD suffix 作唯一判断**。

## 6.3 Gate 判定

强 PASS：

~~~text
all tested z0 pairs bitwise identical
~~~

容忍 PASS：

~~~text
max_abs <= 1e-6
and no systematic suffix-dependent change
~~~

FAIL：

~~~text
max_abs > threshold
or stable suffix-dependent nonzero signal
~~~

一旦 FAIL：
- 禁止复用 exact-window z0 作为 causal historical visual；
- 不允许“先接进去再看效果”。

## 6.4 FAIL fallback order

### Fallback A — dedicated single-frame causal Wan prime

先验证 Wan VAE 是否支持：

~~~text
1 frame
→ 1 temporal latent
~~~

如果支持且稳定：
- 建独立 per-frame causal-prime cache；
- 只使用当前 frame，不引入 future；
- 与 Policy exact-window cache 分离；
- 不替换 Policy native current-condition cache。

### Fallback B — independent frozen RGB history encoder

若 single-frame Wan route 不稳定/不支持：

~~~text
historical RGB
→ frozen lightweight RGB encoder
→ visual summary
~~~

R08 只需保证 causal + repeatable；最终 visual evidence representation 留给后续 matched experiment。

---

# 7. z0 PASS 时的 R08 Visual Summary Baseline

若 Gate-0 PASS，R08 v0.1 允许复用 cache 中每个历史 frame 对应 window 的 latent[0]：

~~~text
history frame i
→ exact-window cache window_start=i
→ z0_i [48,H_lat,W_lat]
~~~

当前 concat_view 是横向 third-person + wrist。

为了避免把每个完整 latent map 都送到 temporal path，R08 smoke 使用 view-aware fixed summary：

~~~text
z0_i
→ adaptive_avg_pool2d(output_size=(1,2))
→ flatten
→ V_i [96]
~~~

解释：
- 左/右两列分别保留两个 concat view 的粗粒度身份；
- 不绑定当前 H_lat/W_lat；
- 无 trainable spatial compressor；
- 只是 R08 evidence baseline，不是最终视觉记忆表征。

若后续证明该 summary 太弱，作为 R09 后的独立 representation experiment，不在 R08 临时换成复杂 encoder。

---

# 8. State Evidence

Gate-0 与 state 独立。

若 state audit PASS：

~~~text
state_raw_j [8]
~~~

R08 不把 state 拼进 Policy native state path；只作为 Local evidence。

推荐：

~~~text
state_raw
→ training-split per-dim normalization
→ state_norm [8]
→ Linear/MLP
~~~

要求：
- stats 只由 train split 生成；
- stats 写 machine-readable artifact；
- std floor；
- 不用 val/test 统计；
- 不擅自把 axis-angle 改成 rot6d，除非单独验证；
- 保留 raw state 用于 trace。

---

# 9. Executed Action Evidence

## 9.1 Source

历史 action 从同 episode parquet row 获取：

~~~text
raw 7D
→ existing LIBERO _build_frame_wise_action()
→ 10D rot6d
~~~

## 9.2 Normalization

**不得复制一份新的 action normalization 数学。**

R08 应复用现有 resolved action normalizer / normalization contract，使：

~~~text
history_action_norm[j]
~~~

与同一 raw action 若作为当前 policy action target 时的前 10 个 normalized real channels一致。

历史 action evidence 不需要 pad 到 max_action_dim=64；Local encoder 输入可保留真实 10D。

必须有 CPU parity test：

~~~text
same raw action
→ current ActionProcessor path
vs
→ R08 history-action normalization helper

first 10 real channels exact / tolerance-equal
~~~

## 9.3 No predicted suffix

R08 不允许：
- 当前 action chunk a_t...；
- model prediction；
- denoised candidate；
- future GT action；
进入 Local history。

---

# 10. R08 Sample Schema

R08 dataset 输出建议：

~~~python
{
    # existing current sample
    "episode_index": scalar,
    "start_frame": scalar,          # anchor t
    "window_frame_indices": [17],
    "latent_source_frame_indices": [5],
    "video_latent": [5,48,H,W],
    "action": [16,10],              # before model padding

    # new R08 history
    "history_frame_indices": LongTensor[H_hist],
    "history_mask": BoolTensor[H_hist],

    # representation chosen by Gate-0
    "history_visual_summary": FloatTensor[H_hist,D_v],

    # state: only if source audit PASS
    "history_state_raw": FloatTensor[H_hist,8] | optional,
    "history_state": FloatTensor[H_hist,8] | optional,

    # executed actions j<t
    "history_action_raw": FloatTensor[H_hist,10],
    "history_action": FloatTensor[H_hist,10],

    "history_age_steps": LongTensor[H_hist],
    "history_dt_s": FloatTensor[H_hist,1],
}
~~~

### shape contract

R08 smoke：

~~~text
H_hist = 16
D_v = 96 if z0 + pool(1,2)
D_state = 8 if enabled
D_action = 10
~~~

最终 Local backend dimension / K_local 不在 R08 冻结。

---

# 11. Per-step LocalEvidenceEncoder

R08 需要把多 source 映射成统一 per-step evidence：

~~~text
visual_j
state_j
executed_action_j
age_j / dt_j
      ↓
LocalEvidenceEncoder
      ↓
E_j
~~~

第一版保持极简：

~~~python
v = VisualProj(history_visual_summary)      # [B,H,D_e]
s = StateProj(history_state)                # optional
a = ActionProj(history_action)              # [B,H,D_e]
p = AgeEmbedding(history_age_steps)         # [B,H,D_e]

E = LayerNorm(v + s + a + p)
E *= history_mask
~~~

推荐：

~~~text
D_e = 256 or 512
~~~

这是 R08 implementation profile，不是项目级永久冻结。

要求：
- source adapter 分开；
- 不把 history source 先 concat 成超大 raw tensor再单线性层；
- mask 必须贯穿；
- no future target；
- no current noisy action/vision target。

---

# 12. R08 Stateless LocalReplayReadout

为了验证真实 history 已经通过 R07 Local 影响 Future/Action，R08 需要一个临时 readout。

它不是 memory backend。

建议：

~~~text
E_hist [B,H,D_e]
+ mask
       ↓
masked_mean
+
latest_valid
       ↓
concat [B,2D_e]
       ↓
MLP
       ↓
Local token [B,1,D_local_input]
       ↓
existing local_memory2llm
~~~

即：

~~~text
K_local_read = 1
~~~

与 R07 dummy 默认 token 数保持一致，尽量减少变量。

为什么不用 Transformer/GRU：
- Transformer 会把 R08 变成新的 temporal model；
- GRU 已属于 R09-A；
- TTT 属于 R09-B；
- R08 只需要证明真实 causal history source + alignment + Local path。

R09 开始后，此 LocalReplayReadout 可保留为 stateless control baseline。

---

# 13. Training Data Flow

R08 offline training：

~~~text
anchor t
│
├─ current policy sample
│    obs_t ... future target window
│    action target a_t...
│
└─ causal replay
     j = max(0,t-H) ... t-1
     ├─ visual_j
     ├─ state_j
     ├─ executed_action_j
     └─ age/dt
          ↓
      LocalEvidenceEncoder
          ↓
      E_history
          ↓
      Stateless LocalReplayReadout
          ↓
      local_memory
          ↓
Text | Local | Vision | Action
          ↓
Cosmos
          ↓
L_vision + L_action
~~~

R08 不新增 Local loss。

LocalEvidenceEncoder + readout 通过：

~~~text
native L_vision + L_action
~~~

获得梯度。

---

# 14. Inference / Closed-loop Semantics

R08 自身可以先做 offline matched smoke，但数据语义必须与未来 closed-loop 一致。

在真实闭环：

~~~text
decision t:
history contains transitions up to a_{t-1}
current obs_t stays in native Vision
predict action chunk starting a_t
execute only q steps
only executed actions become eligible for future Local history
~~~

若 q=1：

~~~text
obs_t
→ predict a_t...
→ execute a_t only
→ observe obs_{t+1}
→ a_t now becomes historical executed action
→ next query uses it in Local history
~~~

绝不把未执行 suffix 写入 Local。

---

# 15. Leakage Rules — Hard FAIL Conditions

任意一条出现即 R08 FAIL：

1. history frame index >= t；
2. history action index >= t；
3. current target action chunk 被拼入 history；
4. predicted but unexecuted action 进入 history；
5. exact-window z0 在 Gate-0 FAIL 后仍被使用；
6. state/action 从其他 episode 取值；
7. padding 位置 history_mask=False 仍影响 readout；
8. DataLoader shuffle 导致 history 与 anchor sample identity 不一致；
9. Local absent 时 R07 no-memory path 不再保持原 contract；
10. 为了 R08 修改 native Vision/Action mRoPE。

---

# 16. Required Tests

## 16.1 CPU — index and boundary

必须覆盖：

### episode start

~~~text
t=0:
history_mask all false
no cross-episode access
~~~

### partial history

~~~text
t=3, H=16:
3 valid history steps
13 padded
~~~

### full history

~~~text
t>=16:
16 valid
indices = t-16 ... t-1
~~~

### last historical action

~~~text
last history action = a_{t-1}
first current target action = a_t
must be different source rows
~~~

## 16.2 CPU — identity trace

每个 sample 至少 trace：

~~~text
episode_index
anchor t
history_frame_indices
history_action source indices
current target action source indices
history_mask
~~~

断言同 episode、严格小于 t。

## 16.3 CPU — state alignment

若 state enabled：

~~~text
state[j] row index
==
timestamp[j]
==
episode[j]
==
visual source j
~~~

## 16.4 CPU — action normalization parity

见 §9.2。

## 16.5 Gate-0 visual causality

见 §6。

## 16.6 R07 regression

R08 disabled：
- no-memory old/current contract 不变；
- R07 Local dummy mode 仍可运行；
- R08 fields optional；
- 不修改 native packing positions。

---

# 17. GPU Runtime Gates

## Gate A — R08 causal history forward

固定：

~~~text
iter2800 baseline
R08 enabled
H=16
stateless replay readout
~~~

要求：
- forward finite；
- backward finite；
- LocalEvidenceEncoder/readout params有 grad；
- optimizer selector 包含新增 R08 trainable params；
- real parameter update PASS；
- save/reload PASS。

## Gate B — real-history intervention sensitivity

同一训练后 checkpoint、固定 weight、同一 batch/noise：

~~~text
Normal History
Zero History
Shuffle History
~~~

Shuffle 必须保持：
- current sample 不变；
- history shape/mask 不变；
- 只将不同 sample 的历史 payload 对换。

要求：

~~~text
all non-history invariants exact
history payload changes
preds_vision changes
preds_action changes
~~~

这验证：

~~~text
real causal history
→ Local
→ Future + Action
~~~

## Gate C — causal ablation

至少：

~~~text
H=0 / Local absent
H=1
H=16
~~~

R08 DONE 不要求 SR 必须提升，但需要：
- pipeline causal；
- real-history sensitivity；
- training/runtime stable；
- evidence provenance 完整。

真正的 matched SR gain 留给 R09 backend 冻结后。

---

# 18. R08 DONE Criteria

必须全部满足：

~~~text
[ ] R07 runtime Gate remains DONE
[ ] Gate-0 historical visual representation decision recorded
[ ] no future-suffix visual leakage
[ ] state source audit complete (enabled or explicitly deferred)
[ ] history action strictly executed j<t
[ ] episode boundary safe
[ ] history mask correct
[ ] per-step evidence sequence generated
[ ] stateless replay readout only; no recurrent/TTT implementation
[ ] R08 parameters train/update
[ ] save/reload
[ ] fixed-weight history Normal/Zero/Shuffle sensitivity
[ ] Future + Action both respond
[ ] no-memory / R07 regression
[ ] machine-readable provenance retained
[ ] raw sidecars kept until independent review completes
~~~

R08 DONE 的含义：

> **真实 causal history evidence 已经可靠进入 Local channel。**

R08 DONE 不等价于：

> **最终 Local Memory backend 已冻结。**

---

# 19. R09 Handoff Schema

R09 只依赖 R08 输出：

~~~python
LocalEvidenceBatch = {
    "evidence": FloatTensor[B,H,D_e],
    "mask": BoolTensor[B,H],
    "episode_id": ...,
    "frame_indices": ...,
    "age_steps": ...,
}
~~~

R09 不应重新读取 raw parquet / RGB 来重做时间对齐。

目标：

~~~text
R08:
raw timeline
→ causal E_t

R09:
E_t + persistent state
→ persistent memory
~~~

---

# 20. RoboTTT Alignment for R09-B

RoboTTT 的关键机制：

~~~text
x_t
→ key/value projection
→ self-supervised KVB loss
→ gradient update fast weights W_{t-1} → W_t
→ apply updated fast-weight model
~~~

其 fast weights：
- training/inference 都更新；
- 是固定大小 recurrent state；
- 历史压缩进 weights，不保存不断增长的 KV history；
- sequence training 使用 TBPTT 解决长序列显存；
- state 跨 segment carry，gradient 在 segment boundary detach。

PSM-WMA R09-B 目标对齐这些“memory dynamics”，但不直接复制 topology：

~~~text
R08 E_t
→ TTT LocalMemoryBackend
→ fast weights W_t
→ LocalReadout
→ existing R07 Local modality
→ Cosmos Future + Action
~~~

而不是首版就：

~~~text
在 Cosmos 每层 attention 后插 TTT layer
~~~

原因：
1. R07 独立 Local modality 已有严格 parity / sensitivity 证据；
2. 先把 temporal backend 隔离，A/B 更容易归因；
3. 避免同时修改 Cosmos shared MoT；
4. 后续若 independent TTT backend明显受限，再单独评估 in-backbone TTT。

---

# 21. Expected Code Touches

R08 开始前 Codex 必须先只读确认最新路径；以下为预计范围，不要求机械照搬文件名。

## 子模块

主要可能修改：

~~~text
cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py
cosmos_framework/data/generator/action/utils/transforms.py
cosmos_framework/data/generator/joint_dataloader.py
cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py
cosmos_framework/model/generator/cosmos3_vfm_network.py
cosmos_framework/model/generator/omni_mot_model.py
~~~

建议新建独立模块：

~~~text
cosmos_framework/data/generator/action/local_history.py
cosmos_framework/model/generator/local_evidence_encoder.py
~~~

名称可按 repo style 调整。

## 根仓

建议新增：

~~~text
tools/g0/verify_r08_z0_suffix_invariance.py
tools/g0/verify_r08_history_alignment.py
tools/g0/compare_r08_history_sensitivity.py
artifacts/g0/r08/...
~~~

---

# 22. Files / Areas R08 Must Not Touch Without New Review

禁止顺手改：

~~~text
Global spatial store / retrieval
Agent / Planner
Reasoner routing
RL
VLA action definition
LIBERO benchmark protocol
Vision/Action FM targets
native decoder
native Vision/Action mRoPE
R07 clean Local semantics
~~~

不要为了 R08：
- 改 Policy current-condition exact-window cache contract；
- 把 Policy native vision representation 换掉；
- 把 state 拼进原生 Vision/Action path；
- 做 TTT/GRU；
- 做 Global。

---

# 23. Codex Execution Order

必须按顺序：

## Step 0 — Source audit only
输出 machine-readable audit：
- current LIBERO fields；
- state schema；
- action timeline；
- cache window/index contract；
- history source feasibility。

不改模型。

## Step 1 — R08-Gate-0 suffix invariance
只实现 diagnostic。
不接训练。

Gate-0 review 后才决定 historical visual route。

## Step 2 — Causal history dataset contract
实现：
- history indices；
- mask；
- visual source；
- optional state；
- executed action；
- age/dt。

CPU only。

## Step 3 — Alignment tests
episode boundary / action off-by-one / state alignment / action normalization parity。

## Step 4 — LocalEvidenceEncoder
只做 per-step evidence，不做 persistent state。

## Step 5 — Stateless LocalReplayReadout
把 real history 转成 1 个临时 Local token，复用 R07 Local interface。

## Step 6 — Runtime trace
单 batch：

~~~text
anchor
history source ids
Local token
Vision/Action positions
Future/Action outputs
~~~

## Step 7 — GPU Gate A
finite / grad / optimizer / update / save-reload。

## Step 8 — GPU Gate B
fixed-weight Normal / Zero / Shuffle real-history sensitivity。

## Step 9 — Independent review
raw sidecar 在 review 结束前不得删除。

## Step 10 — R08 DONE
只在 review 后关闭。

然后才允许 R09。

---

# 24. R08 Review Checklist for ChatGPT/mm/Kimi

Reviewer 必须核：

### Causality

~~~text
history visual index < anchor
history action index < anchor
no future observation
no target action leakage
no predicted suffix
~~~

### Representation

~~~text
Gate-0 evidence exists
PASS/FAIL route followed
cache contract unchanged
~~~

### Data identity

~~~text
same episode
timestamp aligned
mask aligned
no DataLoader sample-cross contamination
~~~

### Model boundary

~~~text
Local remains clean condition
no Local loss/noise
native V/A mRoPE unchanged
R08 disabled regression
~~~

### Scope

~~~text
no recurrent state
no TTT
no Global
no Agent
no RL
~~~

---

# 25. Design Decision Summary

从本文件起，PSM-WMA Local 主线使用以下正式语言：

~~~text
R07:
Local optional-modality infrastructure

R08:
Causal Local Evidence Stream
(history source + alignment + per-step encoding)

R09:
Persistent Temporal Local Memory
(A: recurrent latent, B: RoboTTT-style TTT fast weights)
~~~

并冻结：

> **K_local tokens 是 memory readout / Cosmos interface，不应被等同于 memory 本体。**

最终目标：

~~~text
historical stream
→ E_t
→ persistent memory state M_t / W_t
→ LocalReadout
→ Local tokens
→ Cosmos
→ Future + Action
~~~

R08 只完成到：

~~~text
historical stream
→ E_t
→ stateless readout
→ Local tokens
~~~

以保证 R09 可以干净比较 recurrent latent 和 RoboTTT-style fast-weight memory，而不会重新引入历史数据/causality 变量。
