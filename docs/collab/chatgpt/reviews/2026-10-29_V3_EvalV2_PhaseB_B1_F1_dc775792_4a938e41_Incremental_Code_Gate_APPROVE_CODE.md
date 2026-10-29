# GPT 增量 Code Gate — Phase B 第一批 B1-F1 原始截止时间整改

日期：2026-10-29（Asia/Shanghai）。本轮发布前远端锁定：约15:20 CST。

## 0. 正式结论

**`APPROVE_CODE` — 仅批准本精确 Formal Pair 的 Phase B 第一批 Transaction / Session / Local Fast State / B=1 生产源码。B1-F1 CLOSED；B1-P1 保持 WITHDRAWN。**

本结论基于独立源码增量审查、与前序已审路径的衔接、原始作者 Evidence 及源码身份核验。当前审查范围内没有剩余阻断性 Finding。它不等于独立 DS CPU 验收或真实模型、GPU、网络、RoboCasa/EGL 与900集评测通过。

批准的部署语义是当前同主机 Linux B1 CLI 路径：进程正常经 exec 启动，使用可比的 CLOCK_MONOTONIC，运行期间不在进程内部重配 time namespace。第3节明确说明这一支持前提及真实环境核验边界。

| 身份 | 精确值 |
| --- | --- |
| **Formal Implementation Root** | `dc7757922d7273f50f3de23363d41e12e157a07f` |
| **Formal Child / Root Gitlink** | `4a938e41b0c335baca1c1d8f1caabc433b0e2001` |
| Root / Child 隔离候选 | `v3-eval-v2-transactions-b1-20261029` |
| 前序被审实现 | Root `9a3f88e55893491ea68d16b3f23680ae6941d106` / Child `1bece52ee419d12119c1b3d0b75e0ae5c5139ae9` |
| 本轮作者 Evidence commit | `473c0435e819eaffff4368e7a8c0c2c41d4be4ab` |
| 已观察 Root candidate HEAD | `0e4061005c691cb45b14948a52390f5c041848b9`（publication readback，不替代 Formal Root） |
| 发布前 V3 HEAD | `020f35dc0cf291df7ca2d62fb1d05b62ce4424fa` |
| 已批准 Phase B 设计 | Root `b9c7cf1607ffd38f6e3349bdde0b35703a6d7684` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6`，r1+r2+r3 |
| 前序有效审核 | [B1-F1 OPEN / B1-P1 WITHDRAWN 更正](https://github.com/wxwy/psm_wma/blob/e57f0263757c65521acac7a2c24e7fdbdaa78cfb/docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseB_Transaction_B1_9a3f88e5_1bece52e_Recheck_P1_WITHDRAWN_F1_OPEN.md) |

## 1. 实际增量与版本范围

直接比较 Child `1bece52e..4a938e41`，恰好修改5个文件：

- 生产：`cosmos_framework/inference/robocasa_session_transactions.py`、`cosmos_framework/inference/robocasa_transaction_client.py`、`cosmos_framework/scripts/action_policy_server_robocasa.py`。
- 测试：`cosmos_framework/inference/robocasa_session_transactions_test.py`、`cosmos_framework/scripts/robocasa_transactions_b1_test.py`。

Root 技术变化是新 deadline addendum 和 Gitlink；其余为协作记录、前序 Evidence / Review 的保留与导入。Root scripts/configs/Phase A tests、原 CPU gate 脚本未变；Child Local state owner、Fast update 算法、模型、训练、优化器、数据、Sim 与 Vendor 未改动。无关 Compact 文档仅作为并行协作记录保留，本 Gate 不审核或推进 Compact。

Formal Root 的 `cosmos-framework` 实际 metadata 为 submodule，SHA 精确为 `4a938e41...`。Formal→Evidence→readback 后两笔提交只增加 Evidence/ledger/readback，不是新的生产实现。

[本轮 author handoff](https://github.com/wxwy/psm_wma/blob/473c0435e819eaffff4368e7a8c0c2c41d4be4ab/docs/collab/codex/reviews/2026-10-29_V3_EvalV2_PhaseB_B1_F1_original_deadline_author_handoff.md)；[冻结整改合同](https://github.com/wxwy/psm_wma/blob/dc7757922d7273f50f3de23363d41e12e157a07f/docs/build/PSM-WMA_V3_EvalV2_PhaseB_B1_F1_Original_Deadline_Addendum_2026-10-29.md)。

## 2. B1-F1 的源码关闭依据

以下 Child 行号均属于 `4a938e41b0c335baca1c1d8f1caabc433b0e2001`。

| 关键环节 | 实际源码位置 | 审核结果 |
| --- | --- | --- |
| 冻结原始预算 | `robocasa_transaction_client.py:82–98` | predict入口先冻结started_at/deadline，再编码、hash及上传；同一调用的重试携带完全相同budget。 |
| 生产HTTP传递 | `action_policy_server_robocasa.py:659–667` | /v2/inference严格要求lease/payload/budget；Dispatcher直接传budget给Actor，无旧两字段fallback。 |
| 准入验证 | `robocasa_session_transactions.py:92–106,308–310` | 拒绝不同domain、无效/非有限/bool/过大时间、未来start、超Server cap或已过期预算。 |
| 编码及锁等待 | 同文件 `323–353` | payload验证与锁等待之后、分配Ticket之前再次检查原始预算。Ticket.deadline保存传入的原始绝对值。 |
| 重试不续期 | 同文件 `331–335` | 存在Ticket时复用该Ticket，不修改其deadline；incoming更晚预算也不能延长已接受工作。 |
| 模型及提交检查 | 同文件 `433–477` | 获得模型锁后、prepare之后、强制device drain之后且commit之前，用同一Ticket deadline执行fence。 |
| 迟到响应 | `robocasa_transaction_client.py:40–60` | transport返回和JSON decode后重查原始deadline，迟到不能报告客户端成功。 |
| Poll / ACK | 同文件 `100–112,135–140` | 沿用同一客户端deadline；原始预算不因轮询或ACK而重建。 |
| HTTP过期信号 | server `1535–1543` | 准入TimeoutError映射408；执行中原始fence/abort保留其事务失败与清理语义。 |

来源：[Client](https://github.com/wxwy/cosmos-framework/blob/4a938e41b0c335baca1c1d8f1caabc433b0e2001/cosmos_framework/inference/robocasa_transaction_client.py#L82)、[Actor](https://github.com/wxwy/cosmos-framework/blob/4a938e41b0c335baca1c1d8f1caabc433b0e2001/cosmos_framework/inference/robocasa_session_transactions.py#L308)、[Dispatcher](https://github.com/wxwy/cosmos-framework/blob/4a938e41b0c335baca1c1d8f1caabc433b0e2001/cosmos_framework/scripts/action_policy_server_robocasa.py#L659)。

### 原反例现在被拒绝

在已证明同一时钟域的前提下：client t=0启动、deadline=1.0，首次请求t=0.8到达；新Actor保存的deadline仍为1.0。若generation或device drain到t=1.2才完成，第476行fence拒绝，第477行commit不能发生，旧Fast / Visual / Response snapshot保持不变。源码没有以接收时间重新授予timeout，也没有将remaining_timeout从接收时重新起算。

### Replay与已提交状态的边界

- 尚在执行的Ticket：重复请求共享原Ticket和deadline。
- 已提交但未ACK的Ticket：仍保留所有权；原预算过期后，新的predict预算不能使其重新可交付，需要End清理。此前确实在有效预算内发生的commit不会被伪装成未提交或任意回滚。
- 已提交且ACK的保留Response：后续新读取可以有新的读取预算，但直接返回缓存字节，不分配Ticket，不再次encode/Local scan/generate/commit。r3的无幽灵Ticket与重放优先于分配保持。
- 已在准入前拒绝、从未分配Ticket的请求：本次调用内部重试仍固定预算。若外部重新调用predict，则属于新的API调用；第二批Sim集成必须遵守既有fault/End/new Attempt流程，不能通过外层无限重调predict绕过Episode/run期限。当前没有已接受工作被续期的证据，不为这一未集成调用方策略另设阻断。

**B1-F1 CLOSED。**此结论由上述生产源码不变量与测试覆盖共同支撑，不以PASS数量替代协议判断。

## 3. 时钟域证明、实际环境与一个非阻断支持前提

### 当前支持路径

`robocasa_session_transactions.py:64–89` 检查Linux与CPython的CLOCK_MONOTONIC实现，读取有大小限制的boot UUID及monotonic offset，验证并构造domain。Client初始化探测自己的domain，注册ACK匹配后才接受lease（client:36,73–79）；Server option在模型初始化前探测（server:649），Actor也记录并返回其domain（actor:179,217,255,270）。

缺失或非法kernel证据时，没有接收时间、wall-clock或默认零offset回退。跨host/不同domain直接被拒绝；当前路径不声称支持任意远程monotonic值，也不将可信lease holder的clock声明当作恶意客户端认证机制。

### 非阻断说明：active namespace 与 time_for_children

本轮额外核对上游Linux源码：

- [kernel/time/namespace.c](https://github.com/torvalds/linux/blob/v6.6/kernel/time/namespace.c#L365) 的proc_timens_show_offsets读取time_ns_for_children。
- [include/linux/time_namespace.h](https://github.com/torvalds/linux/blob/v6.6/include/linux/time_namespace.h#L65) 的实际monotonic偏移来自active time_ns。
- [kernel/nsproxy.c](https://github.com/torvalds/linux/blob/v6.6/kernel/nsproxy.c#L259) 的exec_task_namespaces在exec时处理二者不一致，使新程序使用children namespace。

因此，helper的证明依赖当前正常exec启动、运行期间不在进程内部重配time namespace的前提。不能把它泛化为对pending time namespace、任意嵌入式launcher或运行中unshare/setns都成立的通用证明。

当前被审CLI路径没有引入上述进程内namespace重配置；不能仅凭额外构造的嵌入式运行方式，认定本候选正常入口必然可达错误提交。本项记录为**非阻断部署前提**，不新增REQUEST_CHANGES，也不重开已撤销P1。

在第二批改变launcher/进程生命周期或开展真实环境准入时，应把实际Client/Server进程的 `/proc/self/ns/time` 与 `/proc/self/ns/time_for_children` 身份、domain和启动方式一起记录。若实际环境不满足本轮前提，先拒绝该部署或补充active namespace校验；不能用两个可能不对应active时钟的hash相等代替核验。这归入已有环境准入，不要求为本项另跑当前354项或重新设计batch架构。

### 已知cloud阻塞保持可见

[actual_cloud_kernel_probe.json](https://github.com/wxwy/psm_wma/blob/473c0435e819eaffff4368e7a8c0c2c41d4be4ab/docs/collab/codex/evidence/2026-10-29_eval_v2_b1_f1_original_deadline_author_cpu/actual_cloud_kernel_probe.json) 直接记录：

- boot_id存在，timens_offsets不存在；
- `BLOCKED_KERNEL_IDENTITY_UNAVAILABLE`；
- `production_bypass: false`。

最终CPU测试向真正parser提供显式kernel-file byte-stream doubles，分别测试缺失、非法与不一致；没有替换整个parser为固定成功函数。此前无fixture探索运行的kernel缺失失败也单独保留。

**因此可批准当前源码协议，不能宣布该cloud能实际启动B1 profile。**真实Client/Server的环境证明、独立DS CPU和native模型/设备/网络验收仍须按各自范围完成。

## 4. 原始作者Evidence与源码身份核验

| 工件 | JUnit header / 实际testcase | failure / error / skipped |
| --- | --- | --- |
| final/inference.xml | 99 / 99 | 0 / 0 / 0 |
| final/phase_a_regression.xml | 255 / 255 | 0 / 0 / 0 |
| final/junit.xml | 99+255 / 354 | 0 / 0 / 0 |

本轮直接读取 [gate.json](https://github.com/wxwy/psm_wma/blob/473c0435e819eaffff4368e7a8c0c2c41d4be4ab/docs/collab/codex/evidence/2026-10-29_eval_v2_b1_f1_original_deadline_author_cpu/final/gate.json)，确认Root/Child/Gitlink精确绑定dc775792/4a938e41，Ruff0.12.7 check/format、AST9、import origin和source_unchanged记录通过。审查团队直接逐个读取完整Formal SHA对应文件，**15/15 [formal_source_bindings.json](https://github.com/wxwy/psm_wma/blob/473c0435e819eaffff4368e7a8c0c2c41d4be4ab/docs/collab/codex/evidence/2026-10-29_eval_v2_b1_f1_original_deadline_author_cpu/formal_source_bindings.json) Git Blob匹配**。

旧67项inference的classname+name全部保留，新增32项。已直接检查测试增量：旧assert没有放松；旧actor直接submit改为提供必需budget的helper；B1数值对照仍为rtol=0、atol=0。255项Phase A回归保持。

关键新增测试实际经过生产Client→Dispatcher→Actor，包括：

- 首次上传延迟、cold/hot旧snapshot、generation晚于原deadline；
- 请求未接受/已接受时丢失、inflight同Ticket重试；
- upload/generation/device-drain耗尽预算；
- 编码耗时计入原始预算；
- response/ACK迟到不能报告成功；
- 有效预算内成功、ACK丢失、ACK后缓存读取；
- 非法/过期/foreign预算、实际Handler 408、kernel文件缺失/非法/不一致。

### 旧生产RED2的证据边界

原始RED日志与JUnit确认为2个预期失败（cold/hot），均失败在snapshot is before断言；旧3个生产文件的Blob与Child1bece52e直接匹配。

作者明确披露：首次RED运行时测试是未提交追加草稿，没有运行前字节hash。因此本轮把它视为有日志与旧生产身份绑定的预期反例，**不称为完全冻结测试工件的clean旧pair Gate**。该限制不改变新Formal Pair的完整最终测试与源码身份绑定，也没有要求无理由重复旧RED。

**上述354 PASS均为作者执行。本轮GPT进行了独立源码、原始Evidence和版本核验，没有重跑项目CPU测试，没有运行namespace mutation、GPU、模型权重、真实HTTP服务、RoboCasa/EGL、DCP或900集。**Wan/diffusion/网络与kernel边界的doubles不升级为native证据。

## 5. 关闭记录与下一步范围

| Gate / Finding | 更新后状态 |
| --- | --- |
| Phase A动态Sim Slot | 原fd7e43f6/d2c1bda6源码APPROVE_CODE保持 |
| Phase B r1+r2+r3设计 | 原b9c7cf16/d2c1bda6 APPROVE_DESIGN保持 |
| **Phase B第一批Transaction/B1** | **本dc775792/4a938e41 APPROVE_CODE** |
| **B1-F1原始预算** | **CLOSED at本Formal Pair** |
| B1-P1归档事项 | WITHDRAWN保持；不恢复超长历史到live Inbox |
| Phase B第二批M>1 / native B>1 | 第一批Code Gate前置条件已满足；尚未由本轮实现或验收 |
| 独立DS CPU / native Canary / 真实900集 | 本轮未执行、未产生新执行授权 |

依照已有Owner Issue #8分阶段授权，Codex可继续**隔离候选上的第二批生产实现与作者CPU检查**，以已批准r1+r2+r3设计为准：M>1可复用Sim、多Session独立Fast State、一次真实native批量generation、有限排队与partial batch、准确结果分发、事务清理和D1–D5回归。新增代码必须提交新的精确Formal Root+Child、原始Evidence，STOP等待GPT第二批Code Gate；不能把本第一批批准外推到未实现的B>1。

第二批应保留本轮原始deadline语义和Session故障边界，不能让Sim外层重试重建无界预算。若native接口需要改变冻结的模型/张量语义，先重新提交相关设计变化。

本Review与Issue回复不派发DS任务，不执行第二批代码，不合并V3/Child生产分支，不授权GPU/Cosmos/DCP/RoboCasa/EGL/真实900、训练/checkpoint/optimizer/Vendor/历史Core操作。既有未完成的独立CPU/native验收继续保留，不用作者354替代。

本文件和canonical Inbox追加、Issue #8回复均按用户已给出的交接要求发布并回读。审核发布commit是docs-only，不替代上表Formal Implementation Pair。
