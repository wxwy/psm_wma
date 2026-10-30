# PSM-WMA V3 EvalV2 Phase B 真实 Canary：NoTTT Checkpoint 与 required Local-TTT 协议不匹配

- 日期：2026-10-30（CST）；ChatGPT 独立新增运行 Evidence 审核与技术路线裁决。
- **Formal Root**：`7c74dc26ac4837f193727ecf847b9b64554c18b2`。
- **Formal Child/Gitlink**：`53c3c95202e14d3b72d236eee6899a80acf82989`；已核 root GitTree。
- 前序 F5-P1 Code Gate `APPROVE_CODE` 维持；**formal pair 未变化，禁止重复代码技术审核**。此次只增量核对 DS_PRO 在相同 Pair 上的新真实 Canary Evidence。
- **Evidence Gate：`REQUEST_CHANGES`（输入模型选择不兼容；不是新发现的生产代码 blocker）**。状态 `BLOCKED_INPUT_INCOMPATIBLE`；不批准这次真实 Canary 的 B=2/4 Episode 成果，也不要求生产源码整改。
- 原始日志 `/tmp/ds_pro_canary_f5p1_20261030/evidence/fresh.log`、`out/logs/GPU7_server.log` 在 DS 服务器；GPT 未获得原始文件字节。Checkpoint 资产 `iter_000010400` 的 metadata/配置与 TTT A1/A2 均由 DS 现场报告，**不当作已独立查验的物理资产**。

## 1. 独立确认的代码和合同

1. Root `scripts/eval_robocasa_18task_queue.py:257-284` 的 `server_argv` 显式设置 `--local-memory-mode required`；Root `scripts/robocasa_eval_v2/runtime.py:143-198` 的 Phase B 复用它并附加 batch transaction options。
2. Child `cosmos_framework/scripts/action_policy_server_robocasa.py:623-663` 的 `_transaction_options` 在 `off` 模式下**必然拒绝** Batch/Session profile；`:894-930` 又明确要求 raw15、use_state、`k_local=4`、`local_dim=32`，然后才构造 `BatchedSessionTransactions`。
3. Child `cosmos_framework/inference/robocasa_local_memory_policy.py:74-97` 若 `required` 下无 `net.local_memory_runtime`，必须抛 `ValueError`；并核对 raw15 evidence、model-owned scan、Wan tokenizer encoder、FSDP 注册（适用时）。
4. Child `cosmos_framework/inference/robocasa_session_transactions.py:150-167` 在构造器内直接要求 `adapter.mode=="required"` 且 `adapter.memory is not None`；并非只在 CLI 强行卡住，而是事务生命周期依赖真实 Local state。
5. Child `cosmos_framework/evaluation/robocasa_v2/contract.py:72-92` 的 manifest protocol 字面固定 `local_memory:"required"`。故自动探测 NoTTT 然后无审核地退化为 `off` 会改变冻结的 scientific identity 和 Session correctness，不属于 F5-P1 的最小修复。

**独立技术判断**：在当前 Phase B Local-TTT 事务 Canary 的冻结范围内，DS 用 NoTTT checkpoint 是测试输入不兼容，不能将已有严格拒绝行为定性为新的生产 Bug。F5-P1 oversized JSON 修复是否生效的现场 5,085B 小 `run_inputs` 属 DS报告并与已审核实现路径一致；不需要重审原F5代码。

## 2. 新 DS 现场报告与限度

- DS称在 clean exact Pair/GPU7 上 dry-run 4 slots、2 Sim/B2 成功；Fresh 写下5,085字节 `run_inputs` 和独立 probe；Action Server 退出1，报 `required Local-TTT checkpoint has no net.local_memory_runtime`。
- DS称 checkpoint `no_ttt_packed128_droid_fresh_30k_world4_ga4/iter_000010400` config `local_memory_enabled:false`、metadata 不包含 Local runtime。上述错误因果链与正式源码逐字吻合。
- `success=0, invalid=2, pending=2` => **0 valid**，而非“4 个均 invalid”；`native_batches.diagnostic_error=ConnectionError` 是 Server 停止后继发的不可用证据，**没有 B=2 实际命中证据**。
- F5 原 Code Gate 仍 `APPROVE_CODE`；当前真实 Canary `BLOCKED_INPUT_INCOMPATIBLE`，不当作数值/算法失败和性能失败。

## 3. 路线裁决与最小下一步

**推荐 A：若本次目标是已冻结 Local-TTT Phase B 的双Sim/真实Batch事务验证，直接选正确 TTT checkpoint，**不修改评测代码；原NoTTT checkpoint留待今后单独的匹配基线评测工程，不应塞入本次 Gate。

**只读先验匹配，避免再次浪费GPU/污染输出目录**：

- A1 `corrected_phase5/formal_verified_index_30k/iter_000001300`：config.yaml 存在且DS称 `local_memory_enabled=true`，但需直接检查完整 DCP `model/.metadata` 确实包含模型所有必要 Local runtime 键、与真实可加载设置和训练同源；尤其 `K_local=4/local_dim=32`、raw15/state15、H16、`use_state=true`、Model scan/Wan encoder。仅有配置 flag 不足以 PASS。
- A2 `packed128_droid_fresh_g1_20261019/iter_000020000`：DS称 metadata 有167个 Local 相关键，但缺 config.yaml。**不得拿 A1 的配置文件直接充当 A2 同源配置**；先只读发现同 Job 的真实训练 recipe/已保存 config/严格权重与模型结构匹配证据，否则保持 `BLOCKED_CONFIG_PROVENANCE`。
- 优先选择能**完整证明同一训练 Job 的 checkpoint+config 而且满足冻结的 `raw15/state15/H16/K4/local32`** 的候选；若均无，停止，不通过禁用 required 继续。
- 变更 checkpoint 会改变 `model_digest` / Frozen manifest；**旧失败的 fresh namespace不能 Resume/复用**，只能创建新输出。DS在继续执行前须获取Owner对测试模型变更的确认（原用户授权了4Episode测试，但没有冻结TTT checkpoint），并记录实际 Model+Config路径/身份。
- 通过只读兼容检查及Owner模型授权后，仍只运行**原定一次** GPU4–7 中一张卡，2Sim/B2，CloseFridge/OpenCabinet各2、共4 Episode，输出 Batch histogram、session / fast-state/reset与episode Core、MP4、RSS/VRAM/latency、foreign job survival、owned cleanup 等真实证据。不得扩展到900。
- 若项目独立目标是 NoTTT 基线，则未来须另开 NoTTT Batch/Session 设计和代码 Gate：至少需重新定义事务 session 无 Local state 的 lifecycle、manifest身份、adapter/transaction支撑及匹配对照；**不是只把 `required` 改为 `off`**，更不能将两种协议的结果混为一份正式实验。

## 4. Gate 范围

- 旧 `F5-P1 Production Code`：**CLOSED / APPROVE_CODE**，formal pair unchanged。
- 新真实 Canary `Evidence`：**REQUEST_CHANGES（checkpoint/config mismatch, evidence-only）**，未进行有效推理。
- 没有新生产代码整改授权、未合并候选新代码、未启动真实GPU、未验证用户机器上的 A1/A2 真实完整DCP。
