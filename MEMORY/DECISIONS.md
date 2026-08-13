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
