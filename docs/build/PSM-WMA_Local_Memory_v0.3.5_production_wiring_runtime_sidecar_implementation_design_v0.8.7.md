# Runtime Owner / Sidecar 实现设计 v0.8.7

**状态**：docs-only remediation；v0.8.6 superseded；child=`5d16b84`。仅关闭 v0.8.6 attempt-1 `SCALER_SKIP` 可达性缺口，继承全部 exact capability、retained plan、白名单及禁止范围。

`abort(SCALER_SKIP)` 的 owner preflight 必须在 v0.8.4 exact pending tuple 验证之后、任何 transaction/owner/scheduler/sidecar mutation 之前，额外要求：

```python
transaction.plan.attempt == 0
len(transaction.completed_members) == 0
```

任一条件不满足（尤其 attempt-1 suffix transaction 的 scaler skip）立即 fail closed：owner 保持 `PREPARED`，transaction/forward/scheduler/pending/sidecar 均零 mutation，绝不进入 `SKIP_READY`。调用方必须使用既有 attempt-1 exhausted → terminal taxonomy；本 Gate 不定义 attempt-1 skip 的 retry/loop/terminal 新出口。

仅当两项成立时，才允许 v0.8.6 的 exact retained `skipped_identity`/`skipped_plan`、一次 `grad_scaler_skip()` 和一次 exact discard，随后无参数 `resume_skipped()`。CPU/static tests 必须新增 attempt-1 prepared skip 的零-mutation fail-closed fixture，并保持 v0.8.6 的 first-member successful resume、replacement plan、snapshot、retry/terminal 覆盖。

白名单仍限新增 `canonical_segment_runtime.py`、`canonical_segment_runtime_test.py`，以及修改 `local_memory_segment_adapter.py` 和其 test。禁止 production wiring/model/trainer/scheduler source/dataset/config/optimizer/checkpoint/callback、真实 I/O、GPU、torchrun、训练、评测、推理、P4/P5、B2-T 或 LIBERO4IN1。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
