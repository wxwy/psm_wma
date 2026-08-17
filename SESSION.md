# 当前协作状态

更新时间：2026-08-17

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
| DOC-R02 | Codex | DONE | `docs/build/PSM-WMA_G0_R02_checkpoint_audit_runbook_v0.1.md` | Kimi 独立审查 APPROVE；MEDIUM-1 与 LOW-1/2/3/4 已关闭，Runbook 状态 `reviewed` |
| G0-R02 | Codex | DONE | `tools/g0/audit_r02_checkpoints.py`、`artifacts/g0/r02/R02_edge_policy_checkpoint_audit.json` | metadata/config/index audit PASS；provenance 完整，warm-start 边界已冻结 |
| DOC-R03 | Codex | DONE | `docs/build/PSM-WMA_G0_R03_action_contract_runbook_v0.1.md` | Kimi 独立审查 APPROVE；2 MEDIUM + 3 LOW 已关闭或按范围转交，Runbook 状态 `reviewed` |
| G0-R03 | Codex | DONE | `tools/g0/audit_r03_action_contract.py`、`artifacts/g0/r03/R03_action_contract.json`、`cosmos-framework@3b4a929` | 真实 LIBERO runtime contract、参数拆分与 stats provenance PASS，并通过独立审查 |
| DOC-R04 | Codex | IN_PROGRESS | `docs/build/PSM-WMA_G0_R04_forward_loss_runbook_v0.1.md` | 独立版本化 Runbook；不与 R03 混入同一提交 |
| G0-R04 | Codex/Kimi | DONE | `tools/g0/r04_step_metrics.py`、`tools/g0/verify_domain_rows.py`、`artifacts/g0/r04/adamw_nonfused_20step/` | 非 fused AdamW 连续 20 步 PASS；机器可读 loss/资源/domain 行保护证据和末次 checkpoint 完整 |
| DOC-R05 | Codex | DONE | `docs/build/PSM-WMA_G0_R05_tiny_overfit_runbook_v0.1.md` | 已经独立审查与实执验收，状态 `reviewed` |
| G0-R05 | Codex/Kimi | DONE | `artifacts/g0/r05/R05_libero_tiny_overfit.json`、R05 审查报告 | Gate `PASS`；100 步训练、两次 reload、checkpoint 完整性和独立验收全部通过 |
| DOC-R06 | Kimi | REVIEW | `docs/build/PSM-WMA_G0_R06_closed_loop_baseline_runbook_v0.1.md` | 已创建并经实执验证；两处偏差（RLinf venv、TRITON_LIBCUDA_PATH）待升 v0.2 |
| G0-R06 | Kimi | REVIEW | `artifacts/g0/r06/`、`docs/build/PSM-WMA_REVIEW-G0-R06_closed_loop_2026-08-15.md` | Gate `FAIL_SR_ZERO`：链路全绿、逐位可复现，但 zero-shot SR=0/3；待用户决策 baseline |

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
- Kimi 对 G0-R02 独立审查结论 `APPROVE`；关闭 MEDIUM-1（Gate provenance）与 LOW-1/2/3/4（LIBERO 证据锚点、vision extra keys、R01 load 证据复用措辞、Runbook 状态）。

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
- G0-R02 审查收尾复测 PASS：JSON 增加 UTC 时间、repo/cosmos commit、脚本 SHA-256、argv/run_config；LIBERO 契约逐项带官方 recipe 行号；vision encoder 6 个未索引 projector header 键完整列名。`py_compile`、provenance/契约/extra-key JSON 断言与 `git diff --check` 通过。
- G0-R03 本地 LIBERO schema 兼容：现有 20Hz 数据使用 `tasks.jsonl` / `episodes.jsonl` / `episode_*.parquet`，与 loader 原先只接受的 parquet metadata / `file-*.parquet` 布局不一致；`cosmos-framework@59653c5` 增加原格式优先、JSONL/per-episode fallback，并给 `video_path.format` 补 `episode_index`，未改变 action/video 语义。
- G0-R03 真实 LIBERO SFT 样本 PASS：本地 `libero_10_no_noops_1.0.0_lerobot` 加载 379 episodes、95,405 个有效窗口；样本 video `[3,17,192,320]` uint8，action `[16,64]`、`action_raw` `[16,10]`，`raw_action_dim=10`、`domain_id=5`、20Hz、finite、WAM `SequencePlan`。TorchCodec 需在启动命令中把环境内现有 `nvidia/cudnn/lib` 与 `nvidia/cu13/lib` 加入 `LD_LIBRARY_PATH`；无需下载或修改系统配置。
- G0-R03 正式审计 PASS：真实 action 链为 parquet `[16,7]` → rot6d `[16,10]` → `quantile_rot` `[16,10]` → model `[16,64]`；DomainAwareLinear shape smoke 为 64→2048→64 且 finite。按 Policy-DROID header 与官方 selector 实算 trainable `1,423,379,648`；纯 Transformer 为 `3,369,657,024`，selected 占 42.24%；含 vision encoder `412,649,712` 后 model 总计 `3,782,306,736`，selected 占 37.63%。
- R03 warm-start 冻结：LIBERO 使用独立 domain 5，DROID 为 domain 8；继承 shared Generator/time/vision adapters 与 `action_modality_embed`，保留其他 domain 权重，仅重初始化并更新 action projection 的 domain 5 行。R04 必须验证 optimizer step 前后其他 domain 行不变，避免 AdamW weight decay 漂移。
- R03 已知语义限制：LIBERO dataset 已完成 `quantile_rot` 后，通用 transform 将该 10D 张量保存为 `action_raw`；训练输入没有重复归一化，但字段名并非 parquet 原始 7D，R04 前需决定修正文档还是接口。
- Kimi 对 G0-R03 独立审查结论 `APPROVE`：MEDIUM-1 已通过参数分母拆分关闭；MEDIUM-2 已记录 stats 路径与 SHA-256，并转为 G0-R05 前置分布 sanity check；LOW-1 新增 JSONL/per-episode fallback 单测（`cosmos-framework@3b4a929`，1 passed）；LOW-2 Runbook 转 `reviewed`；LOW-3 provenance 语义已显式记录。
- G0-R04 配置阶段：Policy-DROID 已离线转换为 `/gemini/code/models/Cosmos3-Edge-Policy-DROID-dcp`（2026-08-14 自 `/root/models/psm_wma/` 迁入，与源 checkpoint 同级；R04 TOML 经 `BASE_CHECKPOINT_PATH` 环境变量引用，无硬编码路径），包含两个 DCP shard、总计 6.3GB；首次转换因 processor 指向 HF repo 在 offline 模式失败，改用 R01 已验证的本地 processor override 后成功，未修改 checkpoint。
- G0-R04 新增 `action_policy_libero_edge_warmstart` 与单步 TOML（`cosmos-framework@1c0c691`）：复用 Nano LIBERO 数据合同，模型切换为 `EDGE_MODEL_CONFIG`，保留 Policy-DROID action heads，关闭 EMA/compile，并对两个 domain-aware action projection 禁用 weight decay。配置解析、`compileall`、定向 Ruff 与 `git diff --check` PASS。
- 当前 CUDA runtime 仅暴露 1 张 `B4.gpu.large`、25.24GB；R04 将先尝试 1 sample/1 step，若 OOM 记为资源 BLOCKED，不归为代码 FAIL，并在可用 A100/多卡上续跑正式 20–50 steps。
- G0-R04 4090 单卡真实训练诊断：本地 processor、Wan2.2 VAE、LIBERO train split（375/379 episodes、94,250 valid indices）和 DCP 549/549 keys 均加载成功；optimizer 实测选中 294 tensors / 1,423,379,648 elements，其中两个 domain-aware projection 的 4 tensors / 8,456,192 elements 正确进入 `WD=False` 组。forward 与 backward 已完成，finite global grad norm 为 `52.75`；首次 `optimizer.step()` 创建 FP32 Adam 二阶状态时 OOM（23.45/23.51GiB 已用、仅余 58.05MiB、再申请 72MiB 失败）。该结果判定为 4090 资源 BLOCKED，不是代码 FAIL；完整 20–50 steps 需 A100 或多卡 FSDP。
- R04 启动中关闭了离线 smoke 不需要的 W&B basic callback（`cosmos-framework@321afc4`），保留 NaN/grad-clip/device-monitor；原因是当前 wandb 版本无 `wandb.util.generate_id`，且 `wandb_mode=disabled` 时上游 basic callback 仍无条件初始化 W&B。
- 切换 A100 节点后，用户指定将 `/root/venvs/psm_wma` 改为 Python 3.11 + PyTorch 2.7 cu128。旧 Python 3.13/cu130 环境完整备份于 `/root/venvs/psm_wma_py313_cu130_backup`；原路径已建立 Python 3.11.8 环境并从 `/gemini/code/packages/` / `uv-cache-robolab` 离线恢复 torch `2.7.0+cu128`、torchvision `0.22.0`、Triton `3.3.0` 和匹配 CUDA 12.8 运行库。Orion 的只读 NCCL 文件挂载残留在旧 `lib/python3.13` 子目录，不进入新 Python 3.11 site-packages。
- 新节点底层 PCI 为 A100，但 Orion 对当前进程暴露为 `P1.gpu.medium`、39.17GiB。Python 3.11 / torch `2.7.0+cu128` 在不手工设置 CUDA/NCCL `LD_LIBRARY_PATH` 时，最小 `.cuda()` 张量实测 PASS（`cuda:0`，`sum(x²)=14.0`）。此前 exit 151 / `not enough ratio` 与时变 GPU 配额未激活有关（调度层证据）；`LD_LIBRARY_PATH` 是否干扰 Orion 加载链未单独证实，当前成功路径为干净激活环境，后续不注入 CUDA/NCCL 路径。
- 新环境候选 `/root/venvs/psm_wma_py313_cu128` 已完成 Python 3.13.13 + PyTorch `2.10.0+cu128` + CUDA 12.8 核心安装；本地 25 个核心 wheel 哈希通过。`uv pip check` 通过，`torch/flash_attn/natten/megatron.core/transformer_engine/lerobot/datasets/pandas/pyarrow/wandb` 导入和 CUDA 张量验证通过。R04 TOML 在设置 `BASE_CHECKPOINT_PATH`、`WAN_VAE_PATH`、`EDGE_POLICY_CHECKPOINT`、`DATASET_PATH`、`LIBERO_ROOT`、`IMAGINAIRE_OUTPUT_ROOT` 后解析 PASS。配置预检过程中补齐了 `iopath`、MSC 纯 Python 包及其运行依赖、`qwen-vl-utils`、`webdataset` 等小依赖；未自动下载超过 50MB 的新包。当前仍未切换 `/root/venvs/psm_wma` 正式入口，待 R04 单步训练验证。
- G0-R04 py313/cu128 重试：从 `cosmos-framework/` 工作目录并使用实际 LIBERO 数据集根启动后，模型/VAE、DCP 549/549 keys、LIBERO 375/379 episodes、forward、backward 和 finite grad clip 均成功；在 FusedAdam 首次创建 optimizer 状态时再次收到系统 `SIGKILL (-9)`。关闭 DataLoader worker（`num_workers=0`, `prefetch_factor=null`）后仍复现，GPU 约 8.5GiB/40GiB，判定为当前主机内存/资源 BLOCKED，不是代码或 CUDA OOM。日志：`artifacts/g0/r04/py313_cu128_r04_retry_final.log`。
- Kimi R04 中期复核确认容器 `memory.max=34359738368`（32GB）；后续可选缓解包括申请更大容器内存、让 optimizer 状态直接在 GPU 创建，或采用 8-bit optimizer，具体方案待 R04 续跑时决定。

## 下一交接

1. G0-R04 已完成：非 fused AdamW 连续 20 步 PASS；后续若扩展训练，优先接入 R12 latent 缓存或启用 `num_workers>=2`，避免 CPU 视频解码瓶颈。
2. R04 执行器必须在 DCP load 后重初始化 domain 5 行，并验证 optimizer step 前后其他 domain 行不变；`action_raw` 当前按“已归一化的原始维度 action”记录，不在 R04 改公共接口。
3. 后续分别新建版本化 R04-R06 Runbook，不扩写 frozen/locked 文档；同时修复两处残留旧口径，并用新版本/修订记录处理 `frozen/locked` 文档治理问题。
4. G0-R05 启动前完成本地 action 分位数与内置 stats q01/q99 的分布 sanity check。
5. W10/W11 启动时读取 `PSM-WMA_Agent_Harness_reference_addendum_v0.1.md`，复核 arXiv:2608.11246 后再决定 scene/context 与 execution-evaluation 接口是否进入实现。

### G0-R04 正式验收（2026-08-15，Kimi 执行，Codex 验收）

- 产物：`artifacts/g0/r04/adamw_nonfused_20step/{step_metrics.jsonl,domain_row_guard.json,R04_gate.json,train_20step.log}`；终审报告 `docs/build/PSM-WMA_REVIEW-G0-R04_final_nonfused_2026-08-15.md`。
- Codex 复核：`R04_gate.status=PASS`、20 行 metrics 且 iteration 1–20 连续、loss/grad 全 finite、`domain_row_guard.pass=true`、冻结行 bitwise diff=0、domain 5 均更新、末次 checkpoint `iter_000000020` 的 model/optim/scheduler/trainer 四目录齐全；两个新增工具 `py_compile` 通过。
- 数值：loss `16.4969→13.6540`，grad norm（clip 后）最大 `1.00498`；GPU 分配峰值 `34270.6 MiB`，RSS 峰值 `19,954,976 KB`，无 OOM/SIGKILL。
- 结论：G0-R04 正式 Gate `PASS`，任务状态 `DONE`。后续扩展建议使用 R12 latent 缓存或 `num_workers>=2`，当前瓶颈为 CPU 视频解码。
### G0-R04-ADAMW（单步完成，Kimi APPROVE）

- 最小修改：`cosmos-framework/cosmos_framework/utils/generator/optimizer.py` 仅对标准 `Adam`/`AdamW` 允许 `fused=False`；`FusedAdam`、Muon/Dion2 等 fused-only 路径仍拒绝非 fused。
- 验证：`python -m py_compile`、`git diff --check` 通过；R04 单步从 DCP load、forward/backward、grad clip 到 `optimizer.step()` 均完成，日志出现 `Done with training.`。
- 结果：loss/梯度路径未出现 NaN/Inf；checkpoint 已保存至 `/gemini/code/psm_wma/artifacts/g0/r04/adamw_single_step_retry2/psm_wma/g0_r04/edge_libero_forward_loss/checkpoints/iter_000000001`（约 12GB）。
- 资源：GPU 峰值约 `40192/40488 MiB`（99.3%）；训练进程 RSS 峰值约 `16,497,588 KB`（约 15.7GiB）。此前 32GB 容器 SIGKILL 未复现。
- 限制：这是 1 step 诊断，不等同 R04 20–50 steps PASS；正式审查报告为 `docs/build/PSM-WMA_REVIEW-G0-R04_adamw_nonfused_review_2026-08-15.md`。
- Kimi 审查保留：MEDIUM-1 资源峰值尚未写入机器可读产物；LOW-1 单步 loss 未记录；LOW-2 已在本次记录中清理过时的暂停 PID 口径。三项均不阻止本次单步 APPROVE。

### G0-R12-CACHE（已完成，Kimi 核验通过）

- 任务状态：DONE；实际修改 `tools/g0/build_cosmos_rgb_latent_cache.py`、`MEMORY/DECISIONS.md`、`SESSION.md`、`TODO.md`。
- 设计事实：离线 RGB 编码严格复用 Cosmos `OmniMoTModel._encode_vision_item`，按 camera clip 独立 VAE encode，使用 uint8→[-1,1] 归一化，camera-major temporal 拼接；禁止逐帧独立编码。
- 全量完成（Kimi，2026-08-15）：379/379 episode 成功、零错误；产物 `/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_latent` 约 1.2G；`dataset_manifest.json` 为 `episode_count=379`、`image_size=256`、`script_revision=8c9b443`。
- 独立核验：抽查 12 个 episode 的 latent 全部 finite；379 个 episode 全部满足 `latent_frames = 1 + ceil((video_frames - 1) / 4)`；日志 `artifacts/g0/r12/full_dataset_cosmos_image256.log`。编码进程两次被外部 SIGSTOP，均 SIGCONT 无损恢复并正常退出。
- 验证结果：真实 LIBERO RGB `[3,17,192,384]` → latent `[48,5,12,24]`，finite；工具路径与 Cosmos 直接 batch 路径 `max_abs=0.0`、shape 完全一致。Kimi 审查发现并已修复 image_size 默认值、manifest 续跑丢失、非原子写入、uint8 rounding、provenance 和完整 instruction 保存。修复后用 `--image-size 256` 完成 1 个 episode：原始 `[3,214,256,512]`，按 Cosmos `4n+1` 规则补到 217 帧，得到 `[55,48,16,32]` FP16 latent，源帧映射 `[55]`，原文指令已保存；产物位于 `/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_latent/episodes/episode_000000.pt`。`py_compile` 与 `git diff --check` PASS；全量 379/379 已完成并由 Kimi 核验。

### G0-R05（DONE，Kimi 终审 APPROVE）

- stats 前置审计：扫描本地 379 个 parquet、101,469 帧，按 Cosmos axis-angle→rot6d 路径比较内置 `global_raw` q01/q99；10D 全 finite，最大 `[-1,1]` 外尾比例 `0.0306892 < 0.10`，`artifacts/g0/r05/R05_action_stats_sanity.json` 为 PASS。
- 新增确定性 tiny subset：训练 flat index `[0,1,2,3]` 循环，held-out index `4`；索引实测五个窗口均为 episode 0/task 0，互不重叠且不随机 shuffle。
- 新增 R05 分项指标：每步 total/action/vision loss、由 rectified-flow 恒等式推导的 detached `action_x0_reconstruction_mae`、grad、GPU peak、RSS；第 100 步和完整 checkpoint reload 后各记录一次 held-out。
- 新增 `action_policy_libero_edge_tiny_overfit` 与 R05 TOML；100 steps、EMA off、AdamW `fused=false` 由命令 override，checkpoint `iter_000000100`。
- 轻量验证：所有新增/修改 Python `py_compile` PASS；固定 subset 循环、x0 MAE 公式、TOML 生效配置和 `git diff --check` PASS。pytest 未执行，原因是当前 py313/cu128 环境未安装 pytest；已保留对应单测供 Kimi 审查环境执行。
- Runbook：`docs/build/PSM-WMA_G0_R05_tiny_overfit_runbook_v0.1.md`，包含 stats、100-step、reload consistency、Gate collector 的完整命令和判据。
- Phase B 实行：100/100 步 loss/grad 全 finite、趋势阈值全部达标，`iter_000000100` 四件 checkpoint 完整；步后 held-out 验证暴露 `OmniMoTModel.validation_step` 空桩，Kimi 标记 HIGH-1 / REQUEST_CHANGES。
- HIGH-1 修复：`cosmos-framework@fbe85a0` 在既有 `@torch.no_grad()` 下复用 `training_step` 的完整前向/损失路径，返回 trainer 要求的 `(output_batch, total_loss)`；未新增损失实现或改动训练语义。
- 修复验证：`py_compile`、dummy 返回值透传/无梯度断言、`git diff --check` 全部 PASS；真实 GPU reload 未由 Codex 重复执行，交 Kimi 复审后从 Phase C 续跑。
- HIGH-1 复审：Kimi 结论 APPROVE；Phase C 首次 reload 已成功读取 model 549 keys / optimizer 4410 keys，但暴露 HIGH-2：单进程 NCCL 对非 capturable AdamW 的 CPU `step` 标量做多余 broadcast 而崩溃。
- HIGH-2 修复：`cosmos-framework@8421e41` 在 `_broadcast_state_dict` 入口对 `world_size == 1` 直接返回；单 rank 是所有叶子唯一 reader，DCP 已读全状态，因此无需任何补全广播，多卡分支未改动。
- HIGH-2 定向验证：`py_compile` PASS；mock world size 1 且将 tensor/object broadcast 设为调用即失败，含 CPU AdamW `step` 的嵌套状态原样保留且零 collective；`git diff --check` PASS。真实 checkpoint reload 交 Kimi 复审后续跑。
- 最终验收：`artifacts/g0/r05/R05_libero_tiny_overfit.json` 为 `PASS`、`failures=[]`；100/100 步全 finite，total/action/action-x0/vision ratio 分别为 `0.705/0.745/0.735/0.285`；GPU 峰值 16653.5 MiB，RSS 峰值 12.3 GiB，checkpoint 四件齐全。
- Phase C 两次独立 reload 均恢复 iteration 100，held-out 四项逐位一致，`max_abs_diff=0.0`；Codex 独立解析 Gate/JSONL 并核对 DCP metadata/shard，结论 PASS。
- 已记录 deviation：实跑使用 `max_samples_per_batch=1` / `grad_accum_iter=32`；Phase B held-out 因 HIGH-1 未产出，Gate 以两次 iteration-100 确定性 reload 做一致性比对。
- 非阻塞遗留 MEDIUM-3 已转 `DCP-MULTIRANK-RELOAD` 并写入 `MEMORY/DECISIONS.md` D011：正式多卡 reload 前必须修复 CPU optimizer 叶子与 NCCL backend 不匹配。

### G0-R06（Gate FAIL_SR_ZERO，2026-08-15，Kimi 执行）

- 端到端闭环链路验证 PASS：RLinf venv(py3.11, mujoco 3.8.1, robosuite 1.4.1, libero 0.1.0 editable)+ EGL 离屏渲染；policy server(py313/cu128）直载 Edge-Policy-DROID 原始 HF checkpoint,domain_name="libero"(domain 5),10D frame_wise_relative rot6d,chunk 16。
- 两处环境修复已记录：`.r06_sim_pkgs` wheel 版 libero 遮蔽 editable 且缺 assets（已改名禁用，`/root/.libero/config.yaml` 指向 RLinf 资产）;server 端 triton `libcuda.so.1` 缺失，用 `TRITON_LIBCUDA_PATH=/opt/orion/orion_runtime/gpu/cuda` 修复（首轮 BLOCKED 证据归档 `artifacts/g0/r06/eval_task0_failed_triton/`)。
- 正式结果：libero_10 task 0 × 3 episodes，全部 520 步满 rollout、error=null、action 全 finite(3×520×7D)，但 SR=0/3；同 seed 0 重跑逐位一致（max_abs_diff=0.0)。server 193 次 /predict 稳态中位 1714ms/chunk,GPU 观测 9544 MiB。GIF 目视：机械臂悬停移动，未抓取任何物体。
- Gate JSON `artifacts/g0/r06/R06_libero_closed_loop.json`:status=FAIL,failures=[FAIL_SR_ZERO]；报告 `docs/build/PSM-WMA_REVIEW-G0-R06_closed_loop_2026-08-15.md`。
- 判读：zero-shot baseline 在 domain 5 未经 LIBERO 训练的发布 checkpoint 上不成立；SR>0 需用户重新决策 baseline（正式 LIBERO SFT checkpoint)。
- 用户决策（2026-08-15 晚）:R06 改为正式 LIBERO SFT baseline（新任务 G0-R06-SFT);zero-shot SR=0 作为诊断记录保留，其 Gate 证据 `R06_libero_closed_loop.json` 与 `eval_task0*/` 不得修改；SFT baseline 另出新 Gate JSON/报告，与 zero-shot 明确区分。

### G0-R06-SFT 探针(2026-08-16 凌晨,Kimi 执行)

- Probe 1(5 步显存,在线 VAE)PASS:5/5 步,GPU 步峰值 33.1 GiB,RSS 8.6 GB,稳态 75-130 s/step,loss 15.6→13.7 正常。
- Probe 2(latent parity)FAIL:latent max_abs_diff=4.625;连 start%4==0 对齐窗口 diff 仍有 1.79,证明 R12 整段因果编码切片≠17 帧独立窗口编码。cache 不启用,正式训练走在线 VAE。
- 正式 500 步训练预计 10-18 小时,待用户授权后启动。产物:`artifacts/g0/r06/sft_baseline/{probe,parity}/`,详见 `docs/build/PSM-WMA_REVIEW-G0-R06-SFT_code_review_2026-08-16.md`。

### 文件认领(2026-08-16,Kimi)

已全部提交并解除认领(根仓 `efed1ff`、cosmos `3e44d15`)。历史认领文件：`tools/g0/build_cosmos_libero_latent_dataset.py`、`cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py`(仅 cache 注入 dtype)、`docs/build/PSM-WMA_RGB_representation_and_memory_encoding_plan_v0.1.md`(新增)、`MEMORY/DECISIONS.md`、`SESSION.md`、`TODO.md`。

### G0-R06-SFT 口径切换(2026-08-16 下午,Kimi 第一技术审查者)

- 探针结论:Probe1 显存 PASS(在线 VAE,33.1GiB/75-130s每步);Probe2 parity FAIL,R12 整段因果编码≠17帧窗口独立编码(diff 4.625,对齐窗口仍1.79)。
- 契约核查:mowa 主线也是整段因果(其推理用流式 encoder 自洽);Cosmos LIBERO 在线/推理是单 vision item concat_view [3,17,256,512]→5 latent,从不启用 per-camera 路径。Codex 的 f7fe84c/19e0bd3 双视角复制版对新旧契约都不成立,REQUEST_CHANGES 后**暂停**(降级为回退路径)。
- 新方向:冻结文档 `cosmos-framework/docs_zh/psm_wma/REGULAR_EPISODE_LATENT_OVERFIT.md`(8fb48a9/69f2260),Kimi 评审 APPROVE,风险点=视觉 token 网格变化、闭环 oracle O(t) 成本、Codex 周额度 9%。
- 当前:Codex 按 §13 第 1 步实现 regular_episode_latent reader + 单测,Kimi 待复审。

### exact-window cache 阶梯验证(2026-08-16 晚,Kimi 执行)

- 方向确认:主线 = Cosmos-native exact-window offline cache(plan v0.1 + D013);REGULAR_EPISODE 降级历史候选;Codex regular_episode 工作已停止并清理。
- 代码修复(Kimi,未提交):builder 补 uint8→[-1,1] 归一化;cache 注入保持 fp32;parity 改独立在线参照;latent_cache 缺 episode 文件回退在线;schema_version=exact_window_v1。
- 阶梯1 parity:diff=0.0 逐位一致(5 窗口覆盖 start%4 全类);阶梯2 单 episode 构建 198 窗口 97.5MB;阶梯3 对齐 198/198 全对;阶梯4 cached forward 3步 PASS(iter1 与在线逐位一致,iter2/3 ~3e-5 漂移记 LOW);阶梯5 多 worker loader PASS(RSS 1.5GB)。
- 产物:`/gemini/code/data/libero/exact_window_v1_smoke/`、`artifacts/g0/r06/exact_window_v1/`。

### DS/Codex 第二审查跟进与阶梯4b(2026-08-16 深夜,Kimi 执行)

- DS 第二审查 APPROVE,附 MEDIUM-1/2、LOW-1/2;Codex 对修复 diff 复审 APPROVE。
- MEDIUM-1:builder 与 parity 参照从 `torch.round` 改为截断,逐位对齐在线 `base_dataset.py:214`;smoke cache 重建(705 窗口)后 parity ep0/ep18 重跑 diff=0.0。
- MEDIUM-2:阶梯4 表述更正为"混合 batch 全批在线回退的重现";补阶梯4b 全批 cache 命中 forward(tiny_overfit_num_samples=16):16/16 命中、3/3 finite、~50s/步(在线 ~120s),PASS。
- LOW-1:REGULAR_EPISODE_LATENT_OVERFIT.md 加 SUPERSEDED BY D013 横幅;LOW-2:外层 ActionLatentCacheDataset 跳过重复查询。
- 启动方式记录:torchrun 直启脚本路径会被 `cosmos_framework/scripts/hydra.py` 遮蔽 hydra 包,必须 `-m cosmos_framework.scripts.train`。
- 提交:cosmos-framework `3e44d15`,根仓 `efed1ff`(未 push)。
- 方案A(已完成):libero_10 task0 全量 exact-window 编码完成,产物 `/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_exact_window_v1/`(命名约定 `<源数据集名>_cosmos_exact_window_v1`;38 ep / 9199 窗口 / 4.3GiB fp32,script_revision=a9c5a90);Kimi 核验 PASS,DS(Claude 监督)开箱检查 PASS(与 smoke3 ep0 逐位一致 198/198);smoke3 已按约定删除;训练侧经 `LIBERO_LATENT_CACHE_ROOT` 引用,不硬编码。下一步:500 步正式 SFT 待用户授权启动。
- 文件认领解除:本轮 Kimi 编辑文件均已提交,无持锁文件。

### G0-R06-SFT 训练/评测任务错位发现与 iter300 闭环(2026-08-17 上午,Kimi 执行)

- **任务错位(重要偏差)**:训练侧 `task_index=0` 是 LeRobot `tasks.jsonl` 顺序(马克杯/盘子:"put the white mug on the left plate and put the yellow and white mug on the right plate");仿真侧 `--task_ids 0` 是 LIBERO benchmark map 顺序(soup+sauce→basket, LIVING_ROOM_SCENE2)。证据:`/gemini/code/RLinf/.venv/libero/libero/libero/benchmark/libero_suite_task_map.py:38` 的 libero_10 列表第 5 项(index **4**)才是马克杯任务。**之前 zero-shot R06 评测(FAIL_SR_ZERO)与 iter300 首测测的都是模型未训过的 soup 任务;zero-shot 的 SR=0 结论受此偏差影响,但其"发布 checkpoint 在 LIBERO domain 5 无零样本能力"的定性不变。**
- iter300 对齐重测(task_ids 4,3 episode,seed 0):**SR=0/3**;3 episode 均 520 步满 rollout、error=null、action 全 finite(520×7D);GIF 目视机械臂有目的性移动、逼近目标马克杯区域,但未完成抓取/放置。判读:链路正确、任务对齐后行为明显改善(对比 soup 任务的盘旋),iter300(~8.5 epoch)欠训练,非错位或管线问题。产物 `artifacts/g0/r06/eval_task4_iter300_sft/`;错配首测留档 `eval_task0_iter300_sft/`。
- 1000 步正式训练已恢复(tmux r06sft,same-job 从 iter 301 续训,最新完整 checkpoint iter_000000300);计划到 1000 步后用 `--task_ids 4` 复测,中途可在 400/500 checkpoint 加测。
- 评测口径冻结:后续所有 R06-SFT 闭环评测必须使用 `--task_ids 4`(与训练 task_index 0 对齐),并在报告中注明该映射证据。

### G0-R06-SFT iter500/600 评测、OOM 与视觉输入错位修正(2026-08-17 下午,Kimi 执行)

- iter500 闭环评测(task_ids 4×3,seed 0):SR=0/3,链路全通、action finite;与 iter300 同 seed 行为类别一致(悬停不抓取)。zero-shot 原版 DROID 对照:SR=0/3,行为=远离桌面大幅游荡(mean|a|=0.82 vs SFT 0.24),证实 SFT 有效拉向任务。产物 `eval_task4_iter500_sft/`、`eval_task4_zeroshot_droid/`。
- 14:28 训练遭 memcg 32GB OOM SIGKILL(dmesg 实锤:shmem-rss 10.5GB + checkpoint 写网络盘 page cache 叠加);按用户条件删除 iter100-400(释放 48GB,保留 500/600);加 sync 守护每 180s flush 脏页。
- **视觉输入错位(重要修正)**:此前全部闭环评测(zero-shot/iter300/iter500)用 `--camera agentview` 单视角 256×256,而训练是 `camera_mode: concat_view`(agentview|wrist 横拼 256×512,latent [5,48,16,32])。iter600 起评测口径改为 `--camera agentview,wrist` 双视角对齐。
- iter600 双视角评测:**SR=0/3**,3 episode 均 520 步满 rollout、error=null、action finite(mean|a|=0.207);初判"抓取+举起"经用户质疑后**复核更正**:iter600 vs iter500 执行动作 mean|diff| 仅 0.062-0.073、前 60 步逐维均值几乎一致,同帧抽图(200/450 步)两臂姿态相同——均为**悬停在红色花纹马克杯上方未抓取**,双视角对齐后行为无显著变化;且红杯不在任务指令内(指令=白杯→左盘、黄白杯→右盘),疑似 fixation 错误目标。判读:输入错位与训练量均非已证实根因;iter1000 复测若仍 SR=0 立即转契约排查(open-loop 专家动作回放+目标对象核验),不再加步数。产物 `eval_task4_iter600_sft/`(含 comparisons 对比 MP4)。
- 评测后以 4 workers × prefetch_factor 1 从 iter_000000600 same-job 续训(tmux r06sft):实测 48s/步≈2×2 速度,RSS 仅 3.4GB(较 4×2 的 13GB 大降,memcg 安全);resume 从 trainer 保存态 iteration 603 起,loss/grad 连续正常,GPU 36.9GB/100%。
- iter700 horizon=4 诊断(用户假设:只执行前4步):**SR=0/3,与 horizon=16 相同且复跑一致,开环漂移非主因,坐实策略内容问题**;动作 finite,mean|a|=0.157。产物 `eval_task4_iter700_sft_h4/`(384 个逐窗口 17 帧预测 MP4,双编号 win+step,采集时渲染 GT=蓝框/PD=红框)。评测后从 iter700 续训(21:09)。结论更新:horizon、视觉视角均已排除,iter1000 复测仍 0 则转 open-loop 专家回放契约排查。
