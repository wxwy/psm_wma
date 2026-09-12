# PSM-WMA v0.3.5 Immutable Source Authority Root Materialization/Binding 设计 v0.2

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-BINDING-DESIGN`

## 1. v0.1 override 与继承

本版本仅整改 v0.1 §4 的 executor-facing authority ABI 命名冲突，并在该处显式 supersede v0.1；v0.1 的范围、canonical selection/config raw-byte authority、materialization formal-root parent、exact two-path full-entry delta、无自引用、detached candidate、固定 expected-zero CAS ref、独立 verifier、事务证据、失败判据和后续路线全部逐字继承。

本设计仍不创建 selection/config JSON、authority commit/ref，不读取或 hash 真实 source，不执行 collection/receipt/source-evidence/publication、child、GPU或训练。

## 2. 唯一 executor-facing 七键 ABI

conceptual authority-root revision 的唯一 serialization name 冻结为现有已批准 executor 使用的 `root_revision`。materializer/verifier、review evidence、三方 binding 和 collection executor 之间传递的对象必须是 exact seven-key mapping：

```text
{
  root_revision,
  selection_path,
  selection_blob_native_oid,
  selection_raw_sha256,
  config_path,
  config_blob_native_oid,
  config_raw_sha256
}
```

其中 `root_revision` 的语义就是 v0.1 所称 conceptual `authority_root_revision`；这只是该概念的唯一序列化键，不是新增字段、别名或可选 rename。任何 serialized `authority_root_revision`、同时出现两键、missing/extra key、tuple positional transport、caller-side rename、ledger/request translation 或 adapter bridge 均在 source open 前 FAIL。

materializer的候选输出、独立 verifier 的重算输出、review/evidence 中的 binding 与 `tools/psm_wma/immutable_source_collection.py` 的 `_authority_tree()` / `_bound_source_inputs()` 必须逐键逐值使用上述 exact mapping。`root_revision` 仍须为 authority candidate commit 的40位lowercase Git SHA-1，并满足 v0.1 的 formal-root parent、完整 tree delta、固定 ref和remote relookup全部语义；更名不会弱化任何 authority predicate。

## 3. CPU/static acceptance 与授权边界

下一 CPU/static implementation design 必须直接测试：exact `root_revision` mapping可被当前 executor接受；将首键改为`authority_root_revision`、双键、缺键或额外键均在任何 source open/Git mutation前拒绝；verifier输出到executor输入不经过caller adapter。既有v0.1全部负例继续保留。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_MATERIALIZATION_BINDING_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。批准只允许下一步root-only materializer/verifier CPU/static implementation design；不授权真实materialization、source I/O、collection/receipt/source-evidence/publication、child、GPU或训练。
