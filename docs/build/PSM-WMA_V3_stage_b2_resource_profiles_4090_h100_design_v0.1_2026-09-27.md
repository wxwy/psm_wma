# PSM-WMA V3 Stage B2 Resource Profiles — 4090 Smoke vs 8xH100 Formal

- Date: 2026-09-27
- Status: DESIGN_FROZEN_FOR_B2_IMPLEMENTATION
- Applies after Stage B1 closure formal pair `93db96df841a14c4c3ef73bf6b4488142adcf567 / 1ecebf1ab2fa64bc1d5906959c4cb1fe1d1edc5a`.
- Current smoke host: NVIDIA GeForce RTX 4090, 24564 MiB.
- Formal training host: 8xH100.
- This document only separates trainable-parameter/resource profiles. It does not authorize long training.

## 1. Current host-trainable set

The current `action_policy_robocasa_edge` inherits optimizer selection from Nano:

```text
moe_gen
time_embedder
vae2llm
llm2vae
action2llm
llm2action
action_modality_embed
```

`keys_to_select` is an allowlist and freezes all unmatched model parameters by setting `requires_grad=False`.

This is generation/action-policy tuning, not reasoner-tower tuning. The reasoner/understanding tower is not the intended trainable branch here.

## 2. 4090 smoke profile: TTT-only slow parameters

Purpose: validate B2 wiring, outer-gradient reachability, fast-state lifecycle, commit/abort semantics and checkpoint inventory under 24GB. It is not a capability-training run.

Trainable:
- LocalEvidenceEncoder slow parameters;
- ContinualTTTLocalMemoryCore slow parameters;
- total current B0 slow-parameter count = 95,680.

Not optimizer-trainable:
- `moe_gen`
- `time_embedder`
- `vae2llm`
- `llm2vae`
- `action2llm`
- `llm2action`
- `action_modality_embed`
- all reasoner/backbone parameters.

B2 must register all TTT slow modules under one stable model parameter namespace containing `local_memory`; the 4090 smoke optimizer uses only:

```text
keys_to_select = ["local_memory"]
```

Acceptance must enumerate the exact selected parameter names and assert:
1. every selected parameter belongs to the frozen TTT slow inventory;
2. every TTT slow parameter is selected;
3. zero non-TTT parameter is selected;
4. fast state remains ordinary fp32 tensors and never enters optimizer/state_dict as Parameters.

Keep slow optimizer hyperparameters unchanged for smoke unless a later design changes them; only trainable selection changes.

## 3. Critical gradient rule

Freezing host parameters is allowed; wrapping the downstream Cosmos host forward in `torch.no_grad()`, inference mode, or detaching injected Local tokens is forbidden.

Outer loss must still backpropagate through the frozen host to the TTT slow parameters.

Required witness:
- finite nonzero outer-loss gradients on all required TTT slow parameter groups;
- no gradient on frozen host parameters;
- optimizer step changes at least one TTT slow parameter;
- a sampled frozen host parameter remains bitwise unchanged.

## 4. 4090 smoke geometry

Do not change frozen algorithmic constants:
- TTT `T=16`
- `K_local=4`
- `local_dim=32`
- `evidence_dim=256`
- `ttt_dim=64`
- `fast_hidden=256`
- `inner_lr=0.1`
- executed action raw15
- policy chunk=32 / 33-frame consumer contract.

Memory reductions must come from run geometry, not algorithm changes.

Use two 4090 smoke levels:

### S1 minimal production-route backward
- one stable slot;
- one terminal segment with small valid remainder (prefer 1-2 valid consumers, tail PAD to T=16);
- one optimizer step;
- TTT-only trainable;
- Stage-A policy forward/loss unchanged;
- no EMA, compile disabled, activation checkpointing retained.

Goal: prove exact real-data producer -> TTT -> Local injection -> Cosmos loss -> backward -> transaction commit path fits and is correct.

### S2 full-T16 single-slot smoke, only if 24GB permits
- one stable slot;
- one full 16-consumer segment;
- TTT-only trainable;
- one optimizer step.

OOM in S2 is a resource result, not authorization to shrink T/K or alter policy chunk. Canonical multi-slot geometry is deferred to H100.

## 5. What freezing does and does not save

TTT-only selection removes host parameter gradients and almost all host optimizer-state allocation, which is the correct first memory reduction for 24GB.

It does not remove all backward activation memory: because the outer loss must reach the TTT Local tokens, autograd still traverses the frozen downstream host.

Therefore 4090 smoke should also:
- keep activation checkpointing enabled;
- keep the smallest possible real consumer count for S1;
- avoid packing unrelated samples into the same smoke batch;
- keep EMA disabled and compile disabled as in the current Edge recipe;
- record peak allocated/reserved CUDA memory.

Do not use cached latent as the main policy input merely to save memory; that remains a separate parity/acceleration Gate.

## 6. 8xH100 formal profile

Before formal training, run one matched H100 integration smoke.

Formal optimizer trainable set restores the current Edge generation/action-policy parameters and adds TTT slow parameters:

```text
moe_gen
time_embedder
vae2llm
llm2vae
action2llm
llm2action
action_modality_embed
local_memory
```

The exact final list must be asserted from `named_parameters()` after B2 wiring.

Formal H100 training must restore the intended production slot/grouped/GA geometry; the 4090 S1/S2 reduced run geometry must not silently become the training contract.

## 7. Gate interpretation

4090 TTT-only smoke answers:
- is B2 wired correctly?
- does outer loss train TTT?
- are host params frozen as intended?
- do fast-state transaction semantics survive a real backward?
- what is peak memory on a 24GB 4090?

It does not answer:
- final convergence;
- matched performance versus Native Cosmos;
- joint generator+TTT optimization behavior;
- 8xH100 throughput/scaling;
- final SR.

Those belong to the H100 matched smoke / formal training Gate.
