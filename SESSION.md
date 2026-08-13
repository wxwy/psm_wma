# 当前协作状态

更新时间：2026-08-13

## 当前阶段

G0 Foundation。先完善并执行 R01-R06，建立可复现的 `Cosmos3-Edge-Policy-DROID -> LIBERO` 无 Memory baseline；R06 PASS 前不进入 Memory 算法实验。

## 当前事实

- 正式设计主线为 Temporal Local Memory 与 Spatial Global Memory 两个独立 optional clean modalities。
- 项目以 `cosmos-framework` 为工程母体；优先新增项目模块，只对 `SequencePlan`、`PackedSequence`、packer 和 Generator adapter 等必要扩展点做集中最小修改。
- 根仓库以当前 `main` HEAD 为准；本次交接修改基于 `5084057`，`cosmos-framework` 子模块为 `5d6dedc7bac4e8ec4d2b6fb002655bff68e5e5f0`。
- `docs/build/log/kimi_operation.log` 是 Kimi 的执行日志，已确认纳入版本控制；其他 Agent 只追加自己的真实操作，不覆盖已有记录。
- 已拉取另一 Agent 的文档一致性修改。该交付修改了 5 份现有正式文档，但没有新增或完善可执行的 R01-R06 Runbook。
- Kimi 记录 `/gemini/code/models/Cosmos3-Edge-Policy-DROID` 已于 2026-08-12 16:08 下载完成；R01 执行前仍需按权重索引核验文件完整性。当前处于未挂载 GPU 的云端 Docker，未使用 GPU 资源时 `nvidia-smi` 不显示显卡，属于正常调度状态；正式 R01 需在已分配 GPU 的容器中执行。`cosmos-framework/.venv` 不存在，仍需确认项目既有 Python/uv 运行方式。
- 所有 Agent 执行代码、测试、训练、推理或评测前，必须先向用户展示目的、完整命令、工作目录、环境变量、资源/外网需求、输入、产物和判据。

### Edge-Policy-DROID -> LIBERO 新确认

- NVIDIA 官方 LIBERO recipe 是从 bare `Cosmos3-Nano` 做 LIBERO SFT，不是从 `Cosmos3-Nano-Policy-DROID` 继续微调；因此不能把 Nano-Policy-DROID 当作官方 LIBERO 起点。
- Nano LIBERO 的数据/动作/闭环评测合同可作为 Edge 迁移基线：20 Hz、`agentview+wrist` concat、10D `frame_wise_relative` rot6d、`quantile_rot`、action chunk 16，并保留官方 gripper / 图像朝向 / normalization parity 检查。
- `action_policy_libero_nano.py` 直接基于 `NANO_MODEL_CONFIG`，不能只替换 checkpoint 路径用于 Edge。Edge 版本应以 `EDGE_MODEL_CONFIG` 为模型基线，再迁移 LIBERO-specific dataset/action/eval 设置。
- 官方公开的 Nano DROID recipe 属于 Generator-side Full SFT，而不是 action-head-only。公开 selector 包括 `moe_gen`、`time_embedder`、`vae2llm`、`llm2vae`、`action2llm`、`llm2action`、`action_modality_embed`。
- 结合 Cosmos3 policy post-training 论文、官方 cookbook 与 Nano DROID recipe，可高置信推断 `Cosmos3-Edge-Policy-DROID` 也经历了大规模 Generator-side policy specialization；但 NVIDIA 未公开 Edge-Policy-DROID 发布 checkpoint 的 exact `keys_to_select`，不得把 Nano selector 写成 Edge 官方事实。
- 若仅把公开 Nano selector 映射到 Edge 参数结构，derived estimate 约为 1.423B trainable、约占 4B 的 35.6%。这是项目估算，不是 NVIDIA 官方 Edge 数字。
- 默认保留 `Edge-Policy-DROID` 已学到的 shared Generator / world-action coupling。R03/R04 的核心待决策项是 DROID `action2llm` / `llm2action` / `action_modality_embed` 与 embodiment domain 在 LIBERO 10D action space 下如何继承、新建 domain 或部分重初始化。
- R02 先做零大权重下载的 metadata/config/index audit；只有仍存在会改变 R04 初始化策略的关键未决问题时，才按需下载 bare Edge 的必要 transformer shard 做 Edge vs Edge-Policy-DROID tensor diff。`Cosmos3-Nano-Policy-DROID` 完整权重不作为当前依赖。

## 正在进行

| 任务 | 负责人 | 状态 | 预计修改文件 | 备注 |
|---|---|---|---|---|
| DOC-R01 | Codex | IN_PROGRESS | `docs/build/PSM-WMA_G0_R01_implementation_runbook_v0.1.md` | 先形成可独立执行和审查的 R01 Runbook |
| DOC-R02-R06 | 待认领 | TODO | 后续版本化 Gate Runbook | R01 文档通过审查后逐 Gate 推进；R02/R03 必须遵循 D006 |

## 最近完成

- 阅读 `docs/build` 五份核心文档及 `cosmos-framework/AGENTS.md`。
- 核对 `SequencePlan`、`PackedSequence`、Cosmos3 Generator adapters 和 LIBERO dataset/config 的现有扩展基础。
- 完成 `COLLAB-BOOTSTRAP`，建立根目录协作协议、会话状态、任务队列和长期决策文件。
- 拉取并审查 `c428d46`、`42c6a13`；Local/Global 配置、代码结构和 runtime import 核对方向正确。
- 确认 Nano LIBERO official recipe 与 Nano/Edge model config 的边界，并收敛 Edge-Policy-DROID -> LIBERO warm-start 原则；详见 `MEMORY/DECISIONS.md` D006。

## 验证记录

- 文档审查发现：R01-R06 只有目的、检查和 PASS 摘要，缺少精确命令、完整前置资产、源码入口、逐 Gate 修改文件、统一断言、失败分流和回填清单，不能直接执行。
- 文档治理发现：提交直接修改 `frozen/locked` 文件但未升级版本或增加对应修订记录。
- 一致性残留：技术调研第 10 章仍写“Local/Goal persistent state”；Static Audit 仍保留 `K_local/K_goal/K_psm` 旧字段。
- Edge->LIBERO warm-start 事实分级已明确：官方事实、项目高置信推断、derived estimate、待 R03/R04 实证项分开记录。
- 已确认工作目录：`/gemini/code/psm_wma`。

## 下一交接

1. 完成并独立审查版本化 R01 Runbook；R01 PASS 后再进入 R02/R03。
2. R02 按 D006 先做 metadata/config/index audit，不把 bare Edge 全权重下载设为硬前置。
3. R03 明确产出 `action2llm` / `llm2action` / `action_modality_embed` / domain 的 inherit-vs-reinit 决策与运行时证据。
4. 修复两处残留旧口径，并用新版本/修订记录处理 `frozen/locked` 文档治理问题。
5. R04 仅在 R02/R03 contract 明确后执行 Edge-Policy-DROID x LIBERO forward/loss smoke。
