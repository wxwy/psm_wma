# PSM-WMA Local Memory v0.3.5 Canonical Native Runtime Implementation 设计 v0.2

**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-IMPLEMENTATION-DESIGN`
**状态**：docs-only remediation；supersede v0.1。三方仅可批准创建并审核下一份 **docs-only CPU/static implementation design**；child/code 仍须该下一设计独立批准及独立 implementation Gate 后才可触及。

## 1. 修正的 predecessor authority 与不变范围

前置 exact pair 为 root `8d9bcee0df5f414f21c0e4b94c1ed617d58b3c6e` / Gitlink
`c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`；其 ChatGPT corrected canonical review 为
`docs/collab/chatgpt/reviews/2026-09-11_r09b_ttt_v035_canonical_native_runtime_source_audit_review_8d9bcee_c0e6e55.md`，唯一 formal verdict 是：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_IMPLEMENTATION
```

不得使用、别名或保留 `SOURCE_AUDIT_COMPLETE` 为 predecessor verdict。修正只影响 provenance literal，
不改变 source-audit pair、findings 或 blocker count。

继承 v0.1 其余内容，并重申：当前 `omni_mot_model.py:1399-1438` 是 candidate seam，`:1434` 必须保持
fail-closed；`trainer/__init__.py:520-523` 不能删除。禁止 child 代码、真实 I/O、CUDA/GPU、torchrun、真实
forward/loss/backward、optimizer/scheduler、checkpoint/sidecar、training/evaluation/inference 与 LIBERO4IN1。

## 2. 唯一 immutable normal-window owner

future coordinator 只能消费一次 scheduler 在 normal attempt-0 开始时冻结的 exact window transaction：

```text
NormalPlan = (members[], planned_N_valid[], N_window, GA_effective=GA,
              stream-major identities, attempt=0, original transition identity)
```

它不是每 microbatch admission/freeze。每个 member 仅按 frozen member index 取得 exact identity、carrier、
slot/cursor provenance 与 planned count；不得重新计数、admit、resample、重排或创建第二 transition。每 member
forward 前 actual 必等于该 member 的 `planned_N_valid`；`N_window=sum(NormalPlan.planned_N_valid)` 不可改变。

每 member 的唯一 objective 为：

```text
L_member = planned_N_valid[mu] / N_window * primary_consumer_mean
         + auxiliary_loss / GA_effective
```

normal `GA_effective=GA`；full-valid normal case 精确还原 `(L_consumer+L_aux)/GA`。禁止 total-loss ratio
shorthand、ordinary `/grad_accum_iter`、第二次 GA scaling 或未绑定 original transaction 的 new plan。

## 3. suffix-only recovery 与 transaction disposition

仅 frozen attempt-0 的可重试 source transient 可派生 recovery；identity/count/nonfinite/forward/backward
failure、attempt-1 failure或任何已定义 terminal taxonomy 都不得重播。recovery 必须：

1. 从 original frozen transaction 的**未消费 suffix members**派生，保留原 member identity/order/count；
2. 使用同一 scheduler/original-transition lineage，attempt=1，且只可 `consume_retry()` 一次；不得 second
   admission、resample、unrelated refreeze、重建 normal plan 或再写 fast state；
3. 定义 `RecoveryPlan.planned_N_valid`、`N_window=sum(recovery.members planned counts)`、
   `GA_effective=len(recovery.members)`；每 suffix member仍使用 §2 公式，且无第二 `/GA`；
4. 保留任何已成功 post-backward committed fast state；对 failed original transaction 的 controlled partial slow
   grads 恰好 discard 一次，抑制其余 original members及 optimizer/LR；recovery success 只 reconcile original
   transition 一次；
5. attempt-1 再失败为 terminal `RETRY_EXHAUSTED`，不产生 attempt-2 或新 window。

forward/backward 成功的 per-stream detach/commit、S0 `None` prefix、PAD zero update/loss、stream-major gather、
Option-B scaler skip、sidecar unsupported 仍完全继承 v0.1，但必须绑定 normal/recovery exact plan，不得以
“terminalize all exceptions”覆盖上述唯一 suffix path。

## 4. 下一份 CPU/static implementation design 的强制 witnesses

下一设计必须分别列出 normal 与 recovery fixture：

1. normal 多 member window 只 freeze/admit 一次，member 逐一消费 immutable plan；
2. attempt-0 在已成功 member 后出现唯一可重试 source transient：已提交 fast state保留、controlled partial
   slow grads恰一次清理、derived suffix exact identity/count/`N_window`/`GA_effective`、attempt-1无 second admission；
3. normal 与 recovery 非等 valid count/非零 auxiliary 的 formula，各自无第二 `/GA`；
4. attempt-1、identity/count、nonfinite、backward failure 均 terminal、无 suffix/new transition，且无 slow step；
5. S0/continued/PAD、per-stream state、prefix identity、candidate seam/legacy isolation、current hard-stops 和
   no-sidecar fail-closed 继续覆盖。

## 5. 请求 verdict

请求新 formal root/Gitlink 的唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_CPU_STATIC_IMPLEMENTATION
```

或 `REQUEST_CHANGES(file:line)`。该批准绝不授权 child/code；它只允许新建并审核下一份 docs-only CPU/static
implementation design。
