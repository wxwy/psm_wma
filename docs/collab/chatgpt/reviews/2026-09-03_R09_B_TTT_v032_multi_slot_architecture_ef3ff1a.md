# ChatGPT Independent Re-Review — R09-B TTT v0.3.2 Multi-Slot Architecture @ ef3ff1a

**Date:** 2026-09-03  
**Reviewer:** ChatGPT (independent code / design / evidence reviewer)  
**Task/Gate:** `G0-R09-B-TTT-V032-MULTI-SLOT-ROUTE-REVIEW`

## 1. Review identity

- **remediation/design SHA under verdict:** `ef3ff1a9dfe73c62df5991d3ece88b1677a2b6d3`
- **request/ledger SHA observed on `V2`:** `4def62e6b96cae6fb90699dd6bbbfefd0233f65a`
- **actual Cosmos child/Gitlink:** `cf52f43dc328d4c8eec51923d66835125664dee5`
- **authority document:** `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`
- **prior blocked authority SHA:** `3f7e4341d5547eec23d2ff7370b45d34b51a96ca`
- **prior ChatGPT review:** `docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v032_multi_slot_architecture_3f7e434.md`
- **retained K_local=1 CPU-core closure:** root `fc5d4296b2d0e48dad37d7e9f7fd02e9b6cc1312`, child/Gitlink `cf52f43dc328d4c8eec51923d66835125664dee5`

The current remote `V2` head at the pre-write check is the request/ledger commit `4def62e6...`, whose parent is the exact remediation SHA `ef3ff1a...`. The request commit is not used as the design verdict target.

The required literal `git fetch origin V2` was attempted in a temporary local repository, but this environment still cannot resolve `github.com` (`Could not resolve host`). Remote freshness, ancestry and exact root Gitlink were therefore rechecked through the connected GitHub repository interface. No claim is made that shell fetch succeeded.

## 2. Verdict

**APPROVE_R09_B_TTT_V032_MULTI_SLOT_ARCHITECTURE**

The prior provenance blocker is closed. No remaining HIGH or MEDIUM blocker was found for the architecture Gate.

This approval is bound only to root `ef3ff1a9dfe73c62df5991d3ece88b1677a2b6d3` with `cosmos-framework@cf52f43dc328d4c8eec51923d66835125664dee5`.

## 3. Prior blocker closure

Prior HIGH-1 on `3f7e434...` was:

- v0.3.2 authority line 8 incorrectly labeled old `21d064f...` as the current Cosmos Gitlink even though the exact root pinned `cf52f43...`;
- this was material because Section 9 relied on the already-implemented `ContinualTTTLocalMemoryCore`, which exists in `cf52f43...` and not the old pre-core baseline.

The remediation closes this exactly:

```text
当前 Cosmos 实现基线 / Gitlink:
cf52f43dc328d4c8eec51923d66835125664dee5

历史 v0.3.1 / pre-CPU-core source baseline:
21d064f2b7c7aeeb67cfee50ac8d6722a944eddb
```

The root `ef3ff1a...` independently resolves the submodule to `cf52f43...`. The child Gitlink itself is unchanged by the remediation. The v0.3.2 architecture body is not rewritten; the substantive design remains the previously reviewed one-write/many-read design.

## 4. Accepted v0.3.2 architecture

The following are approved as the architecture authority for the next design Gate:

1. `K_local` is a configurable positive Local read-slot count; each new causal evidence still performs exactly one KVB write with one `K_t` and one `V_t`.
2. Multi-slot increases read bandwidth only: after the write, the same post-update `W_t` is read by `K_local` internal TTT queries.
3. Canonical query parameterization is `Q_t^k = theta_Q(e_t) + r_k`, where `r_k` are slow learned slot embeddings and the slots are not assigned fixed human semantics.
4. Q / slot embeddings do not participate in `L_inner`. They receive direct outer-task gradients through `M_local = f_W(Q)` and the downstream Cosmos Memory-conditioning path.
5. K/V remain part of the self-supervised KVB state-transition objective and are meta-learned from the unchanged outer Cosmos task loss through the differentiable inner update. `L_inner` is not added as a weighted ordinary outer loss term.
6. All formal reads use the post-update `W_t`, not `W_(t-1)`.
7. Local output shape generalizes to `[B,K_local,D_local]`, then projects to `[B,K_local,D_cosmos]` and enters the v0.3.1 Memory Prefix as K/V-only conditioning.
8. TTT internal `Q_t^k` and Cosmos attention `Q_MEM` remain distinct concepts. Internal TTT Q exists; Cosmos `Q_MEM` remains absent.
9. AR remains Memory-blind; DM may read Memory + AR + DM; Memory still has no attention output, residual update, post-attention norm/MLP, decoder or RF/FM target.
10. The closed `cf52f43` CPU core remains only the `K_local=1` compatibility/sanity implementation. It does not implement or authorize the multi-slot interface.
11. Any `K_local>1` core extension must receive its own exact implementation design and fresh same-SHA implementation review.

I found no contradiction between this architecture and the previously approved continual-TTT KVB/persistent-state/TBPTT contracts or the v0.3.1 K/V-only Memory Prefix contract.

## 5. Required next design content

The next authorized artifact is a **versioned docs-only multi-slot route / CPU-extension implementation design plus static verification plan**. That design should freeze at least:

- exact construction API for `K_local` and the query-bank/slot parameter registered shape;
- `read_many(state, Q:[B,K_local,D_ttt]) -> [B,K_local,D_local]` or an exact equivalent;
- proof that multi-slot read performs no additional KVB write and does not mutate fast state;
- `K_local=1` equivalence to the closed single-read core;
- slot permutation/output permutation contract;
- outer-gradient reachability to `theta_Q` and every slot parameter;
- parameter/count/checkpoint/optimizer implications of the new slot bank;
- fail-closed behavior for invalid `K_local` and shape mismatch;
- where the later Memory Prefix source/ABI audit consumes `[B,K_local,2048]` without reintroducing Memory queries.

### Non-blocking but mandatory-to-freeze in the next design

Because learned slot embeddings have a parameter shape dependent on `K_local`, the implementation design should treat `K_local` as a **construction/checkpoint-time model hyperparameter** unless it explicitly designs a fixed max-slot bank + mask/selection ABI. `K_local={1,4,8}` can be an ablation family, but one trained checkpoint must not be assumed to change its learned slot-bank cardinality arbitrarily at runtime without a separately audited compatibility mechanism.

## 6. Authorized next step only

After all required reviewers approve this same `ef3ff1a...` authority, the next step may only be:

- create the versioned root docs-only multi-slot route/CPU-extension implementation design and static verification plan;
- then submit that new exact design SHA for independent review.

## 7. Still prohibited

This approval does **not** authorize:

- multi-slot CPU-core/query-bank implementation;
- modification of `local_evidence.py` or the child Gitlink;
- Memory Prefix source/ABI implementation or attention/runtime wiring;
- chronology/native-loss/runtime integration;
- model config / optimizer / checkpoint refreeze;
- GPU/CUDA/torchrun;
- training, evaluation, inference or inference smoke;
- P4/P5 real operations;
- B2-T.

Any later design remediation or implementation SHA requires a fresh same-SHA review; this architecture approval cannot be reused as implementation authority.
