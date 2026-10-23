# Batch C r2 — DS独立CPU验收接收与12秒夹具失败裁决

日期：2026-10-23。
Gate：同一 Formal Pair 的新现场 Evidence 接收；不重复审核此前已通过的C01/C02生产实现。

## 1. 身份与证据边界

- Formal Root：`a4b22b929175e462b6a8db57ad2abee7e220dd37`。
- Child/Gitlink：`c9f21040f462a114d597fc83773cb9b6a9e96214`，未变。
- Vendor：`1ac174585293ed998ffc9cf73e47439798cf6f6c`，本轮不重建、不安装。
- 本轮GPT直接读取的V3 HEAD：`78305dbb7166da818cb3033e797ba35aaec1e664`，与DS报告的advertised/origin/V3一致；它是后续文档提交，不代替Formal Root。
- 现场报告由Owner在对话中转交。DS报告Root/Child前后clean、源对象拉取成功、测试日志/JUnit保存在 `/mnt/data1/data_v2_0617/dspro_batchC_r2_verify_20261022/evidence/`；GPT没有登录目标机、读取本地日志或重新执行测试。接受DS现场取证，不另要求上传全量包。GPT独立核对固定源码中失效的测试条件与断言。

## 2. 当前结论

**独立CPU整体验收 verdict：`REQUEST_CHANGES` — TEST-FIXTURE / EVIDENCE ONLY。**

- 源码同步阻塞：CLOSED。DS服务器已自行从V3拉取完整clone，独立验收worktree固定正确Pair；不再要求Owner转运bundle。
- C01/C02：保留已通过的生产整改审核；其新增完成/Resume证据约束、在线Attempt绑定、环境与预测视频分类，DS定向现场证据支持通过，不重开原生产finding。
- 本轮实际计数：第一组148 passed；第二组33 passed +72 subtests passed、2 failed。合计 **181顶层测试通过、2失败、72 subtests通过**。Ruff0.12.7、format、语法6文件通过。不能写成183/183 PASS，也不能把作者334项报告与现场合计相加。
- 两项失败并未证明生产Queue有新缺陷，但目标故障注入尚未发生，不能据此关闭整体验收。失败不能被skip、换快机器碰到绿或降低断言消除。
- 真实Kitchen/目标Vendor安装/模型推理/正式benchmark Gate与本次CPU结果分开；本文件不授权真实仿真、GPU或训练操作。

## 3. 新finding MEDIUM-TEST-C03：健康Worker完成前，固定12秒夹具守卫先失败

**位置**：`tools/v3/eval_robocasa_queue_identity_test.py:381-396` 的 `wait_completed()` / `fail_initialization()`；`:418-421` 的 `late_launch_failure` 共用该等待；`:1067-1092` 的初始化故障断言；`QueueIntegrationTests.scenario()` 的外层process watchdog也需协调。

实际代码先按summary条件轮询，等待 `total_trials == 20`，但只给12秒。`init_faults.append(operation)` 在等待之前发生。12秒耗尽后抛 `AssertionError('healthy worker did not complete before initialization fault')`；预期的 `OSError('injected worker1 ... failure after all tasks')` 未执行。

DS在该CPU环境独立重试两项，均得到相同失败；报告单任务执行、每任务Server/解码/收尾成本使健康Worker超过12秒。这里只能认定固定性能假设在该环境不可满足，不应扩大成对所有环境都绝无竞态的结论。

**违反验收合同**：这两项要证明的是“健康Worker先完成全部20条，再发生另一个Worker初始化OSError，最终仍INCOMPLETE/RC1，错误不丢失”。本次实际证明的是“另一个Worker的等待守卫抛AssertionError后，生产Queue会保留错误”，属于相邻通用失败处理，不等于指定mkdir/log_open故障的完整时序证明。

`init_faults`已有记录也不是注入成功凭证，因为它在守卫前追加。最终summary有20条结果不能倒推抛错当时已有20条。

**范围与修复验收**：由Codex仅修改正式测试夹具及必要测试辅助，生产Queue/Process/Child/Vendor/G1保持不变。保留真实完成条件驱动的故障触发，给合理且有界的慢CPU等待预算，协调外层scenario watchdog和清理预算；不能取消watchdog或把20条成功结果提前伪造到summary。加实际故障注入后的独立witness，证明completion在先、指定OSError在后。保留原全部关键断言与失败清理。

需要正例：健康Worker完成耗时超出旧12秒假设后，仍能完成20条并注入预期OSError；最终RC1、INCOMPLETE、sr=null、4任务结果保留、4 server/4 sim、准确错误类型/内容、无残留线程进程。
需要反例：健康Worker从不达到完成条件时，夹具必须有界失败，不能绕过条件注入或返回PASS；失败可区分为fixture prerequisite timeout。

## 4. 复验最小范围

不让DS继续在当前旧测试上重复运行，不更换硬件作为永久修复。
Codex提交新的Root源码SHA后，Child应保持c9f21040，给test-only diff和作者定向结果。GPT做这个新Root的窄范围增量审核。
DS随后仅运行两项失败 + 共用等待的 `test_server_launch_error_after_other_tasks_does_not_disappear` + 作者新增的有界同步/超时负例；无需重跑先前148项、整个183项或G1套件，除非实际diff扩大范围。
本次181+72通过记录按原Pair保留；新Root的新定向证据独立绑定，不能把旧JUnit改名为新Pair全量PASS。

## 5. 环境与记录

- DS使用旧editable robocasa/robosuite的CPU解释器不阻塞这些合成测试，但不证明正式Vendor或真实Kitchen已就绪。
- `AGENTS.md` 增加DS环境地图入口，应同时注明2026-10-23源码已自行拉取成功，不能照抄旧地图“源码缺失/需离线交付”的过期状态。
- TLS验证关闭仅是DS本次现场同步事实，不应固化为默认建议或全局配置；后续应采用受信任CA/代理链路并保持日志不含凭据。本轮不据此推翻精确SHA验收，也不在活动环境修改网络设置。

本轮不修改生产代码/测试、Child/Gitlink、Vendor或G1资产，只记录裁决与窄范围整改要求。