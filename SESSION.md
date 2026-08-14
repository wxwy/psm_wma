# 当前协作状态

更新时间：2026-08-14

## 当前阶段

G0 Foundation。先完善并执行 R01-R06，建立可复现的 `Cosmos3-Edge-Policy-DROID -> LIBERO` 无 Memory baseline；R06 PASS 前不进入 Memory 算法实验。

## 当前事实

- 正式设计主线为 Temporal Local Memory 与 Spatial Global Memory 两个独立 optional clean modalities。
- 项目以 `cosmos-framework` 为工程母体；优先新增项目模块，只对 `SequencePlan`、`PackedSequence`、packer 和 Generator adapter 等必要扩展点做集中最小修改。
- 根仓库以当前 `main` HEAD 为准；`cosmos-framework` 子模块已快进同步 NVIDIA `upstream/main` 至 `103c5d1687d290b050e4890f48ff7a38b12742ef`；本地子模块相对 fork `origin/main` 超前 5 个提交，尚未 push。
- `docs/build/log/kimi_operation.log` 是 Kimi 的执行日志，已确认纳入版本控制；其他 Agent 只追加自己的真实操作，不覆盖已有记录。
- 已拉取另一 Agent 的文档一致性修改。该交付修改了 5 份现有正式文档，但没有新增或完善可执行的 R01-R06 Runbook。
- Kimi 记录 `/gemini/code/models/Cosmos3-Edge-Policy-DROID` 已于 2026-08-12 16:08 下载完成；Codex 已按权重索引完成完整性预检，全部引用文件存在且非空。
- 项目 Python 环境已安装到 `/root/venvs/psm_wma`（Python 3.13.13）；大包优先从 `/gemini/code/packages/` 本地安装，Megatron-LM 与 lerobot 使用本地源码快照 override，已规避 Git TLS 中断。当前 GPU 已可见，CUDA 最小张量运算通过。
- 所有 Agent 执行代码、测试、训练、推理或评测前，必须先向用户展示目的、完整命令、工作目录、环境变量、资源/外网需求、输入、产物和判据。
- arXiv:2608.11246 已纳入后续 W10/W11 Agent Harness 高优先级参考，详细记录见 `docs/build/PSM-WMA_Agent_Harness_reference_addendum_v0.1.md` 与 `MEMORY/DECISIONS.md` D007；该参考不改变当前 G0/R01-R09 执行顺序。

### Edge-Policy-DROID -> LIBERO 新确认

- NVIDIA 官方 LIBERO recipe 是从 bare `Cosmos3-Nano` 做 LIBERO SFT，不是从 `Cosmos3-Nano-Policy-DROID` 继续微调；因此不能把 Nano-Policy-DROID 当作官方 LIBERO 起点。
- Nano LIBERO 的数据/动作/闭环评测合同可作为 Edge 迁移基线：20 Hz、`agentview+wrist` concat、10D `frame_wise_relative` rot6d、`quantile_rot`、action chunk 16，并保留官方 gripper / 图像朝向 / normalization parity 检查。
- `action_policy_libero_nano.py` 直接基于 `NANO_MODEL_CONFIG`，不能只替换 checkpoint 路径用于 Edge。Edge 版本应以 `EDGE_MODEL_CONFIG` 为模型基线，再迁移 LIBERO-specific dataset/action/eval 设置。
- 官方公开的 Nano DROID recipe 属于 Generator-side Full SFT，而不是 action-head-only。公开 selector 包括 `moe_gen`、`time_embedder`、`vae2llm`、`llm2vae`、`action2llm`、`llm2action`、`action_modality_embed`。
- 结合 Cosmos3 policy post-training 论文、官方 cookbook 与 Nano DROID recipe，可高置信推断 `Cosmos3-Edge-Policy-DROID` 也经历了大规模 Generator-side policy specialization；但 NVIDIA 未公开 Edge-Policy-DROID 发布 checkpoint 的 exact `keys_to_select`，不得把 Nano selector 写成 Edge 官方事实。
- 若仅把公开 Nano selector 映射到 Edge 参数结构，derived estimate 约为 1.423B trainable、约占 4B 的 35.6%。这是项目估算，不是 NVIDIA 官方 Edge 数字。
- 默认保留 `Edge-Policy-DROID` 已学到的 shared Generator / world-action coupling。R03/R04 的核心待决策项是 DROID `action2llm` / `llm2action` / `action_modality_embed` 与 embodiment domain 在 LIBERO 10D action space 下如何继承、新建 domain 或部分重初始化。
- R02 先做零大权重下载的 metadata/config/index audit；只有仍存在会改变 R04 初始化策略的关键未决问题时，才按需下载 bare Edge 的必要 transformer shard 做 Edge vs Edge-Policy-DROID tensor diff。`Cosmos3-Nano-Policy-DROID` 完整权重不作为当前依赖。
- bare `Cosmos3-Edge` 已位于 `/gemini/code/models/Cosmos3-Edge`（仅 `transformer/` 权重，约 6.3GB）；`Cosmos3-Edge-Policy-DROID` 为完整 HF 推理包（约 8.6GB，含 VAE/vision encoder/tokenizer/scheduler）。两库用途分工见 `MEMORY/DECISIONS.md` D009。

## 正在进行

| 任务 | 负责人 | 状态 | 预计修改文件 | 备注 |
|---|---|---|---|---|
| DOC-R01 | Codex | DONE | `docs/build/PSM-WMA_G0_R01_implementation_runbook_v0.1.md`、`tools/g0/collect_r01_gate_json.py` | Kimi 二轮复审 APPROVE，已关闭全部审查项 |
| G0-R01 | Codex | DONE | `artifacts/g0/r01/`、`tools/g0/`、`cosmos-framework` 最小 guardrail 开关 | Gate JSON `PASS`；用户批准 RoboLab 基础设施豁免，已放通 R02/R03 |
| DOC-R02 | Codex | REVIEW | `docs/build/PSM-WMA_G0_R02_checkpoint_audit_runbook_v0.1.md` | Runbook 已补齐前置资产、命令、Schema、断言、判据、失败分流和回填字段，待独立审查 |
| G0-R02 | Codex | REVIEW | `tools/g0/audit_r02_checkpoints.py`、`artifacts/g0/r02/R02_edge_policy_checkpoint_audit.json` | metadata/config/index audit PASS；warm-start 边界已冻结，待独立审查 |
| DOC-R03 | Codex | IN_PROGRESS | `docs/build/PSM-WMA_G0_R03_action_contract_runbook_v0.1.md` | 独立版本化 Runbook；不与 R02 混入同一提交 |
| G0-R03 | Codex | IN_PROGRESS | `tools/g0/audit_r03_action_contract.py`、`artifacts/g0/r03/R03_action_contract.json` | 运行时核验 LIBERO action/domain/shape/mask/trainable scope，不修改 Cosmos 核心 |
| DOC-R04-R06 | 待认领 | TODO | 后续版本化 Gate Runbook | 不与 R03 混入同一提交 |

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
- 确认 Nano LIBERO official recipe 与 Nano/Edge model config 的边界，并收敛 Edge-Policy-DROID -> LIBERO warm-start 原则；详见 `MEMORY/DECISIONS.md` D006。
- 新增 arXiv:2608.11246 Agent Harness 参考增补并登记 D007；其作用域限定为 W10/W11，不提前影响 G0 或 Memory Gate。
- 完成 G0-R02 metadata/config/index audit：复用支持入口对旧 Edge 导出 K-Norm 根索引的既有兼容逻辑，冻结 Edge-Policy-DROID -> LIBERO warm-start 与数据契约边界。

## 验证记录

- R01 checkpoint 完整性预检 PASS：`cosmos_framework_model.safetensors`、两个 Transformer 分片和 `vision_encoder/model.safetensors` 均存在且非空；另确认 VAE 权重存在。
- 环境验收 PASS：PyTorch `2.10.0+cu130`，CUDA 可用，GPU 小张量运算结果正确；LIBERO、robosuite、lerobot、Megatron Core、Ray、OpenCV 和 OpenPI 导入通过。
- cuDNN 路径根因已定位：`nvidia/cu13/lib` 会命中不兼容的 cuDNN 9.0；将 `/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cudnn/lib` 放在 `LD_LIBRARY_PATH` 首位后，PyTorch 报告 cuDNN `91501`，Policy server CLI 导入及参数解析 PASS。
- 已知例外：`openpi-client==0.1.2` 元数据要求 `numpy<2.0`，而项目 `[tool.uv].override-dependencies` 为 LIBERO/numba 要求 `numpy>=2.0,<2.3`，实际安装 `numpy==2.2.6`；`uv pip check` 因此报 1 条元数据不一致，OpenPI 运行时导入已通过，未修改项目配置。
- Gate JSON 汇总脚本最小验证 PASS：`py_compile` 通过；空证据生成 `BLOCKED`，完整有效伪证据生成 `PASS`，peak VRAM、cuDNN `91501`、warmup/steady latency 与请求级 latency 映射断言通过。Ruff 未执行，原因是环境和 uv 缓存均无 Ruff，未为文档任务新增依赖；`git diff --check` 通过。
- 追加 LOW 复测 PASS：空证据为 `BLOCKED`，完整证据为 `PASS`，仅 1 个 timed request 为 `FAIL_INSUFFICIENT_REQUESTS` 且不再误报 nonfinite；自定义 port/seed/num_steps 准确写入 `run_config`。
- G0-R01 Phase A PASS：checkpoint 索引及 VAE 资产完整，固定 `cosmos-framework@103c5d1`，PyTorch `2.10.0+cu130`/cuDNN `91501`/CUDA 可用。
- G0-R01 Reasoner PASS：实际输入为 `Describe a modern robotics research laboratory in one sentence.`；warmup `14.59s`，3 次稳态 `13.23/13.38/13.40s`，平均 `13.34s`，显存采样峰值约 `6.76GiB`，输出非空且无 NaN/Inf。
- G0-R01 Policy/World PASS：4090 24GB 上加载本地 `Wan2.2_VAE.pth`；1 warmup + 2 timed 请求均返回 finite action `[32,8]` 和 uint8 world video `[33,528,640,3]`，稳态 latency `5961.4/6002.9ms`，峰值显存 `13.69GiB`。Gate JSON 状态 `PASS`、无 blocker/exception；预览视频为 `artifacts/g0/r01/policy_world_preview.mp4`。
- G0-R01 runtime drift：当前云 GPU 只在实际使用时向监控接口报告占用，因此新增 PyTorch CUDA 显存采样器；Policy server 默认 guardrails 改为关闭，显式 `--guardrails` 才启用；checkpoint training config 缺 `_type`，server 回退到 `ActionTransformPipeline(format_prompt_as_json=True)`。
- G0-R01 RoboLab override：真实 `BananaInBowlTask` 启动到 Isaac Sim，但 Orion 虚拟 GPU 的 CUDA/Vulkan/PhysX 设备无法一致映射，报 `No device could be created`，未进入闭环。2026-08-14 用户明确批准 R01 按 Reasoner、Policy action、shared Generator/world smoke 放通；该决定不等同 RoboLab PASS，R06 LIBERO closed-loop 门槛保持不变。
- RoboTTT 文档审查保留项：独立 compressor 下的 TTT-KVB objective、multimodal evidence 到 K/V token 的构造、官方代码/许可证/依赖复用边界尚未冻结；R09-A/B 还需 matched 参数量、训练步数、token budget 和计算预算，不能仅凭“primary candidate”提前选择。
- RoboTTT 文档治理问题：继续直接修改 `frozen/locked` 文件，虽增加 Addendum，但版本号未升级；后续正式冻结应生成新版本，而不是继续累积覆盖。
- 文档审查发现：R01-R06 只有目的、检查和 PASS 摘要，缺少精确命令、完整前置资产、源码入口、逐 Gate 修改文件、统一断言、失败分流和回填清单，不能直接执行。
- 文档治理发现：提交直接修改 `frozen/locked` 文件但未升级版本或增加对应修订记录。
- 一致性残留：技术调研第 10 章仍写“Local/Goal persistent state”；Static Audit 仍保留 `K_local/K_goal/K_psm` 旧字段。
- Edge->LIBERO warm-start 事实分级已明确：官方事实、项目高置信推断、derived estimate、待 R03/R04 实证项分开记录。
- arXiv:2608.11246 当前仅按后续 Agent 参考记录；W10/W11 启动前要求重新核验一手论文/代码，不把当前概括当作冻结实现事实。
- 已确认工作目录：`/gemini/code/psm_wma`。
- DOC-R01 主提交：`dde7621`。
- Edge vs Edge-Policy-DROID 对比（Codex 结构+分层抽样，2026-08-13；Kimi header 级复核，2026-08-14；R02 索引复核，2026-08-14）：base Transformer 为 549 个规范键；Policy-DROID 原始根索引含 56 个 K-Norm 条目（28 个错误旧别名 + 28 个 overlay 条目），项目支持入口会全部移除并从 transformer 子索引补回 28 个规范 K-Norm，最终有效 Transformer 键集同为 549。共同张量 0 shape 不匹配，仅 4 个 `time_embedder` 张量 BF16→FP32（约 +9.4MB），`action_proj_in/out`、`action_modality_embed` 两边都有。Codex 数值变化结论（`moe_gen`/action 模块已改写、`embed_tokens`/普通 norm 未变）仍为分层抽样证据，未宣称全量数值 diff。
- G0-R02 验证 PASS：审计产物 `status=PASS`，原始根索引 1014 键、支持入口有效索引 986 键、有效缺失 0；原始 K-Norm 56 = 错误旧别名 28 + overlay 28，合并 transformer 子索引后规范 K-Norm 28。`py_compile`、JSON 关键断言和 `git diff --check` 均通过；Policy 实际加载/推理证据复用 G0-R01。限制：`cosmos_framework.inference.model` 已兼容该旧导出，`inference2/_model_io.py` 尚未同步，当前不得用后者加载此 checkpoint。

## 下一交接

1. 独立审查 G0-R02 Runbook、脚本与 JSON；通过后将 DOC-R02/G0-R02 转 DONE。
2. 执行 G0-R03；R02/R03 保持独立 Gate 和提交边界，不把 RoboLab 未执行误记为任务成功。
3. R03 明确产出 `action2llm` / `llm2action` / `action_modality_embed` / domain 的 inherit-vs-reinit 决策与运行时证据。
4. R04 仅在 R02/R03 contract 明确后执行 Edge-Policy-DROID x LIBERO forward/loss smoke。
5. 后续分别新建版本化 R03-R06 Runbook，不扩写 frozen/locked 文档；同时修复两处残留旧口径，并用新版本/修订记录处理 `frozen/locked` 文档治理问题。
6. W10/W11 启动时读取 `PSM-WMA_Agent_Harness_reference_addendum_v0.1.md`，复核 arXiv:2608.11246 后再决定 scene/context 与 execution-evaluation 接口是否进入实现。
