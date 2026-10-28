# PSM-WMA V3 — Owner Override：No-TTT Checkpoint 频率与存储职责

- 日期：2026-10-28。
- **最新 Owner 明确指令**：磁盘容量、Checkpoint 保留方案和自动清理由 Owner 本地监控程序负责；GPT/DS_PRO 不再审核、安排、修改或接管这些策略，也**不得继续将磁盘使用率、剩余容量、Cleaner 权限/清理计划或Checkpoint数量预测当作 S2 的独立验收阻塞项**。
- **Checkpoint 保存频率保持 `save_iter=100`**，为减少意外中断后的训练进度损失；不得未经 Owner 另行批准将其改成 1000 或更高。正式 `max_iter=30000, warmup=500` 及 model/data/GA/FSDP 配置不因此变动。
- 生效于新独立 Compact No-TTT Job `no_ttt_compact1_corerun_20261028_world4_ga4` 与旧正式 No-TTT 的未来审阅，不是对任何既有文件的删除授权。**GPT/DS 不操作 Cleaner、不修改保留策略、不删除/移动/覆盖Checkpoint；Owner 的本地监控按其自身既有授权运行。**
- 历史报告中的磁盘使用量、DCP大小、保留数学推算仍是历史证据，但其**“R1 HIGH / S2 DISK BLOCKED” 结论已被 Owner 明确撤销**；不得再要求 Owner 提交Cleaner脚本、容量计划、定期保留点列表或磁盘清理授权作为继续实验的前置条件。
- **区分存储治理与训练正确性**：DCP `complete.v1.json`、4 Rank sidecar、`latest_checkpoint.txt`、Checkpoint可恢复性、训练语义/config digest、Optimizer/Loss/Grad/NaN检查仍是技术验证范围。Owner仅接管“保留与清理”决策，不表示允许使用损坏Checkpoint或发生磁盘写入错误时继续执行。
- **不能把本 Owner 变更当作 S2 自启动授权**：此前新 Job `fresh 1` 的报告证据支持一次 Optimizer Commit；原始S0/S1 JSON/MD 和真正的DCP Manifest若仍未提交，可按既有 Evidence-only 条件补齐而不重跑训练。真实 Compact0/1 Native GPU Forward/Loss/Gradient Parity 依然未完成；进入 `resume 10/100/30000` 的其它模型/数值/共存技术 Gate 及相应启动授权仍须单独决策。
- **状态更新**：`R1_STORAGE_POLICY=OWNER_MANAGED_NOT_A_GPT_GATE`，`SAVE_ITER=100_FROZEN`，`S1_RUNTIME_REPORTED_PASS`，`S1_EVIDENCE_PROVENANCE_PENDING`，`GPU_NUMERIC_PARITY_NOT_RUN`，`S2_NOT_YET_AUTHORIZED_FOR_NON_STORAGE_REASONS`。
- 正式 No-TTT Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`，本次仅更新决策与文档，不更改任何生产代码或运行中的训练。
