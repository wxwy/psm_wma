# GPT 独立 Code Gate — Eval V2 Phase B Increment 1: Session Transaction / Local Fast State / B=1 (2026-10-29)

## 0. Formal pair / 独立结论

**正式技术结论：`REQUEST_CHANGES`，作用范围仅为本次 Phase B 第一批生产源码 Code Gate。** 作者 CPU 322 passed 已核实，但不能抵消源码/冻结设计之间的协议偏差。本轮未发现需要修改训练、模型公式、VLA 策略、DCP、Sim 物理、Phase A Scheduler 的依据；**没有批准**第一批 Code Gate、Phase B 第二批、合并、DS 执行或 GPU/原生运行。

| 对象 | 精确 SHA |
| --- | --- |
| **Formal Implementation Root** | `9a3f88e55893491ea68d16b3f23680ae6941d106` |
| **Formal Child / Root Gitlink** | `1bece52ee419d12119c1b3d0b75e0ae5c5139ae9` |
| Root/Child 隔离候选 | `v3-eval-v2-transactions-b1-20261029` |
| 已批准 Phase A 源码基线 | Root `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |
| 已批准 Phase B 设计目标 | Design Root `b9c7cf1607ffd38f6e3349bdde0b35703a6d7684` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6`, `APPROVE_DESIGN` |
| 作者 handoff | `docs/collab/codex/reviews/2026-10-29_V3_EvalV2_PhaseB_Transaction_B1_author_handoff.md` |
| 作者 CPU Evidence | `docs/collab/codex/evidence/2026-10-29_eval_v2_transactions_b1_author_cpu/`，位于隔离候选的 Evidence/bookkeeping HEAD，**不等于 Formal Root** |

审核前 fresh GitHub 获取了 V3、Root/Child 候选以及两组 Formal commits。独立读取 Root Formal Git tree：`cosmos-framework` 为 mode `160000`，精确 `1bece52ee419d12119c1b3d0b75e0ae5c5139ae9`。比较已批准 Phase A 与本 Formal Pair：Root `scripts/`、`configs/`、`third_party/` 不变，Root 技术改动为 Gate 脚本、文档与 Child Gitlink；Child `d2c1bda6..1bece52e` 新增/修改 8 个 inference/service/test 文件。完整增量不是最后一笔仅 Gitlink 的提交。

冻结设计依据：`docs/build/PSM-WMA_V3_EvalV2_PhaseB_MultiSim_Transactional_Batch_Design_r1_2026-10-29.md` 以及 r2 Ticket/End、r3 post-ACK Replay addenda。先前 B-D1/B-D2/B-D3 在**设计 Gate**关闭，不代表实际实现的所有边界自动合格。

## 1. 源码中已独立确认的正向实现

1. **Unified state owner：** Child `inference/local_memory_state.py` 的 `MemorySnapshot` 统一持有 Fast / Visual / committed response 的只读 MappingProxy；`robocasa_local_memory_policy.py:215–253` 一次构建替换快照并统一 Session reset；`local_memory_online.py:255–286` 在 `paired` 时拒绝绕过视觉 owner 的 Fast-only commit/reset。
2. **真实 Local CPU 路径：** `local_memory_online.py:140–253` 保留模型拥有者扫描与 Fast State clone/detach，W0 新会话 lazy None；各 Session ID 独立，已完成 evidence 连续更新，未修改训练/优化器/生成模型公式。
3. **B1 model owner：** `robocasa_session_transactions.py:103–176,178–308,321–469` 约束 assignment epoch/run/manifest/slot/attempt/capability、pending ticket、单 executor、撤销/终结 Session、冻结响应重放。B1 `_execute` 序列为 prepare→generate→finite H16×raw15→serialize→device quiesce→lease/deadline/cancel fence→统一快照 commit；异常需 abort，未证明设备 drain 则 quarantine，不返回 End ACK。
4. **服务端 B1 显式光闸：** `scripts/action_policy_server_robocasa.py:614–679,683–872,1138–1175,1250–1265,1504–1560` 的 opt-in 预检要求 required Local、max sessions1、H16/raw15/state15/K4/local32、单卡单 rank、私有 owner token；禁止旧 `/predict` 绕过事务；`/predict_batch` 在 required Local 下仍拒绝，不虚称 native B>1 已实现。
5. **B1 客户端：** `robocasa_transaction_client.py:16–143` 实现 register / POST / poll / Delivery ACK / End，以及身份/shape/finite 校验；失败不直接被当作成功，重复服务端响应不会再跑新的 inference；没有冒称 Sim 环境 `env.step` 已集成。

上述正向审查结论仅支持**相关局部实现已存在**，不是 `APPROVE_CODE`。

## 2. 当前阻断性 Finding

### B1-F1 — MEDIUM — client/server 分别重置完整 timeout，违反冻结的单一端到端绝对 Deadline

- **源码位置**：Child `inference/robocasa_transaction_client.py:70–95` 在 `predict` 发起时计算 `deadline = client.clock() + client.timeout_s`，通过 `_call` 在重复 POST、排队响应和 GET 中扣减；而 **`inference/robocasa_session_transactions.py:259–308`** 在服务器第一次收到并接受 `submit` 时重新计算独立的 `ticket.deadline = server.clock() + server.timeout_s`（行301）。`_expire:245–249` 和 `_fence:376–379` 只核对这个新服务器截止时间。HTTP `/v2/inference` 的正式 payload schema 是 `{lease,payload}`，没有携带/换算客户端**原始**预算。
- **冻结 contract**：Phase B r1 设计 `docs/build/PSM-WMA_V3_EvalV2_PhaseB_MultiSim_Transactional_Batch_Design_r1_2026-10-29.md:57–60` 明确要求 **one absolute prediction deadline covers upload, queue, prepare, generation and response fetch; retries/polling do not reset it**。第一批实现 runbook `...PhaseB_Transaction_B1_Implementation_2026-10-29.md:22,35–38,56` 也宣称客户端使用原始绝对 deadline，服务端未共享该原始预算。
- **确定的可达时间序列（独立源码推导；未运行 GPU）**：设置两侧相同 timeout=1s。客户端从 t=0 发起，上传/连接重试耗费0.8s；服务端 t=0.8 才收到请求，于是授予截止时间 t=1.8；CPU fake generator/网络使服务器在 t=1.2 完成 generation+commit。客户端的绝对截止时间 t=1.0 已结束、不会接受该动作，但服务器 `_fence` 在 t=1.2 判断仍未到 t=1.8，**允许 Fast/Visual/Response 新提交**。若没有及时到达的 End/cancel，就会出现“客户端已因 deadline 失败、服务器仍在提交该已过期推理”的不一致。服务器端重复请求未续期并不能修复**第一次到达时新开户一个完整预算**的问题。
- **影响**：设备/事务资源晚于声明的端到端预算释放；失败 Episode 在没有及时 End 的情况下可能保留一个未被客户端消费的已提交 Fast State/响应。当前未发现会自动把该结果计入 RoboCasa SR；这是第一批源码的 deadline/fail-closed 协议阻断，而不是声称已发生真实物理错误。
- **可验收整改**：客户端从第一次 submit 开始冻结唯一剩余预算/截止权威，并能让服务器在第一次 POST 接收后保留同一预算**而不重新授权整段 timeout**（可选同主机时钟证明或明确协议化的预算换算，禁止仅使用未经验证的跨主机绝对 monotonic 值）。客户端重试不刷新服务端预算；服务端 `_fence` 必须在 commit 前检查这同一权威。新增 production API + 真实 Client/Dispatcher/Actor（可 fake clock/transport/generator）负例：上传/重试已消耗大部分预算时，过了原始 deadline 必须不 commit、保留旧 Fast/Visual/Response、清理走明确 End/Quarantine；同 deadline 内正常路径、ACK 丢失、旧 R0 Replay 不改变原始预算。无需 GPU、Wan 权重或修改 Phase A。

### B1-P1 — MEDIUM / 仅协作记录 — 隔离候选把 canonical Inbox 改写为归档指针，未遵守 append-only

- **源码/证据位置**：Root Formal `docs/collab/chatgpt/CODEX_INBOX.md:1–5`，以及 `docs/collab/chatgpt/archive/CODEX_INBOX_20261029_PHASEB_APPROVED_9f66f53e.md`。
- **独立 GitHub 回验**：在候选的 pre-rollover Root `9f66f53e77bb7324b56a7ac1973a5d645caed169`，live Inbox Git Blob 为 `d702c44dd68529e93a491c5353e866ab7be92a07`，完整字节数130996（GitHub UTF-8 字符计数111687）；当前 Formal Root 的同一路径变成 Blob `a094c010814394a304bdae55784f1d4a42ceaf23`，仅剩1548个字符的 rollover 指针及摘要。旧完整内容**确实逐字节完整地保存**于 archive，其 Blob 仍是 `d702c44d...`，但当前 `CODEX_INBOX.md` 并非原 live 文件的追加版。
- **违反要求**：项目 `审核规范与结论.txt` §17–18 规定 canonical `docs/collab/chatgpt/CODEX_INBOX.md` **append-only、不可覆盖旧协作记录**；将旧记录移出到 archive 后重置 live 路径，需要单独 Owner 授权，不能仅因“archive 尚在”就视作遵守 append-only。
- **范围精确说明**：此项**未损坏当前 V3 上的完整 Inbox**——Codex 只在隔离候选分支改了该文件；也不构成 Fast Weight 算法错误。但其作为待审 Formal Root 的不合规文件不能原样晋级。建议在 isolated candidate 修复 live Inbox 的 append-only 衔接并保留未经修改的 archive；追加任何最新 V3/其他协作条目须 fresh-read 后做无损合并，不覆盖合作方的已追加内容。只涉及文档/协作流程，不应以此为由重写生产推理逻辑。

## 3. 原始测试及源码绑定审核（不把 PASS 当作充分条件）

- **作者实际 raw CPU**：候选 Evidence `final/inference.xml` 为67 tests/0 fail/error/skip；`final/phase_a_regression.xml` 为255 tests/0 fail/error/skip；`final/gate.json` 与汇总 `final/junit.xml` 记录合计 **322 passed，0 fail/error/skip**。作者导出 `ruff check`、`ruff format --check`（0.12.7）及 AST9/源码前后冻结/导入来源均 PASS。
- **Git Blob**：审核者通过 GitHub `fetch_file` 从 Formal Root/Child 精确 SHA **直接核对14/14作者 `formal_source_bindings.json` 的 Git Blob**，包括所有新增生产关键文件、对应测试、Gate 脚本与 live/archived Inbox。Child 模型、训练、优化器、DCP、仿真、Vendor/原始评测源码没有本增量修改。
- **覆盖了的行为**：真实 CPU Local tensor、session A/B fast 非别名、W0 不变、generation/NaN/shape/serialization/atomic build fail、End 等待 model mutex、abort cleanup fail、Device sync fail、HTTP parser、模型 B1 对 legacy 的假 Wan 输出/真实 Local State parity、传输丢注册/推理/ACK/End 响应、旧 Frontier/changed payload 重放及 Phase A 255 regressions。
- **缺口**：目前未见 production 接口的 **client→server original-budget cross-boundary test**；`robocasa_transaction_client.py:test_client_retry_deadline_is_absolute_not_reset` 仅证明**客户端**的剩余时间递减，`robocasa_session_transactions_test.py:test_deadline_and_mutable_caller_input_cannot_change_owned_work` 仅证明**服务端**本地计时和 payload freeze。两者独立都通过，无法证明冻结的端到端单一 Deadline。
- 以上均为**作者执行**证据。GPT 没有在作者环境或真实 CUDA/Omni/RoboCasa 运行测试。作者模拟生成、直接 Dispatcher/HTTP Handler CPU doubles 不能代替以后独立 DS 或真实 Native Canary。

## 4. 处置与最小复审目标

**正式技术结论 `REQUEST_CHANGES`。** 当前阻断：**B1-F1 MEDIUM（生产协议/相关测试）**、**B1-P1 MEDIUM（隔离候选协作文档 append-only）**。Phase B 已批准 r1+r2+r3 设计本身无需重审；此前 B-D1/B-D2/B-D3 设计 Finding 均保持 CLOSED，Phase A 已批准代码也保持原 Exact Pair 有效。

**Codex 仅被允许**在同一隔离候选上围绕 B1-F1 修正 B1 客户端/服务器 Deadline authority 及必要负例；围绕 B1-P1 修复 live Inbox append-only 衔接。必须保留测试及现场 Evidence，不改训练、模型方程、Phase A Scheduler/Sim、Vendor、DCP、Checkpoint 或历史 Core。提交新精确 **Formal Root + Child/Gitlink SHA**、完整新增/回归作者 CPU/static/source Evidence，并停止等待 GPT 增量 Code Gate；不能把随后 Evidence/ledger SHA 充当 Implementation Formal Pair。

**仍不授权** Phase B 第二批代码、V3/Child 正式合并、DS_PRO 运行、真机/真实 RoboCasa/MuJoCo/EGL/GPU/Cosmos/DCP/900、训练/Checkpoint/Vendor/old431 操作。Phase A 原始 DS 独立 CPU Gate 仍待完成。

**正式落盘要求**：本详细 Review 与最新 V3 `docs/collab/chatgpt/CODEX_INBOX.md` append-only 记录必须均发布并回读，才构成正式 `REQUEST_CHANGES`。
