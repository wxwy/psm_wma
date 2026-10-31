# PSM-WMA V3 — Issue #13 No-TTT `Starting training...` 前完整日志、之后 Progress-only：窄增量 Code Gate

**2026-10-31。正式 Verdict：`APPROVE_CODE`**（仅本精确Formal Pair与默认终端输出状态机的合成CPU Code/Evidence Gate）。

| 对象 | 精确身份 |
| --- | --- |
| Formal Implementation Root | `3cf7453777a693ac029a79ed8b19afc55df0d4fa` |
| Formal Child/Gitlink（无改动） | `6c83596d6a259e89c4cd3e79424024983426ac3d` |
| 当前Canon V3源码基线 | `cee6f53eef345579c3db1124148f350fd2edc618` |
| Codex交接/Evidence文档Commit | `9022cbc44848e153a17211165367460da8d6e6cc`，**不作为Formal implementation** |

## 一、Owner冻结需求与源码差异

- Owner新要求：**`Starting training...` 前终端完整显示初始化/模型/DCP Resume日志；该标志行本身显示；标志之后只显示Rank0 `[CorrectedV3][progress]`**。全过程完整原始日志优先落盘、非零退出及故障/Signal/owned进程回收保持，已运行正式NoTTT Resume不可触碰。
- GPT从GitHub直接获取Root baseline→Formal compare：`ahead=1, behind=0`，仅7个Root路径变更，其中唯一生产路径`**scripts/no_ttt_console.py**`（新增识别及前置直通，未动Shell启动器）；其余为3个狭窄Test/Fixture、一个设计文档、SESSION/TODO。正式Root Git Tree的mode160000指向确切Child `6c83596d6a259e89c4cd3e79424024983426ac3d`；Child全部源/训练算法/Loader/DCP/Server/EvalV2均保持原样。
- 已核Child `cosmos_framework/trainer/__init__.py:330`真实是`log.info("Starting training...")`，位于Optimizer/Scheduler、Checkpoint `load`、dataloader start位置恢复及分布式模型准备之后。Child `cosmos_framework/utils/log.py`默认INFO的Loguru stdout产生带时间+源码路径+line/function的日志行，rank0默认仅显示；新Root `_TRAINING_LOG`正则与该真实前缀/行号浮动、可选ANSI/机器字段匹配。没有向训练器增加私有marker。

## 二、Contract → Behavior → Evidence

| 条件 | 新正式代码核对 | 测试/原始行为 | 结果 |
| --- | --- | --- | --- |
| 初始化全显示，支持长行/未换行/UTF8分片 | `_Output.poll()`起始`training_started=False`，完整原始chunk先由`_write_all(log_fd, chunk)`写到raw后，通过`_console(1, bytes)`直通终端，不要求换行或截断初始化文本 | 新`no_ttt_console_boundary_test.py`真实pipe无换行可见、大于70KB/无效UTF8、跨chunk逐字节标志等；独立检查integration真实console stdout | PASS |
| 正确完整显示分界并只切换一次 | `_starts_training()`要求整行裸标志或Loguru所定义的trainer INFO/source:function格式，匹配完整换行后才单向切到progress-only；同一read内后续noise立即过滤 | 测试精确格式/ANSI/绝对路径/CRLF、配置引号/错误level/source/function/rank标识误命中拒绝；新6条shell+console真实绑定test | PASS |
| 训练中只显示Rank0 Progress，raw完整保留 | mode切换之后沿用此前审核的16KiB progress整行framing，仅回显`[CorrectedV3][progress]`；full raw包括其他rank/loader/traceback/日志 | 原始`integration_cases/...console0/console.stdout`只展示完整初始化+marker+progress；对应full log额外含`[NoTTT][cpu_loader]`及rank1 | PASS |
| 原日志/故障/中断/进程安全保持 | `_write_all`/`_cleanup`/`main`及2个标准launcher未修改；故障仍非零、显示日志路径+尾部原始异常、跨Session子进程回收 | 原21case覆盖write/sync/pipe失败、SIGINT/SIGTERM/late-owned/foreign不杀、Resume独立日志；新6case模拟world4nw8/zero/world8sync、exit7 | PASS |

## 三、直接Evidence独立核验

- 证据在 `docs/collab/codex/evidence/2026-10-31_nottt_console_start_boundary_author_cpu/`；GPT直接读取原始`junit.xml`与`console.xml`/`integration.xml`：**原Console回归21 + 边界19 + 现有Shell→CPU Trainer接线6 = 46不同Test Cases，全部通过，0 failure/0 error/0 skip**（一律按`classname+name`去重，未重复计算旧49/84/GPU）。
- `gate.json`显示Ruff检查/格式四Python文件、合成40+6测试流程全exit0，严格依赖本Formal Pair，作者`source_unchanged=true`。GPT读取真实源码、测试内容、成功及exit7实例console/raw log，并独立SHA256校验`artifact_manifest.json`中**9份关键Evidence**：`junit.xml`、`console.xml`、`integration.xml`、`gate.json`、`scope_audit.json`、成功stdout/raw、异常stderr/raw，**9/9一致**，未将作者自审冒充GPT真机测试。
- 特别核对：实际成功案例终端显示`synthetic initialization and Resume binding complete`与`Starting training...`，只再显示一条Progress；完整raw还含Loader/rank1诊断。故障案例`training_exit=7`、完整traceback都保留。

## 四、限制与无需整改的注意事项

- 本轮状态机只在**完整、符合格式的`Starting training...`行**出现后切换；若用户人为提高Loguru level导致INFO被完全禁用，显示层将保留全部输出而非自行猜测启动边界。这是已提交默认INFO版本的可观察行为，非本轮正常生产源的blocker；未来若确需支持INFO禁用场景，可另作很小的首Rank0 Progress fallback，但不能在本轮为此重构Trainer/更改真实GPU路径。整行裸`Starting training...`也被识别；它不是任意子串，普通`configuration: Starting training...`或rank1前缀被拒绝。
- 以上合成CPU边界测试没有执行实际GPU、torchrun分布式训练、真实模型/数据/Checkpoint/DCP，也未独立观察已经开始的正式Resume；作者称该运行工作树/Job未动，本Reviewer的工具未访问服务器，故不能据此作实时运行确认。

## 五、正式Verdict与后续权限

**`APPROVE_CODE` — Issue#13 NoTTT启动边界显示功能的精确Formal `3cf7453777a693ac029a79ed8b19afc55df0d4fa` / `6c83596d6a259e89c4cd3e79424024983426ac3d`，合成CPU验收闭合。** 此批准不授权重启当前正式NoTTT、触碰GPU、修改DCP/输出、不自动合并V3或更改训练/EvalV2。

**下一步最短路线**：Codex仅在未来不影响正在运行的共享训练目录时，将这1个已批Root生产文件+必要tests/记录从隔离候选安全提升到当前V3；不改变Child Gitlink，使用非强推/先同步远端/精确Git Blob核对。由于当前Resume已在运行，建议**待该运行完成或使用不与运行共享的隔离代码目录**后再更新工作目录；不需要重跑旧49/84/GPU性能A/B或真实训练来验终端显示。提升回执请绑定实际新Root SHA与unchanged Child。

**必须同时提交本Review和Append-only `docs/collab/chatgpt/CODEX_INBOX.md`，docs-only记录SHA不替代Formal implementation Pair。**