# ChatGPT Independent Review — R09-B TTT v0.3.2 Multi-Slot Architecture @ 3f7e434

**Date:** 2026-09-03  
**Reviewer:** ChatGPT (independent code / design / evidence reviewer)  
**Task/Gate:** `G0-R09-B-TTT-V032-MULTI-SLOT-ROUTE-REVIEW`

## 1. Review identity

- **design/authority SHA under verdict:** `3f7e4341d5547eec23d2ff7370b45d34b51a96ca`
- **request/ledger SHA observed on `V2`:** `34fb5d3a862cd1786e93d05182addf2b6ed80d94`
- **actual root Gitlink at `3f7e434`:** `cf52f43dc328d4c8eec51923d66835125664dee5`
- **authority document:** `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`
- **superseded interface authority:** `4754f5bc25859894e6fc963a9484640ccb5cd082` (v0.3.1)
- **retained single-read CPU-core closure:** root `fc5d4296b2d0e48dad37d7e9f7fd02e9b6cc1312`, child/Gitlink `cf52f43dc328d4c8eec51923d66835125664dee5`

The current remote `V2` head at the final pre-write check was `34fb5d3...`; it is a request/ledger commit above the v0.3.2 authority chain and does not replace the exact design SHA under review.

The required literal `git fetch origin V2` was attempted in a temporary local clone, but this execution environment still cannot resolve `github.com` (`Could not resolve host`). Remote freshness, ancestry and exact Gitlink were therefore rechecked through the connected GitHub repository interface. No claim is made that shell fetch succeeded.

## 2. Verdict

**REQUEST_CHANGES**

The v0.3.2 multi-slot mathematical/architectural direction is accepted, but the authority cannot be frozen on this exact SHA because its declared current Cosmos baseline/Gitlink is false for the reviewed root.

## 3. Accepted architecture

The following v0.3.2 contracts are accepted and should be preserved in the remediation:

1. `K_local` generalizes Local read bandwidth; one new causal evidence still performs exactly **one** KVB write with one `K_t` and one `V_t`.
2. Multi-slot readout uses `K_local` evidence-conditioned internal TTT queries, canonically `Q_t^k = theta_Q(e_t) + r_k`, and reads only from the **post-update** `W_t`.
3. Q / slot queries do not enter `L_inner`; `theta_Q` and `r_k` are trained directly through the unchanged Cosmos outer-task path, while `theta_K/theta_V` are meta-learned through the differentiable inner update.
4. `L_inner` remains a state-transition objective rather than `lambda * L_inner` added to the outer task loss.
5. The resulting tensor is `[B,K_local,D_local]`, projected to `[B,K_local,D_cosmos]`, and enters the v0.3.1 Memory Prefix as **K/V-only** conditioning. TTT internal Q is not Cosmos `Q_MEM`; Cosmos `Q_MEM` remains nonexistent.
6. AR remains Memory-blind; DM may read Memory + AR + DM.
7. The already-closed `cf52f43` CPU core is correctly retained only as `K_local=1` compatibility/sanity evidence. It is not a multi-slot implementation and grants no automatic authority to extend the core.
8. A later multi-slot CPU extension must prove one-write/many-read semantics, no fast-state mutation during `read_many`, slot-permutation behavior, K=1 read equivalence, and outer-gradient reachability to `theta_Q` and all slot parameters.

I found no architecture-level contradiction between these contracts and the previously approved v0.2/v0.2.1 continual-TTT mathematics or v0.3.1 K/V-only Memory Prefix contract.

## 4. Blocking finding

### HIGH-1 — authority declares the wrong current Gitlink

**Location:** `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md:8`

The authority states:

```text
当前 Cosmos 实现基线 / Gitlink = 21d064f2b7c7aeeb67cfee50ac8d6722a944eddb
```

But the exact reviewed root `3f7e4341...` resolves `cosmos-framework` to:

```text
cf52f43dc328d4c8eec51923d66835125664dee5
```

This is not merely cosmetic. Section 9 of the same authority treats the current `ContinualTTTLocalMemoryCore` as the `K_local=1` compatibility/sanity core, and that implementation was added in `cf52f43...`; it does not exist in the old `21d064f...` baseline. Freezing the route while the authority labels `21d064f...` as the current baseline would allow the next source/ABI audit to inspect the wrong child tree and would break exact provenance between architecture, current CPU-core state and subsequent implementation design.

The old `21d064f...` SHA may remain documented as the **historical v0.3.1/pre-CPU-core Cosmos baseline**, but it must not be labeled as the current Gitlink for `3f7e434` or its remediation.

## 5. Acceptance criteria for remediation

A docs/provenance-only remediation is sufficient. On a new exact root SHA:

1. change the v0.3.2 authority header so the current Gitlink is `cf52f43dc328d4c8eec51923d66835125664dee5`;
2. if `21d064f...` is retained, label it explicitly as historical v0.3.1/pre-CPU-core source baseline rather than current state;
3. preserve the accepted one-write / many-read architecture, Q/K/V gradient responsibilities and v0.3.1 K/V-only Memory Prefix contract unchanged;
4. keep the existing `cf52f43` CPU core classified strictly as `K_local=1` compatibility/sanity implementation;
5. do not modify the child Gitlink or implementation for this remediation; `git diff --check` is sufficient static validation;
6. submit the new root SHA for a fresh same-SHA re-review before freezing any multi-slot route/implementation design.

### Non-blocking implementation-design note

Because learned slot embeddings add slow parameters whose shape depends on `K_local`, the next multi-slot implementation design should explicitly freeze whether `K_local` is a construction/checkpoint-time model hyperparameter (recommended) and how `1/4/8` ablations map to separate parameter shapes/checkpoints. Do not silently imply that a trained checkpoint can change `K_local` arbitrarily at runtime unless a max-bank/masking contract is separately designed and audited.

## 6. Scope after this verdict

Until the provenance remediation is approved, only the docs-only correction above is authorized.

Still prohibited:

- multi-slot CPU-core extension / query-bank implementation;
- Memory Prefix source/ABI route freeze beyond the remediation;
- Memory Prefix runtime/attention wiring;
- chronology/native-loss/runtime integration;
- model config / optimizer / checkpoint refreeze;
- GPU/CUDA/torchrun, training, evaluation or inference;
- P4/P5 real operations;
- B2-T.

Any remediation creates a new design SHA and requires a fresh exact-SHA review. This `REQUEST_CHANGES` is bound only to `3f7e4341d5547eec23d2ff7370b45d34b51a96ca` with actual Gitlink `cf52f43dc328d4c8eec51923d66835125664dee5`.
