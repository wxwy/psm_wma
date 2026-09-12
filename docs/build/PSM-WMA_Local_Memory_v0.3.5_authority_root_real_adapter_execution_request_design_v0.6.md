# PSM-WMA v0.3.5 Authority Root Real Adapter / Execution Request 设计 v0.6

**日期**：2026-09-12
**状态**：docs-only；待三方复审。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

本文件 supersede v0.5 §1 的 finalizer outcome dispatch；v0.5 §2 rollback reachability 以及 v0.3 的四文件 allowlist、opaque capability、exact raw bytes/OID、fixed-ref exact-old lease、其余 nested ABI 和全部禁止范围保持不变。本次只关闭 v0.5 exact-pair ChatGPT review 的 1 HIGH；不实现任何 adapter、authority module 或测试。

## 1. authority-owned finalizer outcome dispatch

`publish_candidate(..., finalizer=...)` 必须把 **整个** finalizer invocation 置入 authority-owned inner outcome capture，而不是让 callback exception 直接穿过既有 publication `try/except`。其唯一允许的伪代码控制流是：

```text
outcome = returned(value) | raised(exception)
try:
    perform pre-commit publication work
    issue and pre-validate exact witness/commit
    try:
        outcome = returned(finalizer(witness, commit))
    except BaseException as error:
        outcome = raised(error)

    if commit.state is committed:
        preserve exact candidate refs; leave the rollback boundary normally
    else:
        raise PRE_COMMIT_FINALIZER_OUTCOME(outcome)  # existing rollback path
except publication_pre_commit_error:
    ownership_aware_remote_then_local_rollback()
    raise

if outcome is raised:
    raise PostCommitFinalizerError(outcome.error)  # outside rollback boundary
return exact PublicationWitness                       # returned value ignored
```

`BaseException` 在此只用于把 callback outcome 数据化；不得吞没它：commit 未发生时它必须沿既有 rollback 失败语义重新抛出，commit 已发生时必须以 preserve-refs `PostCommitFinalizerError` 重新抛出。外部 cancellation/termination policy 若另有要求，必须在调用 finalizer 前决定，不能让已经 committed 的 callback exception 回流到 ownership rollback。

因此无论 finalizer 正常返回或抛异常，authority 都**先且只**检查 exact issued `EvidenceCommit.state`：

- `committed`：`consume_by_unlink()`已经成功，accepted PASS 与 candidate refs 都保留；不调用 `_rollback`。normal return 被忽略并返回 exact witness；raised exception 在退出 rollback boundary 后转为 `PostCommitFinalizerError`，并保留原 exception 作 cause。
- 非`committed`：guard 必须仍存在，normal return 或 exception 都是 pre-commit outcome；一律进入既有 remote→local ownership-aware rollback。normal return 的 stable primary code=`FINALIZER_DID_NOT_COMMIT`；exception 使用 stable primary code=`FINALIZER_EXCEPTION`，但保留原 exception 作为 cause。

这明确选用单一 return-value 规则：**finalizer 的 normal return value 在所有状态均不携带 capability 语义，且在 committed 后永远不是 violation。**不同 witness、replayed、wrong 或 unsealed `EvidenceCommit` 只能在 v0.5 的 pre-unlink validation/seal path 中被拒绝；它们不属于“ordinary return value”。`POST_COMMIT_CAPABILITY_VIOLATION`不再用于 ordinary return；仅保留给已 committed 后由 authority 外层/报告层发现的、且不改变 refs/evidence 的不可恢复 protocol corruption。

## 2. 唯一线性化与异常不变量

以下不变量取代 v0.5 对“normal-return dispatch”的局部表述：

```text
guard unlink succeeded
  <=> EvidenceCommit.state == committed
  <=> accepted PASS is verifier-visible
  <=> exact candidate refs are preserved
  <=> every callback outcome bypasses _rollback
```

反向方向同样强制：任何进入 `_rollback` 的 callback outcome 都满足 guard 仍存在、commit 非committed、accepted PASS 不可见。`consume_by_unlink()`成功后，finalizer 后续 Python 语句、normal return、arbitrary exception、exception wrapping 和 caller reporting 都不得修改 evidence/refs 或进入 `_rollback`。

## 3. 强制 CPU/static 验收

四文件 temporary CPU/static tests在 v0.5 矩阵上新增并直接 spy `_rollback`：

1. `consume_by_unlink()`成功后 finalizer 抛普通 exception、`KeyboardInterrupt`和自定义 `BaseException`：均产生 preserve-refs `PostCommitFinalizerError`，accepted PASS/双 candidate refs存在，rollback调用数为零；
2. `consume_by_unlink()`成功后 finalizer 返回 ordinary object、`None`及不同类型 object：返回 exact `PublicationWitness`，返回值被忽略，accepted PASS/双 candidate refs存在，rollback调用数为零；
3. pre-commit finalizer exception、ordinary return without consume、replayed/wrong/unsealed commit：guard存在、accepted PASS不可见，按已有 ownership事实完成rollback；
4. 对所有 callback normal/exception outcome做状态突变：validator与test必须证明“committed iff no rollback iff accepted PASS+two candidate refs”；
5. test double必须验证 `PostCommitFinalizerError` 在 authority rollback boundary 之外产生，且原 callback exception 保留为 cause。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC
```

或`REQUEST_CHANGES(file:line)`。仅授权 v0.3 的四个 root 文件及 temporary directory/local bare-remote CPU/static tests；不授权真实 JSON/candidate/ref/origin/source/collection、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测或推理。
