# GPT 增量复核与更正 — Eval V2 Phase B Transaction / B1

日期：2026-10-29（Asia/Shanghai）。本轮远端锁定观察约 14:34 CST。

## 1. 正式结论与适用范围

**Code Gate 仍为 `REQUEST_CHANGES`。B1-F1 MEDIUM 保持 OPEN；B1-P1 撤销（WITHDRAWN）。**

本文件更正同一 Formal Pair 既有审核中的 B1-P1 判断，并记录对 B1-F1 和作者证据的独立复核；不是新实现版本，也不是已经实施了整改。

| 对象 | 精确身份 |
| --- | --- |
| Formal Implementation Root | `9a3f88e55893491ea68d16b3f23680ae6941d106` |
| Formal Child / Root Gitlink | `1bece52ee419d12119c1b3d0b75e0ae5c5139ae9` |
| Root / Child 候选分支 | `v3-eval-v2-transactions-b1-20261029` |
| 本次观察 Root 候选 HEAD | `0f887a8c00f4514343e887da946136820e6cf16e`（后续 Evidence / publication bookkeeping） |
| 本次观察 Child 候选 HEAD | `1bece52ee419d12119c1b3d0b75e0ae5c5139ae9`（无新生产修复） |
| 本次观察 V3 HEAD | `6eca9eaa2a23479d02bd8d839bab0213b861847d` |
| Phase A 已批准源码基线 | Root `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |
| Phase B 已批准设计 | Root `b9c7cf1607ffd38f6e3349bdde0b35703a6d7684` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |

前序报告：[首次 Code Gate](https://github.com/wxwy/psm_wma/blob/6eca9eaa2a23479d02bd8d839bab0213b861847d/docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseB_Transaction_B1_9a3f88e5_1bece52e_Code_Gate_REQUEST_CHANGES.md)。该历史文件保留；关于 B1-P1 及由其派生的“必须恢复完整历史到 live Inbox”的整改要求，以本更正为准。其他不冲突的源码审查结论与授权边界继续有效。

用户交接中的“Awaiting Code Gate / 尚未审核”已落后于远端记录。本轮已直接读取同 pair 正式 Review、canonical Inbox 和 Issue #8，不把摘要或作者交接当作最终 verdict。

## 2. B1-F1 MEDIUM — 确认成立，仍阻断 Code Gate

### 2.1 实际生产调用链

以下 Child 源码均锁定到 `1bece52ee419d12119c1b3d0b75e0ae5c5139ae9`。

| 生产入口 | 位置 | 本轮直接确认的行为 |
| --- | --- | --- |
| TransactionPolicyClient | `cosmos_framework/inference/robocasa_transaction_client.py:70–95` | 第81行以客户端当前时间启动原始 deadline；第82行 POST 只有 lease 与 payload，没有传输该预算权威。重试和轮询只在客户端扣减剩余时间。 |
| HTTP Dispatcher | `cosmos_framework/scripts/action_policy_server_robocasa.py:657–665` | /v2/inference 只接受 lease、payload 并直接调用 actor.submit；没有隐藏的 deadline 传递或换算。 |
| Actor admission | `cosmos_framework/inference/robocasa_session_transactions.py:259–308` | 第301行在首次收到请求时，重新以 server.clock() + self.timeout_s 创建完整服务端预算。 |
| Actor commit fence | 同文件 `245–249,376–379,420–425` | quiesce 后确实执行 fence，但只检查从首次到达时间重新起算的票据 deadline；随后发布快照。 |
| HTTP 断连与超时 | server `1490–1502,1517–1533` | body-read timeout 不是原始事务预算；BrokenPipe/ConnectionReset 不会自动取消 Actor。 |

来源：[Client](https://github.com/wxwy/cosmos-framework/blob/1bece52ee419d12119c1b3d0b75e0ae5c5139ae9/cosmos_framework/inference/robocasa_transaction_client.py#L70)、[Actor](https://github.com/wxwy/cosmos-framework/blob/1bece52ee419d12119c1b3d0b75e0ae5c5139ae9/cosmos_framework/inference/robocasa_session_transactions.py#L259)、[Dispatcher](https://github.com/wxwy/cosmos-framework/blob/1bece52ee419d12119c1b3d0b75e0ae5c5139ae9/cosmos_framework/scripts/action_policy_server_robocasa.py#L657)。

冻结设计依据为 [Phase B r1 §3](https://github.com/wxwy/psm_wma/blob/9a3f88e55893491ea68d16b3f23680ae6941d106/docs/build/PSM-WMA_V3_EvalV2_PhaseB_MultiSim_Transactional_Batch_Design_r1_2026-10-29.md#L57)：同一个绝对 prediction deadline 覆盖 upload、queue、prepare、generation、response fetch，重试与轮询不续期。

### 2.2 可达反例与影响范围

以下是生产源码可达序列的推导，不是本轮执行过的 CPU/GPU 实验：

1. 两端 timeout 均为1秒，且两端时钟完全一致；客户端 t=0 开始预测，原始 deadline=t=1.0。
2. 首次请求到达服务端前消耗0.8秒。Actor 在 t=0.8 创建票据，当前实现给出新的 deadline=t=1.8。
3. 客户端到 t=1.0 已因原始预算耗尽而失败；predict 没有保证向 Actor 送达 End。
4. generation 与 quiesce 在 t=1.2 完成。服务端 fence 仍判断 1.2<1.8，因而可以提交新的 Fast / Visual / Response 快照。

重复 POST 不再续期、设备 quiesce 和显式 End 均有实际保护价值，但都不能补上首次接收时丢失的原始预算。即使没有跨主机时钟偏差，以上序列也成立。

准确影响是：B1 opt-in 生产协议可能在客户端已经拒绝该推理之后继续提交该 Session 状态并保留未交付票据，违背冻结的 timeout / fail-closed 语义。**没有证据表明已经污染其他 Session、改变真实 RoboCasa SR，或导致 Phase A 现行入口运行错误。**

### 2.3 保留的最小整改与验收要求

Codex 应继续原 B1-F1 的隔离候选整改：

- 第一次预测冻结唯一的截止权威；客户端、HTTP 接口和 Actor 使用同一不续期预算。可使用有证明的同主机时钟域，或显式且经过验证的跨域换算；不能直接假定不同主机 monotonic 值可比较。
- 服务端 commit fence 必须检查该原始截止权威。单纯新增“接收时再加 remaining_timeout”的字段并不天然正确，尤其在首次上传、重试和消息延迟期间。
- 通过实际生产 Client → Dispatcher → Actor 接口，使用可控时钟/传输/生成器，覆盖 delayed first arrival、首次 POST 丢失/重试、原始 deadline 后完成 generation、预算内成功、ACK 丢失和已提交 Response Replay。
- 原始 deadline 后未提交的推理必须保持旧 Fast / Visual / Response；资源清理继续遵守 End / quiescence / quarantine。重放、ACK 和重试不能再次执行 Local 更新或重新授予预算。
- 保留原有事务隔离、旧 B1 数值语义、Phase A 回归与源码冻结证据；新精确 Root + Child/Gitlink 和作者 CPU Evidence 再提交 GPT Code Gate。

## 3. B1-P1 — 撤销对既有 rollover 机制的违规判断

### 3.1 前序报告遗漏了明确规则

Formal Root、已批准 Phase A Root 和本次观察的 V3 使用同一 `AGENTS.md` Blob：

`3bdf04084453bf36b148dc0bdd9977048e449aa6`。

[AGENTS.md:45,51–59](https://github.com/wxwy/psm_wma/blob/9a3f88e55893491ea68d16b3f23680ae6941d106/AGENTS.md#L51) 明确区分：

- 普通写入 append-only；
- live Inbox 硬上限131072 bytes；
- 预计追加后超限时，必须逐字节归档旧文件，再重建带 archive / blob / head / Gate / formal pair / verdict / review 指针的新 live 文件；
- rollover 是 live Inbox 唯一允许的非 append-only replacement。

项目 [psm-execution-governance 技能](https://github.com/wxwy/psm_wma/blob/9a3f88e55893491ea68d16b3f23680ae6941d106/.codex/skills/psm-execution-governance/SKILL.md#L31)（Blob `222ed52898787dedbe065c9495ea9598f1a3f070`）有相同明确例外。

该规则实际由 [beb3f41a722169b63abb6e78561a909188cbc30a](https://github.com/wxwy/psm_wma/commit/beb3f41a722169b63abb6e78561a909188cbc30a) 于2026-09-03引入，早于本轮 Phase A/B。它不是此次候选为了规避审核而新写的规则。Git 提交作者身份不等同于 Owner 原始指令，本轮不作这样的授权推断。

### 3.2 本次数据保全符合已观察到的机制

| 对象 | 本轮确认 |
| --- | --- |
| pre-rollover Root | `9f66f53e77bb7324b56a7ac1973a5d645caed169` |
| pre-rollover live Inbox | 130996 bytes，Blob `d702c44dd68529e93a491c5353e866ab7be92a07` |
| Formal archive | `docs/collab/chatgpt/archive/CODEX_INBOX_20261029_PHASEB_APPROVED_9f66f53e.md`，与旧 live **同一 Blob** |
| Formal 新 live | Blob `a094c010814394a304bdae55784f1d4a42ceaf23`，1550 bytes / 1548字符，保留连续性 header 和当前 Gate 指针 |

旧 live 距硬上限仅76 bytes，本轮实质审核申请会超过该余量。归档同 Blob 证明旧历史逐字节保留；新 live 也记录了 Phase A source approval、Phase B design approval 和当前 B1 Code Gate 边界。

本次观察的 V3 live 文件本身也以2026-10-24 rollover continuity header 开始。这进一步说明仓库现行机制一直是“普通追加 + 明确阈值归档例外”。

### 3.3 更正决定与保留边界

前序报告引用一般 append-only 纪律后，进一步认定任何 rollover 都需额外 Owner 授权，并要求将归档全文恢复到 live 路径。该推断没有处理现行规则的明确例外。本轮没有取得足以证明更晚 Owner 原始指令已明确撤销这一例外的材料，不能沿用前序报告的转述作为独立违规证据。

**撤销 B1-P1 对本次 rollover 本身的 MEDIUM Finding，撤销“必须把完整历史恢复到 live Inbox”的整改要求。**这不是改写或放宽治理文件，也不声称发现了 Owner 逐字授权；它是纠正原审核的依据不足与规则遗漏。

后续候选晋级仍必须 fresh-read、无损保留当前 V3 与候选双方新增协作记录，保留 immutable archive 和正确连续性指针。rollover 不免除对并行协作记录的保护。这是既有文档合并纪律，不是本轮新增生产 Code Gate 阻断。

## 4. 作者证据与本轮验证边界

本轮直接核验作者原始证据和源码身份：

| 工件 | 实际 testcase / header | failure / error / skipped |
| --- | --- | --- |
| final/inference.xml | 67 / 67 | 0 / 0 / 0 |
| final/phase_a_regression.xml | 255 / 255 | 0 / 0 / 0 |
| final/junit.xml | 322 / 67+255 | 0 / 0 / 0 |

[gate.json](https://github.com/wxwy/psm_wma/blob/0f887a8c00f4514343e887da946136820e6cf16e/docs/collab/codex/evidence/2026-10-29_eval_v2_transactions_b1_author_cpu/final/gate.json) 精确绑定 Formal Root `9a3f88e5...`、Child 与 Gitlink `1bece52e...`；记录 source_unchanged、import origin、Ruff check/format、AST9 通过。审查团队从完整 Formal SHA 逐个读取 [formal_source_bindings.json](https://github.com/wxwy/psm_wma/blob/0f887a8c00f4514343e887da946136820e6cf16e/docs/collab/codex/evidence/2026-10-29_eval_v2_transactions_b1_author_cpu/formal_source_bindings.json) 的14个文件，14/14 Git Blob 匹配；Formal Root 的子模块入口确认为 `1bece52e...`。

[Root Formal 到候选 HEAD 的比较](https://github.com/wxwy/psm_wma/compare/9a3f88e55893491ea68d16b3f23680ae6941d106...0f887a8c00f4514343e887da946136820e6cf16e) 只有2笔 Evidence / ledger 提交，没有新的生产源码或 Gitlink 修改，不能视为修复了 B1-F1。

**322 PASS 是作者执行证据，本轮没有重跑这些测试。**本轮进行的是独立源码阅读、原始证据计数、Git Blob/版本核对及治理依据复核。真实 Local CPU Tensor 的作者测试与 Wan / diffusion / 网络边界的 doubles 应继续区分；没有新的 DS 独立验收、GPU、真实 RoboCasa/EGL、DCP、900 Episode 或成功率证据。

既有测试分别验证客户端本地预算和 Actor 本地预算，但没有验证带首次传输耗时的统一 Client→Dispatcher→Actor 原始预算。因此322 PASS 与 B1-F1 成立不矛盾。

## 5. 更新后的推进状态

| Gate | 当前有效结论 |
| --- | --- |
| Phase A 动态 Sim Slot | 原 exact pair 的 APPROVE_CODE 保持 |
| Phase B r1+r2+r3 设计 | 原 exact pair 的 APPROVE_DESIGN 保持 |
| Phase B 第一批 Transaction/B1 | **REQUEST_CHANGES；剩余阻断 B1-F1 MEDIUM** |
| B1-P1 | **WITHDRAWN；不要求反向恢复完整 live 历史** |
| Phase B 第二批 M>1 / true native B>1 | 本轮不准入，等待第一批新 pair Code Gate |
| DS 独立 CPU / native Canary / 900真实评测 | 本轮未执行，未获新的执行授权 |

下一步仍是 Codex 在隔离候选完成 B1-F1 最小整改、作者 CPU/negative/source Evidence、提交新的精确 Formal Root + Child/Gitlink，再交 GPT 增量 Code Gate。保持本轮范围，不修改训练/模型公式、Phase A Scheduler/Sim、Vendor、DCP、checkpoint 或历史 Core。

本更正为 docs-only。按用户本轮要求，详细 Review、canonical CODEX_INBOX 追加和 Issue #8 回复需发布并回读。发布提交仅为审核文档版本，不替代 Formal Implementation Pair。
