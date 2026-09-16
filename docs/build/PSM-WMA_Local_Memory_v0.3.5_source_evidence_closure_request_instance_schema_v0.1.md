# Source-evidence closure request instance schema v0.1

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-REQUEST-INSTANCE-SCHEMA-DESIGN`
**状态**：docs-only；不创建 instance，不执行 source I/O。

## 目的

为已批准的 Stage‑2 source-evidence producer/closure 与 immutable collection executor 冻结一份可独立审核的 canonical request instance schema。本文只解决字段来源与 identity 绑定，不替代 execution approval。

## Exact instance

instance 是 UTF-8 canonical JSON（递归排序、紧凑分隔符、单个 terminal LF），顶层 exact keys：

```text
schema, formal_root, child_gitlink, authority, source, executor, producer,
record, receipt, publication, root_audit, preflight, execution, sha256
```

`schema="root_source_evidence_closure_request_instance_v1"`。所有 path、argv、identity、raw SHA、Git OID 和 ref 均由同轮只读 observation 绑定；禁止从环境、旧 instance 或本文固定值推导。

## 资产字段

- `authority`：Stage‑1 fixed ref、candidate revision、selection/config path、blob OID、raw SHA，以及 local/remote ref observation。
- `source`：source-root FD contract、source kind、selection raw SHA、checkpoint source path grammar；只记录 FD identity，不记录 source payload。
- `executor`：唯一 `tools/psm_wma/immutable_source_collection.py` 的 formal-tree blob OID/raw SHA、interpreter/Git identity、完整 argv、cwd/index/evidence path 与 sanitized environment。
- `producer`：`produce_source_evidence_record`、`produce_source_package`、`produce_source_closure`、`verify_source_package_and_witness` 的 callable/module identity 与 raw-byte/one-shot ABI。
- `record`：fixed record path、exact schema/key set、source digest→receipt 字段映射。
- `receipt`：collection receipt constructor/path/schema、parent-root/child identity 与 post-commit receipt-root boundary。
- `publication`：package/witness derived-only schema、唯一 output path/ref、publication verifier identity；本 instance 只绑定 contract，不执行 publication。
- `root_audit`：唯一 audit entrypoint 的 formal-tree identity、argv 与 PASS/FAIL predicate。
- `preflight`：所有 designated output/ref/path 的 same-round absence observations、index/HEAD/worktree snapshot digest 与 zero-mutation predicate。
- `execution`：固定顺序 `collection → producer → record → receipt → root_audit`、one-shot/no-retry、PASS hard-stop 与 failure/rollback semantics。

## Gate 与禁止范围

构造 instance 仅允许同轮读取上述 identities 并生成一份 JSON/detached Markdown sibling；随后必须对 exact instance SHA 重新取得 MM/DS/ChatGPT 三方审核。审核不授权执行；执行仍须另有 `APPROVE_TO_WRITE_SOURCE_EVIDENCE`，PASS 后必须停在独立 receipt-root review。

禁止真实 source/checkpoint/manifest/data/cache payload 读取、record/publication 写入、authority ref/child/runtime 修改、GPU/CUDA/torchrun、训练、评测和推理。

请求 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_SCHEMA` 或 `REQUEST_CHANGES(file:line)`。
