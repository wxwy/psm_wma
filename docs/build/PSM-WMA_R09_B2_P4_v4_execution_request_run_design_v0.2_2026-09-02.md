# R09-B2 P4-v4 Execution Request `run` 静态合同 v0.2

**状态**：draft；替代未获实现批准的 v0.1。本版只申请 root request parser/validator tooling 与 stdlib CPU fixtures；禁止真实 preflight、run-root/staging/candidate 创建、record/refreeze、P5 export/compose、GPU、训练及任何模型/数据/checkpoint I/O。

## 1. 双 backend 精确表示

root request 的 `run` 精确为 `{recurrent,ttt_fast_weight}`。每个 backend 值保持已冻结、未来 P5 handoff 的 inner key set `{identity,run_token,roster_sha256}`，不得新增或删除 key：

```text
identity = {root,resolved_root,kind,identity_sha256}
kind = "run_root"                    # byte-exact
identity_sha256 = canonical_sha256({root,resolved_root,kind})
run_token, roster_sha256 = 64 lowercase hex
```

两侧 `identity`、`run_token`、`roster_sha256` 都必须彼此不同；任何 root/token/roster reuse 均 FAIL。如此 root request 可无推断地映射到两份 backend-specific P4 request 的同名 `p4_run`，同时不改变 P5 已冻结 inner schema。

## 2. 非存在 future path 的 lexical/canonical 规则

`root` 与 `resolved_root` 都必须是 absolute string，且 `os.path.normpath(root) == root == resolved_root`；禁绝空、`.`、`..`、重复 separator、relative path 与不同 spelling。对 final component 不调用 `resolve(strict=True)`、不创建目录；沿既有祖先逐项 `lstat`，任一 symlink 即 FAIL。该规则为 future-nonexistent root 提供确定的 non-strict canonical spelling，避免 ambient realpath/ancestor alias。

目前唯一命名且已验证的 overlap authority 是 `source.root` 及 `source.root/cosmos-framework`：每个 future run root 必与二者无相等、祖先或后代关系。candidate/staging/evidence/exporter roots 还没有自身被冻结的 named authority，故本 section 不维护环境/隐式 denylist；它们的 non-overlap 和 `candidate.{backend}.run == final_request.run.{backend}` 由后续 candidates/full-request Gate 精确冻结。

## 3. roster SHA 生命周期

本 static-only request **不可执行**。此阶段 `roster_sha256` 仅接受格式与 backend-distinctness 校验，不得被当作 P5 final value、不得 materialize或产生 candidate。后续独立 candidates/backends/full-request Gate 必从精确 planned roster grammar 决定性计算每 backend final digest，生成新的 immutable execution request；其 `run.<backend>` 保持本版 inner key set，且 final `roster_sha256` 必等于该 deterministic digest。真实 preflight 只能消费这份 final request，且不得改写；其 result `p4_run` 必 canonical-equal request，`pre_p5_run_root_roster.sha256` 必等于 request 的 final digest，满足 P5 v0.8/v0.9。

## 4. 若获准实现的静态验收

仅可修改 root `tools/g0/r09_b2_p4_v4_execution_preflight.py` 和 stdlib CPU tests。正反例覆盖 exact two-backend schema、inner identity、kind、normpath/ancestor symlink、64-hex、pair reuse、source/submodule overlap 与 ambient independence。不得调用 subprocess/project entry、网络、torch/GPU，也不得创建真实 run/staging/candidate root。

请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_RUN_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
