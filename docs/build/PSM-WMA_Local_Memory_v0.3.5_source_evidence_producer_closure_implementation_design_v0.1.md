# PSM-WMA v0.3.5 Source-evidence Producer / Closure 实现设计 v0.1

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-IMPLEMENTATION-DESIGN`
**状态**：docs-only；仅请求 CPU/static implementation 授权。

## 1. 目的与范围

本设计把已批准的 producer/closure schema 变成可审计的最小实现入口。只允许修改
`tools/psm_wma/immutable_source_collection.py` 与其对应单元测试；不修改 Cosmos 子模块、训练入口、配置、数据集或缓存。

本 Gate 只授权纯内存 schema/canonical-bytes/identity 校验和失败矩阵实现，不授权真实 source/checkpoint/manifest/data/cache I/O、collection transaction、record 写入、publication、child/runtime 修改、GPU、CUDA、torchrun、训练、评测或推理。

## 2. 实现合同

在现有 `collect_synthetic()` 的 candidate/collection/receipt 输出 seam 之上新增独立、无副作用的 producer/closure helpers：

1. 从已验证的 collection receipt mapping 生成 exact 六键 `root_checkpoint_source_evidence_record_v1` canonical bytes；所有四项 source digest 必须逐字来自 receipt，拒绝 caller/environment/worktree 补值。
2. 从 record bytes、receipt-bound config/descriptor bytes 与 formal root identity 生成 exact 七键 publication input package，以及 exact 七键 derived-only witness；禁止循环引用和自声明 blob OID。
3. 对 record/package/witness 做 canonical JSON、exact key、lowercase hex、schema、digest、formal-root/child identity 校验；任一漂移 fail-closed。
4. 对 producer 输出提供一次性内存 handoff，consumer 只能使用同一 raw bytes；不得重新序列化替换或从路径重新读取。

实现不得打开 source FD、调用 Git mutation/push、创建固定 record/package/witness 文件或修改 authority ref；现有 native `main()` 的真实 collection 调用保持独立，待后续 execution request Gate 批准后再接线。

## 3. 最小验收

- 覆盖 canonical round-trip、exact key/schema、四项 digest 来源、package/witness 非循环绑定、raw-byte identity、one-shot handoff、缺字段/错误大小写/错误 digest/路径与 ref 注入等 fail-closed 负例。
- `/opt/conda/bin/python3 -m unittest tools.psm_wma.test_immutable_source_collection -q` 及新增定向测试全部 PASS。
- 目标文件 `py_compile` 与根仓库 `git diff --check` PASS。
- 仅在新的 implementation formal pair 获得三方同 SHA `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE_CPU_STATIC` 后编码；批准不授权真实 closure execution。

## 4. 禁止范围与后续顺序

本设计不构造 request instance，不运行 collection/record/publication，不生成 receipt root，不启动 single-GPU smoke 或 LIBERO4IN1 训练。顺序固定为：本设计审核 → CPU/static implementation → implementation closure 审核 → fresh Stage‑2 request instance construction/review → 一次受控 source-evidence closure → receipt-root review → smoke/训练 Gate。

请求 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。
