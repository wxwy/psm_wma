# PSM-WMA：RGB 表征与 Memory 编码规划 v0.1

**日期**：2026-08-16  
**状态**：生效，作为 `PSM-WMA_02_detailed_design_v2.1_frozen.md` 的项目级增补，不静默改写 frozen 文档。  
**作用域**：Cosmos Policy/WAM 视觉编码、Temporal Local Memory、Spatial Global Memory、离线缓存边界。  
**与 `MEMORY/DECISIONS.md` 的关系**：本文件同时承载两条决策 —— D013（exact-window cache 实现主线，见下「附录」）+ D014（Policy/Memory 表征解耦原则，见下「第一部分」）。

---

# 第一部分：架构原则（对应 D014 · Policy 与 Memory 的 RGB 表征解耦）

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

项目级规划、架构决策和跨模块实验边界统一记录在根仓库 `docs/build/` 与 `MEMORY/DECISIONS.md`；`cosmos-framework` 子模块内只保留与具体代码实现直接相关的局部说明/测试文档。

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

---

# 附录：exact-window cache 实现契约（对应 D013 · RGB/Memory 编码主线）

> 状态：active（2026-08-16，Kimi 第一技术审查者）  
> 适用范围：G0-R06-SFT 及后续所有使用离线视觉 latent 的 Policy/WAM 训练。  
> 与 `cosmos-framework/docs_zh/psm_wma/REGULAR_EPISODE_LATENT_OVERFIT.md` 的关系：该文档是**历史候选实验记录**，不是主线；本附录与 `MEMORY/DECISIONS.md` D013 为准。

## A.1 决策

Policy/WAM 的本地 RGB 编码采用 **Cosmos-native exact-window offline latent cache**：把当前在线训练路径的每个 17 帧窗口编码原样提前离线计算并缓存，训练时按 `(episode, start_frame)` 精确取用。不改变原生视觉分布，不为未来 Memory 形式预设任何 latent 语义（D010 延续）。

## A.2 实测契约（源码+运行证据）

- RGB window：17 帧（4n+1，n=4）；action horizon：16（chunk_length=16）；anchor：episode 内任意 start，`0 <= start <= T-17`。
- 采样分布：LIBERO 数据集窗口枚举为 **stride=1**（`libero_lerobot_dataset.py:185` `_valid_cum=cumsum(counts-16)`，`:199` `start=idx-prev` 不乘 stride；`sample_stride` 参数在 LIBERO 路径无效）。
- camera：concat_view = agentview（左）+wrist（右）水平拼接，单 vision item `[3,17,256,512]`（`libero_lerobot_dataset.py:359-362`）；不启用 `enable_per_camera_vae_encoding`（`omni_mot_model.py:3535-3536`，action 数据集与 policy server 均不设置）。
- VAE：`Wan2pt2VAEInterface.encode`，输入 uint8→fp32 `/127.5-1.0`（`_normalize_uint8_vision_item` 契约，在线由 `_normalize_video_databatch_inplace` 完成），T=17 命中 `encode_exact_durations` 不 padding，feat_cache 每窗口清零；输出 `[1,48,5,16,32]`（spatial /16：16×32；temporal 17→5）。
- noising/loss 在 x0 注入之后：`_add_noise_to_input`（`omni_mot_model.py:1815-1933`）——condition_mask 条件帧 σ_eff=0 保持 clean、ε~N(0,I)、σ 按 waver 采样、rectified-flow 插值得 xt/vt、xt 转 bf16；action 独立 σ 加噪。cache bypass 只替换 x0 来源，全部保留。

## A.3 数据流

```
parquet episode → concat_view [T,3,256,512] → 窗口 [3,17,256,512] uint8
→ fp32 /127.5-1 → Wan2pt2VAEInterface.encode → [1,48,5,16,32] fp32
→ cache per-episode .pt: windows{start: latent[5,48,16,32] fp32}
→ dataloader（命中跳 RGB 解码，zeros 占位）→ model bypass → x0_tokens_vision fp32
→ condition_mask/ε/σ/rectified-flow 插值 → Transformer → vision FM + action FM loss
```

## A.4 Cache schema（format `exact_window_v1`）

每 episode 一个 `.pt`（atomic 写、断点续跑复用 R12 机制），新目录，不覆盖 R12 历史 artifact：

```
episode_{index:06d}.pt
{
  "format": "exact_window_v1",
  "episode_index": int,
  "windows": { str(start_frame): {
      "latent": FloatTensor [5,48,16,32] fp32,        # [T_latent,C,H,W]
      "source_frame_indices": LongTensor [5],          # start, start+4, ..., start+16
      "global_row_indices": LongTensor [5],
  }},
  "language": {"instruction": str, "instructions": [str]},
  "metadata": {frame_count, window_frames=17, image_size=256, camera_layout="concat_view spatial-left-right",
               num_views=1, normalization="uint8/127.5-1", vae_path, script_revision, task_index, build_config}
}
+ dataset_manifest.json（schema_version, episode/window 计数, git rev, vae_path, image_size）
```

约束（对应任务 item 9）：重叠窗口的 latent 各自独立编码、独立存储，**不做 dedup**；不假设不同窗口中同一 RGB endpoint 的 latent 数值相同。

## A.5 存储格式选型（item 8）

per-episode `.pt`（torch.save）+ `R12CosmosLatentCache` LRU（max_cached_episodes=8）。依据：sampler 按 episode 顺序流式读窗口（`ActionIterableShuffleDataset`），随机访问需求低；最坏内存 8 workers × 8 episodes × ~110MB（fp32）≈ 7GB < 32GB 容器；零新依赖。safetensors（memmap）与 npy/memmap 的随机访问优势在该模式下不必要，不引入。

## A.6 磁盘估算（LIBERO-4in1 实测 parquet 元数据）

1693 episodes / 276,475 帧；单窗口 latent fp32 = 480 KiB：

| stride | 窗口数 | fp32 裸量 | 说明 |
|---|---|---|---|
| 1 | 246,377 | 112.78 GiB | 原生分布（默认） |
| 2 | 123,188 | 56.39 GiB | 降采样备选 |
| 4 | 61,594 | 28.20 GiB | 降采样备选 |

分 dataset：libero_10：379 ep / 95,405 win；libero_goal：428 / 45,194；libero_object：454 / 59,720；libero_spatial：432 / 46,058。

## A.7 与 G0-R12 的关系

- 复用：窗口枚举/get_window_identity、atomic 写、断点续跑、parity 工具骨架、cache 消费骨架、cache bypass。
- supersede：R12 整段 episode 因果编码（2026-08-16 parity 实测与在线窗口路径不等价，max_abs_diff=4.625，对齐窗口仍 1.79）。旧 artifact 全部保留为 R12 Gate 证据，不覆盖、不沿用；新 cache 用新目录 + `exact_window_v1`。

## A.8 执行阶梯（全部需满足才推进）

1. one-sample online/offline parity（cache 构建编码 vs 在线路径同窗口，逐位/≤1e-6）；
2. one-episode exact-window cache 构建；
3. index/alignment 验证（source_frame_indices、global_row_indices、窗口计数 == dataset valid_indices）；
4. cached-latent 真实模型 forward（短时训练步，loss finite，与在线同 batch 数值对比）；
5. multi-worker 小 loader smoke（num_workers>1，无重复/缺窗、RSS 有界）；
6. 多 episode cache smoke；
7. 以上全过后，再决定是否执行 LIBERO-4in1 全量编码（单独授权）。

## A.9 已知遗留修复（执行前必须完成）

- builder `_encode_window` 补 `_normalize_uint8_vision_item`（uint8→[-1,1]）——未提交工作区版本遗漏；
- cache 注入保持 fp32（只搬 device），不向 bf16 提前取整（`omni_mot_model.py` cache bypass 分支）。
