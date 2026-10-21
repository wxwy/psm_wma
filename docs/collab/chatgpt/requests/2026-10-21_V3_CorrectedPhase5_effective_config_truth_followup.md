# V3 Corrected Phase5 — 配置快照与真实数据链路一致性整改（HIGH-07 之后独立推进）

日期：2026-10-21
性质：设计/Scoped Codex follow-up；**不是当前 G1 / iter4000 的生产运行 Gate**，也不构成当前训练代码或冻结资产修改授权。

## 事实与根因

- 冻结 G1 新 Pair Root `950b2dbc6ad112205153a18dc0f733812db30706` / Child `2d128ed5a07601cdd424974f99b67832eafeeb41`。
- 真实 G1 `config.yaml`（DS_PRO 独立现场报告）的 `dataloader_train.dataloader.datasets.robocasa.dataset.chunk_length=32`；当前 Child `_extract_chunk_length_from_config()` 递归扫描它，因此没有显式 CLI override 时 Server 预测 chunk=32。
- 当前 G1 训练代码 `examples/psm_wma_robocasa_corrected_phase5.py`：`_load_config()` 从旧 TOML/experiment recipe 得到原始 Config；`overlay_config()` 替换 trainer/optimizer/local 及 tokenizer，但没有同步旧 `dataloader_train...dataset.chunk_length`。训练实际调用 `get_action_robocasa_exact_window_cached_sft_dataset()`、`ExactWindowSegmentProducer` 和 `GroupedLocalMemoryTrainer.bind_grouped_stream()`，不以原旧 Dataset 节点提供正式样本。
- 真实训练窗口来自 `CorrectedRoboCasaPolicyContract`，其 `action_horizon=chunk_length=16`、`observation_frames=17`，且校验 cache.stats.chunk_length=16。`v3_job_identity.json.contract.h_pred=16`。保存的 `config.yaml` 含旧32，并非正式训练数据流使用32的证据。
- `JobLifecycle.write_config()` 序列化 `config.yaml/config.pkl` 并把 SHA 写入不可变 `v3_job_identity.json`。**不能原位编辑正在进行的 G1 及其已发布 Config/Checkpoint/Job identity**。

## 裁决与两个相互独立的处理方向

### A. 当前 iter4000 评测：保持 HIGH-07 的最小修复

- 在 root Queue 显式传 `--action-chunk-size 16`，保留 `/info.action_chunk_size == 16`、H_pred/R 及其它冻结协议检查；由 HIGH-07 独立 Gate 验收。
- 不为解决历史快照歧义而阻断当前评测，不在本任务中修改旧 `config.yaml`、Child 解析优先级或旧 G1 Snapshot。

### B. 后续 **新** Corrected Phase5 训练任务：修复配置真实性（独立 Gate）

Codex 在**隔离分支**提出最小变更方案，并执行 scoped CPU 实现与测试。目标：

1. 新 job 的**最终 effective** `config.yaml/config.pkl` 必须能被使用者正确理解：`dataloader_train...robocasa.dataset.chunk_length` 如保留给通用 Client/Server 使用，应在冻结/保存前与 `CorrectedRoboCasaPolicyContract.chunk_length=16` 同步（并严格 assert 一致）；不允许继续保存看似“当前”却与实际策略长度冲突的32。**仅限 Exact-Window Corrected Phase5 新 job**，不能全局强行重写其它实验合法的32。
2. 单纯把旧 Dataset 节点32改成16**不等于**这个节点就是实际训练 data input。应同时在版本化 `v3_job_identity` / `launch` sidecar / README 中明确 `effective_data_source=get_action_robocasa_exact_window_cached_sft_dataset + ExactWindowSegmentProducer + bind_grouped_stream`、`action_horizon/chunk_length=16`、`observation_frames=17`、`raw_action_dim=state_dim=15`、`fps=20`，并标注遗留 `dataloader_train` 仅为配置/通用推理兼容字段，不是正式 producer。
3. 保存新 job Config 和 Identity 前做一次交叉检查：实际 contract、缓存统计、序列生成形状、Config 反序列化、Child `_extract_chunk_length_from_config` 对保存快照的解析和有效 identity 的预期值均等于16，且能区分 `TTT T=16` 与 `prediction H=16`。
4. 必须有 CPU Red/Green 例：输入继承的 Stage-A recipe `chunk_length=32` → 新 job effective snapshot 解析为16，producer contract仍为16；错误或多个冲突字段 fail-closed，不能通过默默取优先级掩盖；旧 G1 资产/sha 原样不变；不需要真实 GPU。
5. 若调整 `overlay_config()` 会破坏既有 Schema、resume 身份或 trainer 别的依赖，STOP 先报告最小替代设计，不得为求测试 Green 擅改线上代码或 G1 运行工区。

## 工程治理/执行顺序

- 当前 HIGH-07 先完成、先测试并按单独 Gate 判断 GPU canary/四任务 SR；本配置真实性问题是**后续独立 Gate**，不与 HIGH-07 合并，避免扩大其 diff。
- Codex 可在隔离分支准备新 job 的配置真实性实现、CPU 测试、migration/冻结边界说明；**不得直接改写 V3 线上训练路径、G1 已有 `config.yaml`、Checkpoint、`v3_job_identity.json`，也不得对运行中 G1 的 fresh/resume 行为产生未经批准的变化**。不得直接合并到正在被训练服务器使用的分支；提交隔离候选 pair 后先交 GPT/Owner 审核。
- DS_PRO 仅在新 Pair 被明确送验后执行 CPU 验证；Owner 控制旧 G1 训练中止时机和未来代码合并/新 Job 启动时机。
- 旧 G1 用不可变历史解释记录标记：真实 action chunk=16、持久 Config 旧字段=32、iter4000 eval 显式 CLI16；不要伪造改写旧快照以“修复历史”。

状态：**后续整改设计/隔离实现申请；非立即修改已运行生产任务的授权。**
