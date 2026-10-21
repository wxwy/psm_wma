# iter4000 MEDIUM-05：Worker 初始化异常保全 / 作者交接

日期：2026-10-21。新 Pair 待 GPT fresh incremental review；本报告不是独立验收，也不授权 GPU/真实 Server/仿真。

| 项目 | 精确版本 |
| --- | --- |
| Implementation Root | `6405c9dae02e81be5f267e79e27995c3df7fb988` |
| Child / Gitlink，未变 | `2d128ed5a07601cdd424974f99b67832eafeeb41` |
| 父 Root，保留本轮审核/Inbox rollover | `a5d743d1c2221dd4db21dfa61db814da51b286ed` |
| Queue Blob | `e56eaafe8276aa40cb9e2fbc1110515e8fa19c25` |
| 原已审核实现 | `ca936c8eecd593133b1e6c61ba5691331958c592`，Queue `eec2702d5382358e131928db60ce75c93c0c55d5` |

Root 已非强推发布 V3，并保留分支 `v3-iter4000-worker-init-20261021`；后续证据/文档 HEAD 不是 Implementation。原审核 `2026-10-21_V3_iter4000_HIGH02_ca936c8e_incremental_review.md` 和归档Inbox未改写。

## 最小实现

`scripts/eval_robocasa_18task_queue.py` 的原 `worker` 仅改名为 `run_worker`，函数体 AST 完全不变；新增真正的线程入口 `worker`（:518），在调用 `run_worker` 外统一捕获异常。目录创建、日志打开、资源上下文退出等尚未进入原内部处理的异常，现在同样设置stop、记录 `_worker_<id>` 错误和日志路径、在锁外publish。

因此，即使另一Worker已经消费全部四Task×五条结果，主线程原有worker_errors终态判断仍会给出 `INCOMPLETE`、`sr=None`、非零退出，不再只在线程stderr报错然后宣告成功。失败Worker尚未启动Server时，不会尝试清理不存在的Server；健康Worker仍通过原有路径清理自己的Popen。

生产修改仅为原函数改名及新增线程入口，无其它行为重构；新测试只扩展原定向CPU文件。HIGH-02所有顶层helper、原Worker服务循环、命令和身份校验均保留；threading.Lock及publish锁外关系不变。Child、身份模块、DCP、Trainer、Local-TTT和动作ABI没有修改。SESSION/TODO仅追加当前事实。

## 先失败、后通过的直接证据

Evidence：`docs/collab/codex/evidence/2026-10-21_V3_iter4000_MEDIUM05_author_cpu/`。

| 测试 | 原生产代码 | 新生产代码 |
| --- | --- | --- |
| Worker1 `mkdir` 抛OSError，延迟至Worker0完成20条结果 | RC0、COMPLETE、worker_errors空，存在未捕获线程异常；新增断言失败 | RC1、INCOMPLETE、sr=None，worker_errors包含mkdir错误；20条结果仍在 |
| Worker1 `action_server.log` 打开抛OSError，同样延迟 | 同样复现错误成功；新增断言失败 | 同样正确拒绝，包含log_open错误；20条结果仍在 |

两次都是实际Queue main/结果汇总/退出路径，不是helper-only；每次只启动健康Worker的一个HTTP测试Server，无残留自有进程或Worker线程。注入延迟只用于确定性覆盖“结果已经全齐”的危险分支，不是生产等待逻辑。原代码两项失败保留在 `baseline.log`；`regression_witnesses.json`记录两个分支的前后JSON结果。没有改断言、skip或xfail来获得GREEN。

最终联合CPU：**30 passed**（15个定向方法＋15个既有Identity/Screening回归case）、**41 subtests passed**、55无关项deselected，0fail/error/skip，30.775s。JUnit71含subtest bookkeeping，不是71个独立方法。Python3.12.14、pytest9.0.2、Ruff0.12.7；两文件Ruff check、format --check、语法及diff检查均PASS。

`gate.json`含实际命令/cwd/env/RC/source SHA；`pytest.log/xml`为最终原始输出，`scope_proof.json`证明所有HIGH-02顶层helper和原Worker AST未变、锁外publish、身份模块及Child不变；`implementation.patch`为精确最小diff，`manifest.json`绑定新Pair和证据哈希。原HIGH-02回归的12个集成场景仍通过，新增2个初始化分支，共14个合成Queue场景。

边界仍然是CPU stdlib HTTP子进程、临时Git/元数据/合成Episode结果与视频占位文件；未执行真实Cosmos模型、Simulator、GPU、生产DCP或数据读入。原`/proc`权限、真实H16/协议及四个持久元数据目录的现场准备仍是DS范围，不因此变为PASS。未实现或宣称完整E1仿真整体deadline/取消能力；此前闭合训练Gate不重开。

## DS 最小只读复验 / GPT 交接

用新Root/原Child的clean detached验证工作区、现有CPU Python与新外部Evidence目录；不reset/clean/force或覆盖旧证据，不修改源码。设置CUDA_VISIBLE_DEVICES为空、缓存/pycache外置。首先核对精确版本与Queue Blob，然后可只运行新增负例与正常完成回归：

```bash
python tools/v3/eval_robocasa_queue_identity_test.py \
  QueueIntegrationTests.test_worker_mkdir_failure_after_healthy_worker_completes_all_tasks_is_preserved \
  QueueIntegrationTests.test_worker_log_open_failure_after_healthy_worker_completes_all_tasks_is_preserved \
  QueueIntegrationTests.test_four_tasks_five_episodes_complete_on_one_two_or_four_workers -v
ruff check --config cosmos-framework/.ruff.toml \
  scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_identity_test.py
ruff format --check --config cosmos-framework/.ruff.toml \
  scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_identity_test.py
```

保留命令、环境、退出码、原始日志、Witness及运行前后clean状态；两个故障场景必须保留全部20条结果但整体失败、无未捕获线程异常/残留Worker、自有进程完成清理。无需回退旧源码再次复现，作者red日志已经保留。需扩大CPU回归时可用gate.json的最终命令；不重复旧GPU/训练Gate。

HIGH-02逻辑由源码范围证明复用已闭部分，不重新开发。先前DS只读准备文件 `2026-10-21_DS_PRO_V3_iter4000_HIGH02_CPU_readonly_preparation_ca936c8e.md` 的M03/M04、真实路径和未来手动GPU模板边界继续适用，但**本轮所有外部Root版本断言和工作区必须改为本报告的新Root6405c9da，不能拿旧文档中ca936c8e的版本断言冒充新Pair**。不需要/允许DS修改生产文件。真实Server/GPU/Simulator模板仍未获执行授权。

请求GPT仅对MEDIUM-05增量及必要回归做新Pair审核；原HIGH-02主问题已CLOSED、HIGH-01仍RETRACTED。**作者CPU通过不自授验收；完成本交接后停止，GPU/仿真仍等待独立明确授权。**
