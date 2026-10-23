# Batch C — 完成等待夹具 ee53cbe1 / c9f21040 独立增量审核

日期：2026-10-23。
Formal verdict：**APPROVE — 仅本精确 Pair 的 test-only 整改源码与作者定向 CPU Evidence 范围。**
MEDIUM-TEST-C03 在本次源码/作者验证范围关闭；DS目标机修复后5项独立复验尚未完成，整体独立CPU Gate保持待闭合，不写成PASS。真实环境、模型及GPU执行另行授权。

## 1. 身份、来源与修改范围

- Formal Implementation Root：`ee53cbe1c25ff174f0d92a92e51e901ec6436c18`。
- Child/Gitlink：`c9f21040f462a114d597fc83773cb9b6a9e96214`，mode160000，未变。
- Vendor可重建产物：`1ac174585293ed998ffc9cf73e47439798cf6f6c`，未变。
- 开发父版本：`4a1ab5faf54adfff8be460f850f132c86a3a46d7`；原Batch C r2生产版本：`a4b22b929175e462b6a8db57ad2abee7e220dd37`。
- 本轮开始直接读取的V3 HEAD：`29268a0c473525c44dc218e2a7d4ce20424223ac`，属作者Evidence/报告后续归档，不替代Formal Root。
- 前序裁决：`docs/collab/chatgpt/reviews/2026-10-23_BatchC_r2_DS_CPU_acceptance_fixture_timeout_disposition.md`。
- 最小整改合同：`docs/collab/chatgpt/requests/2026-10-23_Codex_BatchC_fixture_wait_budget_and_DS_delta_recheck.md`。
- 作者交接：`docs/collab/codex/reviews/2026-10-23_BatchC_fixture_wait_author_handoff.md`，证据目录 `docs/collab/codex/evidence/2026-10-23_BatchC_fixture_wait_author_cpu/`，按归档SHA29268a0c读取。

GitHub实际compare(parent4a1ab5fa,ee53cbe1)仅三个文件：测试 `tools/v3/eval_robocasa_queue_identity_test.py` +197/-20；SESSION.md追加7行；TODO.md追加2行。唯一代码修改是该测试文件。Root树中Child/Gitlink、scripts、configs、third_party未变；没有修改生产Queue/Process/结果校验、训练模型/优化器/DCP、Local-TTT数学、Vendor或G1冻结资产。

旧test Blob `b38b238a6f15f7f70df039ecade54490165b77b9`；新Blob `a29513aa10ccfac01a3dab2283f1d3afbc910cf7`；作者记录新文件SHA256 `1cbe51e37b0174f4303a0685b6a7a142183787d96ad262b0c4c080105a8236b3`。GPT直接读取固定新Blob对应实际源码及Git差异，没有独立重新计算完整文件SHA256。

## 2. 前序失败与本次关闭依据

前次DS现场148+33=181个顶层测试通过、2失败、72subtests通过。失败发生于固定12秒测试guard，实际抛的是前置条件超时AssertionError，指定mkdir/log_open OSError没有发生；不能以最终20条结果或等待前init_faults记录代替注入顺序证据。本轮不重审未变的C01/C02生产逻辑。

### 2.1 真实完成条件保留并加强

新测试文件约38–122行 `_raise_after_completed()` 仍读取实际Queue的 `screening_summary.json`；只在目标20/15条结果、4/3个各5条且无error的Task、无worker_errors及对应COMPLETE/INCOMPLETE状态都满足后继续。没有预造成功Summary，也不是sleep结束即注入。

等待预算120秒；仅相关late-completion场景的外层watchdog为180秒，其余原场景保持90秒。共享截止值同时受scenario起点+watchdog−30秒限制，给清理和报告留余量。所有这些是测试侧预算，生产Task/Episode/request/terminate参数未改变。

### 2.2 异常顺序可核验

满足完成条件时记录单调时刻、已观察trial数、Task集合和Summary状态。随后真正raise OSError，捕获后记录异常类型/消息/注入时刻，再原样re-raise。`init_faults`只在这时追加。

约1201–1241行新增 `check_completion_before_fault()` 要求唯一完成witness和唯一实际OSError，目标数一致、异常准确、完成早于截止、完成时刻不晚于注入时刻。原初始化失败断言全部保留：20条/4Task/4Server/4Sim、RC1、INCOMPLETE、sr=null、指定worker1错误、无未处理线程异常；还要求Queue保存的异常以 `OSError: injected worker1` 开头。

`late_launch_failure`仍只等待15条/3Task，不错误改成20；其余Task已经由失败Worker占用的原语义保持。

### 2.3 正反例没有绕过验证目标

慢正例在首个合成Sim启动前，等待故障Worker已经开始真实完成guard，然后对健康路径延迟13秒。后续仍由真实Summary完成条件触发错误，不伪造完成。测试断言健康延迟>=13秒、完成等待>旧12秒门槛、完成发生在延迟结束后；再复用全部初始化失败断言。

超时负例让目标Summary一直不存在，共用guard在0.15秒预算后产生 `FixtureCompletionTimeout`；断言没有完成字段、没有Summary、没有OSError注入、init_faults为空。另有30秒独立子进程watchdog。这证明guard本身有界且不假注入，不把它夸大为一次真实卡死Simulator演练。

父scenario继续核验无robocasa-gpu线程和所有已记录Server退出；外层watchdog仍保留进程组终止逻辑。没有删除原清理或错误断言。

## 3. 作者Evidence独立读取

直接读取：`gate.json`、`delta.xml`、`witnesses.json`、`source_checks.json`、`ruff.log`及实际修改代码。未在本GPT环境或DS机器重新执行pytest，未将作者记录称为DS独立验证。

JUnit：5 tests、0 failure、0 error、0 skip，53.976秒；作者筛选另32 deselected，不是32 skipped。

| 场景 | 原始witness |
|---|---|
| mkdir_failure | 20条完成后OSError；等待约10.317s；最终INCOMPLETE/RC1、错误保留 |
| log_open_failure | 20条完成后OSError；等待约10.391s；最终INCOMPLETE/RC1、错误保留 |
| late_launch_failure | 15条完成后指定OSError；等待约7.459s；3个Sim完成，原15条语义保留 |
| slow_mkdir_failure | 13.000s健康路径延迟；实际等待22.816954s后观察20条；完成438943.490569043，注入438943.490580934；最终20条保留且INCOMPLETE、sr=null |
| completion_never_finished | 实际约0.150s后TIMED_OUT；无Summary、无注入、无init_faults |

Ruff日志为0.12.7、All checks passed、1 file already formatted；source_checks记录AST语法PASS、production_paths_diff=[]。作者Python3.12.14，DS上轮Python3.13.11；不主张目标机已验证或两环境完全等价。

## 4. 当前裁决与最小下一步

**APPROVE：这次窄范围test-only修复符合前序验收合同，未发现新的本scope blocker。Codex无需继续修改该夹具。**

DS从V3自行拉取，建立新隔离clean worktree，固定Root ee53cbe1、Child c9f21040，仅运行作者交接中的5个精确测试及这一个测试文件的Ruff0.12.7、format、语法检查。不要重新安装Vendor，不重跑已通过148项、183项全套或G1训练套件。旧181+72结果保留原Pair，新5项结果单独绑定新Pair；不可加总写成一次新Pair全量PASS。

复验特别要在先前出现12秒失败的同一DS CPU环境观察20条先完成、指定OSError后注入、超时负例无假注入，以及无残留自有进程/线程、前后Root/Child clean。只有这些现场证据通过后，才按已批准的增量证据组合关闭本CPU验收遗留项，无需重复源码审核。

DS不应手工扩大等待、删除断言、skip、修改生产超时，或为获得PASS更换快机器代替现场复验。任何新失败保留日志上报。

**边界：整体独立CPU Gate目前仍PENDING_DS_DELTA；真实Vendor/Kitchen物理验证、模型加载及Owner手动仿真另Gate。活动G1训练保持原工作树与资产不动。**

按当前AGENTS职责，本正式审核结果存放reviews目录，不以Inbox或后续文档HEAD代替此精确Pair的verdict。