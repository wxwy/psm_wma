# ChatGPT 审核申请与交接 Ledger（canonical live）

## Rollover continuity（2026-09-12）

- 立即前序 archive：`docs/collab/chatgpt/archive/CODEX_INBOX_2026-09-12_051938_CST_c6be81e.md`
- archive Git blob SHA：`e85c8d136e2f8c67ed25f50003f985194a2cdd80`（原 live Inbox byte-for-byte 保存后复核一致）。
- pre-rollover root HEAD：`c6be81ef0b9b9937987c53bb84524131019b5d9a`。
- 当前 unresolved Gate：`G0-R09-B-TTT-V035-ROOT-PUBLICATION-FREEZE-DESIGN`。
- 当前 formal target：root=`c6be81ef0b9b9937987c53bb84524131019b5d9a`；child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`。
- 立即前序有效 verdict：ChatGPT 对 root=`de81c294019647e7678ef3f8da484c8d5bdbdba7`/child=`93a89ba61306d840a008813f62f26a34d54850f4` 为 `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_root_publication_freeze_design_v0.1.md:127)`，详见 `docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_root_publication_freeze_design_de81c29_93a89ba.md`；MM/Kimi 同 pair 为 approve。该旧 pair 不得用于当前 formal target。

## 审核申请：Root Publication Freeze Design v0.1 两阶段失败合同 remediation（2026-09-12）

- formal root SHA：`c6be81ef0b9b9937987c53bb84524131019b5d9a`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-ROOT-PUBLICATION-FREEZE-DESIGN`
- 对象：`docs/build/PSM-WMA_Local_Memory_v0.3.5_root_publication_freeze_design_v0.1.md`；根 `SESSION.md`/`TODO.md` 仅记录 Gate 观察与状态。

前轮 root=`de81c294019647e7678ef3f8da484c8d5bdbdba7`/child=`93a89ba61306d840a008813f62f26a34d54850f4` 的 final verdict 已齐：ChatGPT 给出唯一 HIGH（§6:127 的无条件零 mutation 与 §3 post-mutation rollback/`ROLLBACK_INCOMPLETE` 相矛盾），MM/Kimi approve。当前 commit 仅 docs-only 关闭该问题：将 §6 item 4 替换为与 §3 逐项一致的两阶段合同：

1. live transaction 前失败使 target/index/HEAD/authority 逐 byte/entry 不变；
2. live mutation 后失败必须以 snapshot rollback target/index，并逐 byte/entry 核验恢复才可返回 ordinary failure；
3. rollback 或 HEAD-state verification 不完整/不确定时，固定为 `ROLLBACK_INCOMPLETE` fail-stop，保留证据、禁止 authority/audit/runtime/自动重试，且不得声称零 mutation；
4. 任何失败都不得产生 accepted publication authority 或进入 read-only source audit。

验证仅为 `git diff --check` PASS；formal tree scope 为 `SESSION.md`、`TODO.md` 与该 design，Gitlink 从 parent 到 formal root 均为 child SHA。未创建 publication、未运行真实 root audit、未修改 child/runtime，未执行 checkpoint/data/cache I/O、DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。

请重点核验该验收项是否完全消除前轮 HIGH，且没有放宽 §3 事务边界或越权。请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_ROOT_PUBLICATION_FREEZE` 或 `REQUEST_CHANGES(file:line)`。即使批准，也仅允许下一份独立 docs-only source-evidence producer/closure design；不授权 publication、真实 audit、child、真实 I/O、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`，不回写 Inbox。

## 审核申请：Source-evidence Producer / Closure Design v0.1（2026-09-12）

- formal root SHA：`08b069e8b0cff7da7018b74d50e76f42fedd8514`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`
- 对象：`docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md`。

本轮只冻结 future source-evidence record/package/witness 的 producer 与 closure：固定 record path/six键 schema、formal-root tree 作为唯一来源、七键 package/witness 的外部非循环 binding，以及 isolated preflight、live transaction、rollback/`ROLLBACK_INCOMPLETE` 与 staged Gitlink/publication 禁令。未创建 record/publication，未读取真实 checkpoint/data/cache，未修改 child/runtime，未运行真实 I/O、GPU 或训练。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许独立 controlled-write execution design；不授权真实 source evidence collection、record 写入、publication、真实 audit、child、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Source-evidence Producer / Closure Design v0.1 authority remediation

- formal root SHA：`180038024ae2b4cc2e436bddafbcc01018087b0c`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

前轮 `08b069e8` final verdict 已齐：ChatGPT 3 HIGH，MM/Kimi approve。本轮只 docs-only 整改：固定独立 immutable collection design/execution/closure Gate 与 receipt；将 resolved config 绑定到 receipt 的 fixed artifact bytes/digest；定义外部独立 receipt root 的 post-commit package/witness closure receipt，禁止 caller/package/witness authority。无真实 collection/write/publication/I-O/child/GPU/训练。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE` 或 `REQUEST_CHANGES(file:line)`；formal verdict 仅写入 reviews。

## 审核申请：Derived-only witness remediation

- formal root SHA：`1d8f103e1dcf119ac8e90abbcbcde0eaced0bb95`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

前轮 `f3a423c` 三方结论已齐：ChatGPT 1 HIGH、MM/Kimi approve。本轮仅删除 §3 仍要求 witness Git blob OID 的残留文字，统一为 derived-only canonical bytes/SHA-256，禁止声明/保留 Git blob OID。无真实 I/O/GPU/训练。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE` 或 `REQUEST_CHANGES(file:line)`；formal verdict 仅写入 reviews。

## 审核申请：Source-evidence authority non-circular remediation

- formal root SHA：`f3a423c39020081b3ff34128328792af166ba09a`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

前轮 `1800380` 三方结论已齐：ChatGPT 2 HIGH、MM/Kimi approve。本轮仅 docs-only：collection authority 改为 collection root + 独立 receipt root，且 receipt root parent 精确绑定 collection root；post-commit witness 改为 derived-only，移除无 fixed path/tree ownership 的 blob OID。无真实 collection/write/publication/I-O/child/GPU/训练。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE` 或 `REQUEST_CHANGES(file:line)`；formal verdict 仅写入 reviews。

## 审核申请：Immutable Source Collection 收口设计 v0.1（2026-09-12）

- formal root SHA：`9b9b516132806369718361b0e1b7b54c15c0483d`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-DESIGN`
- 对象：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_design_v0.1.md`；formal tree 还只更新根 `SESSION.md`、`TODO.md`、`MEMORY/DECISIONS.md`。

本轮是 source-evidence 链的最后一个横向 provenance 设计：固定 collection root 的两个 canonical artifacts、parent 精确为 collection root 的独立 receipt root、exact paths/schemas/digests/Git object lookup 与 preflight/rollback fail-stop。它将后续真实工作收敛为一次独立的 collection/receipt closure Gate；该 Gate 关闭后路线固定为 `single-GPU smoke design → real optimizer/scaler → 1 batch GPU → 20--100 step TTT smoke`，不得再横向打开 checkpoint/publication/source-binding provenance Gate。

验证仅 `git diff --check` PASS 和文档契约关键词核验；未读取或写入 checkpoint、manifest、data、cache，未创建 collection/receipt，未修改 child/runtime，未运行 audit、DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。

请重点核验：collection/receipt 是否严格非循环、receipt parent/tree/blob 重算是否足以拒绝 authority drift、合并 execution/closure 是否没有遗漏 fail-closed 边界，以及“此处收口、随后 GPU smoke”的路线是否不牺牲现有 source identity 约束。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许申请单一 controlled collection/receipt closure execution Gate；不授权真实 collection、record 写入、publication、read-only audit、child、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`，不回写 Inbox。

## 审核申请：Immutable Source Collection 收口设计 v0.1 authority remediation（2026-09-12）

- formal root SHA：`885956cb6cddf57f04b3ed5097cf87a176779403`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-DESIGN`
- 对象：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_design_v0.1.md`；根 `SESSION.md`/`MEMORY/DECISIONS.md` 仅记录审核与路线边界。

前轮 `9b9b5161` 同 pair 三方最终结论已齐：ChatGPT `REQUEST_CHANGES`（3 HIGH），MM/Kimi approve。本轮只做 docs-only authority remediation：

1. 恢复已批准 source-evidence/publication 全部既有顺序；不再以当前 Gate 合并或删除 collection execution/closure、controlled-write、record/receipt、materializer 或 read-only audit。
2. 固定 `input descriptor → manifest → immutable_source_identifier → exact five-key checkpoint descriptor → collection artifact` 的 canonical raw-byte derivation；禁止 caller/environment/working-tree supplied digest。
3. 增加固定的 source input、manifest、checkpoint descriptor artifacts；receipt 对五个 collection artifacts 均绑定 exact path/schema/raw SHA-256/blob OID，并从 committed tree 逐项重算。
4. 将“尽快 GPU”限定为上述已批准 source-evidence/publication 闭环完成后，不得再新开闭环外 provenance Gate，下一设计才为 single-GPU smoke。

验证仅 `git diff --check` PASS、formal tree 与 Gitlink tree 核验；未读取或写入真实 checkpoint/data/cache，未创建 collection/receipt，未修改 child/runtime，未运行 audit、GPU 或训练。

请重点核验前轮 HIGH-1 的 progression preservation、HIGH-2 的 input authority derivation、HIGH-3 的 exact descriptor raw bytes/tree binding。请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION` 或 `REQUEST_CHANGES(file:line)`。即使批准，仍只允许按已批准顺序进入 collection execution design；不授权真实 collection/I-O、record/package/witness、publication/audit、child、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Immutable Source Collection Execution 设计 v0.1（2026-09-12）

- formal root SHA：`cd4cced4c0cd875b88f98af4fc1bbdad7cad8cf6`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`
- 对象：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_design_v0.1.md`。

本轮仅冻结 future real-source execution：`--source-root` 只作 transport、canonical selection request、regular-file/path-escape fail-closed、流式 byte hash、five fixed artifacts 的 isolated preflight 与 closure handoff。未读取或选择任何真实 source，未创建 collection/receipt，未触及 child、真实 I/O、GPU 或训练。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许下一份 docs-only collection closure design；不授权真实 source read/collection mutation/publication/audit/child/GPU/训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Immutable Source Collection Execution authority remediation（2026-09-12）

- formal root SHA：`c6336a54442c9117823d3ff30da1cba91d46833b`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`

前轮同 pair final 已齐：ChatGPT 3 HIGH，MM/Kimi approve。本轮 docs-only 修复：selection request 与 resolved 15-key config 必须在任何 source open 前与独立 reviewed authority 的 fixed path/raw bytes/SHA-256 逐 byte一致；source root 改为 root-directory FD，entry 从同一 regular-file FD 双读双 hash 且 fstat identity/size/mtime/ctime 一致。无真实 source I/O/mutation/GPU/训练。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_EXECUTION` 或 `REQUEST_CHANGES(file:line)`；正式 verdict 仅写入 reviews。

## 审核申请：Collection Execution authority-root remediation（2026-09-12）

- formal root SHA：`1b658bfbf7068a05dc6b409414ba2c98b7b03cc8`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`

前轮 ChatGPT 2 HIGH、MM/Kimi approve。本轮仅 docs：以 non-circular execution-authority root 固定 selection/config 的 exact root revision/path/blob/SHA tuple；transport 必须逐 byte匹配，禁止 generic record/caller authority。无真实 source I/O/GPU/训练。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_EXECUTION` 或 `REQUEST_CHANGES(file:line)`；formal verdict 仅写入 reviews。

## 审核申请：Immutable Source Collection Closure 设计 v0.1（2026-09-12）

- formal root SHA：`ee4ab4ab4ad6dd8b84aa354afc51ac47aa1c0474`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CLOSURE-DESIGN`
- 对象：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_closure_design_v0.1.md`；formal tree 仅含该设计、`SESSION.md`、`TODO.md`。

前置 execution design root `1b658bfbf7068a05dc6b409414ba2c98b7b03cc8`/同 child 已获三方 `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_EXECUTION`。本轮只新增 docs-only closure 合同：重验 authority-root tuple 与 candidate raw bytes derivation；冻结五-path collection root、单-path receipt root、receipt 精确 parent/tree lookup、snapshot/allowlist、rollback/`ROLLBACK_INCOMPLETE` 与下游 producer handoff。明确它不重新扫描 source、不创建真实 root/receipt，且仅完成既有 source-evidence/publication 闭环，不增加横向 provenance Gate；闭环后路线直接进入 single-GPU smoke design。

验证：根与新文件 `git diff --check` PASS；关键词/范围核验 PASS；formal tree Gitlink 仍为 `93a89ba61306d840a008813f62f26a34d54850f4`。未运行项目代码，未读取/写入真实 source、checkpoint、data、cache，未修改 child/runtime，未运行 GPU、torchrun、forward/backward、optimizer step、训练、评测、推理或 LIBERO4IN1。

请重点核验：authority tuple 和 preflight candidate 是否没有被误当 authority；two-root transaction/rollback 是否不产生部分 accepted authority；receipt parent/tree/blob re-derivation 是否足以拒绝 drift；以及既有 source-evidence/publication 顺序和 “闭环后直接 single-GPU smoke” 路线是否完整保留。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CLOSURE` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许申请独立 controlled collection/receipt execution design；不授权真实 source I/O、collection/receipt mutation、record/package/witness、publication/audit、child/runtime、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Immutable Source Collection Closure authority remediation（2026-09-12）

- formal root SHA：`5f6741ca0bfb61ca0e55fae95709c891fa5c5520`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CLOSURE-DESIGN`

前轮 `ee4ab4ab4ad6dd8b84aa354afc51ac47aa1c0474`/同 child 三方 final 已齐：ChatGPT `REQUEST_CHANGES` 两项 HIGH，MM/Kimi approve。本轮仅 docs-only 最小整改：

1. 候选 blobs 不再是 caller input；改为 approved same-executor source-read preflight 产生的不可序列化、single-use typed handoff，canonical content 绑定 authority tuple、ordered `(ordinal,byte_length,sha256)`、五 artifact fixed path/schema/raw SHA-256、config SHA 与 `candidate_handoff_sha256`。closure 实际 bytes 必须逐项等于 handoff，重启/跨进程/caller replacement 均 FAIL。
2. future 已有 controlled-execution approval 明示 target lineage tuple `(target_ref, expected_base_root_revision, expected_child_gitlink, authority_approval_formal_root_revision)`；source preflight 与 live mutation 前从 Git lookup 复验 target HEAD、base Gitlink、authority-root parent，collection parent 必须精确等于 expected base。

formal tree 仅更新 closure design 与 `SESSION.md`，Gitlink 不变；`git diff --check` 与关键词核验 PASS。未执行真实 source I/O、collection/receipt mutation、record/package/witness、publication/audit、child/runtime、GPU 或训练；没有新增闭环外 provenance Gate，闭环后仍直接进入 single-GPU smoke design。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CLOSURE` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许后续独立 controlled collection/receipt execution design；不授权真实操作。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Immutable Source Collection Controlled Execution 设计 v0.1（2026-09-12）

- formal root SHA：`47a05a526ed98ab477ffad7e7f8548be1c1d981c`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

前置 closure design root `5f6741ca0bfb61ca0e55fae95709c891fa5c5520`/同 child 已获三方批准。本轮新增 root docs-only runbook：冻结 real execution approval 必须回填的 authority/target lineage/source transport/isolated roots/evidence 字段、CPU-only/no-network command shape、same-activation handoff、two-root transaction、rollback 与受限下游。formal tree 仅该设计、`SESSION.md`、`TODO.md`，Gitlink 不变。

验证：`git diff --check` PASS；authority/handoff/lineage/rollback/GPU 禁止范围/下游路线关键词核验 PASS。未运行项目代码、真实 source I/O、collection mutation、source-evidence write、publication/audit、child/runtime、GPU、训练、评测、推理或 LIBERO4IN1。

请重点核验：runbook 是否完整继承已批准 authority、lineage 和 two-root contract；命令/approval 回填是否阻止 caller-selected inputs；failure/rollback 是否 fail-closed；以及它是否仅完成既有闭环而未新开 provenance Gate。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许独立 execution approval；不授权真实执行、source I/O、child、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Controlled Collection Execution v0.2 remediation（2026-09-12）

- formal root SHA：`a3b03c9baea7cd89cc38c591124cae7c3aaea1f0`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

前轮 47a05a5 三方 final 已齐：ChatGPT 3 HIGH、MM/Kimi approve。本轮只新增 v0.2 docs：冻结 executor source identity/allowlist 与 CPU/static witness；exact two-path authority-root materialization/tuple binding；canonical machine-readable PASS/FAIL evidence 字段。保留既有 source-evidence 闭环，未增加横向 Gate。无真实 I/O、mutation、child、GPU 或训练。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`；正式 verdict 仅写入 reviews。

## 审核申请：Execution Evidence exact-schema remediation（2026-09-12）

- formal root SHA：`fc0199178afd547e706f33e38588b50356a448e9`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

仅 docs-only：新增 evidence v0.1，精确冻结 canonical outer/nested key sets、PASS/FAIL status 分支、types、source-entry array、null-record、phase/failure code、固定 check ordering、evidence SHA-256 与路径排除规则，解决 a3b03c9 的唯一 evidence HIGH。无真实执行。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。

## 审核申请：Evidence branch typing remediation（2026-09-12）

- formal root SHA：`c8e05cff42b1a6d4a3a599d2c02f8cdbf648c43c`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

仅 docs：PASS/FAIL execution exact keys 分开；补齐 ordinal、byte_length、command argv、phase/failure code、delta paths、refs/paths、stage-aware nullability 类型合同，解决 eb658e0 的 evidence-only HIGH。无真实执行。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。

## 审核申请：Evidence null-record remediation（2026-09-12）

- formal root SHA：`eb658e0b4f7f006a20ba8a7aca9102d5cc64cb15`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

前轮 evidence review 的 collection/receipt FAIL null-record 键集矛盾已最小修复：collection 严格 4 键 null-record，receipt 严格 5 键 null-record；未到达 stage 用对应 null-record、空 source entries 和既定键 null 值，禁止伪造 digest。仅 docs，无真实执行。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。

## 审核申请：Evidence phase/reachability remediation（2026-09-12）

- formal root SHA：`7e633d1c6b4d74f661d9421c6ab7e75eda0cf203`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

前轮 `c8e05cff42b1a6d4a3a599d2c02f8cdbf648c43c`/同 child 三方 final 已齐：ChatGPT `REQUEST_CHANGES`（1 HIGH），MM/Kimi approve。本轮仅 docs-only 最小整改，修改 `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md`：

1. 冻结 FAIL `phase` 的有限 vocabulary，与 fixed check order 一一对应，并定义为首个未成功完成的检查；禁止任意 phase string 或由 failure_code 改写 nullability。
2. 为 source-read 冻结成功 entry 的严格 ordered prefix，为 candidate derivation 冻结六个 digest 的长度 `0..5` 成功前缀；失败项均不得伪造 digest。
3. 分离 collection 与 receipt 的 partial 边界；冻结 post-check 的 true-prefix/首个 false/null-suffix、push/publication 的固定 false 记录与 rollback 的完整 snapshot/`ROLLBACK_INCOMPLETE` 表示，使 auditor 可仅凭 phase 机械导出每个 nested field 的 concrete/null/empty 形态。

formal tree 仅改 evidence design、`SESSION.md`、`TODO.md`，Gitlink 不变。验证：`git diff --check` PASS。未执行项目代码，未读取或写入真实 source/checkpoint/data/cache，未进行 collection/receipt/source-evidence/publication mutation，未改 child/runtime，未运行 CUDA/GPU、torchrun、forward/backward、optimizer/scaler step、训练、评测、推理或 LIBERO4IN1。

请重点核验：phase vocabulary 是否与检查顺序完整一对一；source-read/candidate 的 partial prefix 是否唯一且无 placeholder digest；collection/receipt/post-check/rollback 的 nullability 是否可由 record 机械审计；以及本轮仍仅完成既有 source-evidence 链而不新增横向 provenance Gate。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许下一既有闭合步骤，不授权 executor implementation、真实 source I/O、collection/receipt/record/package/witness/publication/audit、child/runtime、GPU、训练、评测、推理或 LIBERO4IN1。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Evidence failure-lifecycle remediation（2026-09-12）

- formal root SHA：`9efae217d8c45b7afd651d52e3cb5b8cc63226f9`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

前轮 `7e633d1c6b4d74f661d9421c6ab7e75eda0cf203`/同 child 三方 final 已齐：ChatGPT `REQUEST_CHANGES`（3 evidence-only HIGH），MM/Kimi approve。本轮仅 docs-only 最小整改：

1. FAIL `phase` 保留 first primary failure identity；rollback 改为 live primary failure 后的独立 recovery outcome。collection、receipt、post-check、push/publication 的失败均必须带 concrete before/after snapshot SHA 与 verified witness；rollback 不完整时保持 primary phase 并 fail-stop 为 `ROLLBACK_INCOMPLETE`。pre-live phase 使用唯一 null rollback record。
2. `push_publication` FAIL 允许记录 observed `{pushed:boolean,published:boolean}`，并强制至少一个为 true；该 evidence 只能 FAIL，绝不授权下游。
3. 将 candidate construction 与 complete one-shot handoff 后的 candidate verification 分开：construction 可有 0..5 digest prefix 且 handoff null；verification failure 必须保留 complete candidates 与 complete handoff，用 phase 表示 binding/equality/single-use failure。

formal tree 仅改 evidence design、`SESSION.md`，Gitlink 不变；提交在远端 review notify 后安全 rebase，formal root 为上列 SHA。验证：`git diff --check` PASS。未执行项目代码，未读取/写入真实 source/checkpoint/data/cache，未 mutation collection/receipt/source-evidence/publication，未改 child/runtime，未运行 CUDA/GPU、torchrun、forward/backward、optimizer/scaler step、训练、评测、推理或 LIBERO4IN1。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许既有 source-evidence 闭合的下一步骤；不授权 executor implementation、真实 source I/O、collection/receipt/record/package/witness/publication/audit、child/runtime、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Evidence rollback-semantics remediation（2026-09-12）

- formal root SHA：`9a3f584f36254e00e9483c170f948cc6614b56fd`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

前轮 `9efae217d8c45b7afd651d52e3cb5b8cc63226f9`/同 child 三方 final 已齐：ChatGPT `REQUEST_CHANGES`（2 evidence-only HIGH），MM/Kimi approve。本轮仅 docs-only 最小整改：

1. PASS 和 pre-live FAIL 的 rollback 都冻结为 exact not-required null-record `{before_snapshot_sha256:null,after_snapshot_sha256:null,verified:null}`；不再以 `verified=true` 混淆“未执行”和“已恢复”。
2. live rollback 统一绑定 `target_snapshot_v1` 的 canonical JSON（target ref、HEAD、index tree、worktree tree），before/after SHA-256 必须由实际状态独立重算且精确相等才可 `verified=true`；缺失、不可重算或不等一律 `verified=false` + `ROLLBACK_INCOMPLETE`，但不覆盖 primary phase。

formal tree 仅改 evidence design、`SESSION.md`，Gitlink 不变；`git diff --check` PASS。未运行项目代码或真实 source/checkpoint/data/cache I/O，未 mutation collection/receipt/source-evidence/publication，未改 child/runtime，未运行 CUDA/GPU、torchrun、forward/backward、optimizer/scaler step、训练、评测、推理或 LIBERO4IN1。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许既有 source-evidence 收口的下一步骤；不授权 executor implementation、真实 source I/O、collection/receipt/record/package/witness/publication/audit、child/runtime、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Executor CPU/static implementation design（2026-09-12）

- formal root SHA：`c62bc80440dc2e78091c183b39cec96aa17e7f13`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

前置 controlled-execution design `2c73ad0b...` 已获 ChatGPT/MM/Kimi 同 SHA批准。本轮新增独立 docs-only v0.1：冻结唯一 executor `tools/psm_wma/immutable_source_collection.py` 与直接 stdlib test allowlist；temporary Git/FD fixtures 覆盖 authority/lineage drift、FD race、handoff、allowlists、retained snapshot、rollback/ROLLBACK_INCOMPLETE；只允许构造内存 synthetic evidence，禁止真实 source I/O、authority/collection/receipt/publication、child、GPU、训练。

验证：`git diff --check` PASS。请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`；即使批准也仅授权上述 root CPU/static implementation，不授权真实执行或 GPU/训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Evidence untracked-path snapshot remediation（2026-09-12）

- formal root SHA：`2c73ad0bf9f49d1dd13f0803046ac75f3cd9449c`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

前轮 `981f89873263f5c10fcfc8c30740bf5ce014eb2d`/同 child final 已齐：ChatGPT/MM approve，Kimi `REQUEST_CHANGES` 仅 1 个 evidence HIGH。最小 docs-only 修复：明确六个 allowlist path 中任何 worktree-present 但未 tracked 的状态（包括 porcelain `??`）直接 FAIL，不能写入 snapshot；并将它列入 porcelein/fstype 双重检查的 allowlist 内 FAIL 条件。由此 snapshot 只接受 absent 或 tracked regular 的唯一 record。

formal tree 仅 evidence design，Gitlink 不变；`git diff --check` PASS。未运行项目代码或真实 I/O，未修改 child、GPU、训练、评测、推理或 LIBERO4IN1。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许既有 source-evidence 收口的下一步骤；不授权 executor implementation、真实 source I/O、collection/receipt/record/package/witness/publication/audit、child/runtime、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Evidence canonical worktree-snapshot remediation（2026-09-12）

- formal root SHA：`981f89873263f5c10fcfc8c30740bf5ce014eb2d`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

前轮 `dee42d02a3e40b5da66c8ac96a8a4d5a66066665`/同 child 三方 final 已齐：ChatGPT `REQUEST_CHANGES`（2 evidence-only HIGH），MM/Kimi approve。本轮仅 docs-only 最小整改：早期 FAIL rollback 统一使用 five-key not-required null-record；worktree entries 冻结 repo-relative POSIX path、`100644|100755` mode、absent/regular exact record、raw-byte SHA，及 `git status --porcelain=v1 -z --untracked-files=all` + `find -P` 的 allowlist 外/类型拒绝语义，确保 audit 唯一重算 `worktree_sha256`。

formal tree 仅改 evidence design，Gitlink 不变；`git diff --check` PASS。未运行项目代码或真实 I/O，未修改 child、GPU、训练、评测、推理或 LIBERO4IN1。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许既有 source-evidence 收口的下一步骤；不授权 executor implementation、真实 source I/O、collection/receipt/record/package/witness/publication/audit、child/runtime、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。

## 审核申请：Evidence retained rollback-snapshot remediation（2026-09-12）

- formal root SHA：`dee42d02a3e40b5da66c8ac96a8a4d5a66066665`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

前轮 `9a3f584f36254e00e9483c170f948cc6614b56fd`/同 child 三方 final 已齐：ChatGPT `REQUEST_CHANGES`（2 evidence-only HIGH），MM/Kimi approve。本轮仅 docs-only 最小整改：

1. outer rollback record 现在保留 immutable canonical `before_snapshot` 与 `after_snapshot`，以及各自 SHA-256；审计可用 retained before object 与实际重取的 after object逐组件比对，不再只信任两个无来源 digest。
2. `target_snapshot_v1` exact schema 分离 target ref/revision、actual HEAD mode/symbolic-ref/revision、index tree，并将 worktree 固定为 five collection paths + receipt path 的 ordered allowlist entries；明确 absent/regular/拒绝 symlink-directory-extra-path、mode 与 raw SHA 的确定性派生。

formal tree 仅改 evidence design、`SESSION.md`，Gitlink 不变；`git diff --check` PASS。未运行项目代码或真实 source/checkpoint/data/cache I/O，未 mutation collection/receipt/source-evidence/publication，未改 child/runtime，未运行 CUDA/GPU、torchrun、forward/backward、optimizer/scaler step、训练、评测、推理或 LIBERO4IN1。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。即使批准，也只允许既有 source-evidence 收口的下一步骤；不授权 executor implementation、真实 source I/O、collection/receipt/record/package/witness/publication/audit、child/runtime、GPU 或训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。
# 审核申请：Executor implementation seam remediation（2026-09-12）

- formal root SHA：`ed824b2e06c27328f6639aba6b5c06e1de6bee73`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

前轮 `c62bc804...` 三方 final 已齐：ChatGPT `REQUEST_CHANGES` 两项 HIGH，MM/Kimi approve。本轮仅 docs-only 最小整改：具体 executor/test blob/raw-SHA/interpreter identity 延后绑定到文件存在后的 CPU/static implementation formal root/closure，禁止 request/ledger/handoff 替代；生产 executor 冻结一次 explicit DI seam（Git transaction、root-FD opener、evidence sink），CPU/static temporary fixture 与未来仅在独立批准后的 real inputs 复用同一未改源码、只替换依赖。

`git diff --check` PASS；未运行真实 source I/O、authority/collection/receipt/publication、child、GPU 或训练。请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`；不授权真实执行或 GPU/训练。ChatGPT formal verdict 请仅写入 `docs/collab/chatgpt/reviews/`。
# 审核申请：Executor interpreter-identity remediation（2026-09-12）

- formal root SHA：`97ed73442fc56aa57e4bae27028bc5ffef7897bc`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

前轮 `ed824b2e...` 三方 final 已齐：ChatGPT 对 interpreter authority 给出唯一 HIGH，MM/Kimi approve。本轮只分离 authority：executor/test path/blob/raw-SHA 从 CPU/static implementation tree 绑定；CPU/static 仅记录 test interpreter witness；future controlled execution approval 独立冻结 `{executable_path,executable_raw_sha256,version}`，由 executable bytes 与 `--version` 派生，禁止 caller default，任一 drift 在 source open 前 FAIL。

`git diff --check` PASS；无真实 source I/O、authority/collection/receipt/publication、child、GPU 或训练。请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。

## 审核申请：Executor CPU/static implementation（2026-09-12）

- formal root SHA：`fb9c5e04e811865247e2ed44072af59acc8b93c9`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

依批准 design 新增唯一 executor 与 stdlib tests：显式 DI 的 Git/root-FD/evidence sink、exact authority/five-path allowlist、同 FD re-read drift、single-use handoff、retained snapshot rollback/ROLLBACK_INCOMPLETE。仅内存 synthetic bytes。验证：5/5 unittest、py_compile、diff-check PASS。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`；不授权真实 source I/O、collection/receipt/publication、child、GPU 或训练。正式 verdict 请仅写入 reviews/。

## 审核申请：Executor CPU/static 累计整改复审（2026-09-12）

- formal root SHA：`1db0d539fd3d52fa7d521962a47204b578e0f94f`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`
- 冻结名册：ChatGPT（reviews/）、MM（mm:0.0）、Kimi（kimi:0.0）。

请相对首轮 `fb9c5e04e811865247e2ed44072af59acc8b93c9` 复审累计两文件整改，不只看最后一个 commit。证据为 formal tree 的 `tools/psm_wma/immutable_source_collection.py`、`tools/psm_wma/test_immutable_source_collection.py` 和 SESSION。累计加入 exact evidence ABI/phase/FAIL、authority parent/tree/blob/raw-byte/lineage 查询、单 handle stat/rewind 双 hash、五 artifact canonical derivation/one-shot handoff、隔离 preflight 与五加一 raw blob transaction/receipt relookup/rollback、approved-vs-observed identity 和最终 postchecks。本次又补 sink 拒绝后的恢复与内存记录深拷贝。

验证：根仓 `python3 -B -m unittest tools.psm_wma.test_immutable_source_collection -v` 26/26 PASS；`git diff --check` PASS。仅 CPU 标准库/内存 fixtures；没有真实 source/checkpoint/cache I/O、collection/receipt/publication、child 改动、GPU 或训练。

请逐一复核前轮 5 HIGH 的 acceptance，给出已关闭项与剩余 file:line，不能以 tests 数量替代生产算法覆盖。特别明确仍需审查的失败边界：sink 保存后抛异常时持久化状态未知；snapshot 无法重取时不能编造 exact live rollback witness。当前 sink 拒绝后恢复 ref/index/worktree 并抛 EVIDENCE_SINK_FAILED，恢复失败抛 ROLLBACK_INCOMPLETE，不宣称 FAIL 已落盘；这不构成新增 phase/schema。请判断是否满足现有冻结合同；如不满足，请在同一 implementation Gate 给最小整改，不新开横向 provenance Gate。真实适配器/运行未获批准，合成 tree/commit 标识不冒充生产证据。

请求唯一 final verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。不请求真实执行授权。ChatGPT 正式结果仅放 `docs/collab/chatgpt/reviews/`，写清完整 pair。等待三方同 pair final 后才合并整改，source-evidence 既有闭环后直接 single-GPU smoke。

## 审核申请：Executor 三项 HIGH 最小整改（2026-09-12）

- formal root SHA：`08afbed4e1843c23a1cc3542f0184a1898c1772c`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

前轮 `1db0d539fd3d52fa7d521962a47204b578e0f94f` 三方 final 在同轮回收：ChatGPT REQUEST_CHANGES（三项 HIGH）、MM/Kimi APPROVE，凭证见 SESSION。现仅原两工具文件整改：

1. HIGH-1：共用 `_authority_tree` 检查父树与 full committed tree 的 exact two-path delta；source open 前与 post-check 均执行，继承 blob/Gitlink 不得增删改。fixture 现在含真实语义的继承项，覆盖两路径新建/修改、继承项漂移、无变化不算 delta、late post-check。
2. HIGH-2：采用 review 允许的方案 (a)，EvidenceSink.emit 明确原子接口：异常保证无新增可见/持久记录。MemoryEvidenceSink 以 lock 隔离 staging 和读取，partial_write/after_write 注入均撤销新增记录，保留以前记录；测试验证事务回滚后没有 stale PASS。未来真实 sink 适配器必须独立满足该原子合同，内存测试不代表磁盘耐久性证据。
3. HIGH-3：不可重取/无效 after snapshot 均抛 RollbackUnavailable，稳定消息 ROLLBACK_INCOMPLETE，保留 primary_phase；仅非 authority 异常诊断，不 emit canonical evidence、不编造 after_snapshot、不自动重试/推进。可重取 snapshot 时保留既有 canonical FAIL witness。直接测试 restore 抛错/成功与 snapshot 抛错/畸形组合。

证据：formal tree 的 `tools/psm_wma/immutable_source_collection.py`、对应 unittest 和 SESSION；`python3 -B -m unittest tools.psm_wma.test_immutable_source_collection -v` 29/29 PASS；两文件临时目录 py_compile PASS；git diff --check PASS。无真实 source/checkpoint/cache I/O、collection/receipt/publication、child、GPU 或训练。

请求同 Gate final：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`，逐项确认三项 acceptance。请特别确认原子 sink 接口与 unavailable-snapshot 非 authority 诊断的实现语义；不新增横向 provenance Gate。ChatGPT 正式结果仅写 reviews/，请完整声明 formal root/child。三方同 pair final 到齐后才合并执行；本申请不请求真实执行权限。

## 审核申请：Executor tree-entry / selection-transport 两 HIGH 整改（2026-09-12）

- formal root SHA：`d281d6f3079602632000b1576c47fd4546de22e6`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

前轮 `08afbed4e1843c23a1cc3542f0184a1898c1772c` 三方 final 完整回收后，仅原两工具文件整改 ChatGPT 新两 HIGH（前轮三 HIGH 已关闭，不重开）：

1. tree_entries 改为 path→(Git mode,type,native OID)；authority pre/post 共用完整 entry 的父树 delta 比较；collection/receipt 所有 inherited preservation 同样比较完整 entry。固定 JSON artifacts 为 100644/blob，拒绝其 mode/type 漂移。CPU fixture 包含继承普通文件和 Gitlink；直接测试 OID 不变的 mode/type 漂移、五加一路径及继承项 mode-only mutation 的拒绝/回滚。
2. collect_synthetic 的 caller paths mapping 移除，替换必填 selection_request: bytes；executor 验证其与 bound authority selection blob 完全逐字节一致，随后仅从该 blob 导出 ordered entries，校验全部在 source open 前完成。测试同语义不同换行/缩进/Unicode escape 的字节漂移、parsed mapping 拒绝以及 exact bytes PASS。调用点检索仅原两工具文件，已全部迁移。

证据为 formal tree 的 `tools/psm_wma/immutable_source_collection.py`、对应 unittest、SESSION。标准库 unittest 32/32 PASS；两文件临时目录 py_compile PASS；git diff --check PASS。无真实 source/checkpoint/cache I/O、authority/collection/receipt/publication、child、GPU 或训练。

请求 final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`，完整声明 exact pair，逐项核验上述两 acceptance。不请求真实执行授权，不新增横向 provenance Gate；ChatGPT 正式结果仅写 reviews/。三方 final 齐后才合并整改或推进。

## 审核申请：Immutable Source Authority Root Materialization/Binding 设计 v0.1（2026-09-12）

- formal root SHA：`36b4e6bc3144a67d16d6c9684649e8939d181230`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-BINDING-DESIGN`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_binding_design_v0.1.md`

前置 CPU/static executor formal `d281d6f3079602632000b1576c47fd4546de22e6` 已获 ChatGPT/MM/Kimi 同 pair批准并关闭。本申请仅承接 controlled-execution v0.2 已冻结的 authority-root materialization/binding 步骤，不新增横向 provenance Gate。

请重点审核：selection/config exact canonical raw bytes 与 schema；materialization formal root 作为唯一 parent；相对 parent 恰好两 fixed `100644/blob` path 的 full `(mode,type,OID)` delta 与 Gitlink/继承项保持；authority payload无自引用；candidate 不推进 V2；固定 `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1` expected-zero CAS；独立 verifier 不信任自报 tuple；三方 review 明示绑定七字段 tuple，collection executor source-open 前重算全部字段与远端 ref。

批准仅允许下一步 root-only materializer/verifier CPU/static implementation design。当前不创建 selection/config JSON、authority commit/ref，不执行 source I/O、collection/receipt/source-evidence/publication、child、GPU或训练。请给唯一 final：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_MATERIALIZATION_BINDING_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`；完整声明 exact pair。ChatGPT 正式回复仅写 `docs/collab/chatgpt/reviews/`。

## 审核申请：Authority Root Binding v0.2 ABI 最小整改（2026-09-12）

- formal root SHA：`31819169c9430087f5e293cd1dce169ec055b371`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-BINDING-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_binding_design_v0.2.md`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

前轮 formal `36b4e6bc3144a67d16d6c9684649e8939d181230` 三方 final 齐：ChatGPT一项HIGH，MM/Kimi批准。v0.2仅按ChatGPT acceptance方案1整改：conceptual authority-root revision的唯一executor-facing serialization key冻结为现有实现的`root_revision`。exact seven-key mapping用于materializer候选、独立verifier、review/evidence binding及现有`_authority_tree()`/`_bound_source_inputs()`；serialized `authority_root_revision`、双键、tuple、caller rename或adapter全部pre-source FAIL。v0.1其余parent/tree/ref/canonical bytes/边界完整继承。

请确认该HIGH关闭并给唯一 final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_MATERIALIZATION_BINDING_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`，完整声明exact pair。本申请仍只请求进入root CPU/static implementation design，不授权真实materialization/source I/O/collection/publication/child/GPU/训练；不新增横向Gate。

## 审核申请：Authority Root CPU/static Implementation 设计 v0.1（2026-09-12）

- formal root SHA：`c61f32f3a99688043f2dfdb3d69480e11b1811dd`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_cpu_static_implementation_design_v0.1.md`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

前置binding v0.2 formal `31819169c9430087f5e293cd1dce169ec055b371` 已获三方批准。本设计只冻结下一步root-only两文件实现：`immutable_source_authority_root.py`及test；单一DI算法`prepare_candidate→verify_candidate→publish_candidate`；full tree entry、detached single-parent candidate、fixed-ref expected-zero CAS、post-CAS relookup/exact rollback、same-activation one-shot capability、`ROLLBACK_INCOMPLETE`。exact seven-key `root_revision` binding必须直接进入现collection executor真实authority seam，不能只比较常量。

请逐项审核allowlist/复用边界、DI protocol是否足以支持future real adapter、canonical schema/parent/delta、candidate不信任、CAS/rollback、capability lifecycle、executor ABI正反例及CPU matrix。请求唯一final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`，完整声明exact pair。批准仅授权root CPU/static synthetic implementation；不创建真实JSON/authority commit/ref，不访问真实source/remote，不执行collection/publication/child/GPU/训练。

## 审核申请：Authority Root CPU/static Implementation 设计 v0.2（2026-09-12）

- formal root SHA：`ee0de157d337bc85bf3d8d1c9e4957c31aa03c07`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_cpu_static_implementation_design_v0.2.md`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

前轮 formal `c61f32f3a99688043f2dfdb3d69480e11b1811dd` 三方 final 已齐：ChatGPT 两项 HIGH `REQUEST_CHANGES`，MM/Kimi批准。v0.2逐项整改：实现allowlist扩为authority-root tool/test与现collection executor/test四文件；实际 `_bound_source_inputs()` / `collect_synthetic()` 在source-open前直接重查不可覆盖fixed ref的local+remote观察，任一absent/wrong/disagree/error零mutation拒绝；publication冻结local→remote expected-zero CAS与逐端点activation-owned witness；rollback冻结remote→local、仅exact-candidate→absent条件删除、foreign/unreadable不删除、fresh两端观察与统一`ROLLBACK_INCOMPLETE`；CPU matrix注入首CAS后、CAS/postcheck间、rollback中竞态及单端冲突。

请确认两项 HIGH 均关闭，并给唯一 final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`，完整声明exact pair。批准仅授权上述四文件synthetic CPU/static实现及标准库测试；不授权真实JSON/authority commit/ref、source/remote I/O、collection/publication、child、GPU或训练。

## 审核申请：Authority Root synthetic CPU/static Implementation（2026-09-12）

- formal root SHA：`8cd1103deecc0720b7168e9e2b86b576e818b2bd`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`
- 设计 authority：v0.2 formal `ee0de157d337bc85bf3d8d1c9e4957c31aa03c07`，已获 ChatGPT/MM/Kimi 同pair批准。
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

请逐文件审核四文件allowlist实现：新authority-root模块/test；现collection executor/test的fixed-ref扩展。重点核验真实`_bound_source_inputs()`/`collect_synthetic()`是否在source-open前直接要求local+remote fixed ref精确等于七键`root_revision`；三阶段candidate独立复验、只读one-shot capability；local→remote expected-zero CAS；逐endpoint activation-owned witness；remote→local且仅candidate→absent条件回滚；foreign/unreadable/竞争状态不删除并`ROLLBACK_INCOMPLETE`。证据：stdlib unittest 41/41 PASS；两个新文件Ruff PASS；四文件py_compile及diff-check PASS。全部fixture为内存synthetic，无真实I/O/ref/remote/GPU/训练。

请求唯一 final `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`，完整声明exact pair。批准只关闭synthetic implementation，不授权真实JSON/authority commit/ref/source/remote、collection/publication、child、GPU或训练。

## 审核申请：Authority Root synthetic implementation remediation（2026-09-12）

- formal root SHA：`fce040f645e2427d11d9cd9026adc2f0e8004bda`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`
- 前轮 review：`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_authority_root_cpu_static_implementation_8cd1103_93a89ba.md`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

前轮三方final齐：ChatGPT 4 blockers、MM/Kimi批准。本提交逐项整改：`parents()` tuple与共享结构validator在prepare返回前和verify内分别证明exact single parent/full-tree/fixed blobs/inherited entries；formal-root Gitlink直接核验完整`160000/commit/OID` entry；pre/post/rollback两端观察各自执行后聚合，禁止短路；request/candidate/publication witness同样拒绝copy/deepcopy/pickle；新增verifier mapping经synthetic publication state直入真实`collect_synthetic()`的PASS，以及派生alias/缺键/额外键pre-source拒绝。新增zero/two parent、Gitlink missing/mode/type/OID、mode drift与最终双端read event测试。

证据：stdlib unittest 46/46 PASS；两个新文件Ruff PASS；四文件py_compile与diff-check PASS。请求唯一 final `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`，完整声明exact pair。仍不授权真实I/O/ref/remote/GPU/训练。

## 审核申请：Authority Root synthetic implementation remediation 2（2026-09-12）

- formal root SHA：`ae52cb313cfafda4eedad600501030f4dc01297c`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

前轮formal `fce040f...`三方final齐：ChatGPT 1 HIGH+1 MEDIUM、MM/Kimi批准。本次shared independent validator明确拒绝formal parent预含任一fixed path，并以两path table-driven adversarial candidate测试；collection暴露最小公共canonical/tree/blob/digest helper surface，authority不再跨模块导入private helper；补alias-only verifier→real executor负例。既有结构、ref、rollback与typed边界合同不变。

证据：unittest 47/47 PASS；新文件Ruff、四文件py_compile、diff-check PASS。请求完整pair唯一final `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`。不授权真实I/O/ref/remote/GPU/训练。
