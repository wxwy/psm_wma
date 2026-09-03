# ChatGPT Independent Review — R09-B TTT v0.3.1 Architecture / Implementation Route @ af9caf0

**Date:** 2026-09-03  
**Reviewer:** ChatGPT (independent code / design / evidence reviewer)  
**Task/Gate:** `G0-R09-B-TTT-V031-ARCHITECTURE-ROUTE-REVIEW`

## 1. Review identity

- **implementation/design SHA under verdict:** `af9caf0cfffbb70b7fbf2e8bc3f763bf9bd9d1a2`
- **request/ledger SHA observed on `V2`:** `d99490a169f84fa01b005db757609f5909a3c097`
- **v0.3.1 architecture authority:** `4754f5bc25859894e6fc963a9484640ccb5cd082`
- **CPU-core design in exact reviewed state:** `216f1261c81cf6f2bd13053b5e937beeccd335b3`
- **Cosmos submodule/Gitlink:** `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- **route document:** `docs/build/PSM-WMA_R09_B_TTT_v031_implementation_route_v0.1_2026-09-03.md`
- **architecture document:** `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.1.md`
- **CPU-core document:** `docs/build/PSM-WMA_R09_B_TTT_CPU_algorithm_implementation_design_v0.1_2026-09-03.md`

The current remote `V2` head at final review check is the request/ledger commit `d99490a...`, whose parent is the exact reviewed SHA `af9caf0...`. The ledger commit is not used as a substitute for the implementation/design verdict.

The required literal `git fetch origin V2` was attempted in a temporary local repository, but this execution environment cannot resolve `github.com` (`Could not resolve host`). Remote freshness and branch ancestry were therefore verified through the connected GitHub repository interface. This limitation is recorded explicitly; no claim is made that the shell fetch succeeded.

The root at `af9caf0...` resolves `cosmos-framework` to the declared Gitlink `21d064f2...`.

## 2. Verdict

**APPROVE_R09_B_TTT_V031_IMPLEMENTATION_ROUTE**

**APPROVE_TO_IMPLEMENT_R09_B_TTT_V02_CPU_ALGORITHM_CORE**

Both approvals are bound to the exact repository state at root `af9caf0cfffbb70b7fbf2e8bc3f763bf9bd9d1a2` plus Gitlink `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

The second approval is a fresh review of the unchanged CPU-core design as present in the `af9caf0` repository state. It is not reuse of an approval for an older SHA. `216f126 -> af9caf0` does not modify the CPU-core design file; the intervening changes add the v0.3/v0.3.1 architecture documents, the implementation route, and status bookkeeping.

## 3. Architecture review

### 3.1 K/V-only Memory Prefix is the correct v0.3.1 interpretation

Accepted contract:

```text
Memory Prefix : K/V-only, read-only conditioning context
AR            : native causal Q/K/V; cannot read Memory or DM
DM            : native Q/K/V; may read Memory + AR + DM
```

The route correctly preserves the central v0.3.1 constraints:

- no `Q_MEM`;
- no Memory query row;
- no Memory attention output;
- no Memory residual update;
- no Memory post-attention norm or MLP/FFN;
- no Memory decoder or native RF/FM loss target;
- Local TTT fast state remains outside the Cosmos backbone.

This is materially different from the superseded Local-as-ordinary-GEN-token path and is the correct implementation direction for the current authority.

### 3.2 Memory must leave the native query pack

The current Gitlink still treats Local as an ordinary packed sequence span: the Local payload is included in native sample length / full split, receives ordinary sequence indexes and position ids, and is scattered back into the packed GEN stream after adapter/embed.

Therefore the route is correct to require:

```text
native PackedSequence : [AR, DM] only
MemoryPrefixContext   : separate per-sample hidden payload + offsets + present
```

A separate Memory context is the minimal structure that can satisfy all of the following simultaneously:

- Memory does not create query indexes;
- Memory does not advance native AR/DM position or mRoPE authority;
- Memory produces no Transformer-side hidden-state output;
- AR stays on its existing causal path;
- DM gains an additional K/V provider.

Keeping Memory in the native `PackedSequence` and merely masking its query row would preserve too much of the superseded token semantics and would not be an adequate v0.3.1 implementation.

### 3.3 Single varlen joint softmax is the right first dense implementation

The current dense `two_way_attention()` already computes:

1. a separate causal AR pass from causal Q/K/V; and
2. a generator full-attention pass where DM queries attend the native per-sample `[AR, DM]` K/V set.

For v0.3.1, the mathematically correct minimal extension is:

```text
AR pass : unchanged
DM Q    : existing full_q
DM KV   : per-sample [K_MEM, K_AR, K_DM]
```

with one varlen attention call using separate Q and KV cumulative offsets.

This is preferred over two independent softmaxes followed by addition: separate normalization changes the attention function and is not equivalent to one softmax over the union of allowed keys. The route is therefore correct to freeze a single joint KV softmax for the first dense slice.

### 3.4 Fail-closed compatibility boundary is adequate

For the first implementation slice, it is appropriate to support only the current LIBERO Edge `two_way` dense path and fail closed when Memory is present for unsupported combinations, including:

- `three_way`;
- FlexAttention;
- NATTEN / multidimensional sparse attention;
- multi-control paths not separately audited;
- CP/Ulysses;
- CUDA graph combinations.

No-Memory must continue through the original branch unchanged and must be tested for exact parity. This scope is narrow enough to be reviewable and avoids silently extending a new Memory ABI into attention/parallel modes whose offset, mask, sharding or graph-capture contracts have not yet been frozen.

### 3.5 Exact source/ABI audit must precede Memory Prefix runtime wiring

The route correctly does **not** freeze the following from inference or naming alone:

1. Memory pre-attention norm family, epsilon, sharing granularity and checkpoint/FSDP behavior;
2. Memory K/V projection ownership;
3. Memory position/RoPE semantics relative to DM queries;
4. Memory-present warm-start behavior.

The warm-start warning is especially important: appending a zero K/V key still changes a softmax denominator, so `K_MEM=V_MEM=0` is not automatically function-preserving. The exact treatment must be decided in the later source/ABI design Gate, not improvised during runtime implementation.

## 4. CPU-core design re-review

The v0.3.1 architecture change does not invalidate the backbone-independent continual-TTT core frozen in the CPU algorithm design:

```text
completed causal evidence
 -> learned theta_K/theta_Q/theta_V
 -> per-sample KVB inner update of four-member fast MLP state
 -> post-update query read
 -> Local token [B,1,D_local]
```

The CPU core owns only Local evidence projection, fast-state transition/read, reset/detach primitives and their CPU contract tests. It does not own native packing, Cosmos K/V projection, Memory pre-attention norm, mRoPE, attention dispatch, chronology, outer loss, inference registry or optimizer/config authority.

The exact CPU design remains internally consistent with v0.2.1:

- `K/Q: 256 -> D_ttt`, `V: 256 -> D_local`;
- fast MLP `D_ttt -> D_ff -> D_local`;
- four-member per-sample fast-state pytree with learned W0;
- feature-mean per-sample KVB loss;
- post-update read;
- no batch/valid/rank/grad-accum scaling of the inner step;
- `create_graph=True` for the canonical training meta-gradient;
- detach changes graph connectivity, not fast-state values;
- no chronology or production state owner is hidden inside the core.

Therefore **Gate B may start before the later Memory Prefix source/ABI audit**. Doing so does not prejudge the Memory Prefix ABI and does not require touching any attention/packer/runtime seam.

## 5. Non-blocking source-anchor correction

**LOW / non-blocking documentation note**

`docs/build/PSM-WMA_R09_B_TTT_v031_implementation_route_v0.1_2026-09-03.md:62` says the current LIBERO recipe “沿用 `model_config.py:220` 的默认 `joint_attn_implementation="two_way"`”. The effective LIBERO Edge recipe actually copies `EDGE_MODEL_CONFIG`, and `cosmos_framework/configs/base/experiment/sft/models/edge_model_config.py:44` explicitly sets:

```python
joint_attn_implementation="two_way"
```

The effective runtime conclusion is unchanged: current LIBERO Edge is `two_way`. This does not block the route or CPU-core implementation. To avoid creating a new route SHA solely for wording cleanup, the later Gate-C exact source/ABI audit should cite the effective recipe/config path explicitly rather than inheriting the shorthand `model_config.py:220` statement.

## 6. Authorized next action

This review authorizes **Gate B only** as the executable implementation step:

- modify only:
  - `cosmos-framework/cosmos_framework/model/generator/mot/local_evidence.py`
  - `cosmos-framework/cosmos_framework/model/generator/mot/local_evidence_test.py`
- run only the CPU-only contract tests / `py_compile` / diff-check commands frozen by the CPU-core design;
- create the child implementation commit and the necessary root Gitlink/status bookkeeping commit;
- submit the resulting exact root SHA + new submodule SHA/Gitlink for a fresh CPU-core implementation closure review.

After Gate-B implementation closure, the next design/static activity is Gate C: the documentation-only exact Memory Prefix source/ABI audit. Gate C does not itself authorize Memory Prefix runtime code.

## 7. Explicitly not authorized

This approval does **not** authorize:

- Memory Prefix runtime wiring;
- packer/attention/block/model ABI implementation outside the Gate-B CPU core;
- chronology / state-owner integration;
- native outer-loss/noise integration;
- model construction or production Local runtime wiring;
- GPU/CUDA/torchrun;
- bounded GPU smoke before its own Gate;
- training or formal LIBERO runs;
- evaluation;
- inference or inference smoke;
- inference request/state registry implementation;
- optimizer/config/checkpoint authority refreeze;
- P4/P5 real preflight, staging, candidate, record/refreeze, export or compose;
- B2-T.

Any implementation/remediation commit after `af9caf0...`, including the upcoming child CPU-core implementation + root Gitlink bump, requires a fresh same-SHA review. These approvals may not be reused for that new implementation SHA.
