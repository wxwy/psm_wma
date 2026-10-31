# Codex 实施单：No-TTT 标准训练默认终端只显示 Progress，完整原始日志保留

2026-10-31，Owner明确要求：**不是每次外部手动过滤，也不是可选开关；代码改动后 No-TTT 默认就只在训练工作终端显示 Rank0 `[CorrectedV3][progress]`，但全部训练/Loader/其他Rank/异常和Checkpoint详细日志必须完整可追溯地落到文件。**

**角色：只有 Codex 可更改 Git 仓库生产脚本与源码；GPT仅审核；DS仅编辑仓库外临时启动脚本或执行Owner授权的验证。此请求不代表已有改码。**

## 现有代码事实

- `cosmos-framework/examples/psm_wma_robocasa_corrected_telemetry.py:583-585`：rank0 的 Observer 每次optimizer commit已经同时生成 `[CorrectedV3][progress]` 与 `[CorrectedV3][train]`。无需修改进度内容，也不要对训练计算/监控实现重构。
- `cosmos-framework/examples/psm_wma_robocasa_formal_monitor.py:72-126`：`TelemetryJournal` 将 `[CorrectedV3][train]` 持久化到 `monitor/train_rank0.jsonl`、observer内容到 `monitor/rank0.log`，且训练JSON原本就不回显console。不要删除JSONL或更改保存时机。
- `cosmos-framework/cosmos_framework/trainer/matched_no_ttt.py:349-355`：NoTTT Loader 通过标准print记录 `[NoTTT][cpu_loader]`，绕过Journal；Cosmos/torchrun/其他rank/Warning/Traceback也可能直写stdout/stderr。**仅抑制Journal的print无法使全终端progress-only**。
- 现有标准Root入口 `scripts/train_v3_matched_no_ttt_4gpu.sh` 及 `scripts/train_v3_matched_no_ttt.sh` 以 `exec ... python -m torch.distributed.run` 运行训练。建议Codex仅在这些 **No-TTT启动脚本的最外层**改默认console/full-log输出分流，并保证直达训练的命令/模型/DataLoader/资源参数一字不变。不要修改 Local-TTT/EvalV2。

## 默认行为的精确验收

1. **正常训练界面**：从训练开始后，只输出已有 `[CorrectedV3][progress]` 行（Rank0；每个committed step一次），不刷 `[CorrectedV3][train]`、`[NoTTT][cpu_loader]`、重复Rank日志、PyTorch Warning或大量JSON。训练启动前可显示一次`full log`路径；若失败，必须显示错误概述与详细日志位置、必要的末尾错误上下文。
2. **完整日志绝不丢**：将原始 torchrun进程树的 **stdout+stderr 全部先落盘**（含初始化、模型日志、Loader/所有Rank、Traceback/Warning、Checkpoint等），之后只对送往终端的副本按progress前缀过滤；保留现有 `monitor/train_rank0.jsonl` 与 `monitor/rank0.log`。不得在进日志前grep，也不得用静默print抑制代替持久化。
3. **默认开启，无需用户每次设置环境变量或加管道**：不要求 `PROGRESS_ONLY=1`；若选择增加显式debug选项可读全量console，默认仍必须progress-only，且不应增加无关配置。
4. **日志安全和Resume**：单次运行的全量日志使用不同且不可覆盖的输出文件，建议在 `OUTPUT_ROOT` 下一个独立于 Trainer/Checkpoint Job Namespace 的 `_launch_logs/$JOB_NAME/`，避免Fresh训练预先创建其正式Job目录而触发claim冲突。不要覆盖历史launch.log、config、DCP/Checkpoint或其他Rank文件。启动失败也要保留原始log。
5. **退出码和中断**：shell管道的 `tee`/`awk` 不能吞掉真正的torchrun非零退出码（立即正确保存 `PIPESTATUS`）；正常代码0返回0，训练失败必非0并在console显示失败摘要，`Ctrl+C`/SIGTERM时仅清理本次owned进程，不能留下rank/Worker孤儿，且不能kill其它正式训练。`tee`或日志无法持久化时必须fail closed，不能继续无Evidence的训练。
6. **源与实验隔离**：新实现仅在隔离Codex候选开发，不修改现役正式30k工作树，不影响已经批准的 C12200 `nw0`/`nw8` 独占matched A/B这轮Frozen source/命令，避免把日志改动混入性能基线。日后如要合并到Canonical V3（当前带独立EvalV2 Child），仅由Codex做对应Root的最小移植与独立新Formal Pair，不整树覆盖V3 Child。

## 推荐最小实现（不是强制重构方案）

Root launcher维持现有torchrun命令、参数和环境。只将其stdout/stderr引导至外层安全分流：全部 `tee` 到每次唯一full log，再由line-buffered `awk` 或同等工具仅回显 `^[CorrectedV3][progress]`；保证Python输出不因重定向无限缓存（如设置`PYTHONUNBUFFERED=1`），保留完整退出码/中断/错误尾日志。不要依赖应用里遍地改print，也无需新增持久log collector后台服务。

## 最小验收（synthetic shell only，不占GPU）

- 假训练同时输出初始化行、Rank1 warning、Loader JSON、Rank0 progress、Train JSON、stderr Traceback；终端仅进度，full log逐行全保留，保存路径为非正式Job命名空间。
- 假训练exit=7后，launcher exit非0并显示错误摘要/日志路径；`tee`写入失败、只有warning无progress、SIGINT/TERM、重复Resume多次启动不覆盖旧log。
- `bash -n`、shell静态检查及上述脚本级最小合成测试通过。**不重跑旧NoTTT CPU58/301、不跑真实GPU或DCP，不修改模型/Optimizer/Frontier/Loader/120s Timeout。** Codex提交新独立Root implementation SHA（若Child未修改，保留正式对应Child SHA），精确Diff及简单raw测试证据给GPT增量Code Gate。

## 先前建议覆盖规则

本单明确**取代** `docs/collab/chatgpt/requests/2026-10-31_V3_NoTTT_Console_ProgressOnly_FullLogs_Preserved_Minimal_Handoff.md` 中“只有DS外部可选包装、仓库标准入口暂不修改”的先前默认做法；现在Owner要求**Git仓标准 NoTTT 入口直接代码实现并默认启用**。旧C12200独占 A/B冻结不受此新需求影响。