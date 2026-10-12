# DS_PRO — V3 Dense 默认 OFF + Console 精简 CPU验收（Owner转交证据）

**Date:** 2026-10-12
**证据类型:** Owner完整转交 DS_PRO 验收报告；GPT本次不能直接读取训练机隔离目录中的原始pytest/ruff文件或现场DCP，测试数值来源为DS本轮陈述。
**Formal new implementation Root:** `b159f45906f7261d028aecc226ab7f2bb9807eb9`, **Child/Gitlink:** `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
**Original running Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`, **Child:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**隔离目录:** `/tmp/ds_pro_v3_dense_cpu_acceptance_20261012/{root,child}`; 训练既有venv Python3.13.11, torch2.10.0+cu128, pytest9.0.2; `PYTHONPATH`指向隔离Child实际源码路径。

## 1. DS_PRO CPU Evidence

### Gate A（报告PASS）
- 环境变量 `PSM_V3_COMPACT_CACHED_VIDEO` / `PSM_V3_SHARED_EPISODE_CACHE`均unset→Compact=False, Shared安装=None。
- Dense视频全零、连续、`uint8`、`(3,17,256,512)`且实占`3*17*256*512`字节。
- 显式1/1→Compact单字节shape proxy + SharedRoboCasaEpisodeReader，SourceReader也指向同缓存。显式0/0→同默认，非法值→ValueError。
- 无任何绑定特定Job名称或Resume阶段的运行时特判。

### Gate B（报告PASS）
- 控制台保留`[CorrectedV3][progress]`、`[CorrectedV3][checkpoint]`、`[CorrectedV3][logging_error]`与其它告警；不再回显`[CorrectedV3][train]`整字典。
- `monitor/train_rank0.jsonl`仍完整append机器可读记录；`monitor/rank0.log`仍包含原始完整记录；`read_train_records`仍识别历史记录和幂等回放。
- Console回调失败被隔离，JSONL和Raw优先写入；不改变任何Optimizer已成功提交的状态。

### pytest / 静态检查的真实时间线

- `examples/psm_wma_robocasa_formal_monitor_test.py`: **10 passed / 3.54s**。
- `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py`首次未设置`HF_HUB_OFFLINE`：**11 passed, 1 teardown ERROR /12.63s**。失败栈定位 `conftest.py::detect_env_modifications`，检测到新增 `HF_HUB_OFFLINE`。其设置发生于项目已有`cosmos_framework/data/generator/action/datasets/cosmos3_action_lerobot.py::_ensure_hf_hub_offline`，`conftest.py`未将其列入环境允许集合。第一次错误必须保留，不得伪写第一次全绿。
- 以正式训练环境等价 `HF_HUB_OFFLINE=1`预置后，**11 passed / 15.59s**，没有teardown error。对应真实项目正式 Phase5 preflight也设置此离线环境。
- 5个变更文件 `py_compile` **PASS**（exit0），`ruff check` **All checks passed**（exit0）。

### Git差异/隔离声明（由DS报告 + GPT代码对比核实）

- Child从`e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`到`937066ffd90f2bf783ad4fbb4909e9c0b8922982`精确五文件：默认开关各1行、TelemetryJournal echo过滤、两处CPU测试；Root `b159f45906f7261d028aecc226ab7f2bb9807eb9`仅更新`cosmos-framework`gitlink。未改`config_digest`、优化器、TTT、Scheduler、Checkpoint、jsonl schema。
- 隔离测试没有触碰训练工作树、原DCP、GPU、torchrun或生产Resume；DS观察原Root HEAD`444c232b976e80ac68cde9e7370e73b9f6410f0e`/Child`e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`、Child clean。

## 2. 非本CPU验收动作引起但必须记录的Formal30k进程观测

- DS报告在其检查时训练已经停止：tmux `robo15train`中看到`torch.distributed.elastic...SignalException: Process 385913 got signal: 2`（SIGINT），最后一条`[progress]`为**iter839（2026-10-12 11:57）**。
- 该Formal恢复启动过程中曾由DS独立报告实际在Compact/Shared ON/ON模式下执行，因此**不能把这段801–839结果直接标记为原合同Dense OFF/OFF训练**。
- DS报告验收窗口`>=12:15`原Formal Job目录无新增/变更文件，原进程已经不在运行；但GPT没有原机现时`latest_checkpoint.txt`指针及各DCP文件Hash。**从iter839不等于能恢复839；具体有效恢复点必须以实际上一次完整DCP和作业身份为准**。
- 本CPU验收 PASS 不会热更新旧进程，不授权自动重启、不批准对原DCP/历史日志覆盖/回写。

## 3. 审核结论位置

Formal `APPROVE` CPU-only Gate closure见 `docs/collab/chatgpt/reviews/2026-10-12_V3_dense_defaults_quiet_console_CPU_acceptance_closure_b159f459_937066ff.md`，不包含线上GPU训练合法性、模型等价、D1判定或新Formal Pair部署授权。