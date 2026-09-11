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
  3. R03/R04 设计时注意：Policy-DROID 的 `use_und_k_norm_for_gen=true` 会在生成路径激活 28 个 `k_norm_und_for_gen` 参数；加载该 checkpoint 必须走 `cosmos_framework.inference.model._diffusers_weight_map` 的兼容入口（`inference2/_model_io.py` 尚未同步该兼容）。
- 事实边界：
  - 规范键集（Kimi 复核 2026-08-14，经 R02 索引审计确认）：base 与 Policy-DROID 的 Transformer 规范键集完全相同，同为 549 个（均含 28 个 `layers.N.self_attn.k_norm_und_for_gen.weight`）；共同张量 0 shape 不匹配；仅 4 个 `time_embedder` 张量由 BF16 保存为 FP32（约多 9.4MB，非新增层）；`action_proj_in` / `action_proj_out` / `action_modality_embed` 两边结构均存在。
  - Policy-DROID 的物理差异不在参数集合，而在打包方式：多一个 overlay 文件 `transformer/cosmos_framework_model.safetensors`，以模型内部名（`model.net.language_model...`）重复存储同样 28 个 K-Norm 张量；其根索引含 56 个 K-Norm 条目，其中 28 个 `layers.layers.` 旧别名为指向不存在键的陈旧条目，依赖加载端兼容逻辑剔除。
  - Codex 分层抽样数值对比（2026-08-13，非全量扫描）：`action_modality_embed`、`action_proj_in/out`、`moe_gen` 生成塔权重已训练改写；`embed_tokens` 与普通 `input_layernorm`/`norm` 未变。该覆盖结论为抽样证据，全量数值 diff 留待 R02/R03 正式 audit 复核。
  - 修订（2026-08-14）：本条早先版本称"base 完全没有 `k_norm_und_for_gen`，Policy-DROID 新增 28 个参数"，经 R02 审计复核该说法不准确——base 的扩散 shard 同样含 28 个规范 K-Norm 键，Policy-DROID 多出的仅是 overlay 重复存储与陈旧索引别名。以本修订为准。
- 原因：Policy-DROID 是 DROID 策略专项微调后的完整发布包，与 base Edge 的职责不同；明确分工避免把基础权重误当策略 checkpoint；同时明确该 checkpoint 的根索引缺陷与唯一受支持的加载入口，防止 R03/R04 误用未兼容的 inference2 路径。

## D010 RGB 离线编码必须对齐 Cosmos

- 日期：2026-08-15
- 状态：生效
- 决策：RGB 离线缓存复用 `OmniMoTModel._encode_vision_item` 的契约：每个 camera clip 独立切分，uint8 按 `x / 127.5 - 1.0` 归一化，调用同一 `tokenizer_vision_gen.encode()`，再按 camera-major 在 temporal 轴拼接。禁止逐 RGB 帧独立 VAE encode，也不得把 StarVLA/UMT5 的 latent 直接当作 Cosmos latent。
- 原因：Wan VAE 是 causal temporal tokenizer；离线缓存必须与在线 temporal compression、视角顺序和 latent shape 一致，才能避免训练/推理语义漂移。

## D011 多卡 DCP 恢复前必须处理 CPU optimizer 叶子

- 日期：2026-08-15
- 状态：生效
- 决策：
  1. `cosmos_framework/checkpoint/dcp.py::_broadcast_tensor_leaf` 的普通 tensor 分支直接调用默认进程组 `dist.broadcast`；当进程组为 NCCL 且叶子是非 capturable AdamW 的 CPU `step` 标量时，会报 `No backend type associated with device type cpu`。
  2. `8421e41` 的 `world_size == 1` 短路只解决单卡 R05；多卡根因仍然存在，记为 MEDIUM-3，不得把单卡 PASS 解读为多卡 reload 已支持。
  3. R06 或任何正式多卡训练/reload 启动前，必须在不改变 dedup reader 选举和 DTensor mesh 语义的前提下修复；候选方案为 CPU 叶子使用 Gloo 辅助进程组，或经证明无精度/内存风险的临时 CUDA 搬运广播。
- 验收：至少 2 rank 的真实 AdamW checkpoint save/reload 在 NCCL 环境 PASS；CPU `step`、非 tensor `param_groups` 和 CUDA/DTensor 叶子全部恢复一致；补充多 rank 定向单测，且现有单 rank 路径不回归。
- 原因：G0-R05 Phase C 首次恢复带 optimizer 状态的 checkpoint 时暴露了 CPU tensor 与 NCCL backend 不匹配；单卡无操作短路不能代替多卡正确性修复。

## D012 Gate 静态审查必须附最小 GPU smoke

- 日期：2026-08-15
- 状态：生效
- 决策：后续 R Gate 的代码审查在批准长任务前，必须先跑一次最小 GPU smoke（几步训练 + 一次 validation + 一次 checkpoint reload），覆盖改动实际触发的运行路径；仅通过静态代码路径审查不得直接 APPROVE 长训练/评测任务。
- 原因：G0-R05 的 HIGH-1（`validation_step` 桩导致 held-out 崩溃）在静态审查 APPROVE 后、Phase B 第 100 步末段才暴露——trainer 触发条件与模型侧实现的接口失配只有端到端运行才能发现。监督者 P6 提出，Kimi 已采纳为审查惯例。
- 参考：`docs/build/PSM-WMA_OVERSEER_COLLAB_Codex_Kimi_2026-08-15.md`、`docs/build/PSM-WMA_REVIEW-G0-R05_tiny_overfit_2026-08-15.md`(HIGH-1/HIGH-2)。

## D013 RGB/Memory 编码主线 = Cosmos-native exact-window cache

- 日期：2026-08-16
- 状态：生效
- 决策：
  1. Policy/WAM 本地 RGB 编码主线为 Cosmos-native exact-window offline latent cache：每个 17 帧窗口按在线路径(单 vision item concat_view [3,17,256,512] → uint8/127.5-1 → `Wan2pt2VAEInterface.encode`)独立离线编码,cache format `exact_window_v1`,按 `(episode, start_frame)` 精确取用。规范见 `docs/build/PSM-WMA_RGB_representation_and_memory_encoding_plan_v0.1.md`。
  2. `cosmos-framework/docs_zh/psm_wma/REGULAR_EPISODE_LATENT_OVERFIT.md` 降级为历史候选实验记录,不是当前主线;项目级规划不再写入 `cosmos-framework/docs_zh/psm_wma/`。
  3. G0-R12 的整段 episode 因果编码 cache 被 supersede(parity 实测 FAIL:整段因果 ≠ 窗口独立);其 artifact 保留为 R12 证据,不覆盖、不沿用。
  4. Memory representation 未冻结;不得因未来 Local Memory 可能使用 continuous Wan latent 而提前修改 Policy 的 native visual distribution。
- 原因：cache 必须与训练/推理的窗口独立编码契约逐位一致(因果 VAE 上下文敏感性已由 parity 探针实证);exact-window 是构造上保持原生训练分布的唯一零风险路径。

## D014 Policy 与 Memory 的 RGB 表征解耦

- 日期：2026-08-16
- 状态：生效
- 决策：
  1. 当前 Policy/WAM 主路径保持 Cosmos-native temporal sample contract；LIBERO 继续以原生 17-frame clip 做 Wan2.2 VAE temporal encode，并允许将 exact-window 结果离线缓存。离线化本身不构成改成 MoWA-style whole-episode latent 的理由。
  2. Memory 从 episode 开头按因果历史积累。对于 anchor `t`，Memory 只读取 `f0...f(t-1)` 及对应已执行 action/state/depth/pose 等证据；Memory update cadence 可与 action chunk 的 policy re-query cadence 解耦。
  3. Temporal Local Memory 的视觉表征暂不冻结，保留历史 Cosmos prime `z0`、MoWA-style continuous Wan regular latent、以及独立 RGB/Depth/State/Action evidence encoder 等候选。只有 Local 调研与 R08/R09 给出证据后，才决定是否需要 continuous Wan latent。
  4. Spatial Global Memory 默认不绑定 Wan2.2 latent；主候选仍为 RGB semantic feature + depth/geometry + pose/trajectory + xyz/region + timestamp/confidence 的 persistent spatial store。Wan latent 仅作为 feature 候选之一。
  5. 若 Local 最终选择 continuous Wan regular latent，新增独立的 episode-level memory latent cache；默认不以该 cache 替换 Policy 的 native current-condition cache。把 regular `z_k` 进一步接入 Policy 必须作为独立架构实验验证。
  6. `cosmos-framework/docs_zh/psm_wma/REGULAR_EPISODE_LATENT_OVERFIT.md` 从“当前优先规划”降级为候选实验记录，不再作为 PSM-WMA 项目级规划的权威入口。项目级架构/规划统一放在根仓库 `docs/build/` 与本文件；`cosmos-framework` 子模块只保留与具体代码实现直接相关的局部说明与测试文档。
- 与既有决策关系：D010 对 **Policy native offline cache** 继续生效；D013 明确 Policy 的 exact-window cache 主线，D014 明确 D010/D013 不自动约束未来 Memory encoder/cache 的表征选择。
- 详细记录：`docs/build/PSM-WMA_RGB_representation_and_memory_encoding_plan_v0.1.md`。
- 原因：在 Memory 方案尚未冻结前提前把 Policy 从 native prime condition 改成 whole-episode regular latent，会同时引入不必要的 representation distribution shift 和实验变量；解耦后可以先保住 Cosmos baseline，再分别用实验决定 Local 的时间表征与 Global 的空间表征。

## D015 Local Memory 实现准入与设计冻结边界

- 日期：2026-08-25
- 状态：生效
- 决策：
  1. Temporal Local Memory 与 Spatial Global Memory 必须作为独立 optional clean modality 实现、训练和评测；不得先拼接二者的 evidence/token 再复用同一 encoder 或 adapter。
  2. 当前详细设计已冻结 Local 的输入 schema、因果边界、输出适配器和 state-management 硬约束，但未冻结可直接实现的 temporal compressor 算法或超参数。
  3. 在已证明 no-Memory baseline 有效后，Local 主线依次执行 R07（Local optional-modality contract/dummy smoke）、R08（causal history replay/alignment）和 R09（`recurrent_latent` 与 `ttt_fast_weight` 的最小对比 smoke）；R09 后才冻结正式 Local backend 并进入 no-memory vs +Local matched experiment。
  4. R07 为共享基础设施时可保留 Global 的空接口/独立 dummy coverage，但不得以此启动 Global store、retrieval 或联合 Local+Global 算法实验；Global 主线在 Local 阶段结论稳定后单独启动。
- 未冻结项：Local visual evidence representation、`K_local`、history/token budget、internal dim、TBPTT segment、TTT update rule 与 checkpoint/runtime state schema；不得在实现前把它们写成项目既定事实。
- 依据：`docs/build/PSM-WMA_02_detailed_design_v2.1_frozen.md` 第 3–5 章和第 20 章，以及 `docs/build/PSM-WMA_G0_runtime_execution_plan_v0.6_aligned.md` R07–R09。
- 原因：先通过可验证的接口、因果数据合同和 backend A/B 对比冻结变量，才能将后续收益归因于 Local Memory，避免与 Global 或未验证的视觉表征发生耦合。

## D016 双仓库提交与推送顺序

- 日期：2026-08-26
- 状态：生效
- 决策：只要 `cosmos-framework` 子模块存在代码、脚本、配置或文档更新，必须先在子模块 `v2` 分支创建独立提交并推送到子模块远端；随后根仓仅提交更新后的 Gitlink 及对应根仓范围文件，并推送根仓 `V2` 分支。不得将子模块源码修改与根仓修改混入同一 Git 提交。
- 原因：子模块提交必须先在远端可访问，根仓 Gitlink 才不会指向远端不存在的对象；独立提交也保持两仓审查、回滚和归因边界清晰。

## D017 R06 baseline 冻结与 R07 解锁 override

- 日期：2026-08-26
- 状态：生效（用户明确 override）
- 决策：`iter_000002800` 立即冻结为 R06 No-Memory baseline，G0-R06 记为 DONE；取消 `ACCEPT-CANONICAL-R06-BASELINE` 的额外 400-episode 准入要求。13-ckpt 1-trial sweep 保留为训练趋势证据，不再阻塞 Local。R07 implementation 自此 UNBLOCKED，仍严格按 R07 → R08 → R09 Gate 顺序，禁止提前实施 R08/R09。
- 覆盖范围：本条覆盖 D003/D015 中“R06 PASS 后才实现 R07”的准入判定以及 SESSION/TODO 中 canonical-400-episode 口径；不篡改历史 R06 zero-shot FAIL 证据或 frozen 文档。
- 原因：用户确认现有 `iter_000002800` 四 suite no-Memory 结果足以作为后续 matched +Local 对照；继续等待 canonical acceptance 只增加无关阻塞。

## D018 Local Memory addendum v0.3.3 chronology 口径登记

- 日期：2026-09-05
- 状态：生效（user-directed 设计澄清；implementation 前仍需独立 Gate 三方审核）
- 决策：后续 R09-B TTT 实现、audit、review 统一以 `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.3.md`（commit `fa65c0c`）为 chronology 口径：双时间轴（z1..z4 禁入 TTT evidence）、past-only 一步错位 `M_t := ReadAfterUpdate(e_{t-1}, W_{t-2})`、`ttt_tbptt_steps=16` 仅限 meta-gradient 长度（非 memory horizon、非 grad_accum）、segment 结束 detach 图但数值 carry、仅 episode done/reset 回 learned W0、未 detach fast-state graph 不跨 optimizer step、§7 硬合同 A-J 优先在 manifest/sampler 层证明。
- 悬置对齐项：addendum §4 的 `B_seg=8 × T=16` fixed-length packing + stable stream slots 与 v0.6+ 已批准 manifest-route owner-run 组织的结构差异，须在 ⑪ GPU smoke 设计 Gate 显式裁决，不得静默二选一。
- 原因：消除旧图/旧实现对双时间轴与 TBPTT 语义的歧义，保证后续 Gate 审核与实现使用同一 chronology 语言。

## D019 审核事实防遗漏协议

- 日期：2026-09-11
- 状态：生效（用户要求）
- 决策：审核状态只能由同一轮、可复核的远端锁定和三方 exact-pair 证据得出。每轮必须记录 CST 时间、`before_head`、远端 advertised SHA、fetch/fast-forward、完整新增提交范围、formal root/child、ChatGPT review 精确检索、MM/Kimi capture 与逐方状态；任一检查失败即为“状态未知”，不可表述为无回复或审核齐全。审核固定五分钟轮询，收到用户回复提示时立即额外检查。ChatGPT 的正式事实仅来自 `docs/collab/chatgpt/reviews/` 的 exact formal pair；MM/Kimi 仅来自已提交且锚定该 pair 的 tmux 最终 verdict。
- 覆盖范围：覆盖所有依赖旧轮询结果、远端提交线索、Inbox 文本或输入框内容进行审核状态判断的做法；项目 `AGENTS.md` 与治理技能需保持同一节奏和字段。
- 原因：此前出现未在本轮 fetch/精确扫描/回读完成前就断言“无新审核”或“审核已齐”的失真；把判断前提、失败语义和审计字段固定下来，才能让 Gate 推进可追溯且不可由记忆替代。

## D020 审核推进令牌与名册冻结

- 日期：2026-09-12
- 状态：生效（用户要求）
- 决策：每一审核申请在 `SESSION.md` 冻结 ChatGPT、MM、Kimi 的身份/pane 名册；任何替换必须由用户明确指定，并废弃旧观察、重新送达。审核状态只由同轮观察凭证产生；三位冻结审核者对完全相同 formal root/child 的 final verdict 同时存在时才形成推进令牌。全批准令牌仅授权申请中明确的范围；含 `REQUEST_CHANGES` 的令牌仅授权汇总意见；其余情形无令牌且 Gate 保持 `REVIEW`。用户转述、远端提交、Inbox、相似 review 文件、旧 capture 和 tmux 输入框仅为重新检查线索，不能成为审核事实。
- 覆盖范围：任何依靠跨时间、跨 SHA、跨审核者或未送达消息拼接出“已齐/可推进”的做法；没有推进令牌时，禁止整改、实现、提交、执行、训练和关闭 Gate。
- 原因：仅规定检查步骤还不足以防止把旧观察、线索和不同审核者的结论拼接成推进判断。以名册、凭证和令牌三者同源互锁，使审核事实可机械复核并 fail-closed。
