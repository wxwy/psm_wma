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

## 审核申请：Authority Root consumer-side remediation 3（2026-09-12）

- formal root SHA：`0b18620f84959bf25379f3c227b796edc1097efd`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

前轮formal `ae52cb3...`三方final齐：ChatGPT 1 HIGH、MM/Kimi批准。本次真实collection `GitTransaction`增加exact `commit_parents()->tuple`，`_authority_tree()`要求精确单parent等于approval formal root并在delta前拒绝parent预含任一fixed path；direct `collect_synthetic()` adversarial tests覆盖selection/config预含、zero/two parent、Unopened sentinel与零commit。47/47 PASS；新文件Ruff、四文件py_compile、diff-check PASS。

请求完整pair唯一final `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`。不授权真实I/O/ref/remote/GPU/训练。

## 审核申请：Authority Root Real Adapter / Execution Request 设计 v0.1（2026-09-12）

- formal root SHA：`7c17c90a3b25182436fef89fbe063de9fcf1d67e`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.1.md`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

synthetic implementation formal `0b18620f...`已三方关闭。当前无真实Git adapter/CLI，故设计冻结最短两阶段：两文件real adapter CPU/static implementation closure；随后立即以formal-tree tool identity发一次exact materialization execution request，不增加其他横向Gate。已冻结8-entry selection与15-key config exact canonical raw bytes/SHA/blob OID；adapter必须复用既有三阶段算法、absolute identity-bound Git argv、temporary index/plumbing、expected-zero fixed-ref与ownership rollback。当前仅请求adapter CPU/static implementation授权，不请求真实JSON/candidate/ref/source/remote/GPU/训练。

请求唯一final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`，完整声明exact pair。

## 审核申请：Authority Root Real Adapter设计 v0.2整改（2026-09-12）

- formal root SHA：`dd0ecdf19e3413be4f8dad5e7b069e106f88e8ad`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.2.md`
- 冻结名册：ChatGPT reviews/、MM mm:0.0、Kimi kimi:0.0。

v0.1三方意见齐并均要求更正blob OID；ChatGPT另要求CAS/evidence合同。v0.2更正selection/config OID为`9f03614b...`/`89b12047...`，测试须raw→SHA/OID并由temporary native `hash-object`交叉验证；remote仅允许fixed-ref per-ref exact`--force-with-lease`，creation expected absent、rollback expected candidate，禁止unconditional force/普通overwrite/delete-recreate；冻结exact transaction evidence v1的十个顶层section、phase/reachability/ownership/pre-post observations/rollback及原子writer故障矩阵。

请求完整pair唯一final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。仅授权两文件temporary CPU/static adapter实现，不授权真实JSON/candidate/ref/origin/source/GPU/训练。

## 审核申请：Authority Root Real Adapter设计 v0.3整改（2026-09-12）

- formal root SHA：`c4133389f856f5ab7a5ad01923f71c0c3892ce09`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.3.md`
- 证据：前轮 ChatGPT 2 HIGH review=`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_execution_request_design_dd0ecdf_93a89ba.md`；`git diff --cached --check` PASS。
- 冻结名册：ChatGPT reviews/、MM `mm:0.0`、Kimi `kimi:0.0`。

v0.3 仅整改 evidence transaction 合同：allowlist从两文件扩至 authority module/direct test + adapter/direct test 四文件；future `publish_candidate(..., finalizer=...)`把 writer failure 保持在已有 remote→local ownership-aware rollback 内，opaque witness/commit capability禁止构造、复制与重放；冻结 execution/observation/authority/candidate nested ABI、first-failure nullability、ordinary FAIL/ROLLBACK_INCOMPLETE/PASS terminal invariants、pending-guard accepted-evidence commit及清理规则。v0.2 的 raw OID、per-ref exact-old remote lease 与禁止项不变。

请求完整pair唯一final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。仅授权四文件的 temporary CPU/static 实现及本地 bare-remote tests；不授权真实JSON/candidate/ref/origin/source/collection/GPU/训练。

## 审核申请：Authority Root Real Adapter设计 v0.4整改（2026-09-12）

- formal root SHA：`be833f807e50a9a1d433c8fdf7f341e7ad3544f6`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.4.md`
- 证据：前轮 ChatGPT review=`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_execution_request_design_c413338_93a89ba.md`；`git diff --cached --check` PASS。
- 冻结名册：ChatGPT reviews/、MM `mm:0.0`、Kimi `kimi:0.0`。

v0.4 把guard成功`unlink`定义为 writer visibility、sealed EvidenceCommit与authority transaction共同的唯一PASS linearization；所有fallible fsync/re-read/validator均留在guard存在的pre-commit阶段，unlink后禁止异常回流rollback。failure改为exact primary/rollback双字段；rollback-required仅允许verified authority/candidate与concrete pre-observation，并按四个primary origin冻结ownership与终态。

请求完整pair唯一final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。仅授权四文件temporary CPU/static implementation/tests；不授权真实JSON/candidate/ref/origin/source/collection/GPU/训练。

## 审核申请：Authority Root Real Adapter设计 v0.5整改（2026-09-12）

- formal root SHA：`066de7052310dc889074632981cc3cdec880ab41`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.5.md`
- 证据：前轮 ChatGPT exact review=`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_execution_request_design_be833f8_93a89ba.md`；该 pair 三方 final 已齐（ChatGPT 2 HIGH，MM/Kimi批准）；`git diff --check` PASS。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

v0.5逐项整改前轮两项 HIGH。第一项：authority在finalizer前创建并预验证同activation的opaque `PublicationWitness`/`EvidenceCommit`；所有identity/type/token/replay/seal检查在guard存在时完成；`consume_by_unlink()`是唯一one-shot消费操作；authority仅作total state dispatch，unlink后任何callback-return/report异常统一为preserve-refs `POST_COMMIT_CAPABILITY_VIOLATION`，绝不回到rollback。第二项：将`rollback.required`严格定义为owned delete需求，并新增`entered`表达无owned的恢复/终态证明；完整冻结`pre_publication`、`local_cas`、`remote_cas`、`post_publication`、`binding_reverify`、`evidence_write`的真实可达矩阵，收紧post_publication为local/remote六bit均true。新增针对callback坏返回、foreign/unreadable、lost-race与impossible evidence的CPU/static验收。

请核验两项 HIGH 是否关闭，并给完整 exact pair 的唯一 final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。本申请仅请求 v0.3 四个root文件的temporary CPU/static implementation及temporary local bare-remote tests；不授权真实JSON/candidate/ref/origin/source/collection、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测或推理。

## 审核申请：Authority Root Real Adapter设计 v0.6整改（2026-09-12）

- formal root SHA：`944c1305bcaef818e178c781b5cf2ce8aebbc9a8`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.6.md`
- 证据：前轮 ChatGPT exact review=`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_execution_request_design_066de70_93a89ba.md`；该 pair 三方 final 已齐（ChatGPT 1 HIGH，MM/Kimi批准）；`git diff --cached --check` PASS。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

v0.6只关闭“post-unlink finalizer exception”遗漏。authority把整个finalizer调用（normal return与`BaseException`）捕获为outcome，并在既有rollback boundary内仅按exact issued `EvidenceCommit.state`分流：non-committed outcome仍pre-commit并rollback；committed outcome绝不rollback。committed后的exception在boundary外变为保留cause的`PostCommitFinalizerError`；normal return值统一被忽略、返回exact witness，因而不是违约。新增post-unlink普通/custom/BaseException、ordinary return及pre-commit对照的direct CPU/static spy验收。

请核验前轮 1 HIGH 是否关闭，并给完整 exact pair 的唯一 final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。本申请仅请求 v0.3 四个root文件的temporary CPU/static implementation及temporary local bare-remote tests；不授权真实JSON/candidate/ref/origin/source/collection、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测或推理。

## 审核申请：Authority Root Real Adapter CPU/static implementation（2026-09-12）

- formal root SHA：`166e5f5f6470bcc7c77f8c3326914e1281e922b6`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 设计依据：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.3.md`至`v0.6.md`。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。
- 实现范围：仅`tools/psm_wma/immutable_source_authority_root.py`及其test、`tools/psm_wma/materialize_immutable_source_authority_root.py`及其test；只用temporary directory/local bare remote CPU/static fixture。formal tree不含child Gitlink变化。
- 验收：两模块unittest=36/36 PASS；`py_compile`、`git diff --check` PASS。覆盖one-shot commit、pre/post-unlink outcome、exact CAS lease/foreign保留、Evidence v1 ABI/digest/failure rows、guard/cleanup fail-stop。

请求完整 exact pair 唯一 final `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`。仅审CPU/static implementation；不授权真实JSON/candidate/ref/origin/source/collection/child/runtime/checkpoint/data/cache、CUDA/GPU、训练、评测或推理。

## 审核申请：Authority Root Real Adapter CPU/static implementation remediation（2026-09-12）

- formal root SHA：`64db875135addac644c96d0028ab5c08a1dddf54`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮结论：`166e5f5f6470bcc7c77f8c3326914e1281e922b6`/同child三方final已齐；ChatGPT review=`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_166e5f5_93a89ba.md`提出4 HIGH，Kimi提出F401，MM批准。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

整改范围仍严格限于批准的四个root文件及正常记账。新增实际CLI argv surface：两个regular FD的raw-SHA与canonical preflight，formal-root完整tree/Gitlink、adapter/authority module blob+raw、Python/Git absolute path+raw+version、双端fixed ref absent均在candidate object/ref mutation前验证；随后唯一调用既有`prepare_candidate→verify_candidate→publish_candidate`。CAS要求本次Git命令成功和fresh post-observation；remote还要求`--porcelain`中有本次`*`创建或`-`删除，从而拒绝same-candidate up-to-date与concurrent-delete误归因。commit-tree使用显式冻结author/committer/date/message；Evidence v1拒绝primary=`rollback`与ordinary FAIL secondary rollback。

证据：`python -m unittest tools.psm_wma.test_immutable_source_authority_root tools.psm_wma.test_materialize_immutable_source_authority_root`=`44/44 PASS`；四文件`py_compile` PASS；Ruff=`All checks passed!`；`git diff --check` PASS。CLI tests仅使用temporary working repository与local bare remote，覆盖CLI PASS、raw/canonical/formal-root/Gitlink/module/tool/ref drift pre-mutation rejection、local/remote same-candidate create与concurrent-delete races、冻结metadata不受ambient Git config/time影响。

请求完整exact pair唯一final `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`。本申请不授权真实JSON/candidate/ref/origin/source/collection、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root Real Adapter CPU/static evidence-transaction remediation（2026-09-12）

- formal root SHA：`2f9fd4bcaec0fd0ea0c6302aa69910e24ce9e378`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮 ChatGPT review：`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_64db875_93a89ba.md`；同pair三方final已齐（ChatGPT 4 HIGH、MM/Kimi批准）。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

本整改仍限四个批准root文件及temporary directory/local bare-remote CPU/static tests。CLI接受absolute fresh `--evidence-path`并冻结actual argv digest；其finalizer在同一个`publish_candidate` transaction中以实际identity/authority/candidate/ref witness构造PASS record，调用`write_pending_evidence()`，所以成功CLI现在断言accepted evidence与两端candidate refs同时存在。`EvidenceCommit`不再接受任意callable：它绑定同一opaque witness activation、实际pending guard、evidence path与evidence digest，并且仅authority-owned `os.unlink(guard)`能使`committed=True`。所有publication-try ordinary FAIL（包括无owned的pre-publication/local-CAS）要求entered+complete与双端absent final proof。preflight还绑定实际`sys.executable`、adapter `__file__`与authority module `__file__`；真实临时CLI在copy的formal tree子进程运行，直接调用当前加载模块而只提供pristine copy会在candidate/ref mutation前拒绝。

## 审核申请：Authority Root Real Adapter HIGH-4 failure-evidence remediation（2026-09-12）

- formal root SHA：`2249fdd3377f82d037d85b7f3ed854cf90472303`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮 ChatGPT review：`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_2f9fd4b_93a89ba.md`；同pair三方 final 已齐，ChatGPT=`REQUEST_CHANGES`（4 HIGH），MM/Kimi=`APPROVE_TO_CLOSE`。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

请只审核 formal tree 的四个批准 tooling/test 文件相对 `2f9fd4bcaec0fd0ea0c6302aa69910e24ce9e378` 的累计整改。HIGH-1--3 已在前序提交完成；本次收口 HIGH-4：publication/rollback failure witness 逐端点保留 `value` 与 read-error，serializer 规范化为 exact `absent`/`revision`/`unreadable` evidence observation；`pre_publication` 不再不可序列化，post/final 读取失败也不再被伪装为 absent。temporary local-bare-remote CLI 子进程覆盖 pre-publication、local/remote CAS、post-publication、binding reverify、evidence-write 及 persistent post-read 触发的 `ROLLBACK_INCOMPLETE`，全部经 `verify_evidence_path()`复验。验收：root unittest=53/53、py_compile、Ruff、diff-check PASS。范围严格限 root CPU/static temporary fixtures；禁止真实 source/selection/config/candidate/ref/origin/collection/evidence、child、GPU、模型/数据/训练/评测/推理。请给出同一完整 pair 的最终 `APPROVE_TO_CLOSE...` 或 `REQUEST_CHANGES`（含 `file:line`）。

证据：`python -m unittest tools.psm_wma.test_immutable_source_authority_root tools.psm_wma.test_materialize_immutable_source_authority_root`=`47/47 PASS`；四文件`py_compile` PASS；Ruff=`All checks passed!`；`git diff --check` PASS。无真实JSON/candidate/ref/origin/source/collection、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

请求该exact pair唯一final `APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`。

## 审核申请更正：Authority Root Real Adapter HIGH-4 failure-evidence remediation（2026-09-12）

- 更正原因：上一申请把 formal root 错写为不存在的`2249fdd3377f82d037d85b7f3ed854cf90472303`。该错误 pair 的 ChatGPT/MM/Kimi final 均为`REQUEST_CHANGES`，仅要求准确重锚；旧条目保持 append-only。
- formal root SHA：`2249fdd3f7503d7e4c2be89bdd102cb4daf5aa49`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

这是同一已推送、可解析 implementation commit 的新 exact-pair 申请，非对错误 SHA verdict 的替换或继承。请相对`2f9fd4bcaec0fd0ea0c6302aa69910e24ce9e378`审核 formal tree 四个已批准 tooling/test 文件的累计整改：HIGH-1--3已在前序提交完成；HIGH-4补齐每 endpoint value/read-error witness，serializer输出exact `absent`/`revision`/`unreadable`，并让`pre_publication`、post/final read-error 可落盘。temporary local-bare-remote CLI 子进程覆盖pre/local/remote/post/binding/evidence失败及 persistent post-read 的`ROLLBACK_INCOMPLETE`，均由`verify_evidence_path()`复验；unittest=53/53、py_compile、Ruff、diff-check PASS。仅 root CPU/static temporary fixtures；不授权真实 source/selection/config/candidate/ref/origin/collection/evidence、child、GPU、模型/数据/训练/评测/推理。请对这个完整 pair 给出新的唯一最终`APPROVE_TO_CLOSE...`或`REQUEST_CHANGES(file:line)`。

## 审核申请：Authority Root Real Adapter activation/ref-race/FD-cleanup remediation（2026-09-12）

- formal root SHA：`8879742c4ea99bf2676903d4085a77aee91cd4e1`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮精确审核：`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_2249fdd_93a89ba.md`；同pair三方final已齐（ChatGPT=`REQUEST_CHANGES`四项HIGH，Kimi=`REQUEST_CHANGES`，MM=`APPROVE_TO_CLOSE`）。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

请相对`2f9fd4bcaec0fd0ea0c6302aa69910e24ce9e378`审核四个批准root tooling/test文件的累计整改。H1：witness/commit capability只在同一activation内有效，stale retained object不能用于下一transaction。H2：guard unlink前fresh观察local/remote fixed refs；任一endpoint drift会拒绝提交且保留foreign ref。H3：guard/tmp/final的cleanup由创建FD的dev/inode身份绑定，path被外来替换即fail-stop且绝不unlink/overwrite foreign bytes，含实际CLI failure/PASS writer回归。H4：verify失败保留prepared candidate、pre-input request error产生preflight Evidence-v1、cleanup不确定产生可验证`ROLLBACK_INCOMPLETE`/`EVIDENCE_CLEANUP_INCOMPLETE`。验证：temporary directory/local bare remote CPU/static unittest=`58/58 PASS`；`py_compile`、Ruff、限定任务文件`git diff --check` PASS。formal tree Gitlink不变。

请求完整exact pair唯一最终`APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。范围只限四个root工具/测试的temporary CPU/static fixture；不授权真实source/selection/config/candidate/ref/origin/collection/evidence操作、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root Real Adapter identity-safe unlink remediation（2026-09-12）

- formal root SHA：`153bf17b3755b20296e69d2f5790becd8520875d`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮 exact reviews：ChatGPT=`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_8879742_93a89ba.md`（1 HIGH）；Kimi同pair=`REQUEST_CHANGES`（seal后altered-record witness）；MM同pair=`APPROVE_TO_CLOSE`。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

请仅审相对`8879742c4ea99bf2676903d4085a77aee91cd4e1`的四个批准root tooling/test文件累计整改。原先identity-check后直接pathname unlink改为`_unlink_exact_regular()`：先验证public regular-file dev/inode，再原子rename至同父目录下mode-0700私有parking目录；只在private pathname重验相同identity后删除。handoff边界若发现foreign replacement，则原样restore并fail-stop。该原语同时用于`EvidenceCommit.consume_by_unlink()`的PASS guard和adapter `_unlink_owned()`的guard/tmp/final cleanup。新增direct adversarial回归：guard handoff边界foreign replacement保留foreign并rollback；adapter cleanup handoff边界foreign保留；seal后改写evidence bytes则consume拒绝、guard与篡改record保留。temporary CPU/static unittest=`61/61 PASS`，`py_compile`、Ruff、`git diff --check` PASS；formal Gitlink不变。

请求完整exact pair唯一最终`APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。仅授权四个root工具/测试的temporary directory/local bare remote CPU/static fixture；不授权真实source/selection/config/candidate/ref/origin/collection/evidence、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root Real Adapter PASS-linearization remediation（2026-09-12）

- formal root SHA：`e1d5e1115023caa0e18d80108f218a9f5d2382b6`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮 exact review：`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_153bf17_93a89ba.md`（1 HIGH PASS linearization）；Kimi/MM同pair批准。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

请仅审相对`153bf17b3755b20296e69d2f5790becd8520875d`的批准root files。为关闭public guard handoff可见性，`EvidenceCommit.consume_by_unlink()`现在以authority-owned exclusive `flock`持有identity/digest/ref recheck、guard handoff、private parked inode重验/删除与`committed=True`；`verify_evidence_path()`以同lock shared读取，因此handoff期间verifier阻塞，只有commit后才能观察guard absent。parked lstat/unlink失败在unlock前restore guard；handoff后foreign `.pending`重现则fail-stop、不commit且verifier拒绝。新增direct tests覆盖：handoff内线程verifier不可在commit前返回、parked-lstat失败恢复guard、handoff后foreign guard阻止commit/acceptance，以及此前altered-record。CPU unittest=`64/64 PASS`；py_compile、Ruff、diff-check PASS；Gitlink不变。

请求完整exact pair唯一最终`APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。仅授权四个root工具/测试temporary CPU/static；不授权真实I/O、child/runtime、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root Real Adapter final-evidence-lock remediation（2026-09-12）

- formal root SHA：`1440fd3391d46ef383d60387da8d7e7aa8238d5f`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮ChatGPT review：`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_e1d5e11_93a89ba.md`（sidecar lock identity HIGH）；Kimi/MM同pair批准。

请仅审相对`e1d5e1115023caa0e18d80108f218a9f5d2382b6`的批准root文件整改。移除`<evidence>.lock` sidecar；writer/verifier均锁定已seal final evidence的`O_NOFOLLOW` FD。writer要求locked FD dev/inode等于seal identity并从该FD读取；verifier在同一locked FD上读取，guard检查仍处于同一临界区。新增direct tests：writer取得锁后final evidence pathname被foreign替换，guard保留且verifier拒绝；foreign旧sidecar无法改变实际lock identity。CPU unittest=`66/66 PASS`、py_compile、Ruff、diff-check PASS，Gitlink不变。仅temporary CPU/static，不授权真实I/O、child/GPU/训练。

请求该exact pair唯一最终`APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。

## 审核申请：Authority Root PASS linearization设计 v0.7（2026-09-12）

- formal root SHA：`c396ad298057810c04016e9d6116b7f9e5ac16d4`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.7.md`
- 前轮 ChatGPT exact review：`2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_1440fd3_93a89ba.md`要求回到design Gate，禁止继续隐式pathname coordination artifact。

v0.7选择同进程 sealed-final-FD `AcceptedPass` capability：authority在同一transaction内核验sealed FD identity/digest与fixed refs、执行guard transition后签发不可复制/不可重放 capability；只有capability是 acceptance authority。`verify_evidence_path()`保留为不改变refs/commit的内容观察API，pathname success不再授权PASS。Evidence-v1 bytes ABI保持，但旧“path verifier success即authorization”consumer必须迁移。无service/port/sidecar/durable coordination artifact；任何输出目录pathname锁/marker/rename/lstat方案明确拒绝。

请求完整exact pair唯一最终`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC`或`REQUEST_CHANGES(file:line)`。本申请只请求后续四root工具/测试的temporary CPU/static implementation；不授权真实source/candidate/ref/evidence操作、child/runtime、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root PASS 线性化设计 v0.8（2026-09-12）

- formal root SHA：`0ad5fb3379456f485fd861595e3db4ab62c3555f`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_pass_linearization_design_v0.8.md`
- 前轮ChatGPT exact review：`2026-09-12_R09_B_TTT_v035_pass_linearization_design_c396ad2_93a89ba.md`提出return/lifetime、nonthrowing issuance、crash closure三项HIGH；MM/Kimi批准。

v0.8明确：保留v0.6 `publish_candidate`→exact `PublicationWitness`返回ABI，`AcceptedPass`永不出authority transaction；它是preallocated、activation-scoped的`prepared→issued→consumed`内部capability。所有字段预验证后，唯一total transition同步标记issued、EvidenceCommit committed与preserve-refs branch，紧接total internal consume；transition后异常永不rollback。崩溃选择永久fail-stop：没有capability重建/自动retry/自动close，后续只能独立人工 recovery design Gate。Evidence-v1 bytes ABI保持，path verifier只是观察。

请求完整exact pair唯一最终`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC`或`REQUEST_CHANGES(file:line)`。只请求后续四root工具/测试temporary CPU/static implementation；不授权真实source/candidate/ref/evidence、child/runtime、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root PASS 线性化设计 v0.9（2026-09-12）

- formal root SHA：`a98e82714940d7bed1969cafb2ef32100c287d59`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_pass_linearization_design_v0.9.md`
- 前轮 ChatGPT exact review：`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_pass_linearization_design_0ad5fb3_93a89ba.md`（H1 terminal state非不可分、H2 guard/crash语义不完整、H3 ref witness语义不充分）；MM/Kimi同pair批准。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

v0.9仅为设计整改：全部 acceptance、rollback、preserve-ref、witness资格均由单个不可变`AuthorityTerminalState` cell派生，唯一状态变更为不可抛出的`PENDING→ACCEPTED`指针替换；guard转移是最后一个fallible pre-state action，并冻结A/B/C crash/restart matrix，B/C一律不自动恢复；ref witness明确为最后一次精确观察，之后漂移按external corruption fail-stop处理。formal tree仅新增v0.9设计并更新`SESSION.md`/`TODO.md`；Gitlink不变。

请求完整exact pair唯一最终`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC`或`REQUEST_CHANGES(file:line)`。批准范围仅为后续四个root工具/测试文件的temporary CPU/static implementation；不授权真实source/candidate/ref/evidence、child/runtime、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root PASS 线性化设计 v0.10（2026-09-12）

- formal root SHA：`001336fa5d785d8c77a2685ac1c754c096b4fb06`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_pass_linearization_design_v0.10.md`
- 前轮三方同pair final：ChatGPT=`REQUEST_CHANGES(...v0.9.md:38)`、MM/Kimi=`APPROVE_TO_IMPLEMENT...`；整改仅处理ChatGPT唯一HIGH。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

v0.10选择并完整落实ChatGPT推荐Option A：最后一次双端exact observation是唯一绑定进pointer swap的历史 ref fact；该观察之后（**包括pointer swap前**）的外部drift不可由authority观察，故不撤销历史-witness transition。任何后续ref check不一致均为external corruption并fail-stop/recovery，禁止静默将其称为current exact ref、自动修复或rollback已ACCEPTED terminal cell；只有最后观察前验证失败才按既有pre-state rollback。单一`AuthorityTerminalState`、A/B/C crash matrix、v0.8 ABI及范围保持。

请求完整exact pair唯一最终`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC`或`REQUEST_CHANGES(file:line)`。批准范围仅为后续四个root工具/测试文件的temporary CPU/static implementation；不授权真实source/candidate/ref/evidence、child/runtime、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root PASS线性化 CPU/static implementation（2026-09-12）

- formal root SHA：`885b94fe8ed4c859014410dd7f53abb4550f3dc1`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前置授权：v0.10 design=`001336fa5d785d8c77a2685ac1c754c096b4fb06`获三方同pair `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC`。
- 冻结名册：ChatGPT reviews、MM `mm:0.0`、Kimi `kimi:0.0`。

请审核四文件临时CPU/static实现：`EvidenceCommit._committed`替换为与witness共享的`_AuthorityTerminalCell`；`committed`及全部terminal语义只派生自immutable PENDING/ACCEPTED state；guard成功转移后唯一`cell.state=ACCEPTED`写入。新增在last ref observation后、guard转移期间注入remote drift的回归：保留historical acceptance，后续namespace不应被宣称为current exact。CPU unittest=`67/67 PASS`、四文件`py_compile`、Ruff与`git diff --check` PASS；Gitlink不变。

请求该exact pair唯一最终`APPROVE_TO_CLOSE_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。只限temporary CPU/static；不授权真实source/candidate/ref/evidence、child/runtime、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root PASS lifecycle HIGH remediation（2026-09-12）

- formal root SHA：`bc40191f0e80f98201774cce8a1b551fa2343128`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮：`885b94fe`三方final齐，ChatGPT 4 HIGH；MM/Kimi approve。
- 冻结名册：ChatGPT reviews、MM `mm:0.0`、Kimi `kimi:0.0`。

整改：拒绝`finalizer=None`成功旁路；`_AuthorityTerminalState`改frozen；私有不可复制/序列化的`_AcceptedPass`绑定activation/witness/cell；restart classifier仅允许guard-visible PENDING，guard缺失+evidence一律B/C recovery；普通与BaseException guard interruption回滚。CPU=70/70、Ruff、py_compile、diff-check PASS；仅temporary CPU/static。

请求唯一`APPROVE_TO_CLOSE_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`；不授权真实I/O、child、GPU、训练或LIBERO4IN1。

## 审核申请：Authority Root PASS lifecycle recovery remediation（2026-09-12）

- formal root SHA：`8534ae8d5a0979a6dd7e90cedf45f6ad33a14ae5`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮 exact pair：`bc40191f0e80f98201774cce8a1b551fa2343128` / 同一 Gitlink，ChatGPT=`REQUEST_CHANGES`（3 HIGH），MM/Kimi=`APPROVE_TO_CLOSE...`。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

请仅审相对`bc40191f0e80f98201774cce8a1b551fa2343128`的四个批准 root tooling/test 文件。整改关闭三项 HIGH：

1. callback-visible `PublicationWitness` / `EvidenceCommit` 不再持有 mutable terminal cell；terminal 仅存 authority-private registry，cell无公开 setter，唯一 token-gated acceptance transition 在 guard 成功后发生。
2. private `_AcceptedPass` 在 transition 前绑定 candidate revision、binding SHA-256、sealed evidence dev/inode + evidence/record digest、最后双端 candidate ref observation；篡改 binding/evidence/record/ref witness 必拒绝。
3. guard 已成功移除但 terminal 尚未 ACCEPTED 的 B 窗口抛 `PASS_CLOSURE_RECOVERY_REQUIRED` 并绕过普通 rollback、保留 refs；adapter preflight 在 fresh-destination 拒绝前调用 restart classifier，使 B/C 均进入 recovery，而非普通 preflight FAIL。

新增 adversarial CPU tests：callback不能伪造 acceptance、四类 binding/evidence篡改拒绝、B窗口普通/custom `BaseException`路径保留 refs 且 recovery、真实 preflight entrypoint 路由 B/C recovery。`python -B -m unittest tools.psm_wma.test_immutable_source_authority_root tools.psm_wma.test_materialize_immutable_source_authority_root -q`=`74/74 PASS`；四文件`py_compile`、Ruff、`git diff --check` PASS。Gitlink不变。

请求该 exact pair 唯一最终 `APPROVE_TO_CLOSE_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`。范围仅 temporary directory/local bare-remote CPU/static fixtures；不授权真实 source/selection/config/candidate/ref/origin/collection/evidence、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测、推理或 LIBERO4IN1。

## 审核申请：Authority Root PASS lifecycle identity/B-window remediation（2026-09-12）

- formal root SHA：`074d0a0f036ac6a107a693a3b9903d17e2565e10`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮 exact review：`2026-09-12_R09_B_TTT_v035_pass_linearization_cpu_static_implementation_8534ae8_93a89ba.md`，ChatGPT 3 HIGH；MM/Kimi approve。

请仅审相对`8534ae8d5a0979a6dd7e90cedf45f6ad33a14ae5`的批准root CPU/static整改：authority identity slots不可改写；AcceptedPass改为私有不可改写对象且不再通过commit暴露；新增stale terminal-key substitution负例。guard helper若在durable移除后抛普通/custom BaseException，B窗口统一`PASS_CLOSURE_RECOVERY_REQUIRED`并永不ordinary rollback；新增真实helper完成后再中断回归。CPU=76/76、py_compile、Ruff、diff-check PASS；Gitlink不变。

请求 exact pair 唯一最终`APPROVE_TO_CLOSE_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。仅temporary CPU/static；不授权真实I/O、child、GPU、训练或LIBERO4IN1。

## 审核申请：Authority Root acceptance authority/sticky-B remediation（2026-09-12）

- formal root SHA：`a18d178877c192fdc9682033acbd36c4184b3639`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮 exact review：`2026-09-12_R09_B_TTT_v035_pass_linearization_cpu_static_implementation_074d0a0_93a89ba.md`，ChatGPT=`REQUEST_CHANGES`（2 HIGH）；MM/Kimi=`APPROVE_TO_CLOSE...`。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

仅审相对`074d0a0f036ac6a107a693a3b9903d17e2565e10`的两个批准root文件整改：authority-private `_AcceptanceAuthority` 在callback前冻结revision、binding SHA-256及最终双端ref observer，`PublicationWitness`/`EvidenceCommit`不能替换参与acceptance的authority输入；新增drift后伪造observer/binding的负例。guard已durable移除而accept失败时，authority粘滞`recovery_required`，`publish_candidate()`在callback返回后强制fail-stop，callback吞掉`PassClosureRecoveryRequired`亦不触发ordinary rollback；新增直接回归。

验证：`python -B -m unittest tools.psm_wma.test_immutable_source_authority_root tools.psm_wma.test_materialize_immutable_source_authority_root -q`=`78/78 PASS`；四文件`py_compile`、Ruff与`git diff --check` PASS。Gitlink不变。请求该 exact pair 唯一最终`APPROVE_TO_CLOSE_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。范围只限temporary CPU/static fixtures；不授权真实source/candidate/ref/origin/collection/evidence、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root handoff/restore recovery remediation（2026-09-12）

- formal root SHA：`313b1dc81d83646b310d86c58c10d20b453fc739`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮 exact review：`2026-09-12_R09_B_TTT_v035_pass_linearization_cpu_static_implementation_a18d178_93a89ba.md`，ChatGPT=`REQUEST_CHANGES`（1 HIGH）；MM/Kimi=`APPROVE_TO_CLOSE...`。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

仅审相对`a18d178877c192fdc9682033acbd36c4184b3639`的两个批准root文件整改：`_commit_exact_guard()`明确区分handoff前A失败与handoff后B失败；handoff后仅在恢复的public guard精确匹配原identity时才返回`False`，否则`PassClosureRecoveryRequired`。新增真实handoff→parked unlink失败→restore失败、callback吞即时异常后outer authority仍粘滞fail-stop的回归；双端refs保留且无rollback delete。`79/79` CPU unittest、py_compile、Ruff、diff-check PASS。该commit因承接远端ChatGPT ledger被安全rebase，formal SHA为上列`313b1dc8...`，代码diff相对`a18d1788...`不变。Gitlink不变。

请求该 exact pair 唯一最终`APPROVE_TO_CLOSE_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。范围只限temporary CPU/static fixtures；不授权真实source/candidate/ref/origin/collection/evidence、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root Materialization Execution Request 设计 v0.1（2026-09-12）

- formal root SHA：`1eb08dea015c1c3c64d504d96a52f02de4665dbd`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_design_v0.1.md`
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

本设计仅冻结既有 source-evidence 闭环内 one-shot materialization request 的可审核格式：绑定已关闭 real-adapter formal pair、两个 formal-tree 工具 identity、selection/config raw-byte digest、expected-zero fixed ref、clean-worktree `-I -S -B` bootstrap、完整 argv、fresh destination、PASS/FAIL/`ROLLBACK_INCOMPLETE`。正式 request 仍须在执行前填充并三方复审所有实际 metadata、环境、FD、remote/evidence path 和 argv；本申请不创建 JSON/candidate/ref，不读 source，不执行 collection/publication/GPU/训练。

请求该 exact pair 唯一最终`APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_REQUEST`或`REQUEST_CHANGES(file:line)`。批准范围仅为生成下一份 docs-only one-shot request；不授权任何真实 materialization、source I/O、child/runtime、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority Root One-shot Materialization Execution Request v0.1（2026-09-12）

- formal root SHA：`d3cd3c9b26cea021814c9f48bcd864183a811293`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
- 请求：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.1.md`
- 前轮三方final：`1eb08dea...` ChatGPT=2 HIGH，MM/Kimi approve；本次不再引入 request-design Gate。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

这就是唯一实际 one-shot request：冻结 formal parent/Gitlink、selection/config、Python/Git、clean worktree/index/evidence和fixed ref；在任何项目 import 前将完整 transitive closure（adapter、authority、collection、audit）按regular/non-symlink、raw SHA、formal-tree blob三重验证。实际执行仍须三方同pair批准；不创建 JSON/candidate/ref，不读source，不执行collection/GPU/训练。

请求唯一最终`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT`或`REQUEST_CHANGES(file:line)`。

## 审核申请：Authority Root foreign-public-guard recovery remediation（2026-09-12）

- formal root SHA：`ad9e0110494a582e707ed5f041610d4cc40a82df`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`
- 前轮 exact review：`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_pass_linearization_cpu_static_implementation_313b1dc_93a89ba.md`，ChatGPT=`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:135)`（1 HIGH）；MM/Kimi=`APPROVE_TO_CLOSE...`。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

仅审相对`313b1dc81d83646b310d86c58c10d20b453fc739`的两个批准 root CPU/static 文件整改：当 `_commit_exact_guard()` 已明确抛出 `PassClosureRecoveryRequired` 时，`EvidenceCommit.consume_by_unlink()` 无条件先对 authority 置 sticky recovery，再重新抛出；因此 callback 吞掉该异常后，`publish_candidate()` 仍永久 fail-stop，不进入 ordinary rollback。两条 handoff 后 foreign-public-guard 对抗回归均断言 outer recovery、candidate 双端 refs 保留、无 delete。`79/79` CPU unittest、四文件 py_compile、Ruff、diff-check PASS；Gitlink不变。

请求该 exact pair 唯一最终`APPROVE_TO_CLOSE_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。范围只限temporary CPU/static fixtures；不授权真实source/candidate/ref/origin/collection/evidence、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority-root execution-authority implementation 设计 v0.1（2026-09-12）

- formal root SHA：`569a34d50e5106f982c3ed111171d67ea3344bc9`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-EXECUTION-AUTHORITY-IMPLEMENTATION-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.1.md`
- 前轮 exact pair：`d3cd3c9b26cea021814c9f48bcd864183a811293` / 同一Gitlink；ChatGPT/Kimi=`REQUEST_CHANGES`，MM=`APPROVE_TO_MATERIALIZE...`。
- 冻结名册：ChatGPT `docs/collab/chatgpt/reviews/`、MM `mm:0.0`、Kimi `kimi:0.0`。

请只审核 docs-only 最小实现路线，目标是闭合已批准 source-evidence 链中 real materialization 的既有执行权威缺口，不新增 checkpoint/publication/provenance Gate：

1. 仅允许后续修改 `tools/psm_wma/materialize_immutable_source_authority_root.py` 与既有 `test_materialize_immutable_source_authority_root.py`；不触碰 child/Cosmos。
2. 将 adapter、authority、collection、audit 四模块、bootstrap raw/argv identity、FD protocol、canonical remote endpoint 与 Git isolation 纳入同一 parser/invocation/Evidence-v1 exact-key ABI。
3. bootstrap 在任何 project import 前完成四模块 regular/non-symlink + raw SHA + no-replace formal blob 三重检查；以collection/audit漂移、symlink、shadowing、HEAD漂移为直接CPU/static拒绝witness。
4. Git transaction 只使用 canonical endpoint，不接受remote alias；对replace/global/system/local config、attributes/filter/hooks注入 fail-stop，并证据绑定 endpoint digest/isolation fingerprint。
5. 下一 actual request 须一次性冻结 bootstrap bytes、完整argv、FD、输入binding、metadata/env、endpoint与路径；本设计不创建或执行该request。

请求 exact pair 唯一最终`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC`或`REQUEST_CHANGES(file:line)`。批准范围仅为两root文件的temporary CPU/static实现及测试；不授权真实JSON/candidate/ref/origin/source/collection/evidence、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority-root execution-authority implementation 设计 v0.2（2026-09-12）

- formal root SHA：`e69d78c0758cb77111e371897093e0765018d7bc`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-EXECUTION-AUTHORITY-IMPLEMENTATION-DESIGN`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.2.md`

仅审相对`569a34d...` ChatGPT两项HIGH的docs-only整改：以Python 3.11 `sys.orig_argv`对实际`-c` payload做进程级bootstrap/raw+argv摘要观测并写入Evidence-v1；冻结Git exact env/prefix、HTTPS endpoint grammar、config reject/fingerprint；要求production NativeAuthorityGit经temporary local bare remote直接验证replace/config/rewrite/CAS。范围仍只允许后续两root文件CPU/static实现，不新增Gate。

请求唯一`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC`或`REQUEST_CHANGES(file:line)`；不授权真实执行、child、GPU或训练。

## 更正审核申请：Authority-root execution-authority implementation 设计 v0.2（2026-09-12）

上一条 formal root 误写为不可达 SHA，现明确撤回；不得以该错误 pair 作技术审核。

- **唯一正确 formal root SHA**：`e69d78c02bd946d44a3a00e455668e83a639917c`
- child/Gitlink SHA：`93a89ba61306d840a008813f62f26a34d54850f4`
- Gate/设计/范围/verdict 请求与上一条相同：仅审 v0.2 docs-only 两root文件CPU/static路线。

请对这个 exact reachable pair 重新审核，唯一`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC`或`REQUEST_CHANGES(file:line)`；不授权真实执行、child、GPU或训练。

## 审核申请：Execution-authority implementation 设计 v0.3

- formal root：`65836016ebc4fbcb73c50dc055cae206a690bc4f`
- child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`
- 文件：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.3.md`

仅审v0.2 ChatGPT local-config HIGH整改：冻结typed config ABI、实际Git-dir/config路径、完整allowlist与值约束、production isolation fingerprint、accepted/rejected native temporary-repo witnesses。请求唯一`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC`或`REQUEST_CHANGES(file:line)`；仅两root文件CPU/static，不授权真实执行、child、GPU或训练。

## 审核申请：Execution-authority implementation 设计 v0.4

- formal root：`9aba4460469ddab4640e90694e78968d497a9273`
- child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`
- 文件：`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.4.md`

仅审v0.3 linked-worktree HIGH整改：冻结absolute git-dir/common-git-dir、common config唯一authority、same-FD raw/parsed view一致性、worktreeConfig与config.worktree拒绝及actual linked/detached worktree正反native witness。请求唯一`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC`或`REQUEST_CHANGES(file:line)`；仅两root文件CPU/static。

## 审核申请：Authority-root execution-authority CPU/static implementation closure（2026-09-12）

- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`。
- formal root：`bb17774ce6da4e4d14c57993fe97f813065de319`；formal child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 范围：相对已批准设计`9aba4460469ddab4640e90694e78968d497a9273`，仅`tools/psm_wma/materialize_immutable_source_authority_root.py`、其stdlib test及`SESSION.md`/`TODO.md`/既有ledger记录；formal tree Gitlink未变。实现包括four-module closure、`python -I -S -B -c`的`sys.orig_argv` bootstrap、canonical HTTPS endpoint、固定Git env/prefix、common/linked-worktree config authority与Evidence-v1 exact fields。
- 证据：`python -B -m unittest tools.psm_wma.test_immutable_source_authority_root tools.psm_wma.test_materialize_immutable_source_authority_root -q`=`88/88 PASS`；四文件`py_compile`、Ruff、`git diff --check` PASS。direct temporary-only witnesses覆盖tampered bootstrap payload/argv/flag/contract、endpoint、symlink、raw/Git-view drift、linked worktree与local-bare CAS；无外网、GPU、模型/数据或真实source/materialization操作。
- 禁止范围：真实JSON/candidate/ref/source/collection/receipt/publication、child、GPU、训练、评测、推理。
- 请求：请只针对该exact pair给出`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。

## 审核申请：Authority-root execution-authority remediation closure（2026-09-12）

- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`。
- formal root：`cc36db3a6b863d86d57f5eb0e3fcefb5aef3376d`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。

## 审核申请：Bootstrap local-config remediation closure

- formal root：`aa48efebfcd54767e43c9156d3d0ce8301ddf9c4`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 整改：bootstrap module symlink拒绝；首个Git命令前stdlib common config allowlist并拒绝fsmonitor/include。
- 证据：94/94 CPU tests、py_compile、Ruff、diff-check PASS；禁止真实I/O/GPU/训练。
- 请求：`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。
- 相对前轮`bb17774...`整改：bootstrap 在`sys.path/runpy`前以stdlib frozen Git验证HEAD/formal与四模块raw/formal-tree closure；collection/audit drift import-sentinel反例；endpoint grammar、replace-ref、hostile parent Git config、Evidence remote digest witnesses。

## 更正：Bootstrap local-config remediation closure formal pair

- 前条 `aa48efebfcd54767e43c9156d3d0ce8301ddf9c4` 仅为 SESSION 送达记录，非实现 formal root，作废。
- 正确 formal root：`5efcbdf8954f65da9c7dfd1d0f34c96204c5ddf6`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。该 root 的父提交 `08de3f89` 同属本整改序列；审核范围为 `cc36db3a..5efcbdf8` 的两项 root tooling/test 修改。
- 请求：仅对正确 pair 回复 `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`；禁止真实 I/O、child、GPU、训练。

## 审核申请：Bootstrap executable/worktreeConfig remediation closure

- formal root：`a564e953aadc646daeed66e46115ecdb614e80b8`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 整改 ChatGPT 两项 HIGH：项目 import 前验证 interpreter/Git regular、non-symlink、raw SHA 与 version；bootstrap 禁止 `extensions.worktreeConfig=true`；新增 version/path/hash 与 worktreeConfig isolated-bootstrap 拒绝 witnesses。
- 证据：50/50 CPU unittest、py_compile、diff-check PASS。请求 `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`；禁止真实 I/O、child、GPU、训练。

## 审核申请：Bootstrap common-config identity remediation closure

- formal root：`817191c91ae8c8eb7e1a66f15055d2286d0b76c4`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 整改：bootstrap common config 使用 no-follow FD、identity/bytes 重验，拒绝预存 `config.worktree`；新增 isolated-bootstrap witness。
- 证据：51/51 CPU unittest、py_compile、diff-check PASS。请求 `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`；禁止真实 I/O、child、GPU、训练。
- 证据：`python -B -m unittest tools.psm_wma.test_immutable_source_authority_root tools.psm_wma.test_materialize_immutable_source_authority_root -q`=`92/92 PASS`；py_compile、Ruff、diff-check PASS。只使用temporary repo/local bare remote；不含真实source/materialization、child、GPU、训练。
- 请求：仅对exact pair回复`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC_IMPLEMENTATION`或`REQUEST_CHANGES(file:line)`。

## 审核申请：Bootstrap linked-worktree/config-observation remediation closure（2026-09-12）

- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`。
- formal root：`fff6d05ef330ada5f6db5edbdc8dde32e2c99019`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 前轮 exact pair：`817191c91ae8c8eb7e1a66f15055d2286d0b76c4`/同一Gitlink；ChatGPT/Kimi=`REQUEST_CHANGES`、MM=`APPROVE`。本轮仅汇总三方共同授权的最小root CPU/static整改。
- 范围：仅 `tools/psm_wma/materialize_immutable_source_authority_root.py`、既有 stdlib test、`SESSION.md` 与 `TODO.md`；formal tree Gitlink 不变。linked `.git` marker、`gitdir` reciprocal 与 `commondir` 均以 no-follow FD 绑定；实际 `<git_dir>/config.worktree` 必须不存在；每次 native Git bootstrap observation 前后均重验 common config pathname identity 与 retained-FD bytes。
- 直接 isolated-bootstrap temporary-fixture 负例覆盖：actual detached linked worktree `config.worktree`、伪造 gitdir escape、Git precheck 后 common-config replacement；定向=55/55、组合root stdlib=100/100、py_compile、diff-check PASS。仅临时目录/local bare remote；不含真实source/materialization/ref/evidence/collection/receipt/publication、child、GPU、数据、训练、评测、推理或LIBERO4IN1。
- 请求：请仅对该 exact pair 给出 `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`。

## 审核申请：Bootstrap routing-authority race remediation closure（2026-09-12）

- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`。
- formal root：`9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 前轮 exact pair：`fff6d05ef330ada5f6db5edbdc8dde32e2c99019`/同一Gitlink；ChatGPT=`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:172)`，MM/Kimi=`APPROVE_TO_CLOSE`。本轮仅整改其routing-authority HIGH。
- 范围：仅 root adapter、既有 stdlib test、`SESSION.md`；formal Gitlink未变。normal `.git` directory 和 linked `.git` marker/`gitdir`/`commondir` 的 no-follow FD identities/raw bytes、linked `git_dir`/common-dir identities、`config.worktree` absent 与 common config identity/FD bytes均进入`routecheck()`，每个 native Git observation 前后执行。
- 直接 actual detached linked-worktree wrapper-race witness分别在precheck后替换`.git` marker和`commondir`，均证明拒绝且无 project import/evidence/ref；保留config replacement、config.worktree、gitdir escape及symlink见证。定向=56/56、组合root stdlib=101/101、py_compile、diff-check PASS。只用临时目录/local bare remote；不授权真实materialization/source/ref/evidence/child/GPU/训练。
- 请求：请仅对该 exact pair回复 `APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC_IMPLEMENTATION` 或 `REQUEST_CHANGES(file:line)`。

## 审核申请：Authority-root materialization execution request v0.2 rebind（2026-09-12）

- formal root：`cfdd2fc79142b500910613759d316b283bfe372a`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 文件：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.2.md`。
- v0.1 request绑定旧`ad9e011...` adapter tree，已由v0.2替代。v0.2仅将formal parent和四模块formal-tree blob/raw identity重绑到三方刚关闭的`9dd2fb8...` routing-authority tree；其余v0.1 single-transaction、PASS/FAIL/rollback、禁止范围不变。
- 请求只允许准备一次只读运行时 snapshot annex，冻结clean paths、tools、env/remote/input/native-OID/bootstrap/argv digests；annex和实际命令仍须独立三方`APPROVE_TO_MATERIALIZE`。不创建JSON/worktree/index/candidate/ref/evidence，不读source，不执行collection/child/GPU/训练。
- 请求唯一 verdict：`APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_SNAPSHOT` 或 `REQUEST_CHANGES(file:line)`。

## 审核申请：Authority-root v0.2 runtime-authority remediation（2026-09-12）

- formal root：`15e665576c8af37dbbbaf15cd05d2b4bf6af2f63`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 文件：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.2.md`。
- 相对`cfdd2fc...`仅处理ChatGPT HIGH：v0.1仅继承transaction/PASS/FAIL/rollback/prohibitions；所有runtime fields由annex唯一冻结，明确canonical HTTPS endpoint+SHA而非remote alias、fresh paths、tools/env/input/bootstrap/argv/FD ABI以及annex批准后不可变；annex不得覆盖v0.2 §2/§3。
- 仍只请求 `APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_SNAPSHOT`；禁止创建JSON/worktree/index/candidate/ref/evidence、source读、child/GPU/训练。

## 审核申请：Authority-root execution snapshot annex v0.1（2026-09-12）

- formal root：`29c8aaa2a048f538892295afa6bc6d49031b0d0c`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 文件：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.1.md`。
- 前轮`15e66557...`三方批准仅允许本只读 annex。annex冻结formal parent/Gitlink/ref、credential-free HTTPS endpoint SHA、Python/Git identity、fresh路径观察、selection/config identity、module identity、sanitized env与FD ABI/停止条件；不创建JSON/worktree/index/candidate/ref/evidence，也不读source。
- 请求唯一 verdict：`APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_REQUEST` 或 `REQUEST_CHANGES(file:line)`；批准后仅允许撰写完整执行 request，仍不授权 materialization。

## 审核申请：Authority-root execution snapshot annex v0.2 remediation（2026-09-12）

- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`。
- formal root：`81f7526881dc4f93cf03da13988e2b74dda7d0de`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 文件：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.2.md`。相对 `29c8aaa...`，本轮仅落实 ChatGPT/Kimi same-pair HIGH：v0.1 显式 supersede；annex 直接冻结 selection/config canonical JSON、sanitized env canonical JSON+digest、FD=3/4/5、candidate metadata、exact bootstrap extraction identity/length/digest，以及 complete parser argv tuple/length/digest；后续 request 不得新增或替换 runtime authority。
- 范围仅 docs/ledger；`git diff --check` PASS。禁止 materialization、source/checkpoint I/O、JSON/worktree/index/candidate/ref/evidence 创建、collection/receipt/publication、child、GPU、训练、评测、推理及 LIBERO4IN1。
- 请求唯一 verdict：`APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_REQUEST` 或 `REQUEST_CHANGES(file:line)`；即使批准仍不授权 materialization。

## 审核申请：Authority-root execution snapshot annex v0.3 remediation（2026-09-12）

- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`；formal root：`b2fc05489abb2a4c1bc7314844c94c197834b9ff`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 文件：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.3.md`。相对`81f752...`只落实三方同pair整改令：内联2,427-byte parser argv JSON/digest；分离并冻结带leading `--`的2,432-byte bootstrap argv digest、182-byte bootstrap contract JSON；内联471-byte `NativeAuthorityGit.env`（含`GIT_INDEX_FILE`和六author/committer键）与digest，message仅为commit-tree stdin。
- 标准库重canonicalization/length/SHA与`git diff --check`均PASS；仅docs/ledger。禁止materialization、source/checkpoint I/O、JSON/worktree/index/candidate/ref/evidence、collection/receipt/publication、child、GPU、训练、评测、推理和LIBERO4IN1。
- 请求唯一 verdict：`APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_REQUEST` 或 `REQUEST_CHANGES(file:line)`；批准仍不授权materialization。

## 审核申请：Authority-root one-shot materialization execution request v0.3（2026-09-12）

- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`；formal root：`3b67d317de595ac8df2529eabfb239efbf988733`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 文件：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.3.md`。仅收敛三方已批准annex v0.3的唯一authority为一次事务、preflight、PASS/FAIL、ownership rollback和停止条件；不新增runtime字段。
- 请求唯一 verdict：`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` 或 `REQUEST_CHANGES(file:line)`。批准范围仅一次authority-root materialization；不授权source/checkpoint I/O、collection/receipt/publication、child、GPU、训练、评测、推理或LIBERO4IN1。

## 审核申请：Authority-root launcher remediation（2026-09-13）

- formal root：`17767c0c52cb2e5856a9c98baf29f520ce27fc5b`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 相对`3b67d317...`仅整改ChatGPT HIGH：冻结launcher pre-adapter worktree/backing-object/FD/execve顺序及其ownership cleanup/`ROLLBACK_INCOMPLETE`语义；仍不执行。
- 请求：`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` 或 `REQUEST_CHANGES(file:line)`；禁止source I/O、collection、child、GPU、训练。

## 审核申请：Authority-root launcher procedure v0.4（2026-09-13）

- Gate：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`；formal root：`11950c953d7c3e781f821ab648d45af83e60d340`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 文件：`docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.4.md` 与 replacement request v0.4。相对`17767c0...`仅按三方 final（ChatGPT/Kimi request changes、MM approve）补齐同 Gate launcher authority：2,144-byte canonical procedure descriptor（SHA-256=`4de774a525b183261b7e89b7351ffe605e1fc21f0461897732e18a5bab0709c4`）、absolute frozen Git worktree add/remove argv/env、三份 backing path/identity/fsync/re-read、FD 3/4/5 dup2/seek/CLOEXEC/close set、从 v0.3 bootstrap observation 派生的 final execve，以及 pre-adapter cleanup/reproof。
- 标准库 descriptor JSON/digest/字段断言与`git diff --check` PASS；仅docs/ledger。禁止任何materialization、source/checkpoint I/O、JSON/worktree/index/candidate/ref/evidence、collection/receipt/publication/root audit、child、GPU、训练、评测、推理及LIBERO4IN1。
- 请求唯一 final：`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` 或 `REQUEST_CHANGES(file:line)`；请完整声明 exact root/child，重点核对 launcher 是否已无 post-approval authority-bearing choice。

## Formal-pair 澄清：v0.4 申请仍为当前 active request（2026-09-13）

- 本条不构成新申请、不改变范围或验收条件。当前 active formal pair 唯一为 root=`11950c953d7c3e781f821ab648d45af83e60d340`、child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`，即紧邻上一条 v0.4 申请所列 pair。
- rollover continuity 头部的`c6be81e...`只记录 2026-09-12 rollover 时的旧 Gate continuity，不能被解释为本 Gate 的 current target；`17767c0...`是`11950...`的祖先，ChatGPT 对`17767...`的 review 只绑定旧 pair，不能替代本 v0.4 申请的 final verdict。
- 请只对上述`11950.../93a89...`写入正式 review，并完整声明 exact root/child 与 verdict；MM/Kimi 同样只按该 pair 回收。本 Gate 在三方同 pair final verdict 完整到齐前保持 REVIEW，不执行整改或 materialization。
