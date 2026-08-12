# 当前协作状态

更新时间：2026-08-12

## 当前阶段

G0 Foundation。先完善并执行 R01-R06，建立可复现的 `Cosmos3-Edge-Policy-DROID -> LIBERO` 无 Memory baseline；R06 PASS 前不进入 Memory 算法实验。

## 当前事实

- 正式设计主线为 Temporal Local Memory 与 Spatial Global Memory 两个独立 optional clean modalities。
- 项目以 `cosmos-framework` 为工程母体；优先新增项目模块，只对 `SequencePlan`、`PackedSequence`、packer 和 Generator adapter 等必要扩展点做集中最小修改。
- 根仓库当前提交为 `5084057`，`cosmos-framework` 子模块为 `5d6dedc7bac4e8ec4d2b6fb002655bff68e5e5f0`。
- `docs/build/log/kimi_operation.log` 是 Kimi 的执行日志，已确认纳入版本控制；其他 Agent 只追加自己的真实操作，不覆盖已有记录。
- 已拉取另一 Agent 的文档一致性修改。该交付修改了 5 份现有正式文档，但没有新增或完善可执行的 R01-R06 Runbook。
- Kimi 记录 `/gemini/code/models/Cosmos3-Edge-Policy-DROID` 已于 2026-08-12 16:08 下载完成；Codex 已按权重索引完成完整性预检，全部引用文件存在且非空。当前处于未挂载 GPU 的云端 Docker，未使用 GPU 资源时 `nvidia-smi` 不显示显卡，属于正常调度状态；正式 R01 需在已分配 GPU 的容器中执行。`cosmos-framework/.venv` 不存在，仍需确认项目既有 Python/uv 运行方式。
- 所有 Agent 执行代码、测试、训练、推理或评测前，必须先向用户展示目的、完整命令、工作目录、环境变量、资源/外网需求、输入、产物和判据。

## 正在进行

| 任务 | 负责人 | 状态 | 预计修改文件 | 备注 |
|---|---|---|---|---|
| DOC-R01 | Codex | IN_PROGRESS | `docs/build/PSM-WMA_G0_R01_implementation_runbook_v0.1.md` | 先形成可独立执行和审查的 R01 Runbook |
| DOC-R02-R06 | 待认领 | TODO | 后续版本化 Gate Runbook | R01 文档通过审查后逐 Gate 推进 |

## 最近完成

- 阅读 `docs/build` 五份核心文档及 `cosmos-framework/AGENTS.md`。
- 核对 `SequencePlan`、`PackedSequence`、Cosmos3 Generator adapters 和 LIBERO dataset/config 的现有扩展基础。
- 完成 `COLLAB-BOOTSTRAP`，建立根目录协作协议、会话状态、任务队列和长期决策文件。
- 拉取并审查 `c428d46`、`42c6a13`；Local/Global 配置、代码结构和 runtime import 核对方向正确。

## 验证记录

- R01 checkpoint 完整性预检 PASS：`cosmos_framework_model.safetensors`、两个 Transformer 分片和 `vision_encoder/model.safetensors` 均存在且非空；另确认 VAE 权重存在。
- 文档审查发现：R01-R06 只有目的、检查和 PASS 摘要，缺少精确命令、完整前置资产、源码入口、逐 Gate 修改文件、统一断言、失败分流和回填清单，不能直接执行。
- 文档治理发现：提交直接修改 `frozen/locked` 文件但未升级版本或增加对应修订记录。
- 一致性残留：技术调研第 10 章仍写“Local/Goal persistent state”；Static Audit 仍保留 `K_local/K_goal/K_psm` 旧字段。
- 已确认工作目录：`/gemini/code/psm_wma`。
- 提交：未提交。

## 下一交接

1. 新建版本化 R01-R06 Runbook，不继续扩写现有 Runtime Plan 摘要。
2. 修复两处残留旧口径，并用新版本/修订记录处理 `frozen/locked` 文档治理问题。
3. 由未参与 Runbook 编写的 Agent 对照 `AGENTS.md` 逐项复审。
4. 审查通过后认领 R01；在已挂载 GPU 的云端容器中核验 Python/uv 环境和 checkpoint 完整性，再执行官方 smoke。
