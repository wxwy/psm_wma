# PSM-WMA Local Memory v0.3.5 Canonical Native Consumer Runtime Source-Audit 设计 v0.2

**日期**：2026-09-11
**状态**：P0 docs-only remediation；须本文件 formal pair 三方同 SHA 批准后，才可执行定义的只读审计
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-SOURCE-AUDIT-DESIGN`

## 1. Scope 与 authority

本文件只整改 v0.1 formal `91dc6f16/08775da` 的 ChatGPT 两项 design-only HIGH，显式 supersede v0.1 的 authority、loss/recovery acceptance 和 §20.2 enumeration；其 variable-valid/PAD、真实 feature-disable、source `file:line`、active-wiring supersession 与只读边界保持不变。

本审计的不可降级 authority 依次为：

- `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §3--§20，尤其 §20.2 **A--H**；
- `PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.6.md` §3--§8；
- `PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.8.md` §2--§4；
- `PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.9.md` 全文；
- `PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.3.md` 与已关闭 `e1a0c53/08775da` CPU/static Gate。

只允许阅读源码、文档和既有测试；禁止 child 修改、Python/pytest、真实 I/O、GPU/CUDA、torchrun、native forward/loss/backward、optimizer/scheduler step、sidecar、训练、评测、推理和 LIBERO4IN1。

## 2. P0 审计问题

### A--F：以 source evidence 裁决

1. variable-valid `[B_stream,T]` consumer gather/PAD 与 native packer；禁止 trainable zero-PAD。
2. native modality reduction、sample identity 与 primary/auxiliary split。
3. normal/recovery planned count、queue/seed/epoch/category exposure 与 provenance。
4. state/dt/age branch 是否从 construction 与 forward 真正移除，禁止常数零伪关闭。
5. canonical route 与 legacy row-wise active-wiring 的 retain/bypass/delete 和 mutation authority 边界。
6. prefix `[N_valid,K_local,32] -> [N_valid,K_local,2048]` 与 stream-major gather identity。

审计入口包括 `omni_mot_model.py` canonical/ordinary native path、`trainer/__init__.py::training_step`、`local_memory_segment.py`、`canonical_segment_adapter_scheduler.py`、`canonical_segment_production_adapter.py`、`attention.py`、`unified_mot.py` 及 `cosmos_framework/model/generator/utils/data_and_condition.py`。

### 2.1 不可降级的 normal/recovery loss 与 retry acceptance

审计产物必须用 `file:line -> unique owner -> fail-closed` 证明或明确否证：

```text
actual_N_valid[mu] == planned_N_valid[mu]            # pre-backward
N_window = sum(planned_N_valid)
L_backward_mu = planned_N_valid[mu] / N_window * L_consumer_mu
              + 1 / GA_effective * L_aux_mu
```

normal plan 固定 `GA_effective=GA`；suffix recovery 只包含未提交 suffix、固定 `GA_effective=len(recovery.members)`、`N_window=sum(recovery.planned_N_valid)`。recovery 是 plan-chain 唯一 attempt=1：不得 nested/replay/rebind/resample，attempt=1 任意 member transient 必为 retry exhausted。必须映射 objective 在 GradScaler/backward/optimizer 之前的形成位置，并证明该 canonical objective 之后没有第二次无条件 `/grad_accum_iter` 或 `/GA`。full-valid normal 必严格退化为 native `(L_consumer + L_aux)/GA`。

### G--H：不得丢失的 deferred obligations

- **G**：P0 只静态追踪 fp32 `W_fast` storage、higher-order graph lifetime、single-device admission、CP/DDP restrictions。实际 memory/throughput/budget 满足性一律 `DEFERRED / NOT PROVEN`，只能在独立批准的 single-GPU smoke Gate 测得；P0 不估计、不分配 GPU、不执行。
- **H**：runtime-sidecar schema/restore、distributed ownership 与 world-size-change fail-closed 必须保留为**正式训练前 mandatory separate Gate**；P0 产物须逐项列为未实现 obligation，不得归入笼统 future work。

## 3. 必须产物与分流

唯一后续产物 `...canonical_native_consumer_runtime_source_audit_v0.1.md` 必含：A--F source `file:line` PASS/FAIL 和 identity；loss/recovery上述公式及 owner table；`[B,T] -> valid gather -> [N_valid,K,2048]` ownership；legacy retain/bypass/delete；以及 G=`DEFERRED / NOT PROVEN`、H=mandatory separate Gate 的 named handoff。

任何需要 data/collate/packer/model/trainer 改动或真实执行才能回答的项必须 fail closed 并新建对应 Gate。

## 4. Verdict

请求唯一 verdict：`APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_SOURCE` 或 `REQUEST_CHANGES(file:line)`。批准仅授权上述只读 audit，不授权任何 child 或真实执行。
