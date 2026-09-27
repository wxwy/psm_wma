# PSM-WMA V3 Stage B2-B Single-Segment Gradient Relay CPU/Static Design v0.1

- Date: 2026-09-27
- Gate: `V3-STAGE-B2B-SINGLE-SEGMENT-GRADIENT-RELAY-CPU-STATIC`
- Baseline formal pair: B2-A root `21f20f2c436e9627a938148afca039da6023d145` / child `366501b3b4626f30f0739d2e5765139a52f2308f`.
- B2-A closure bookkeeping does not replace that formal pair.
- Resource authority: Stage B2 resource profiles v0.3.
- CPU/static only. No checkpoint, real Cosmos model, GPU, trainer, DCP, inference, or long run.

## 1. Goal

Connect the already-closed pieces into one exact single-segment training lifecycle:

```text
B1 SegmentBatch
→ B0 scan (same model-owned Local slow parameters)
→ gathered native payload + S0/non-S0 Local prefix
→ serial native consumer loss/gradient relay
→ TTT slow backward
→ Local-only optimizer step
→ B0 fast-state commit
```

B2-B is intentionally one slot / one GA member. Multi-member GA/grouped training remains a later H100 production Gate.

## 2. Exact module identity

The `CanonicalLocalMemorySegmentAdapter` used by B2-B must be constructed from the exact same objects registered under the model:

```text
model.net.local_memory_runtime.encoder
model.net.local_memory_runtime.core
```

No duplicate encoder/core instance is allowed. This is required so `keys_to_select=["local_memory"]` owns exactly the slow parameters used by the scan.

The sidecar and scheduler remain runtime state and are not Parameters.

## 3. One-member transaction contract

B2-B accepts only:
- `GAWindowPlan.ga_effective == 1`;
- exact plan member == SegmentIdentity.member;
- planned count == produced/scan valid count;
- one pending adapter scan at a time.

It rejects multi-member plans before native consumer work.

The runner/capability must preserve exact object identity for segment identity, transaction and scan result; stale/equal-but-not-identical capabilities fail closed.

## 4. S0 / Local mapping

After B0 scan and gather:
- gathered payload order is stream-major valid consumer order;
- `local_prefix is None` iff gathered consumer step == 0;
- every valid consumer with step > 0 has Local `[K=4,D=32]`;
- PAD never appears in gathered payloads.

B2-B directly tests this rule. This closes the B2-A deferred S0 caller responsibility.

## 5. Native consumer callback ABI

B2-B defines a narrow callback/protocol rather than importing the real trainer:

```text
native_forward(payload, local_prefix_leaf_or_none, consumer_index)
    -> NativeConsumerResult(loss: scalar Tensor, output: optional metadata)
```

The B2-C 4090 Gate will implement this callback with:
- one-item `custom_collate_fn`;
- move to model device;
- `OmniMoTModel.training_step(..., _local_memory_prefixes=(leaf_or_none,))`.

B2-B tests use a deterministic frozen toy host.

The callback must report/reject sample-coupled auxiliary loss; this Gate supports the dense Edge objective only.

## 6. Serial exact-gradient relay

Let N be the exact number of gathered valid consumers.

Before the segment:
- zero Local optimizer grads exactly once.

For each consumer:
- if Local is None (S0), run the native loss for accounting; no Local backward is required;
- otherwise create a detached leaf from the Local prefix with `requires_grad=True`;
- run one native consumer forward;
- require finite scalar loss;
- backward `loss / N`;
- require a finite prefix-leaf gradient and save a detached clone;
- bridge/embed gradients accumulate normally;
- release this native graph before the next consumer.

After all native consumers:
- backward the saved gradients into the corresponding original Local tensors from B0 scan;
- require all selected Local grads finite;
- require at least one runtime/core slow grad and bridge grad non-zero in the smoke/test fixture.

No native consumer batch may contain more than one sample in the serial runner.

## 7. Success ordering

Success order is frozen:

```text
scan
→ all native forwards
→ serial native backwards
→ TTT gradient relay backward
→ transaction.successful_backward(...)
→ Local-only optimizer.step()
→ verify selected Local parameters finite
→ adapter.commit(...)
```

Fast state must not publish before optimizer-step success.

After commit:
- sidecar fast state is detached fp32 ordinary tensor state;
- transaction is closed for the one-member plan;
- scheduler frontier is updated exactly once.

## 8. Failure ordering

Any of the following before commit must leave sidecar/frontier unchanged and no pending adapter scan:
- native forward exception;
- non-scalar/nonfinite native loss;
- missing/nonfinite prefix-leaf gradient;
- relay backward exception;
- nonfinite Local slow gradient;
- optimizer-step exception;
- stale capability / identity mismatch.

On failure:
- zero Local slow grads;
- discard/terminalize the pending B0 transaction;
- do not commit fast state.

An optimizer exception after partial optimizer mutation is treated as process-fatal and is not claimed rollback-safe; tests use a pre-mutation failing optimizer. Formal long-run optimizer atomicity is a later Gate.

## 9. Objective / no double scaling

B2-B one-member serial relay owns exactly one division by `N_valid` across consumer losses.

It must not:
- divide again by GA;
- add Local inner/reconstruction loss to the outer objective;
- reinterpret B0 `GAWindowPlan.objective` for multi-member use.

The Local inner loss remains exclusively the fast-update mechanism.

A deterministic toy fixture must compare:
- monolithic reference mean loss/backward;
- serial relay mean loss/backward;

and show matching gradients for original prefixes/upstream Local slow parameters, bridge and modality embedding within numerical tolerance.

## 10. CPU/static acceptance

Tests must prove:

1. exact model-runtime encoder/core identity and optimizer parameter ownership;
2. B1-like SegmentBatch → B0 scan → gathered S0/local mapping;
3. stream-order/cardinality preserved;
4. serial callback is invoked one consumer at a time;
5. serial relay gradients match monolithic reference;
6. all required Local grad groups finite/non-zero in the positive fixture;
7. no frozen toy-host parameter grad;
8. successful optimizer step changes Local slow params, then and only then commits fast state/frontier;
9. candidate/committed fast state is detached fp32 ordinary tensors;
10. forward failure / NaN loss / missing leaf grad / relay failure / optimizer failure / stale capability all do not commit;
11. multi-member plan rejected before native work;
12. exactly one `/N_valid` scaling;
13. no Local auxiliary objective;
14. B0/B1/B2-A regression suites remain PASS.

## 11. Implementation scope

Prefer one new module plus tests:
- `cosmos_framework/model/generator/mot/local_memory_native_segment.py`
- `cosmos_framework/model/generator/mot/local_memory_native_segment_test.py`

Existing B0/B1/B2-A production files should remain unchanged unless a tiny import/type-only seam is unavoidable. Any semantic edit needs explicit justification.

Do not modify trainer, launchers, checkpoint, inference, policy server, dataset, or GPU config in B2-B.

## 12. Next Gate

After fresh B2-B approval:
- B2-C: actual RTX4090 24GB S1 using a real RoboCasa cursor0 T=16 segment and real OmniMoT native callback, Local-only optimizer profile, peak-memory Evidence.
- No formal H100 training until B2-C closes.

