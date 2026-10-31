# Issue13 — Starting training 之前完整显示、之后 Progress-only

**REVIEW / 作者 CPU PASS**。请求 GPT 对本次输出层增量做 fresh Code Gate。
本文件不自授批准，不包含当前运行 Resume 的更新/重启或 V3 合并。

| 身份 | SHA |
| --- | --- |
| Formal implementation Root | `3cf7453777a693ac029a79ed8b19afc55df0d4fa` |
| 未变 Child / Gitlink | `6c83596d6a259e89c4cd3e79424024983426ac3d` |
| 当前 V3 代码基线 | `cee6f53eef345579c3db1124148f350fd2edc618` |
| 隔离候选分支 | `v3-nottt-console-start-boundary-20261031` |

后续 Evidence/Inbox/回执提交不是 Formal implementation SHA。
Owner 指令来源：Issue13 comment6540535680 及本轮明确要求。

## 行为与最小变更

实际核对 Child core Trainer 当前第330行 `log.info("Starting training...")`，
发生在 Checkpoint load、迭代定位和分布式模型设置之后。`utils/log.py` 默认
Rank0 输出，标准 INFO 包含时间、source path、行号及 train 函数。
Child 代码原样保留，不新增训练标记或改变日志级别。

生产只改 **`scripts/no_ttt_console.py`**：

- 进入包装器后先完整显示初始化 stdout/stderr；每个原始 chunk **先写文件，
  再回显**，不等待换行，UTF8 分片及原始字节不被重复解码破坏。
- 完整的 `Starting training...` 行正常显示后，单向切换为 Progress-only。
  支持精确裸消息及当前真实 Cosmos INFO Trainer 格式、ANSI、machine fields、
  absolute path 和 CRLF。同一 read 内分界后的 Loader JSON 已会被隐藏。
- 配置中的引用、错误 source/function/level、rank-prefix 文字不触发切换；
  没有分界行时保持完整显示。每次启动/Resume 重新处于初始化显示模式。
- 全程完整日志、非零退出诊断、SIGINT/SIGTERM、owned cleanup 与独立日志
  均维持。训练阶段的进度分帧上限不变，识别器只在初始化阶段运行。

两份训练 launcher 完整 mode/type/blob 未改，整个 Child、训练/DCP/config/
算法/EvalV2 未改。Scope 审计证明另外 **12,456个 Root 对象**不变；
`_write_all/_owned/_signal/_cleanup/main` 的 AST 与基线相同。
仅3个对应测试文件调整/新增；没有新增选项、依赖或运行时服务。

## 新版本作者 CPU 结果

原始包：
`docs/collab/codex/evidence/2026-10-31_nottt_console_start_boundary_author_cpu/`。

| 检验 | 结果 |
| --- | --- |
| 原控制台回归 | 21 passed |
| 新边界用例 | 19 passed |
| 原模拟启动接线 | 6 passed |
| 合计唯一用例 | **46 passed，0 failure/error/skip** |
| Ruff0.12.7 check / format / AST | 4个 Python 文件 PASS |
| exact Pair / clean / source before-after | PASS / unchanged |

新用例覆盖实时未换行初始化、同读切换、逐字节分界、ANSI/source variants、
假阳性、大日志/缓冲上界/非法UTF8、EOF、初始化失败、每次Resume重置。
原21个测试的 Raw、失败码、写盘故障、signal/late-child/foreign-survival/
独立日志断言保留；只按新要求更新显示期望和分界 fixture。
原6个模拟启动用例仍使用真实 shell、包装器、CPU profile/Trainer binding，
现在发出模拟分界，并严格比较原始初始化前缀＋Progress；不调用真实训练。

保留 Gate/命令/env、原始JUnit和日志、完整 Diff、43份工件 SHA256 清单、
8个源码绑定（4个被检 Python、2个未变 launcher、2个未变 Child 日志来源）。
6个实际模拟 case 的 stdout/stderr/full raw/receiver JSON 原样保存，不计 symlink。
首轮 frozen CPU Gate 通过；冻结前的两处未用测试 import 已清理，未放宽 Ruff。

**这是作者合成 CPU Evidence。** 没有完整重跑旧49/84，也没有 GPU、原生
torchrun/worker pool、真实模型/数据/DCP/OS/仿真。原测试中的 Resume 仍只是
模拟CLI及绑定，不冒充正式恢复证据；当前已启动 Resume 的工作树、进程、
Checkpoint/config/Job Identity 和 `_launch_logs` 均未访问或修改。

## 交接与停止条件

计划及语义见
`docs/build/PSM-WMA_V3_NoTTT_Console_Starting_Training_Boundary_2026-10-31.md`。
请求只审本次日志显示状态与对应 CPU 回归；不重开 No-TTT/EvalV2 已关闭 Gate，
不扩大到训练或日志架构改造。发布隔离候选并回验 Root/Child/Gitlink 后停止。
未经后续审核/授权，不提升 V3、不更新或重启当前 Resume；新行为供后续启动使用。
