# PSM-WMA V3 — iter4000 DS_PRO HIGH-06 CPU Evidence 与 G1 真实 Action Chunk 解析审核

日期：2026-10-21
Gate：新证据触发的 **真实推理配置/集成准入 Gate**，不是对同一 formal pair 重做已经关闭的技术代码审核。
Formal Implementation Root：`950b2dbc6ad112205153a18dc0f733812db30706`
Child/Gitlink：`2d128ed5a07601cdd424974f99b67832eafeeb41`
Queue Blob：`cb829cec0e43c09e8298e9d896a473b7b8285739`
前一静态修复 verdict：`docs/collab/chatgpt/reviews/2026-10-21_V3_iter4000_HIGH06_950b2dbc_incremental_review.md` 的 `APPROVE` 维持有效、仅覆盖 HIGH-06 CPU/static scope。

## Verdict

**`REQUEST_CHANGES` — 真实 G1 iter4000 推理长度协议 Gate**。
- DS_PRO 提交新 Pair 的 5 项独立 CPU 定向测试全部 PASS，Ruff check/format RC0、SHA clean、错误路径 fail-closed（以 DS 现场报告为准）；旧 HIGH-06 CPU/static verdict 不重新审核或重开。
- 但 DS 用**真实** G1 `config.yaml` 执行固定 Child `_extract_chunk_length_from_config` 原函数后确认 `action_chunk_size=32`，与 G1 canonical `h_pred=16` / Queue `H_pred=16` 的推理合同不一致。当前 Queue 启动 Server 未显式传 `--action-chunk-size`；若真实 Server加载成功，则 `/info.action_chunk_size=32`，Queue 的 `validate_server_info` 会 fail-closed，无法开始四任务仿真。
- **本轮不进行 GPU 状态检查**（Owner 决定适时停训练腾出空间）。不启动 GPU、Action Server、Simulator；当前不存在本 Gate 的执行授权。`optim/` 不属于 model-only inference 条件。

## Independent source cross-check 与 Finding

### HIGH-07 — frozen G1 h_pred16 被过期 dataset chunk_length32 覆盖，Server 实际构建33帧推理输入

- **Source**：DS 现场报告的 Config 文件 `/mnt/data1/data_v2_0617/psm_wma_v3_packed128_runs_fresh_g1_20261019/psm_wma_v3/corrected_phase5/packed128_droid_fresh_g1_20261019/config.yaml`，sha256 `f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e`，与 G1 job identity 对应。唯一实际命中：`dataloader_train.dataloader.datasets.robocasa.dataset.chunk_length = 32`（据 DS 源函数现场运行/只读证据，非 GPT 直接读取本地文件）。
- **Root file:line**：`scripts/eval_robocasa_18task_queue.py:267-285,351-374`（固定 `protocol.H_pred=16`，启动指令没有 `--action-chunk-size 16`）、`:83-113`（Server `/info.action_chunk_size` 强制校验为16）。
- **Child file:line**：`cosmos_framework/scripts/action_policy_server_robocasa.py:495-501` 公开 `ActionServerArgs.action_chunk_size`；`:200-231` 从 `dataloader_train` 递归提取 `chunk_length/num_action_per_chunk`；`:639-659` 解析优先级 **CLI explicit > config value > fallback32**；`:976-1027` 真正依赖 `self.cfg.action_chunk_size` 构造 `video_length=chunk+1`、`action_length=chunk+(state present)`、`sequence_plan` 与 Action tensor；`:890-913` 暴露 `/info.action_chunk_size`。
- **Root cause**：G1 当前数据路径与模型契约为 `h_pred=16`（17帧包含 State），但冻结训练 Config 保留旧 datasets 节点 `chunk_length=32`；Server 当前未获得独立于训练旧节点的显式预测长度，错误选用32。这不仅是数字标签不一致，模型请求将按33帧构建。
- **Violated contract**：iter4000 required Local-TTT / raw15 / state15 / 16-step prediction +17 frames / Camera left_wrist / fps20；绝不能默默按32推理，也不能放宽 `/info` 校验。

## Codex 修复范围与验收条件

- **首选最小修复**：只改 root `scripts/eval_robocasa_18task_queue.py` 的 Server 子进程 CLI，使每个 Worker **显式提供 `--action-chunk-size 16`**（Child 源码已提供此公开参数，解析优先级明确），并在 Evaluation Identity protocol 中明确记录实际 `server_action_chunk_size=16` 或同等可审计字段。必须保留已有 `H_pred=16` / `R=action_horizon`（二者不同语义）。
- **不得**为这轮修复修改 frozen G1 `config.yaml`、模型权重、Checkpoint、Child 全局默认解析规则、`optim/`、Local-TTT、训练/Trainer/DCP 或已关闭 HIGH-02/MEDIUM-05/HIGH-06 的严格身份/错误路径与锁机制。不得让 DS 临时手工追加未审核参数绕过 Gate。
- **CPU Evidence** 要直接覆盖实际 root queue 启动命令携带该参数（所有 1/2/4 Worker）、Child 在给定 config `chunk_length=32` 时因显式 CLI=16 得到 effective16、若缺 flag 按真实代码落到32（负例），以及 `/info.action_chunk_size=32` 必须被拒绝。1/2/4 Worker 的 4 Task ×5 合成 Episode、错误 checkpoint/config/mode/foreign listener/worker error 原有回归仍 PASS。可通过 pinned Child 源码/AST/轻量 mock 证明优先级；不必加载大型模型。
- 根脚本与聚焦测试之外的生产修改禁止；如需越权，STOP 重新提案。交付新 Root implementation SHA + 原 Child/Gitlink、差异、测试原始日志和 Gate Evidence；提交后暂停，等待 GPT 对**新 Pair** 增量验收。
- 已观察到 G1 job identity 报告 `h_pred=16`；本 Gate 以该已冻结协议和 DS 实测 Config 为边界，不授权重新定义模型训练 Horizon。

## DS_PRO 下一步与执行 Gate 边界

- 现有 HIGH-06 新 Pair 5 项独立 CPU **报告 PASS**，无需重复旧 test；本地新证据因设备未接入 GPT，仅根据 DS 文本纳入 Evidence，不宣称 GPT 读到了原始服务器日志。
- 待 Codex 新 Pair 形成并通过 GPT 技术审核后，DS 仅执行新预测长度修复的定向 CPU 独立复验和读取真实 Config 验证；无需 `nvidia-smi` 或当前 GPU 检查，不检查 optimizer，不能启动真实 server/simulator。
- 未来 Owner 自行决定何时停止训练并释放 GPU，再由后续明确的独立执行 Gate 授权启动真实模型加载、`/info` 检查、最终 4 Task ×5 Episodes 的 rollout；先 canary 后正式评测。

**此 `REQUEST_CHANGES` 只对本次新增真实推理长度协议 Gate 生效，不推翻已关闭 HIGH-06 的历史 CPU/static `APPROVE`。**
