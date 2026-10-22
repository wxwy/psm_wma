# V3 以官方最新框架为准：V2 功能继承必要性复核

日期：2026-10-22。范围：Owner 要求的只读源码复核与判断修正。本文重新裁决上一份 [V2→V3 盘点](2026-10-22_V2_to_V3_functional_inheritance_static_review.md) 各项的**继承必要性和优先级**；原报告保留，不将“V2 有而 V3 没有”自动视为整改要求。

## 1. 版本与判断原则

| 对象 | 本轮锁定身份 |
| --- | --- |
| NVIDIA/cosmos-framework 官方最新 main | `9a70e64d2ad7ff1417484d12d10fb121b270baaf` |
| 官方提交日期/内容 | 2026-10-21；`docs(cosmos3/nim): update Cosmos3 NIM cookbook to 2.1.0 (#296)` |
| V3 本轮复核起点 HEAD | `f620a34d9f40f3a6ff347f695fb7f119c8010e02`（前次盘点文档） |
| V3 生产 Implementation Root | `a4b22b929175e462b6a8db57ad2abee7e220dd37` |
| V3 Child/Gitlink | `c9f21040f462a114d597fc83773cb9b6a9e96214` |
| V2 参考 Root / Child | `b13024456e313b545871a0d5de07f5495848f4e3` / `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92` |

本轮实际执行 `git ls-remote https://github.com/NVIDIA/cosmos-framework.git refs/heads/main`，fetch 到 Child 的 `refs/remotes/nvidia-audit/main`，用精确 Git 对象和 archive 源码核对配置及调用链；Root V3 也重新 fetch/ls-remote 确认。后续文档提交不替代生产 Implementation Root。

**当前 V3 Child 不能称为已包含今天官方 main 的全部实现。** 两者共同祖先为 `cf5d68c00d97ccd2480a2320ed652b92dec63102`，且关键源码仍有差异。但共同祖先不代表 V3 只有旧实现：例如当前 V3 已有与官方相同的 job_monitor 机制和普通 Trainer 的 `_backward_loss` hook 顺序。本文只复核此前列出的差异及相关接口，没有完成整个最新上游的升级兼容验收。

采用以下原则：

1. Host 的训练、推理、FSDP/DTensor 和公共接口以冻结后的当前官方实现为依据；不为恢复 V2 文件名而恢复旧架构。
2. Packed128、Exact-Window、H16/raw15/state15、Persistent Local-TTT、严格恢复和手动评测属于已批准项目合同。官方没有 Local-TTT，不等于这些扩展应删除；上游通用 recipe 的 chunk32 也不能覆盖项目 H16。
3. 区分“需要某项正确性/语义证据”与“必须移植 V2 的诊断工具”。采用当前 Host 的扩展点完成前者即可。
4. 本轮仅文档复核，不授权代码整改、Host 升级、改写冻结配置或改变运行中 G1。

## 2. 对上一份盘点逐项重判

| 原项 | 是否需要继承 | 本轮结论与处理方向 |
| --- | --- | --- |
| **I-01 全局梯度裁剪** | **需处理当前官方优化策略差异** | 官方 RoboCasa recipe 仍配置 `GradClip(1.0)`；Phase5 清空 callbacks 后没有替代裁剪。未来新任务应接入当前官方 FSDP/DTensor 全局范数语义，或先取得明确的取消裁剪设计裁决；配方默认并非任何项目都不可调整的硬合同。不是复制 V2 参数同步，也不自行热改 G1。 |
| **I-02 action-only / 精细 profiling** | **可选优化** | 官方 RoboCasa 串行预测也每次 decode、PNG 编码；V3 保持该行为。官方通用 profiler 已存在，但没有自动接入这个 HTTP 请求。需要时优先复用官方能力，不作为迁移阻断。 |
| **I-03 zero / init 消融模式** | **可选研究能力** | 官方无 Local-TTT 消融合同。当前 off/required 不构成官方功能缺失。此前“必须恢复”的措辞撤回；若以后开展因果消融，再冻结独立实验协议。 |
| **I-04 Slow 实际更新 / Native 验证工具** | **需要项目功能证据；不要求继承 V2 工具实现** | V3 已有 bounded 缺梯度审计和真实模型/FSDP 诊断入口。应核查这些证据是否满足 Local 合同，必要时补有界更新见证；不恢复 V2 Active Driver、环境变量 API 或复制态同步。 |
| **I-05 专家轨迹 open-loop** | **可选诊断** | 官方和 V3 都有开发用 Native validation；它不是完整 raw15 固定专家轨迹验证，但也不能说 V3 完全没有验证入口。旧 action7/LIBERO 工具不应原样移植。 |
| **I-06 公开脚本及当前状态文档** | **需要整理指引，不继承旧接口内部实现** | README/verify 等仍指向旧接口，应指向现有 V3 入口或清楚标记旧入口已停用。无需为旧 verify 恢复不存在的 replicated Local helper；也不能直接换成通用官方训练而丢掉 grouped Local-TTT。 |
| **I-07 跨 Resume 累计 task exposure** | **可选报表增强** | 当前字段明确标注进程内、Rank-local 范围，没有冒充全程覆盖。官方统计也不是持久化 per-task 台账；可从已提交日志汇总，不为计数增加训练状态。 |
| **I-08 旧 SIGUSR1 sentinel 保存** | **不继承旧实现；按部署需求选择当前机制** | 当前官方和 V3 Host 都已用可选 `WallClockCheckpoint`。此前对旧机制的描述不应成为回迁待办。是否增加抢占处理取决于实际集群，且须符合 Local 已提交边界和 F1 完整性合同。 |
| 同 GPU 多 Session batched Local-TTT | **当前不迁移，已有明确串行边界** | 官方 stateless batch 与 V3 off-mode batch 已有；它们不提供 Local Session 事务。required 串行是批准的实现范围，多 Session 另开并发设计。 |
| LIBERO 四套任务 | **官方通用能力已继承；Local 配套延期** | V3 已有官方 LIBERO-all Nano SFT 配方和入口。尚未移植的是 V2 Local/history/验收编排，不是所有 LIBERO 四套任务能力。 |
| none/window/GRU/TTT 历史对照 | **当前不迁移** | 属于 V2 研究路线；官方 rolling KV/teacher-forcing replay 是不同机制。没有理由仅为模式齐全恢复旧架构。 |
| 首 Member 带标签同进程 retry | **不要求继承** | 不是官方训练契约。当前事务 abort/fail-closed 与严格 DCP 恢复是已选择的策略；上游可选 LossSpikeRollback 也不是该协议。 |
| 自动评测 watcher | **不恢复** | Owner 已明确选择手动评测。最新官方功能不改变这一执行边界。 |
| Index8 显式兼容 | **独立的项目兼容合同债** | 不是 V2 A2 功能丢失；V2 A2 本身使用 Packed128。按既有裁决分批处理，不阻塞 Packed128 主线。 |

## 3. 关键源码依据与修正

以下 `cosmos_framework/`、`examples/` 路径在各自锁定的 Child 内，`scripts/` 公共门面另标 Root。链接固定到精确 SHA。

### 3.1 I-01：是官方优化策略接线差异，不是必须回到 V2

- 官方 `configs/base/experiment/action/posttrain_config/action_policy_robocasa_nano.py:69,116` 选择 optimization 并设置 clip_norm=1.0；`configs/base/defaults/callbacks.py:130–134` 注册 GradClip。结构化 SFT schema 也默认有 GradClip（`configs/toml_config/sft_config.py:532–550,640`）。[官方 RoboCasa 配方](https://github.com/NVIDIA/cosmos-framework/blob/9a70e64d2ad7ff1417484d12d10fb121b270baaf/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_robocasa_nano.py#L116)。
- V3 `examples/psm_wma_robocasa_corrected_phase5.py:754–755` 将 callbacks 清空；`trainer/local_memory_grouped.py:363–381` 在 optimizer 前执行两处有限性检查、callback/model hook，但没有裁剪；`omni_mot_model.py:899–919` 也无替代。[V3 覆盖配置](https://github.com/wxwy/cosmos-framework/blob/c9f21040f462a114d597fc83773cb9b6a9e96214/examples/psm_wma_robocasa_corrected_phase5.py#L755)。
- 最新官方 `callbacks/grad_clip.py:84–201,335–391` 按 mesh 计算逻辑全局范数，通过 DTensor collectives 得到标量，再以同一系数缩放各组。V3 Local Slow 参数位于 `net.local_memory_runtime`、`net.local_memory2llm` 等 net 子树，不能只按 Rank-local 分片裁剪。[官方实现](https://github.com/NVIDIA/cosmos-framework/blob/9a70e64d2ad7ff1417484d12d10fb121b270baaf/cosmos_framework/callbacks/grad_clip.py#L335)。
- 若批准未来修复，须核验 optimizer 的实际参数覆盖、空分片、GA/terminal partial 的累积梯度，以及范数本身溢出。最新官方新增 `error_if_nonfinite`（`:253–263,364–368`），旧 V3 Callback 尚无该构造参数；不能只向旧类传入新参数。保留当前全 Rank fail-closed 和失败 rollback，不盲目恢复整个 optimization bundle 或默认 NaN 清洗行为。

静态发现不证明运行中 G1 的实际梯度幅度、结果或训练无效；未读取其运行配置和状态。改变裁剪会改变训练更新语义，需要独立范围和版本裁决。

### 3.2 I-02/I-05：V3 继承了官方的推理与开发验证主路径

- 官方 RoboCasa Server `scripts/action_policy_server_robocasa.py:1154–1184` 的串行预测直接调用 `generate_samples_from_batch`、decode、PNG/base64；V3 `:1188–1211` 保持该行为。官方 `predict_policy_batch:1024–1071` 则已有 action-only batch，但不带 PSM Local 事务。[官方串行预测](https://github.com/NVIDIA/cosmos-framework/blob/9a70e64d2ad7ff1417484d12d10fb121b270baaf/cosmos_framework/scripts/action_policy_server_robocasa.py#L1154)。
- 官方 `inference/common/args.py:1026–1029` 和 `inference/common/inference.py:173–241` 提供通用 profiler，V3 保留对应能力。HTTP Server 的上述直接模型调用没有经过 `Inference.generate`，因此请求级细分 profiling 既不是必须复制的 V2 能力，也不能宣称已自动接通。
- 官方 Server `:1217–1282`、V3 `:1254–1319` 保留开发用 train/val 抽样及部分 action MSE。它可能因配置/数据加载而跳过，覆盖也不等于完整 raw15 或 Local 功能验证。[官方开发验证](https://github.com/NVIDIA/cosmos-framework/blob/9a70e64d2ad7ff1417484d12d10fb121b270baaf/cosmos_framework/scripts/action_policy_server_robocasa.py#L1217)。

### 3.3 I-04：保留 Local 的验收目标，复用新版验证路径

V3 `examples/psm_wma_robocasa_corrected_phase5.py:903–926,1126,1186` 有 bounded `--audit-missing-grads`；`examples/psm_wma_local_fsdp_scan_micro_smoke.py:150–160,252` 和 `psm_wma_robocasa_local_s1.py:544–551` 有真实模型 Local/FSDP 诊断。后者 `:605,629–635` **已有 Local 投影参数的 optimizer 前后变化断言**，因此上份报告对“没有 Slow 前后变化见证”的表述必须收窄：已有 Local-only 诊断，尚不能据此推定联合 Formal 路径覆盖充分。官方另有通用 `callbacks/norm_monitor.py:176,290–301` 和 `parameter_geometry_callback.py:18–27`，但这些都不自动证明 Prefix 因果作用或在线适应改善 SR。

因此应评估现有语义 Evidence，再决定是否补低频、全 Rank/FSDP 合理的 before/after 更新见证。不能将“V2 工具类没移植”判成“算法没实现”，也不能用 Loss/Norm 或源码存在宣告 GPU 功能 PASS。旧 B1 严格元素级数值等价不重新成为前置。

### 3.4 I-06/I-08：使用新入口与新部署机制

- 官方 `docs/training.md:228–230`、`examples/_sft_launcher_common.sh:98–106` 使用配套 shell → `scripts.train --sft-toml`。项目现有 Root `scripts/train_v3_packed128_staged.sh:29–37` 走批准的 Corrected Phase5 grouped driver；评测有 `scripts/run_robocasa_eval.sh`。修旧指引即可，不为 Root `scripts/verify.sh:26–38` 的旧导入恢复 replicated Local helper。
- 官方与当前 V3 `configs/base/defaults/job_monitor.py:10–25` 已注册 `WallClockCheckpoint`，由 `COSMOS3_CHECKPOINT_WALL_CLOCK_MINUTES` 控制，未设置/非正时关闭。旧 SIGUSR1 实现不是最新官方要求。[官方 job_monitor](https://github.com/NVIDIA/cosmos-framework/blob/9a70e64d2ad7ff1417484d12d10fb121b270baaf/cosmos_framework/configs/base/defaults/job_monitor.py#L10)。
- 上游 wall-clock 保留/裁剪机制不能直接套到 Local DCP：其组件完整性判定不等于项目 F1 的 Local Sidecar、Frontier/RNG 合同。仅在有实际部署需求时适配和验收。

### 3.5 LIBERO 与原生 ABI：避免把已继承或主动限定的能力算缺失

官方与 V3 都有 `examples/launch_sft_action_policy_libero_all_nano.sh:5–15`、`configs/base/experiment/action/posttrain_config/action_policy_libero_all_nano.py:4–9,44–61`。这证明通用四套任务代码存在，**不证明 V3 Local-TTT 四套任务已验收**。[官方 LIBERO-all](https://github.com/NVIDIA/cosmos-framework/blob/9a70e64d2ad7ff1417484d12d10fb121b270baaf/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_all_nano.py#L4)。

官方 `simulation/robocasa/eval_utils.py:91–112` 与 V3 `:89–110` 的 raw15→env12 映射相符；官方 `closed_loop_eval.py:24–31,120–162` 的 state/camera/horizon/target 协议在 V3 保留，并加入项目身份和 Local Evidence。实际安装环境、物理行为和任务效果仍取决于独立运行验收，不能由静态比对替代。

## 4. 官方最新与当前 V3 的后续兼容边界

以下是定向检查发现的升级注意事项，不新增本轮整改或运行阻断项：

- **Loss/Hook**：最新 `loss_reduction_mode=global_sample_mean` 为 opt-in，默认仍是 local_item_mean；Edge/Nano Aux 系数默认 None。V3 grouped trainer `:292–293` 明确拒绝 `_backward_loss`，已有自己的 Consumer 加权合同。未来启用新归一化时必须适配；不能直接套上游通用 backward/GA 或 V2 Aux 拆分，不能据此推定 G1 目标错误。
- **DCP**：最新支持可选 `save(..., epoch=...)`，当前 F1 SafeLocal wrapper 是 iteration 接口。未来 Host 更新需适配或限制调用，同时保留 F1 发布完整性和严格 RNG 恢复。当前 Phase5 `:763` 明确禁用 async DCP，不为上游 async 优化改变当前同步保存路线。
- **FSDP/执行路径**：新的 CP raw-video 生命周期、activation offload、temporal-window AC、Transfer 编译路径按实际使用需求评估。它们不要求恢复 V2 replicated Local，也不是当前 CP1/cached-latent 路线的自动整改项。

**建议执行顺序**：先由 GPT/Owner 裁决 I-01 未来任务的裁剪策略；整理 I-06 当前入口/文档；复用已批准的 Local 语义验收。I-02/I-03/I-05/I-07 按实测收益或研究计划立项，I-08 按部署需要评估，其余延期能力维持边界。上游版本同步单独冻结 SHA、核查接口并验收，不与本轮继承盘点混为一次全仓升级。

## 5. 本轮交付边界

仅提交本复核文档及 SESSION/TODO 记录；保留上一轮报告和全部历史 Evidence。未修改生产源码、测试、配置、Child/Gitlink、Vendor 或 G1，未执行项目代码/测试、GPU、模型、Action Server、仿真、训练或真实 DCP。本文不关闭新的实现/运行 Gate，也不改变 Batch C 或 G1 的既有授权。
