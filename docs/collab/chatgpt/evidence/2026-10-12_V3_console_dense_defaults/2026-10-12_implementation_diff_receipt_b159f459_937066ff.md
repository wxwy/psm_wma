# V3 — Dense 默认关闭优化 + 控制台只回显紧凑进度：代码提交证据

**日期:** 2026-10-12
**发起:** Owner `你直接改吧`，此前已确认无需 Job 名称硬编码校验。
**旧已审核 Formal 实现 Pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`, Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**本次新 Implementation Target:** Root `b159f45906f7261d028aecc226ab7f2bb9807eb9`, Child/Gitlink `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
**远端新 Child Commit:** https://github.com/wxwy/cosmos-framework/commit/937066ffd90f2bf783ad4fbb4909e9c0b8922982
**远端新 Root Gitlink Commit:** https://github.com/wxwy/psm_wma/commit/b159f45906f7261d028aecc226ab7f2bb9807eb9
**执行方式:** GPT 经 GitHub 连接器直接修改并提交；未接触 DS 训练服务器当前工作树，未加载 GPU 模型、数据集或正式 DCP。

## GitHub 远端差异已独立回读

旧 Child→新 Child **仅5个文件**：
1. `cosmos_framework/data/generator/action/utils/cached_pixel_geometry.py`: `os.environ.get("PSM_V3_COMPACT_CACHED_VIDEO", "1")` → `..."0"`，仅1行。
2. `cosmos_framework/data/generator/action/datasets/robocasa_shared_episode_reader.py`: `os.environ.get("PSM_V3_SHARED_EPISODE_CACHE", "1")` → `..."0"`，仅1行。
3. `examples/psm_wma_robocasa_formal_monitor.py`: 原来 `TelemetryJournal.__call__` 无条件 `self._console(line)`；现在训练完整JSON仍原样先写 `monitor/train_rank0.jsonl` 并保留 `monitor/rank0.log`，但仅 `not line.startswith(TRAIN_PREFIX)` 才回显console；progress/checkpoint/logging_error/其他异常不受过滤。
4. `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py`: 新增两项 CPU回归测试，确认两个env均缺省时Dense非共享、显式1/1仍开启原Compact/Shared路径，Dense视频完整连续零张量，Compact占位为stride0单字节。
5. `examples/psm_wma_robocasa_formal_monitor_test.py`: 更新既有journal stdout计数，检查原train JSON仍append持久化、终端仅progress/checkpoint，并新增warning/logging_error console透传测试。

**根仓 Root Code Commit `b159f45906f7261d028aecc226ab7f2bb9807eb9` 只改 `cosmos-framework` Gitlink**；没有Root训练代码变更。只改默认值和日志路由，不改 `config_digest()`、TTT/Action、Optimizer、Checkpoint、数据shape、正式 `args`、scheduler等。

## 实证范围

- **远端提交和 diff、全部修改文件回读完成。**
- **尚未在与固定 Child 相同的完整 Cosmos 运行环境执行 pytest**（GPT当前环境没有整套项目 + 依赖 `pyarrow`），新tests属于提交的可执行验收，不等于已跑PASS。未来需要DS在**独立**测试工作树进行CPU-only定点验证；不在运行中的Formal30k锁定工作树切换代码。
- 当前正在运行的 `formal_verified_index_30k` 进程与旧 `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` 代码/环境不因远端提交而自动改变；新默认值不追溯已产生的ON/ON运行记录。若原任务以错误模式运行，仍按之前Owner运行决策与实际 DCP来源隔离处理，不因修改默认值自动修复原Checkpoint。
- 此次**没有**加入 `if args.job_name == "formal_verified_index_30k"` 这样的任务条件，也没有强制阻断显式 ON/ON。两个优化功能仍可通过env=1/1正常开启。

**后续CPU验证请求:** `docs/collab/chatgpt/requests/2026-10-12_V3_console_dense_defaults_scoped_CPU_validation_to_DS.md`；**增量审核:** `docs/collab/chatgpt/reviews/2026-10-12_V3_console_only_progress_dense_defaults_implementation_review_b159f459_937066ff.md`。
