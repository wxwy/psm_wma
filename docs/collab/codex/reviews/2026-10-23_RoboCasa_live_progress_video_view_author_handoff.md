# RoboCasa 终端进度与视频浏览导出：作者交付

日期：2026-10-23（Asia/Shanghai）。状态：**REVIEW — 作者聚焦 CPU 检查通过，等待 GPT 独立增量审核与 DS_PRO 验收**。

## 精确版本与范围

| 项目 | SHA |
| --- | --- |
| Implementation Root | `e6a970caba4bdc77f7d9b56a6a8fbcdafe57f1e0` |
| Child / Gitlink | `813a550dab5d6b5b5e3be90d38bb97527956b4dc` |
| 原 Root 文档基线 | `07cd858ee7dd4edabfa1a7b694745c80e4c86bad` |
| 原 Child | `c9f21040f462a114d597fc83773cb9b6a9e96214` |
| Vendor（未改） | `1ac174585293ed998ffc9cf73e47439798cf6f6c` |

Root/Child 隔离分支均为 `v3-robocasa-live-progress-20261023`；先发布 Child，再更新 Root Gitlink，Root 非 force 推送到 V3。后续 Evidence/Inbox 文档提交不是新的 Implementation Root。

Owner 本轮授权默认终端进度和独立视频浏览导出。只修改评测可观测性及对应测试/文档，不实施另行排队的 action snapshot，也不处理先前六项静态审核建议。当前真实评测、G1 训练工作树及其 Config、Checkpoint、Job Identity 未访问、更新或重启；未启动 GPU、模型、真实 Action Server、Kitchen 或仿真。

## 交付行为

### 默认终端汇总

- YAML/CLI 默认 `progress: true`、`progress_interval_s: 5.0`；支持 `--no-progress`、`--progress-interval-s 10`，遵循 CLI > YAML > 默认值。严格拒绝错误 bool、非有限或非正间隔。
- 一条独立 UI 线程集中输出并 flush；Worker 仅提交内存状态。每5秒显示 Worker/GPU、Task、Episode/总集数、执行步数/官方上限、返回预测次数、最近预测耗时及阶段。Episode 边界、任务完成和错误立即报告，结束行显示原始 Episode outcome。
- 阶段包括模型加载、环境初始化、预测/执行、环境/生成视频保存、Local cleanup、进程回收和结果验证。未知字段显示 `?`。不新增 GPU 查询或同步，不以进度静默推断卡死。
- Child 独立可选 `--live-progress-file` 写入 `psm_eval_live_progress_v1` JSONL，绑定 Run/Task/Attempt/Episode。Root 同时增量读取现有动作和预测 JSONL；读取与输出异常不进入任务结果，UI 正常关闭后不留线程，关闭等待最多1秒。
- 最新预测的 live 记录可能先于 mandatory prediction JSONL；按预测序号选择最新耗时，避免显示新次数配旧耗时。
- `--no-progress` 仅关闭终端读取/打印，统一入口仍保留轻量 live metadata 以记录错误 Episode 的真实指令。原 `episode_progress.jsonl` 继续精确2N条、有序 start/end；新流不是完整性或 Resume 输入。
- 显示选项不进入 protocol identity；同一源码 Pair 的 Resume 可调整显示设置。更新 Root/Child 自身仍会改变评测身份，本次不放开跨源码评测 Resume。

主要入口：`scripts/robocasa_eval_progress.py`、`scripts/eval_robocasa_18task_queue.py`、Child `closed_loop_eval.py` / `utils/rollout_progress.py`。

### 独立视频浏览副本

- 所有 Worker 已终止、进程清理与任务结果已经确定后，导出到 `<run>/videos_view/<Task>/<attempt>/`。也可用独立 CPU CLI 处理已保存结果；不加载策略、不认领评测 Namespace、不改变 summary/SR/退出码。
- 原始 MP4、Episode JSON、生成视频清单、动作与预测 JSONL 不改名、不覆盖。副本使用独立 inode，禁止硬链接原视频；写临时副本后以 no-clobber 方式发布。
- 文件名使用 `rolloutXX_success|fail|error|incomplete_<实际指令>[_generated_replanXXXX].mp4`。`fail` 仅指正常行为失败；运行异常为 `error`，无最终结论或明确 KeyboardInterrupt 为 `incomplete`。原始结果不被重分类回写。生成片段继承本集最终标签，**不代表预测准确性已验证**。first 模式也映射为 replan0000，原清单名称不变。
- 指令来自本集实际 `prompt`；失败时可回退到同 Run/Task/Attempt/Episode 的 live 原文。路径特殊字符过滤、空格变下划线、长 UTF-8 名称截断并附短摘要；索引保留完整原文。历史缺失明确写 `unknown_instruction`，不使用 Task 类名猜测。
- `index.json` 保存原文件/源 SHA256、输出路径、Episode outcome 标签、指令来源、Task/Attempt 和 revision；`last_export` 保存告警与统计。相同导出复用，源内容/标签/指令变化追加 revision，不覆盖此前副本；另一 Run 的浏览目录被拒绝。
- Run 内只允许规范 `videos_view`，自定义目录必须在 Run 之外，避免污染尚未开始的 Task 并破坏 Resume。已有浏览树不作为原始视频重新扫描。
- 单片错误/冲突标为 PARTIAL 并留索引告警；整体导出失败为 ERROR。独立 CLI 非零退出提示异常，Queue 保持已经确定的评测返回码。副本需要额外磁盘空间，不自动删除历史内容。

事后导出示例（路径由 Owner 指定，本轮未执行真实结果导出）：

```bash
python scripts/robocasa_eval_video_view.py \
  --run-dir /absolute/path/to/saved_run \
  --view-dir /absolute/path/to/separate_browsing_directory
```

当前正在运行的评测不需要停止或更新源码；可在独立 checkout 和外部浏览目录中事后导出。未完成 Episode 的浏览标签为 incomplete，完成后再导出会保留旧版并追加最终版。

## 作者 CPU Evidence

目录：`docs/collab/codex/evidence/2026-10-23_RoboCasa_live_progress_video_view_author_cpu/`。包含 `gate.json`、原始日志/JUnit、精确 `commands.json` / commands.txt、Root/Child unified=0 diff、源码 SHA256、静态检查及内部只读复核记录。

| 组 | 顶层测试 | subtests | 结果 |
| --- | ---: | ---: | --- |
| Config | 92 | 0 | PASS |
| Terminal observer | 31 | 0 | PASS |
| Video browsing exporter | 44 | 0 | PASS |
| Child 新增进度18项 + 既有六组58项 | 76 | 0 | PASS |
| Queue 新增进度/关闭/Resume/故障隔离 | 5 | 0 | PASS |
| Queue 既有多 Worker/取消/超时/视频/Resume/预览 | 7 | 16 | PASS |
| Queue 导出通知 stdout 关闭负例 | 1 | 0 | PASS |
| 合计 | **256** | **16** | **0 failure/error/skip** |

pytest-subtests 的既有回归 JUnit 声明 tests=23、实际 testcase=7，另16个 subtests；不能将其混报为23个顶层用例。多组 `deselected` 是聚焦选择，非 skip；未重跑整个仓库或旧183项验收。

Ruff **0.12.7** 使用既有 `cosmos-framework/.ruff.toml`，本批11个 Python 文件 check、format --check、py_compile 均通过。14项静态边界检查通过：protocol AST、Server 启动/身份/等待、结果读取/视频分类以及 authoritative episode emit AST 未变；Process/Results/Identity/Vendor helpers、Vendor Lock、Child Local Client 和 rollout evidence 原文件未改。

CPU 用例使用临时目录、合成 JSONL/录像及真实本机线程/HTTP/进程边界。Child on/off/回调失败比较了动作、Local 调用序列和原异常；进度观察不改业务文件字节/mtime；导出测试验证四类结果、原文、异常原文、每次 replan、路径/冲突/修订、独立副本和无原证据覆盖。内部审查发现的目录污染、旧耗时覆盖、通知异常遮蔽退出码均已修复并增加负例。

这些是作者检查，不能视为 GPT verdict、DS_PRO 独立 CPU Gate、真实模型/厨房兼容性、GPU 性能或 SR 验收。

## 后续审核与停止边界

请 GPT 对上述精确新 Pair 作 fresh incremental review，聚焦观测失败隔离、真实指令/四类标签、复制隔离和结果/Resume 契约。已有 C01/C02 等未变的生产语义无需重新打开；内部作者团队审查不是独立验收。

DS_PRO 待审核后在 clean detached Worktree 对同 Pair 只读复验：Root Config/Progress/Video 三个测试文件、Child 新进度与既有六组，以及 Queue 的13个定向用例。完整命令在 Evidence；Queue 选择为 `commands.json` 中三个 `-k` 表达式的并集。禁用 GPU，外置缓存，禁止生产源码/旧 Evidence/正在运行的工作树修改。作者13项包含正常1/2/8 Worker（部分空闲）、2 Worker live 事件、取消/超时与全任务 Resume；不是8 GPU实测。

Codex 在非 force 发布、远端精确 Pair/Gitlink 回验和 canonical Inbox 交付后停止。任何真实模型、仿真启动、当前评测更新或训练操作仍需后续独立授权；本次交付不替代该授权。
