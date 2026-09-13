# PSM-WMA v0.3.5 Immutable Source Collection Real Adapter 实现设计 v0.2

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-IMPLEMENTATION-DESIGN`

本版替代 v0.1。除本版明确变更外，v0.1 的 CPU/static-only 边界、禁止真实 I/O/GPU/训练、FD/no-follow、
native Git、atomic evidence、one-shot handoff、rollback 与验收要求保持不变。

## 唯一 executor identity 修正

已批准 controlled-execution v0.2 与 executor implementation design 冻结唯一 production executor 为：

```text
tools/psm_wma/immutable_source_collection.py
```

因此不得新增或调用 `execute_immutable_source_collection.py`。future real CLI、import-free bootstrap、
`NativeCollectionGit`、`FdRootOpener` 与 `AtomicCollectionEvidenceSink` 必须实现于该既有唯一 executor，
并且只连接其已有 injected seams；不得复制或改变 canonical validation、candidate construction、one-shot
handoff、receipt 或 rollback semantics。

后续 CPU/static implementation allowlist 严格为：

```text
tools/psm_wma/immutable_source_collection.py
tools/psm_wma/test_immutable_source_collection.py
```

formal-tree identity、bootstrap/import route、interpreter、child Gitlink 与该二文件 allowlist 任一漂移，均须在
source open 或 Git/evidence mutation 前 fail-close。future exact execution request 必须绑定同一唯一 executor 的
path、committed blob OID、raw SHA-256 与 import route；不得从 ambient `PYTHONPATH`、cwd、caller mapping 或
未审核模块加载它。

本版不授权 implementation、request execution、真实 source/checkpoint/manifest/data/cache I/O、authority/
collection/receipt/record/package/publication mutation、child/runtime/config 修改、GPU/CUDA/torchrun、训练、评测、
推理或 LIBERO4IN1。

请求最终 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。
