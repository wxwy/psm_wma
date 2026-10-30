# EvalV2：取消 GPU 独占拒绝 — Quick CPU PASS / Owner 授权提升

- 日期：2026-10-30（Asia/Shanghai）。
- Owner 指令：分享会话末尾“你自己快速 CPU 回归和 Ruff 检查 合并”；本轮进一步明确“代码修改可以让codex做，直接去掉独占显卡的BLOCKED_RESOURCE”。
- 被验证的正式源码 Root：`19342b35011a8ce0f4f81d59779d5da86f9bc9f4`。
- Child / Gitlink：`0ae313e329d290fc6b8a50fda1112820fb7ac485`，本次不变。
- V3 提升前基线：`e5fde3f7279aaf171d32c4d3a78b038da0ac4d4f`。
- 结论：**APPROVE_CODE_AND_QUICK_CPU / 允许按 Owner 指令快进合并 V3**。
- 本记录所在提交仅加入验证证据、SESSION/TODO；生产源码与被测试的 `19342b35011a8ce0f4f81d59779d5da86f9bc9f4` 一致。V3 ref 更新使用精确 expected head，非 force。

## 1. 最小改动

相对上述 V3 基线，仅两项代码/测试变更：

1. `scripts/robocasa_eval_v2/resources.py`：删除 `--query-compute-apps=gpu_uuid,pid` 查询，以及外来 PID 触发的 `BLOCKED_RESOURCE: selected GPU has a foreign process`。默认直接允许共享，不增加配置开关或 PID 白名单。
2. `tools/v3/eval_v2_production_tests/entry_test.py`：更新旧独占断言，新增共享 GPU、显存预算和缺失 GPU 回归。

候选包含 `904083b20129c61afed7c1fad34fcde70712fa2c`（行为及测试）与 `19342b35011a8ce0f4f81d59779d5da86f9bc9f4`（测试空行格式）两个提交，基线相对 ahead=2、behind=0。独立窄范围源码复核未发现 blocker，无需重新设计 Batch 架构。

## 2. 保留的行为

- `nvidia-smi` GPU 查询仍为 `check=True, timeout=10`；失败不放行。
- 选中 GPU 必须存在。
- 所有进程的全卡 `memory.used` 仍进入显存预算；默认 `max_gpu_fraction=0.85`，模型启动前仍保留 20 GiB。
- 本次 owned 进程的 RSS 预算保留。
- 进程身份验证、PID 复用检查、只清理本 run 注册 PGID 的逻辑均未改动。没有清理、停止现有训练或外来计算进程的新增路径。
- 统一资源检查在 Phase A/B 原有调用点生效；无需新增参数传播。

## 3. 本轮实际验证

| 项目 | 结果 |
| --- | --- |
| entry_test：CLI、共享 GPU、显存/缺卡、Resume | 15 passed |
| process_test：owned actor、PID 复用、外来进程存活 | 8 passed |
| Phase B config_test：G/M/B 布局与配置合同 | 17 passed |
| robocasa_processes_test：清理、取消、截止时间 | 23 passed |
| **合计** | **63 passed，0 failure / error / skipped，2.99 s** |
| Ruff 0.12.7 check：两项改动文件 | PASS，exit 0 |
| Ruff 0.12.7 format --check：两项改动文件 | PASS，exit 0 |
| 测试前后 Root / Child 工作树 | clean，源码未改 |
| Git diff --check | PASS |

精确命令、Python/依赖版本、测试环境变量、Git Blob 与 SHA256 见 [status.json](../evidence/2026-10-30_evalv2_shared_gpu_quick_cpu_19342b3/status.json)。原始最终 [JUnit](../evidence/2026-10-30_evalv2_shared_gpu_quick_cpu_19342b3/junit.xml)、[pytest 输出](../evidence/2026-10-30_evalv2_shared_gpu_quick_cpu_19342b3/pytest.log)、[Ruff check](../evidence/2026-10-30_evalv2_shared_gpu_quick_cpu_19342b3/ruff_check.log)、[Ruff format](../evidence/2026-10-30_evalv2_shared_gpu_quick_cpu_19342b3/ruff_format.log) 随本记录保存。

### 环境处理与口径

初次执行因隔离环境缺 requests / torch 版本信息，在 8 passed 后失败；仅安装正常 requests 与官方 CPU torch 依赖。第二次在 15 passed 后触及普通沙箱的 PID / procfs 不一致：stdlib 探针证明 Python getpid=5 而 /proc/self/stat 为1241，子进程活着但数字 PID 路径属于不同视图。原始失败日志保存在外部证据目录的 attempt1_env_missing、attempt2_process_probe。

随后使用受支持的执行权限；执行前探针验证 Python PID、/proc/self/stat、/proc/<pid>/stat 三者均为1251。**未改任何源码、断言或测试选择**，原样重跑以上四组，最终63项全绿。不得把前两次环境失败称为第一次运行即通过，也不把普通沙箱的失败归因于此次共享 GPU 改动。

## 4. 验证范围

这是 Owner 要求的快速 CPU / Ruff 增量回归；不重复旧435项完整 Gate，不将旧结果叠加为本轮用例数。未运行真实 GPU、Cosmos 模型、RoboCasa 环境、DCP 或训练。真实1 GPU / 2 Sim / B≤2 Canary尚无本轮运行结果。

共享 GPU 已有进程不再构成独占阻断；显存预算仍按实时资源检查。其他 No-TTT DCP / 吞吐实验的独立资源条件不因此改变。
