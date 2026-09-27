# V3 Stage B2-B Single-Segment Gradient Relay CPU/Static closure review

- Date: 2026-09-27
- Gate: `V3-STAGE-B2B-SINGLE-SEGMENT-GRADIENT-RELAY-CPU-STATIC`
- formal root: `81fa515593e7cd8e2d4f7d226efb915b17be3b5b`
- formal child/Gitlink: `bf6c80e679812b7d2881d6a54aa0b518299e3869`
- design authority: `bf5c8d134014d0023a03c25f95d8e971922f40fd`
- resource authority: B2 resource profiles v0.3
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2B_SINGLE_SEGMENT_GRADIENT_RELAY_CPU_STATIC`

## Fresh review

The exact formal pair was independently synchronized before review. Relative to the closed B2-A child, B2-B adds only:
- `cosmos_framework/model/generator/mot/local_memory_native_segment.py`
- `cosmos_framework/model/generator/mot/local_memory_native_segment_test.py`

No B0/B1/B2-A production file was changed.

ChatGPT independent exact-pair CPU rerun:
- B2-B + B0/B1/B2-A seven-file suite: **175/175 PASS**
- zero failures/skips
- 38.28 s
- only unrelated torchao deprecation warnings.

ds_pro independently validated the same pair:
- B2-B focused tests: **22/22 PASS**
- B0/B1/B2-A regression: **153/153 PASS**
- independent `/tmp/v3_b2b_verify.py`: **27/27 PASS**
- final checklist: **0 hard-fail, 0 blocker**.

## Closed contracts

### Exact module and optimizer ownership

The relay constructs its B0 adapter from the exact model-owned objects:
- `model.net.local_memory_runtime.encoder`
- `model.net.local_memory_runtime.core`.

The Local-only optimizer inventory is exactly **165,312 parameters** and equals the `local_memory` named-parameter set by object identity. Host parameters are frozen; fast state, sidecar and scheduler are runtime state and do not enter the optimizer.

### S0 and stream mapping

For the cursor0 T=16 segment:
- gathered consumers preserve stream-major order;
- S0 prefix is `None`;
- `prefix is None` iff consumer step is 0;
- every step > 0 has Local `[4,32]`;
- PAD never enters the gathered native-consumer stream.

The B1 producer reaches this route without changing the policy chunk32/33-frame contract.

### Exact serial gradient relay

For every Local-bearing consumer, the native boundary uses:
`p_leaf = p.detach().requires_grad_(True)`.

The native consumer objective is backpropagated once as:
`loss_i / N_valid`.

Leaf gradients are captured and explicitly relayed into the original B0 Local tensors after all native consumer graphs have been released.

This preserves the exact Local gradient while keeping only one expensive native graph resident at a time.

Independent serial-vs-monolithic validation found:
- identical mean objective: `0.69200861`;
- all Local-Memory parameter gradients matched;
- maximum absolute gradient difference: **7.451e-09**.

There is no extra GA division and no Local inner/reconstruction loss in the outer objective. Sample-coupled auxiliary loss is rejected.

### Gradient witnesses

Independent positive evidence observed non-zero gradients on:
- `core.slot_queries`;
- `core.w0_fast_in_weight`;
- `local_memory2llm.weight`;
- `local_memory_modality_embed`.

Bridge, encoder/core and Local subsystem gradients were finite. Frozen host gradients remained `None`.

### Success ordering

The implemented order is:

```text
scan
→ serial native forwards/backwards
→ relay backward into original Local tensors
→ transaction.successful_backward
→ Local-only optimizer.step
→ parameter finite check
→ adapter.commit
```

Independent observation confirmed that at `optimizer.step` time both sidecar and scheduler frontier were still empty. Fast state/frontier publish only after the step succeeds.

Committed fast state is detached fp32 ordinary tensor state.

### Failure ordering

The reviewed pair leaves sidecar/frontier unchanged and clears pending state for:
- native forward exception;
- NaN/non-scalar loss;
- missing/nonfinite prefix-leaf gradient;
- relay exception;
- nonfinite Local slow gradient;
- stale/copied capability;
- multi-member/count/member mismatch;
- pre-mutation optimizer exception.

Optimizer-step failure sets the fatal latch and rejects further prepare calls, consistent with the design's process-fatal boundary after optimizer step begins.

A continuation failure preserves the previously committed fast state/frontier.

## Scope boundary

`APPROVE_TO_CLOSE_V3_STAGE_B2B_SINGLE_SEGMENT_GRADIENT_RELAY_CPU_STATIC`

This closes only the CPU/static single-slot serial exact-gradient relay.

It does not approve:
- a real OmniMoT callback on GPU;
- RTX4090 S1 memory fit;
- trainer/launcher/DCP integration;
- multi-member/grouped GA training;
- inference;
- 8xH100 joint generation/action + Local training;
- SR/task capability claims.

The next Gate is B2-C: real RTX4090 S1 using one real RoboCasa cursor0 T=16 segment, Local-only optimizer and the ordinary OmniMoT native callback.
