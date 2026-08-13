# 当前协作状态

更新时间：2026-08-13

## 当前阶段

G0 Foundation。先完善并执行 R01-R06，建立可复现的 `Cosmos3-Edge-Policy-DROID -> LIBERO` 无 Memory baseline；R06 PASS 前不进入 Memory 算法实验。

## 当前事实

- 正式设计主线为 Temporal Local Memory 与 Spatial Global Memory 两个独立 optional clean modalities。
- 项目以 `cosmos-framework` 为工程母体；优先新增项目模块，只对 `SequencePlan`、`PackedSequence`、packer 和 Generator adapter 等必要扩展点做集中最小修改。
- 根仓库当前提交为 `cbdf544`，`cosmos-framework` 子模块已快进同步 NVIDIA `upstream/main` 至 `103c5d1687d290b050e4890f48ff7a38b12742ef`；本地子模块相对 fork `origin/main` 超前 5 个提交，尚未 push。
- `docs/build/log/kimi_operation.log` 是 Kimi 的执行日志，已确认纳入版本控制；其他 Agent 只追加自己的真实操作，不覆盖已有记录。
- 已拉取另一 Agent 的文档一致性修改。该交付修改了 5 份现有正式文档，但没有新增或完善可执行的 R01-R06 Runbook。
- Kimi 记录 `/gemini/code/models/Cosmos3-Edge-Policy-DROID` 已于 2026-08-12 16:08 下载完成；Codex 已按权重索引完成完整性预检，全部引用文件存在且非空。
- 项目 Python 环境已安装到 `/root/venvs/psm_wma`（Python 3.13.13）；大包优先从 `/gemini/code/packages/` 本地安装，Megatron-LM 与 lerobot 使用本地源码快照 override，已规避 Git TLS 中断。当前 GPU 已可见，CUDA 最小张量运算通过。
- 所有 Agent 执行代码、测试、训练、推理或评测前，必须先向用户展示目的、完整命令、工作目录、环境变量、资源/外网需求、输入、产物和判据。

## 正在进行

| 任务 | 负责人 | 状态 | 预计修改文件 | 备注 |
|---|---|---|---|---|
| DOC-R01 | Codex | DONE | `docs/build/PSM-WMA_G0_R01_implementation_runbook_v0.1.md`、`tools/g0/collect_r01_gate_json.py` | Kimi 二轮复审 APPROVE，已关闭全部审查项 |
| DOC-R02-R06 | 待认领 | TODO | 后续版本化 Gate Runbook | R01 文档通过审查后逐 Gate 推进 |

## 最近完成

- 阅读 `docs/build` 五份核心文档及 `cosmos-framework/AGENTS.md`。
- 核对 `SequencePlan`、`PackedSequence`、Cosmos3 Generator adapters 和 LIBERO dataset/config 的现有扩展基础。
- 完成 `COLLAB-BOOTSTRAP`，建立根目录协作协议、会话状态、任务队列和长期决策文件。
- 拉取并审查 `c428d46`、`42c6a13`；Local/Global 配置、代码结构和 runtime import 核对方向正确。
- 审查 `82892f3`：RoboTTT 被限制在 R06 PASS 后的 R09 backend 候选，未侵入 G0 Foundation 顺序；独立 Local compressor 的集成边界合理。
- 完成 `/root/venvs/psm_wma` 全量依赖安装；uv 解析 431 个包，本轮安装 286 个包，无新的未落地 >100MB 组件。
- 将 `cosmos-framework` 从 `5d6dedc` fast-forward 到 `upstream/main@103c5d1`；上游变更不包含 `pyproject.toml` 或 `uv.lock`，无需重装环境。
- 根据 Kimi `REVIEW-R01` 首轮 `REQUEST_CHANGES` 修订 Runbook：补齐 Reasoner warmup/steady timing、Reasoner/Policy VRAM 采样、RoboLab 响应证据契约、真实产物层级、preflight 日志、commit 自动断言及 provenance 字段；新增独立 Gate JSON 汇总脚本。
- Kimi `REVIEW-R01` 二轮结论 `APPROVE`；追加 LOW N1/N2 已修复为独立请求数不足标签和可配置 port/seed/num_steps provenance，N3 通过定向暂存排除 `__pycache__`。

## 验证记录

- R01 checkpoint 完整性预检 PASS：`cosmos_framework_model.safetensors`、两个 Transformer 分片和 `vision_encoder/model.safetensors` 均存在且非空；另确认 VAE 权重存在。
- 环境验收 PASS：PyTorch `2.10.0+cu130`，CUDA 可用，GPU 小张量运算结果正确；LIBERO、robosuite、lerobot、Megatron Core、Ray、OpenCV 和 OpenPI 导入通过。
- cuDNN 路径根因已定位：`nvidia/cu13/lib` 会命中不兼容的 cuDNN 9.0；将 `/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cudnn/lib` 放在 `LD_LIBRARY_PATH` 首位后，PyTorch 报告 cuDNN `91501`，Policy server CLI 导入及参数解析 PASS。
- 已知例外：`openpi-client==0.1.2` 元数据要求 `numpy<2.0`，而项目 `[tool.uv].override-dependencies` 为 LIBERO/numba 要求 `numpy>=2.0,<2.3`，实际安装 `numpy==2.2.6`；`uv pip check` 因此报 1 条元数据不一致，OpenPI 运行时导入已通过，未修改项目配置。
- Gate JSON 汇总脚本最小验证 PASS：`py_compile` 通过；空证据生成 `BLOCKED`，完整有效伪证据生成 `PASS`，peak VRAM、cuDNN `91501`、warmup/steady latency 与请求级 latency 映射断言通过。Ruff 未执行，原因是环境和 uv 缓存均无 Ruff，未为文档任务新增依赖；`git diff --check` 通过。
- 追加 LOW 复测 PASS：空证据为 `BLOCKED`，完整证据为 `PASS`，仅 1 个 timed request 为 `FAIL_INSUFFICIENT_REQUESTS` 且不再误报 nonfinite；自定义 port/seed/num_steps 准确写入 `run_config`。
- RoboTTT 文档审查保留项：独立 compressor 下的 TTT-KVB objective、multimodal evidence 到 K/V token 的构造、官方代码/许可证/依赖复用边界尚未冻结；R09-A/B 还需 matched 参数量、训练步数、token budget 和计算预算，不能仅凭“primary candidate”提前选择。
- RoboTTT 文档治理问题：继续直接修改 `frozen/locked` 文件，虽增加 Addendum，但版本号未升级；后续正式冻结应生成新版本，而不是继续累积覆盖。
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
