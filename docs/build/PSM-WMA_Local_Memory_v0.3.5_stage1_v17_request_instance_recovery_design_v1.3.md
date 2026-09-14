# Stage-1 v1.7 request-instance recovery design v1.3

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN`。
**状态**：仅 docs-only recovery；本版不复用 v1.2 的 construction authority。

## 事实与目的

v1.2 已获批准的 C 在 `2026-09-14 23:57 CST` 开始并完成 allowlist snapshot 与
canonical JSON/Markdown candidate 生成，但候选只停留在命令标准输出，未成为冻结的
`...request_instance_v0.3.{json,md}` pair。按 v0.7/v1.2，C 已消费且不得补写、重跑或重试。
本版不改变该事实，仅为一次未来的、独立审核后的构造权冻结可靠交接方式。

future request identity tuple 保持逐字不变：

```text
formal_parent = 08d5828cdb4c12afa3b798ff01826c91ceb8755a
child_gitlink = 93a89ba61306d840a008813f62f26a34d54850f4
json = docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json
markdown = docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.md
```

## future P0/P1/C handoff contract

P0 仍只取得 v1.0 literal binding 所列三项冻结 Git object，P1 仍只对注入 bytes 调用已关闭的
projection helper；两阶段均不消费未来 authority。新的 C 必须在第一次 freshness observation 前开始，
并且只有一次。

C 的 producer 必须在内存中构造 canonical JSON raw bytes 与 detached Markdown raw bytes，并把两者、
JSON SHA-256、JSON byte length 与计算出的 Git blob OID 作为一个不可截断的 handoff value。它不得只
打印候选而把“落盘”留给事后人工重建。

唯一允许的 consumer 是同一 C 内紧接 producer 的受控 `apply_patch` 写入：

1. 只允许新建上述两条 designated path；先断言二者不存在，绝不覆盖；
2. consumer 必须逐字使用 producer handoff 的 JSON/Markdown bytes，不得重新 snapshot、重算 closure、
   读取旧 request 或从环境推断字段；
3. 写入后立即重新读取两个 designated files，机械验证 canonical JSON、length、SHA-256、Markdown 五项
   detached binding 与 JSON Git-blob preimage OID；
4. producer、consumer、identity verification 任一步失败均为零/不完整 request failure，永久禁止 retry；
   PASS 只允许 pair 存在并硬停以待独立 exact-pair review。

为保持可审计性，future execution notice 必须先完整列出 producer 的 two remote queries、六项环境、
designated path list、以及 consumer 的 exact two output paths；不得由 shell redirection、Python 文件写入、
临时文件、Git mutation 或非 allowlist I/O 代替受控 `apply_patch`。

## 范围

本设计不授权构造、materialization、launcher/materializer、source/checkpoint/manifest/data/cache I/O、
collection/receipt/record/publication、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理或
LIBERO4IN1。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or
`REQUEST_CHANGES(file:line)`.
