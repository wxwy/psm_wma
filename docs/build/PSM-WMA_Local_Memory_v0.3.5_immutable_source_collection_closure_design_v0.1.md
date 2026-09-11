# PSM-WMA v0.3.5 Immutable Source Collection Closure 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CLOSURE-DESIGN`

## 1. 目的、前置与禁止范围

本 Gate 只冻结 future collection closure：将已通过 `IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN` isolated preflight 的候选 raw blobs，经过不依赖 source root 的逐字复验后，按两个非循环 Git root 的既有合同提交为 collection root 和 collection-receipt root。它实现并不得改写：

- `PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_design_v0.1.md` §2--§4；
- `PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_design_v0.1.md` §2--§4；
- 已批准 source-evidence controlled-write、record/receipt、publication materializer/verifier、read-only root audit 的既有顺序。

它不创建或审核真实 execution-authority root，不选择、打开、读取、复制或重新 hash source bytes，不执行 collection/receipt mutation，不修改 child/runtime，不运行真实 checkpoint/data/cache I/O、DCP、CUDA/GPU、`torchrun`、模型 forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。真实 mutation 仍须在本 Gate 获三方批准后，以独立受控 execution Gate 进行。

## 2. Closure 输入与先验重验

future closure executor 只接受下列显式 inputs；环境变量、当前工作树发现、caller digest、默认配置、stdin 或前轮进程内存均不是 authority：

1. 已三方绑定的 execution-authority tuple：
   `(authority_root_revision, selection_path, selection_blob_native_oid, selection_raw_sha256, config_path, config_blob_native_oid, config_raw_sha256)`；
2. 由同一受控 executor 的 approved source-read preflight 产生、尚未 relinquish 的 typed one-shot `immutable_source_collection_preflight_handoff_v1`；
3. 未来 real controlled-execution approval 明示绑定的 target lineage tuple：`(target_ref, expected_base_root_revision, expected_child_gitlink, authority_approval_formal_root_revision)`，以及 target/index/worktree 的受控 snapshot handle。

handoff 不是 caller file、CLI 参数、环境变量、stdin、可重载 temporary path 或前轮进程内存。它由 approved preflight 在完成同一 regular-file FD 的双读/双 hash 与五 artifact 候选导出后，作为同一 executor activation 内不可序列化、仅可消费一次的 typed value 直接交给 closure；任何 restart、重复消费、跨 process handle、caller-provided replacement 或 source-read 后重新构造都 FAIL。其 canonical logical content exact 为：execution-authority tuple、ordered `(ordinal,byte_length,sha256)` source-entry results、五个候选 artifact 各自 fixed path/schema/raw SHA-256、candidate config raw SHA-256，及由这些固定字段 canonical JSON 计算的 `candidate_handoff_sha256`。它不含 source raw bytes、路径、URL、环境变量或 caller label。closure 从该 single-use value 取 candidate raw blobs，并要求每项 bytes/digest 与 handoff 逐字一致；因此不能以另一组自洽 candidate bytes 替代 preflight source-read output。

closure 先以 Git object lookup 读取 tuple 的 authority root，严格确认该 tree **只**含 execution design §2 的 fixed selection/config paths，并逐字核对 path、blob OID、raw SHA-256、selection schema 和 resolved 15-key config schema。任何 tuple/tree/path/blob/bytes/schema mismatch、不可达 object、unknown key、非 canonical JSON 或 transport 输入缺失均在 live mutation 前 FAIL。

handoff 中的 preflight candidate 不是独立 authority，也不得因“候选自洽”而被信任；它只是在同一 activation 内证明 preflight source-read result 与 closure bytes 不可替换的固定桥。closure 不重新扫描 source root；它只用 handoff 提供的候选 raw bytes 重算 canonical JSON、key/type/value、entry ordinal/count、所有 SHA-256 与下列纯 derivation：

```text
input descriptor -> manifest -> immutable source identifier
                 -> exact checkpoint descriptor -> collection artifact
```

其中 ordered source-entry results 必须逐项等于 handoff 的 entry results，model-config candidate 必须逐 byte 等于 authority-root 的 config blob；selection request 不得写入 collection 或 receipt payload。任何 handoff/candidate/authority drift 均 FAIL，且不得创建 accepted authority。

## 3. 两阶段受控 transaction

执行前，以 target lineage tuple 验证 `target_ref` 当前 `HEAD` 精确等于 `expected_base_root_revision`，base root tree 的 `cosmos-framework` 精确等于 `expected_child_gitlink`，且 `authority_root_revision^` 精确等于 `authority_approval_formal_root_revision`；这四项均从 Git object lookup 复算，不能由 tuple 自证。任一 ref/base/Gitlink/authority-parent drift 都在 source preflight 与 live mutation 前 FAIL。随后记录并可独立验证 target ref、`HEAD`、index tree、worktree allowlist 状态和 remote publication state。preflight 在 isolated temporary index/tree 完成；它的唯一允许新 tree entries 为 collection design §2 的五个 fixed paths：

```text
docs/build/PSM-WMA_immutable_source_collection_v1.json
docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json
docs/build/PSM-WMA_immutable_source_input_descriptor_v1.json
docs/build/PSM-WMA_immutable_source_manifest_v1.json
docs/build/PSM-WMA_immutable_source_checkpoint_descriptor_v1.json
```

preflight 必须从 candidate raw bytes 重建 tree，并对五个 path 的 canonical bytes、raw SHA-256 与 Git blob OID 作独立 lookup；候选 delta 含任何额外 path、已有 path 覆盖、`cosmos-framework` Gitlink、Inbox、publication target、checkpoint/cache 或训练 residue 时 FAIL。preflight 期间 target ref、live index、live worktree、remote 和 authority root 均逐 byte不变。

仅 preflight PASS、typed handoff 尚未消费且 lineage tuple 复验仍 PASS 后，live transaction 才可按以下顺序进行：

1. 再次确认 snapshot 与 target lineage 未漂移，写入并提交 collection root；其 delta 恰为五个 fixed paths，且 commit parent 精确等于 `expected_base_root_revision`。
2. 仅从**已提交 collection root tree** lookup 五个 blobs，重算 collection design §2 所有 digest、schema、path 与 blob identity；不得复用 candidate 内存对象。
3. 构造唯一 receipt path `docs/build/PSM-WMA_immutable_source_collection_receipt_v1.json` 的 canonical raw blob；其 exact key set、路径、schemas、five artifact blob OID/digest 与 `collection_formal_root_revision` 必须完全符合 collection design §2。
4. 提交 receipt root；其唯一 delta 恰为 receipt path，且 parent 精确等于 collection root。再次从 receipt root 的 parent tree 与 receipt blob lookup，独立重算全部字段。

任一 live 写入、Git tree/commit、post-commit lookup、parent、allowlist、canonical/digest、target/HEAD 或 remote-state 检查失败，均立即停止。未 publication 前恢复 snapshot ref/index/worktree；若 rollback 或 HEAD/index/worktree 恢复的任何一项无法证明完整，返回唯一 fail-stop `ROLLBACK_INCOMPLETE`，禁止自动重试、authority、producer、publication、runtime 或 GPU。普通已恢复失败同样没有 accepted authority。不得在 collection root 与 receipt root 成功且全部 post-check PASS 前推送、发布或交给 downstream。

## 4. 成功 authority 与下游交接

只有 receipt root 成功且 post-check PASS，future downstream producer 才可接受经三方 review 绑定的：receipt-root revision、receipt path 和 receipt blob native OID。producer 必须从 receipt 的 parent collection tree lookup，而不是 caller mapping，导出：

```text
immutable_source_identifier
source_manifest_sha256
source_input_sha256
checkpoint_source_descriptor_sha256
canonical_model_config_sha256
```

collection root、receipt root、preflight candidates、authority-root tuple、source-evidence record/package/witness 和 publication/audit 各有独立角色：任一前者均不得提前替代后者。成功仅允许进入既有 source-evidence controlled-write execution；不新增 checkpoint authority、publication evidence 或相同 source binding 的横向 Gate。既有 source-evidence/publication 闭环全部完成后，下一设计固定为 `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`，集中真实 optimizer/scaler、single batch GPU 与 20--100 step TTT smoke。

## 5. 验收与失败分流

future execution 的 PASS 必须同时证明：

1. authority-root tuple 的 Git tree/path/blob/raw-byte binding 和 selection/config schema 均在 source entry 打开前已锁定，且 authority-root Git parent 精确等于 reviewed `authority_approval_formal_root_revision`；
2. source-read result 仅经 same-activation typed one-shot handoff 传入，handoff 的 ordered entry results、五 artifact digest 和 `candidate_handoff_sha256` 与 closure 实际 bytes逐项相等；不读取 source root 的 closure 仍可独立验证五 artifact derivation，且 config candidate 逐 byte等于 reviewed authority；
3. target ref/expected base/Gitlink 均在 preflight 与 live mutation 前复验；collection delta 恰为五个 fixed paths、collection parent 精确等于 expected base、receipt delta 恰为一个 fixed path，receipt parent 精确等于 collection root；
4. 两个 committed tree 的 raw bytes、canonical bytes、SHA-256、blob OID、receipt exact schema/keys 与全部 derivation 均可独立 lookup/recompute；
5. preflight 零 live mutation，live failure 已完整 rollback，或明确以 `ROLLBACK_INCOMPLETE` fail-stop；成功前无 push/publication/downstream consumption。

任一输入、canonicalization、digest、allowlist、Git reachability、parent、snapshot、rollback 或 post-check 失败均为 FAIL，并依 §3 处理；不得产生 accepted collection/receipt authority。

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CLOSURE
```

或 `REQUEST_CHANGES(file:line)`。批准只允许后续独立的 real collection controlled-execution design/review；不授权真实 source I/O、collection/receipt mutation、source-evidence record/package/witness、publication/audit、child/runtime、GPU 或训练。
