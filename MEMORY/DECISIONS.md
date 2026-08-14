# 长期工程决策

## D001 文档分层

- 日期：2026-08-12
- 状态：生效
- 决策：`docs/build/` 保存版本化正式文档；`SESSION.md` 保存当前交接状态；`TODO.md` 是唯一任务队列；本文件保存跨会话长期决策。
- 原因：正式设计、临时进度和长期决策的更新频率不同，混写会导致 Agent 使用过期结论。

## D002 Cosmos 工程边界

- 日期：2026-08-12
- 状态：生效
- 决策：以 `cosmos-framework` 为工程母体。业务逻辑优先新增模块；原生 optional memory modality 所需的核心修改集中在明确扩展点并配套单测。
- 原因：完全不改框架会迫使 Memory 伪装成已有模态，破坏 position、attention 和实验归因合同。

## D003 G0 准入顺序

- 日期：2026-08-12
- 状态：生效
- 决策：先完成并执行 R01-R06；只有 R06 PASS 后才实现 R07-R09 和正式 Memory 实验。
- 原因：无 Memory baseline 不成立时，Memory 收益无法归因，且不得用 RL 或 Agent 掩盖基础失败。

## D004 多 Agent 文件认领

- 日期：2026-08-12
- 状态：生效
- 决策：Agent 编码前必须在 `SESSION.md` 标记预计修改文件；同一文件同一时间只允许一个 Agent 编辑，其他 Agent可并行做只读审查或不重叠任务。
- 原因：共享工作区中的并行编辑容易覆盖修改，也会污染提交边界。

## D005 代码执行前可视化告知

- 日期：2026-08-12
- 状态：生效
- 决策：执行代码、测试、训练、推理或评测前，Agent 必须向用户展示目的、完整启动命令、工作目录、关键环境变量、资源与外网需求、输入、产物路径和结果判据。只读文件检查和文本检索可简化说明。
- 原因：用户需要清楚掌握每次运行正在验证什么、使用什么资源、会生成什么，以及如何判定结果。

## D006 Edge-Policy-DROID -> LIBERO warm-start 原则

- 日期：2026-08-13
- 状态：生效
- 决策：
  1. Edge->LIBERO 不直接复制 `action_policy_libero_nano.py`，也不把 `Cosmos3-Nano-Policy-DROID` 当作官方 LIBERO 起点。官方 Nano LIBERO recipe 从 bare `Cosmos3-Nano` 开始。
  2. 复用官方 Nano LIBERO 的 dataset/action/eval contract：20 Hz、`agentview+wrist` concat、10D `frame_wise_relative` rot6d、`quantile_rot`、chunk 16，以及 gripper / 图像朝向 / normalization parity。
  3. Edge LIBERO experiment config 以 `EDGE_MODEL_CONFIG` 为模型基线，再叠加 LIBERO-specific 设置；不得只替换 Nano recipe 的 checkpoint 路径。
  4. 默认保留 `Cosmos3-Edge-Policy-DROID` 的 shared Generator / world-action coupling。R03/R04 再实证决定 `action2llm`、`llm2action`、`action_modality_embed` 与 embodiment domain 在 LIBERO 10D action space 下的继承、新 domain 或部分重初始化策略。
  5. R02 采用 metadata/config/index-first：先比较 Nano LIBERO recipe、`NANO_MODEL_CONFIG`、`EDGE_MODEL_CONFIG`、Edge-Policy-DROID config/index 和官方 policy-posttraining 资料；bare Edge 权重 diff 降为 conditional，不作为硬前置。只有关键未决问题会改变 R04 初始化策略时，才按需下载 bare Edge 必要 transformer shard。
  6. `Cosmos3-Nano-Policy-DROID` 完整权重不作为当前依赖，也不做 Nano-Policy-DROID vs Edge-Policy-DROID 的逐 tensor 数值比较。
- 事实边界：
  - 官方公开 Nano DROID recipe 是 Generator-side Full SFT，不是 action-head-only；公开 trainable selector 包括 `moe_gen`、`time_embedder`、`vae2llm`、`llm2vae`、`action2llm`、`llm2action`、`action_modality_embed`。
  - 结合 Cosmos3 policy post-training 论文、官方 cookbook 与 Nano recipe，可高置信推断 Edge-Policy-DROID 也经历了大规模 Generator-side policy specialization；但 NVIDIA 未公开该发布 checkpoint 的 exact `keys_to_select`，不得将 Nano selector 写成 Edge 官方事实。
  - 将公开 Nano selector 映射到 Edge 参数结构得到的约 1.423B trainable / 约 35.6% of 4B 是项目 derived estimate，不是 NVIDIA 官方 Edge 数字。
- 原因：把“LIBERO-specific contract”“Nano-specific model config”“DROID-specific specialization”拆开，既最大化利用 Policy-DROID 已学到的 world-action coupling，又避免为不影响初始化策略的问题额外下载模型权重或引入无意义的跨架构 tensor diff。

## D007 arXiv:2608.11246 作为后续 Agent Harness 参考

- 日期：2026-08-13
- 状态：生效
- 决策：将 arXiv:2608.11246 纳入 W10/W11 的高优先级 Agent / Planner / Harness 参考，但不作为 G0、R01-R09、Local Memory、Spatial Global Memory 或 Edge->LIBERO baseline 的前置依赖。
- 参考重点：
  1. 用 harness 把现有 memory、world-action policy、skills/tools 与 verifier 组织成闭环，而不是新增一套替代 Cosmos3 的 Agent 主体；
  2. Spatial Global Memory 可以额外生成 Agent-readable 的结构化 scene/object/place/status 摘要，但 scene graph 只作为 Planner context，不替代连续 Global Spatial Memory；
  3. 执行反馈采用结构化 `success / continue / failure(reason)` 或 exit-code-style interface，服务 replan / retry / re-observe / re-query memory；不得把这些状态扩展成手写任务 FSM。
- 适用实验：W10 Planner dynamic modality routing / E013；W11 Cosmos Reasoner Agent thin slice / E014 / failure recovery。
- 事实边界：当前仅把论文作为后续设计参考。W10/W11 启动前必须重新核验 arXiv 一手页面、项目页/代码（若开放）及具体接口，当前讨论中的 scene/context/evaluation 概括不得直接当成冻结实现事实。
- 详细记录：`docs/build/PSM-WMA_Agent_Harness_reference_addendum_v0.1.md`。
- 原因：该方向与“Memory + World-Action Model 为主体，Agent 只做薄层 orchestration”的项目边界兼容，并可为动态 MemoryRequest、执行验证和失败恢复提供更系统的 harness 设计参考。

## D008 模型与数据资产入口

- 日期：2026-08-13
- 状态：生效
- 决策：Agent 优先从根目录 `pretrained_models/`、`datasets/` 和 `simulators/` 查找模型、数据与仿真环境；这些目录只保存指向外部实际存储位置的软链接及说明文件，不复制或提交大文件。
- 原因：统一项目内资产发现入口，同时保持大模型与数据的实际存储位置可配置。

## D009 Edge 与 Edge-Policy-DROID 的用途分工

- 日期：2026-08-14
- 状态：生效
- 决策：
  1. DROID/RoboLab 零样本策略测试与 G0 smoke 一律使用 `Cosmos3-Edge-Policy-DROID`（完整 HF 推理包，含 VAE、vision encoder、tokenizer、scheduler 与 `droid_lerobot` 策略配置）。
  2. 原版 `Cosmos3-Edge`（本地仅 `transformer/` 权重，约 6.3GB）只作为基础模型、训练起点或权重差异基准；不得假定它已具备可用的 DROID 控制策略。
  3. R03/R04 设计时必须考虑 Policy-DROID 相对 base Edge 多出的 28 个 `k_norm_und_for_gen` 参数，不能按"两库参数名完全一致"处理。
- 事实边界：
  - Kimi safetensors header 级复核（2026-08-14）：base 549 个张量、Policy-DROID 577 个；共同 549 个张量 0 个 shape 不匹配；仅 4 个 `time_embedder` 张量由 BF16 保存为 FP32（Transformer 约多 9.4MB，非新增层）；`action_proj_in` / `action_proj_out` / `action_modality_embed` 两边结构均存在。
  - Codex 分层抽样数值对比（2026-08-13，非全量扫描）：`action_modality_embed`、`action_proj_in/out`、`moe_gen` 生成塔权重已训练改写；`embed_tokens` 与普通 `input_layernorm`/`norm` 未变。该覆盖结论为抽样证据，全量数值 diff 留待 R02/R03 正式 audit 复核。
  - Codex 原始结论中"两库参数名完全一致、无新增参数名"经复核不准确，以本条 header 级事实为准。
- 原因：Policy-DROID 是 DROID 策略专项微调后的完整发布包，与 base Edge 的职责不同；明确分工避免把基础权重误当策略 checkpoint，也避免 R03/R04 忽略生成路径新增的 K-norm 参数。
