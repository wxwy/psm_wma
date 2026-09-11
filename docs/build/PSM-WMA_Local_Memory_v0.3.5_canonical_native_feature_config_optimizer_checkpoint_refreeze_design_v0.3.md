# PSM-WMA v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint Refreeze 设计 v0.3

**日期**：2026-09-11
**状态**：docs-only remediation；须本文件 formal root/child 三方同 SHA 批准后才可进入下一份 CPU/static implementation design。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-DESIGN`

**supersedes**：v0.2 §4 中关于 optimizer/scheduler/payload `iteration` progress relation 的未冻结表述。v0.2 其他章节，以及 v0.1 中仍 binding 的范围、唯一 slow owner、inventory 和 fresh/quiescent admission 均继续有效；若冲突，以本文件为准。

## 1. 前置与不变范围

前置 closure 为 `420fc259d938d12f41c7f42d7b6aaec8076eb0f3` / `f49f568923555fe15efe546925cbe6cc9140170e` 的三方 `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_CPU_STATIC`。本 Gate 仍只冻结 versioned identity 与 **in-memory** slow-only restore；禁止 child 修改、真实 data/cache/checkpoint I/O、DCP、CUDA/GPU、torchrun、native forward/loss/backward、optimizer/scheduler step、sidecar、训练、评测、推理或 LIBERO4IN1。

FeatureConfigIdentity、BaseIdentity、optimizer/scheduler class、ordered groups/members、typed hyperparameters、state schema 与 shadow preflight 必须完整遵守 v0.2 §1--§4。所有 identity mapping 均使用 v0.2 §1 所定义的 canonical JSON/SHA-256 exact-match 纪律。

## 2. 本 Gate 唯一 canonical progress relation

因为本 Gate 和其允许的下一 CPU/static implementation 都明确禁止 optimizer/scheduler step，唯一允许的 checkpoint progress identity 是 **pristine-before-first-step**，不是可选择的 class-dependent policy：

```text
payload.iteration == 0
AND every canonical optimizer member has no saved state entry
AND saved optimizer.state is the exact empty mapping
AND saved scheduler state == pristine_state(approved scheduler identity)
```

`pristine_state(approved scheduler identity)` 的精确定义是：对已 exact-validated class、constructor/config、ordered optimizer groups/members 新建 detached shadow optimizer 与 detached shadow scheduler，**只允许其构造函数执行**，在任何 user-visible `optimizer.step()` 或 `scheduler.step()` 之前，读取其 canonical `state_dict()` 得到的 mapping。它包括该 scheduler class 在构造时合法写入的 progress fields（例如 `last_epoch`、`_step_count`），并以完整 canonical mapping exact match；不得将这些字段泛化为“任意零值”，也不得仅检查字段存在。

因此 staged acceptance predicate 唯一为：

```text
payload.iteration == 0
AND payload.optimizer_identity/progress exactly equals the approved pristine optimizer identity
AND payload.optimizer.state == {}
AND payload.scheduler_identity/progress exactly equals pristine_state(approved scheduler identity)
```

optimizer 或 scheduler 任一不存在时，二者 identity/state 都必须 explicit `null`，且上述 predicate 退化为 `payload.iteration == 0`；禁止单独携带 scheduler 或 optimizer。任何 nonzero iteration、任一 member state entry/`step`、非 pristine scheduler progress、类/constructor/group/member/hyperparameter/schema drift 都在首个 live mutation 前 reject。

这不是对未来训练 resume 的声明：一旦存在真实 optimizer/scheduler progress，必须另起并经三方批准的 checkpoint/runtime Gate，显式冻结其 class-specific iteration/accumulation/scheduler relation；不得借本 Gate 的 pristine contract migration、warm-start 或 silently reinterpret。

## 3. 原子顺序与直接 witness

唯一顺序保持：

```text
decode/clone in-memory payload
  -> validate FeatureConfigIdentity + BaseIdentity + exact slow inventory/tensors
  -> construct detached pristine shadow optimizer/scheduler and evaluate §2 predicate
  -> validate fresh/quiescent runtime admission
  -> copy existing registered tensors once, then load already-validated live optimizer/scheduler state
```

下一 CPU/static implementation design 必须将 §2 predicate 原样实现为单一可执行 validator，并有 direct zero-live-mutation witnesses：`iteration != 0`、任一 optimizer member `step`/state entry、empty-state drift、scheduler `last_epoch`/`_step_count` 或任意 pristine-state field drift、单边 optimizer/scheduler presence 及 class/group/hyperparameter/schema drift。valid witness 只能是 exact pristine payload；不得执行 optimizer/scheduler step 或以真实训练状态冒充通过。

任何 reject 后 registered tensor bytes、optimizer groups/state、scheduler state、iteration、Parameter/module/adapter identity、frontier/pending authority 必须 byte/object-for-object 不变；禁止 post-mutation rollback、创建/替换 module 或 Parameter。fresh/quiescent admission、runtime-fast-state exclusion、`w0_fast_*` slow-seed inventory 与所有禁止范围仍按 v0.2/v0.1 binding。

## 4. Verdict

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_REFREEZE
```

或 `REQUEST_CHANGES(file:line)`。批准只允许创建并审核下一份 docs-only CPU/static implementation design，不授权 child 实现或任何真实执行。
