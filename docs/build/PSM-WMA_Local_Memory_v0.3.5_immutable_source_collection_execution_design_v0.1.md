# PSM-WMA v0.3.5 Immutable Source Collection Execution 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`

## 1. 目的与边界

本 Gate 只冻结未来一次 collection execution 的真实-source 读取合同，严格实现已批准 `immutable_source_collection_design_v0.1` §2--§3 的五个 artifact 与 derivation；不创建、选择、读取、复制或哈希任何真实 source。本文件不替代其后的 `IMMUTABLE-SOURCE-COLLECTION-CLOSURE`、source-evidence controlled write、record/receipt、publication materializer 或 read-only root audit。

本 Gate 不修改 child/runtime，不创建 collection root/receipt，不运行 audit、DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。

## 2. future invocation 与 source transport

future executor 的唯一 real-source 输入是显式 `--source-root <absolute-directory>` 与 `--selection-request <canonical-json-file>`；二者只用于定位和读取 bytes，绝不是 accepted authority。selection request 必须是 exact canonical `immutable_source_selection_request_v1`，keys=`schema,source_kind,entries`，`source_kind="checkpoint_source_manifest_v1"`；`entries` 是 nonempty、ordinal 严格递增 array，每项 exact keys=`ordinal,relative_path`。relative_path 必须是 POSIX relative normal path：非空、无 leading slash、无 `.`/`..` component、无 NUL，且 UTF-8 bytewise sort 顺序与 ordinal 一致。

`--source-root` 必须 realpath 后仍为目录；每个 resolved candidate 必须 realpath 后仍在 root 下、是 regular file、非 symlink。request 不得来自 env、stdin、working-tree discovery 或 caller-supplied digest；request raw canonical bytes 与其 SHA-256 只记录在 isolated preflight evidence，不能替代 collection artifacts 的 authority。root、request 或任一 file transport error/missing/duplicate/escape/type drift 都 preflight FAIL。

## 3. isolated preflight derivation

executor 在独立 temporary index/tree 中按 ordinal 一次顺序流式读取每个 regular file，计算 byte_length 与 SHA-256；不载入模型、不解析 checkpoint payload、不联网，且不得写 source root。它构造：

1. `immutable_source_input_descriptor_v1`：仅 `schema,source_kind,source_entries`，entries 为 `ordinal,byte_length,sha256`；
2. `immutable_source_manifest_v1`：仅 `schema,source_kind,source_input_sha256,source_entries`，其中 entries 逐字等于 input descriptor；
3. 既有 exact 三键 `immutable_source_identifier_v1` canonical derivation object；
4. fixed-path exact five-key `root_gitlink_checkpoint_source_descriptor_v1`；
5. fixed-path `immutable_source_collection_v1` 与已批准 canonical model config artifact。

每项必须 canonical UTF-8 bytes、递归 key sort、`separators=(',', ':')`、`ensure_ascii=false`、`allow_nan=false`；逐项重算所有 SHA-256、key/type/value/ordinal/count/equality relation 后才可构造候选 collection tree。任一错误、source bytes read race（pre/post `stat` identity/size 不一致）、canonical/digest drift 或 temporary write failure均 FAIL；live target/index/HEAD/authority 逐 byte/entry 不变。

## 4. staged boundary、产物与移交

本 Gate 只定义 preflight output：five candidate raw blobs、candidate tree digest、per-entry ordinal/byte_length/sha256 与 stable failure code；它们必须在 temporary location 清理或保留为不含 source bytes的最小失败证据，绝不构成 authority。不得将 absolute root、relative paths、raw source bytes、环境变量或 caller labels 写入 collection/receipt/publication payload。

只有独立 `IMMUTABLE-SOURCE-COLLECTION-CLOSURE` 获三方批准后，才可采用 preflight 的逐 byte-equal candidate blobs 创建 collection root、再从 committed tree 构造 receipt root。closure 必须重新验证 candidate blob equality、parent、allowlist、rollback/`ROLLBACK_INCOMPLETE`；不得信任 preflight 内存状态或重新扫描 source root。成功 receipt 才能成为后续 producer 的 authority。

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_EXECUTION
```

或 `REQUEST_CHANGES(file:line)`。批准仅允许下一份 docs-only collection closure design，不授权真实 source read、collection mutation、publication、child、GPU 或训练。
