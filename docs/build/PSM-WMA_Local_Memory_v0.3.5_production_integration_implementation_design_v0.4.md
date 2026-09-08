# PSM-WMA Local Memory Production Integration Implementation Design v0.4

**日期**：2026-09-08
**状态**：docs-only remediation；未授权代码、真实 I/O、GPU 或训练
**取代**：v0.3 对 GA transaction owner 的 symbol whitelist 缺口。

## 1. 唯一允许文件与符号

| 路径 | 状态 | 唯一允许变更 |
|---|---|---|
| `cosmos_framework/model/generator/mot/local_memory_segment.py` | existing/modified | 仅 `SegmentBatch`、`RankLocalSegmentScheduler`、`GAWindowPlan`、`LocalMemoryTransactionSnapshot`、`LocalMemoryTransaction` 的 canonical integration facade；后两者仅可增加本文件第 2 节的不可逆 transaction guards/state。 |
| `cosmos_framework/model/generator/mot/local_memory_segment_test.py` | existing/modified | 仅相邻 transaction integration fixtures。 |
| `cosmos_framework/model/generator/mot/c6_runtime_adapter.py` | existing/modified | 仅 `CanonicalSegmentRuntimeAdapter`。 |
| `cosmos_framework/model/generator/mot/c6_runtime_adapter_test.py` | existing/modified | 仅 `CanonicalSegmentRuntimeAdapter` fixtures。 |
| `cosmos_framework/trainer/__init__.py` | existing/modified | 仅 `ImaginaireTrainer._run_local_memory_segment_backward`。 |
| `cosmos_framework/trainer/trainer_local_memory_integration_test.py` | existing/modified | 仅该 seam 的 synthetic tests。 |

所有其他路径与 symbols 保持行为不变；尤其历史 `C6SyntheticRuntimeAdapter` 不修改、不调用、不删除。不得增加任何其他文件。

## 2. 不可逆 GA transaction 合同

- `validate_success()`、`successful_backward()` 与 `slow_optimizer_step_succeeded()` 必须先拒绝 terminal、original-plan suffix recovery、或 GradScaler skip 后的 transaction；不得把记录字段当作仅供观察的标记。
- success 的顺序固定为 frozen identity/count precheck → raw finite objective → `loss.backward()` → fast commit；仅该最后一步可推进 fast chronology。
- `LOAD_DECODE_TRANSIENT` 且 `attempt=0` 只能产生一次 immutable suffix；创建后 original plan 永久拒绝剩余成员，只有独立 attempt-1 suffix transaction 可执行。attempt=1 必须 terminal `LOCAL_MEM_RETRY_EXHAUSTED`。
- identity、numerical、outer 与 backward failure 都是 terminal：清理 partial slow grads、保留已完成 fast commits、抑制剩余成员、禁止 slow optimizer/LR。GradScaler skip 同样保留既有 fast commits，清理 slow grads，并禁止 slow optimizer/LR。
- primary/auxiliary ABI、raw-native finite predicate、normal/recovery objective 与唯一 scaling owner 逐字继承 v0.3；不得增加第二个 `/grad_accum_iter`。

## 3. 必须可见的 CPU/static 证据

相邻 fixtures 必须通过唯一 trainer seam 证明：真实 non-finite native loss 的 numerical route、实际 `backward()` exception 的 outer route、至少一个已 fast-commit member 后的 GradScaler skip retention/no-slow-step、以及 immutable attempt-1 suffix 的实际执行（unequal valid counts、nonzero aux、recovery `GA_effective`、full-window equivalence、无第二次 GA scaling）。另须对 terminal/recovery/skip 后的 `validate_success()`、`successful_backward()` 与 slow step 给出 fail-closed negative fixtures。

## 4. Gate

仅在三方对同一 docs-only formal pair 批准 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC_V04` 后，才可改动第 1 节的精确 surface。新 implementation SHA 仍需 fresh 三方 closure review。

production wiring、registry/default/config、真实 checkpoint/data/cache I/O、CUDA/GPU/torchrun、训练/评测/推理、P4/P5、B2-T 与 LIBERO4IN1 一律未授权。
