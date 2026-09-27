# PSM-WMA V3 Stage B2 Resource Profiles v0.3 — 4090 Exact Serial Relay vs 8xH100 Formal

- Date: 2026-09-27
- Supersedes v0.2 for 4090 execution geometry only.
- Local-Memory trainable inventory is unchanged from v0.2: **165,312 params**.
- B2-A formal pair: root `21f20f2c436e9627a938148afca039da6023d145` / child `366501b3b4626f30f0739d2e5765139a52f2308f`.

## 1. Why S1 changes

A real RoboCasa cursor0 segment normally contains 16 valid consumers. Starting directly from a later terminal remainder would require a previously committed fast state and therefore is not a valid fresh-slot shortcut.

Do not truncate a real episode, fake `training_stream_end`, reduce T, or drop consumers merely to fit 24GB.

Instead, preserve one real T=16 segment and serialize the expensive native Cosmos consumer forwards.

## 2. Exact 4090 serial gradient relay

The 4090 TTT-only profile freezes every host parameter and trains only the 165,312 Local-Memory parameters.

For one B0 scan:

1. scan the real T=16 SegmentBatch once with `create_graph=True`;
2. gather the exact valid native payloads and their Local32 prefixes;
3. process consumers in stream order, one native Cosmos consumer at a time;
4. for a consumer with Local prefix `p`, create `p_leaf = p.detach().requires_grad_(True)` only at the native-host boundary;
5. run the ordinary native policy forward with `p_leaf`;
6. backward `loss_i / N_valid`; bridge/embed grads accumulate normally and `p_leaf.grad` is captured;
7. free that native consumer graph before loading the next consumer;
8. after all consumers, backward the original TTT prefixes with the captured per-prefix gradients;
9. validate Local grads, perform one Local-only optimizer step, then commit the B0 fast-state candidate.

The detach in step 4 is permitted only because the exact gradient is explicitly relayed back in step 8. An unpaired detach remains forbidden.

S0 has no Local prefix. Under the TTT-only profile its native loss has zero Local gradient; it is included in detached loss accounting but requires no Local backward.

## 3. Exact objective scaling

For Edge, the host is a dense model with no MoE load-balancing auxiliary. The one-member segment objective is the mean of the native per-consumer total policy losses:

```text
L_segment = (1 / N_valid) * sum_i L_native(i)
```

Each Local-bearing serial backward therefore uses `L_native(i) / N_valid`.

B2-B must prove on a deterministic toy frozen host that serial gradient relay matches a monolithic reference gradient for:
- original Local prefixes / upstream TTT slow params;
- local_memory2llm;
- local_memory_modality_embed.

This serial relay is not authorized for a host with sample-coupled auxiliary losses. It must fail closed if such an objective is reported.

## 4. Peak-memory purpose

Only one native Cosmos consumer activation graph is resident at a time. The shared TTT graph remains live across the segment, but it is tiny relative to the 4B host.

Record on 4090:
- peak allocated CUDA memory;
- peak reserved CUDA memory;
- per-consumer peak if practical;
- forward/backward completion;
- Local grad witness;
- optimizer step and fast-state commit.

## 5. 4090 S1 / S2

### S1 required
- real RoboCasa cursor0 segment;
- one stable slot;
- T=16 unchanged;
- up to 16 valid consumers exactly as the producer emits;
- serial native consumer forwards using the exact relay;
- one Local-only optimizer step;
- no fake terminal/truncation.

### S2 optional
If memory permits, run the same segment as one native batch for comparison. S2 is not required to close the 4090 integration smoke if S1 is correct.

## 6. H100 formal profile

8xH100 restores the joint trainable set:
- existing Edge generation/action-policy parameters;
- complete Local-Memory subsystem.

The 4090 serial relay is not the formal joint-training contract because detached prefix leaves would omit host-parameter gradients unless those were separately relayed. H100 formal training uses ordinary joint autograd and its production grouped/GA geometry.

## 7. Frozen algorithm constants

Unchanged:
- T=16
- K_local=4
- local_dim=32
- evidence_dim=256
- ttt_dim=64
- fast_hidden=256
- inner_lr=0.1
- raw15
- policy chunk=32 / 33-frame consumer
- cached latent remains Local evidence only, not main policy input.

