# PSM-WMA：RGB 表征与 Memory 编码规划增补 v0.1

**日期**：2026-08-16  
**状态**：生效，作为 `PSM-WMA_02_detailed_design_v2.1_frozen.md` 的项目级增补，不静默改写 frozen 文档。  
**作用域**：Cosmos Policy/WAM 视觉编码、Temporal Local Memory、Spatial Global Memory、离线缓存边界。  

---

## 1. 本轮决策

PSM-WMA 不再预设“Policy 与 Memory 必须共享同一种 RGB 编码方式”。

采用以下原则：

1. **Policy/WAM representation 与 Memory representation 解耦。**
2. **当前 Policy/WAM 主路径优先保持 Cosmos 原生视觉分布。**
3. **Local / Global Memory 的 RGB/视觉表征在对应方案调研与 Gate 中单独冻结。**
4. 若后续 Local Memory 明确需要 MoWA-style continuous Wan regular latent，则新增一条 **episode-level memory latent stream/cache**；默认不以它替换 Cosmos Policy 的原生 current-condition 路径。

一句话口径：

```text
Policy：先保持 Cosmos-native。
Memory：从 episode 开头因果积累，但视觉编码器暂不预设必须与 Policy 相同。
```

---

## 2. Policy/WAM：保持 Cosmos-native 视觉编码

LIBERO 当前主路径继续遵循 Cosmos action-policy 的官方 temporal sample contract：

```text
17-frame RGB clip
    ↓
Wan2.2 VAE temporal encode
    ↓
[z0, z1, z2, z3, z4]

z0      : clean current vision condition
z1..z4  : future vision slots；训练时按原生 WAM/Flow-Matching 方式加噪并监督
```

允许将该过程离线本地化：

```text
RGB episode
  ↓ sample native 17-frame windows（可重叠）
Wan2.2 VAE exact-window encode
  ↓
window-local latent cache [z0..z4]
```

约束：
- 保持 Cosmos 原生 camera preprocessing / concat-view / temporal encode 语义；
- cache 必须通过 online-vs-offline parity；
- 不因“以后可能做 Memory”提前把 Policy current condition 从 prime `z0` 改成 whole-episode regular `z_k`；
- 17-frame window 是否全步长滑动、按 policy cadence 采样或采用折中重叠率，属于数据吞吐/存储策略，不改变模型语义。

因此，**离线 cache 本身不是采用 MoWA-style episode latent 的理由**。

---

## 3. Memory：从 episode 开头建立因果历史

对于 anchor/current observation `f_t`：

```text
f0 ... f(t-1) | f_t | f(t+1) ...
<-- memory --> | now | future target
```

定义：

```text
Memory_t = Update/Replay(f0 ... f(t-1), executed actions, state, depth/pose ...)
Current  = Cosmos-native current condition at t
Future   = Cosmos-native future slots / action target
```

首版保持职责清晰：
- Memory 只读取当前时刻之前的 episode prefix，禁止 future leakage；
- Memory 从 **episode start** 开始积累，而不是从当前 17-frame sample 才开始；
- Memory 的更新频率可以与 Policy query / action-chunk replanning cadence 解耦；
- policy 一次预测 16 个动作、执行 `q` 步后再推理，不意味着中间 observation 不能被 Memory 持续记录。

---

## 4. Temporal Local Memory：视觉来源暂不冻结

Local Memory 负责“最近发生了什么”，第一阶段保留以下候选：

### A. 历史 Cosmos prime `z0`

```text
z0(t-k), ..., z0(t-1)
+ state / executed action / optional depth
→ Local compressor
```

特点：保持与 Policy current-condition 接近的原生 latent 统计，不要求 whole-episode Wan encode。

### B. MoWA-style continuous Wan regular latent

```text
whole-episode RGB
→ causal Wan2.2 VAE stream
→ z0, z1, z2, ...
→ Local temporal memory
```

特点：encoder temporal state 连续，更适合作为 continuous temporal state 候选；但它改变 latent 生成历史，不应在 Local 方案尚未冻结前强制替换 Policy 的 native `z0`。

### C. 独立视觉/多模态 evidence encoder

```text
RGB / visual feature
+ depth / pose
+ robot state
+ executed action interval
→ LocalEvidenceEncoder
→ Local Memory
```

该路线与 v2.1 的 `LocalEvidenceEncoder` 契约一致。

**当前结论：Local 有较大概率会利用 Wan2.2 VAE feature/latent，但尚无依据要求必须使用 continuous regular latent。** 由后续 Local 调研与 R08/R09 实验冻结。

---

## 5. Spatial Global Memory：默认不绑定 Wan2.2 VAE

Global Memory 负责“以前在哪里见过什么、空间关系如何、对象/区域如何变化”，更自然的证据结构为：

```text
RGB semantic feature
+ depth / geometry
+ camera pose / trajectory
+ xyz / region / view direction
+ timestamp / confidence
→ persistent spatial store
→ retrieval/compression
→ Global clean tokens
```

Wan2.2 latent 可以作为视觉 feature 候选之一，但当前不把它设为 Global 的硬依赖。

因此第一优先级仍是保留完整可追溯的 episode-level 原始证据：

```text
RGB
Depth（若有/可离线生成）
Pose
Robot state
Executed actions
Timestamp / source index
```

---

## 6. 推荐缓存分层

不要强求一份 latent cache 同时服务 Policy 与 Memory。

### 6.1 必选：Policy native cache

```text
native 17-frame window
→ Wan2.2 VAE
→ [z0..z4]
```

用途：Edge→LIBERO SFT、无 Memory baseline、后续 matched +Memory 对照。

### 6.2 保留：episode raw observation archive

```text
RGB / depth / pose / state / action / timestamp / source index
```

用途：Local/Global 方案冻结后重新构建 Memory evidence，避免当前过早绑定 encoder。

### 6.3 可选：Memory episode latent cache

只有当 Local 方案明确选择 continuous Wan temporal latent 时新增：

```text
whole episode RGB
→ causal Wan2.2 VAE
→ [z0,z1,z2,...]
```

该 cache 服务 Memory；是否进一步把 regular `z_k` 接入 Policy current condition，必须作为**独立架构实验**验证，不与“Memory 需要连续 latent”自动等同。

---

## 7. 对原 Regular Episode Latent 规划的修订

此前 `cosmos-framework/docs_zh/psm_wma/REGULAR_EPISODE_LATENT_OVERFIT.md` 将：

```text
Cosmos native prime z0
→ whole-episode regular z_k
```

作为当前优先实验方向。

本增补将其**降级为候选实验，而非当前主线**：

- 当前没有必要为了离线 cache 改变 Cosmos 原生 latent distribution；
- 当前也没有必要为了尚未冻结的 Memory 方案提前改变 Policy current-condition distribution；
- 如果后续 Local Memory 研究证明 continuous Wan regular latent 明显必要，再启用该实验；
- 该子工程文档不再作为 PSM-WMA 项目级规划的权威入口。

项目级规划、架构决策和跨模块实验边界统一记录在 `wxwy/psm_wma/docs/build/` 与 `MEMORY/DECISIONS.md`；`cosmos-framework` 子模块内只保留与具体代码实现直接相关的局部说明/测试文档。

---

## 8. 当前执行顺序

```text
G0 / Edge→LIBERO baseline
  ↓
Cosmos-native 17-frame Policy cache / parity
  ↓
Memory 调研与 representation freeze
  ├─ Local：prime-z0 history / continuous Wan / independent evidence encoder
  └─ Global：RGB semantic + geometry/depth + pose/time + retrieval
  ↓
分别实现 Local / Global memory cache or encoder
  ↓
matched ablation：no-memory / +Local / +Global / +Local+Global
```

在 Memory representation freeze 之前，不启动“为了统一 RGB encoder 而统一改成 MoWA-style whole-episode latent”的工程改造。

---

## 9. 研究假设边界

当前要验证的不是“MoWA-style latent 一定优于 Cosmos-native latent”，而是：

1. Cosmos-native Policy/WAM baseline 能否稳定成立；
2. Local Memory 最需要什么时间表征；
3. Global Memory 最需要什么空间表征；
4. Memory representation 是否有必要与 Policy representation 共享 encoder/latent space；
5. 若共享 continuous Wan latent，收益是否足以抵消对 Policy 原生分布的改变。

只有第 4/5 项得到正证据后，才考虑把 whole-episode regular latent 从 Memory 支路进一步升级到 Policy 主路径。
