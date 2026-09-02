# R09-B2 P4-v4 Execution Request `candidates` 静态合同 v0.1

**状态**：draft。仅申请 root request parser/validator tooling 与 stdlib CPU fixtures；禁止创建 candidate、run-root 或 staging，禁止真实 preflight、record/refreeze、P5 export/compose、GPU、训练及模型/数据/checkpoint I/O。

## 1. 冻结输入与职责

本 section 仅消费已关闭的 `entry`、`source`、`interpreter`、`environment`、`authorities`、`run` static sections。它不读取候选目录、不调用 `stage_atomic_publication()`，也不产生 P5 evidence。

`candidates` 精确为：

```text
{
  root: {root, resolved_root, kind, identity_sha256},
  attempt_id: 64 lowercase hex,
  recurrent: {backend, candidate_root, identity_sha256},
  ttt_fast_weight: {backend, candidate_root, identity_sha256},
  identity_sha256
}
```

`root.kind` 固定 `candidate_root`，其 identity 是删除 `identity_sha256` 后的 canonical SHA256。`root.root == root.resolved_root` 必为 absolute、`normpath` 不变、无 `.`/`..`/重复 separator；逐项 `lstat` 现有祖先，任一 symlink FAIL。它必须与 `source.root` 和 `source.root/cosmos-framework` 无祖先/后代/相等重叠。该 root 此时只可作为词法 future location；validator 不创建、不要求其存在。

## 2. attempt 与双 backend 映射

`attempt_id` 仅为未来 immutable candidate namespace 的 64-lowercase-hex token；不等同 P4 `run_token`，不得重复使用后者。

每 backend record exact 为 `{backend,candidate_root,identity_sha256}`，其中 backend 分别 byte-exact `recurrent`、`ttt_fast_weight`，`candidate_root` 必是 lexical absolute path，精确等于 `<candidates.root.root>/<attempt_id>/<backend>`。其 identity 是删除自身 digest 后的 canonical SHA256。

两个 candidate root 必不同，且都不得与对应或另一 backend 的 `run.<backend>.identity.root` 重叠。`attempt_id`、backend labels、candidate identity 任何交叉复用或第三 backend 都 FAIL。候选 root 的最终目录树、PASS/FAIL 文件集、failure poison、payload byte preservation 与 pair atomicity仍唯一由已关闭 P4-v4 static contract 的独立 Gate 管理；本 section 不预填任何候选 payload、manifest、roster 或 P5 result。

## 3. 静态验收与范围

若三方批准，仅可修改 root `tools/g0/r09_b2_p4_v4_execution_preflight.py` 和其 stdlib CPU tests。正反例至少覆盖 exact outer/inner schema、canonical identities、attempt grammar、backend/path mapping、relative/dot/dotdot/repeated/double separator、existing ancestor symlink、source/submodule/run overlap、backend reuse、ambient independence 与不创建任何 future root。

不得调用 subprocess、项目 entry、网络、torch/GPU；不得创建或写入 candidate、run-root、staging、evidence 或 P5 paths。

请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_CANDIDATES_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
