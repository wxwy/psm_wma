# PSM-WMA V3 Stage B2-A Native Memory Prefix CPU/Static Design v0.1

- Date: 2026-09-27
- Gate: `V3-STAGE-B2A-NATIVE-MEMORY-PREFIX-CPU-STATIC`
- Baseline: Stage B1 closure pair root `93db96df841a14c4c3ef73bf6b4488142adcf567` / child `1ecebf1ab2fa64bc1d5906959c4cb1fe1d1edc5a`.
- Resource authority: Stage B2 resource profiles v0.2.
- V2 commit `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92` may be read only as semantic reference. No cherry-pick.
- This Gate is CPU/static only. No model checkpoint, real GPU, trainer loop, DCP, training/eval, or long run.

## 1. Goal

Add the minimum native Cosmos seam needed for B0 Local tokens `[K_local=4, local_dim=32]` to affect the official policy flow-matching forward as a **generation-side K/V-only Memory Prefix**.

This Gate does not yet run a real segment through GPU. It proves the data/attention/gradient semantics needed by the subsequent segment-backward and 4090 S1 Gates.

There is no Local auxiliary objective. The only outer supervision remains the native Cosmos policy objective.

## 2. K/V-only invariant

Local Memory must not become an ordinary packed token.

For a sample with Local:
- Local contributes no Q tokens.
- Local consumes no native sequence index.
- Local changes neither `sequence_length`, `sample_lens`, `split_lens`, nor `attn_modes`.
- Local has no mRoPE position and no RoPE application.
- Local has no timestep/noise token and no MSE/CE loss index.
- Local is visible to generation/diffusion queries through additional K/V only.
- Causal text/reasoner self-attention remains unchanged.
- S0 carries no prefix.

The formal Edge path is `joint_attn_implementation="two_way"`; B2-A only authorizes the two-way training path. Three-way, multiview, context parallel, CUDA graphs, inference KV-cache integration and online Local inference stay fail-closed/out of scope.

## 3. Data/packing ABI

Add an explicit Local field to the clean-generation carrier:

```text
GenerationDataClean.x0_tokens_local_memory:
    list[Tensor[K_local,local_dim]] | None
```

The dense list contains entries only for samples whose `SequencePlan.has_local_memory=True`, in sample order.

Add:

```text
SequencePlan.has_local_memory: bool = False
```

The packer must maintain a separate `idx_local_memory`. For every sample it stores exactly one out-of-band entry:
- present sample → Tensor[K=4,D=32]
- absent sample → None.

The finalized PackedSequence owns immutable per-sample Local-prefix payload metadata, but no Local native span.

No legacy `data_batch["local_memory"]` authority is allowed in B2-A. The only model-side Local input is an explicit private/canonical override supplied after B0 scan.

## 4. MemoryPrefixContext

Implement a small dedicated module, semantically equivalent to the proven V2 concept but re-authored against current Cosmos:

```text
MemoryPrefixContext:
    hidden          [N_present*K, hidden_size]
    sample_offsets  [B+1] long
    present         [B] bool
    k_local         int (=4)
```

Build it from per-sample Local32 tokens using:
- `local_memory2llm`
- `local_memory_modality_embed`.

Validate K=4 and D=32 before projection. Mixed S0/non-S0 batch presence must preserve sample isolation.

The bridge parameters are part of the Local-Memory trainable namespace and use the non-zero initialization frozen in resource profiles v0.2.

## 5. Attention semantics

For each MoT decoder layer, after the normal generator-side input layernorm:
- normalize Memory Prefix with the same generator-side memory input normalization used for generator K/V;
- K = generator `k_proj_moe_gen` followed by generator K norm;
- V = generator `v_proj_moe_gen`;
- **do not apply RoPE** to memory K;
- concatenate memory K/V before that sample's native K/V for generation-query attention only.

Native Q/K/V values and native offsets remain unchanged.

Mixed-presence batch must be represented by per-sample prefix offsets; no Local from one sample may be visible to another.

When no Local is present, native attention output and metadata must be exactly the ordinary path.

## 6. Model registration / parameter namespace

When B2 Local is enabled, register under `net`:
- `local_memory_runtime`: an nn.Module owner containing the B0 LocalEvidenceEncoder + ContinualTTTLocalMemoryCore;
- `local_memory2llm`;
- `local_memory_modality_embed`.

All resulting parameter names must contain substring `local_memory`.

The B0 fast state remains plain fp32 tensors owned by runtime sidecar/transaction state; it must not become nn.Parameter and must not enter the optimizer inventory.

B2-A may add explicit config fields:
- local_memory_enabled
- local_memory_dim=32
- evidence_dim=256
- action_dim=15
- ttt_dim=64
- fast_hidden_dim=256
- inner_lr=0.1
- ttt_tbptt_steps=16
- k_local=4.

No state/dt/age reintroduction.

## 7. Private native-forward seam

Add a private/canonical training seam that can attach a tuple/list of Local prefixes 1:1 to an already materialized native consumer batch.

Required ordering:

```text
B0 scan
→ gathered payloads + gathered Local prefixes
→ ordinary native consumer materialization
→ assert native materialization is Local-neutral
→ attach Local presence to copied SequencePlan/GenerationDataClean
→ native pack/noise/denoise/native loss
```

The seam must not let the ordinary dataset/collate path become a second Local authority.

No commit occurs in model forward. Fast-state commit remains a post-backward transaction action for B2-B.

## 8. CPU/static acceptance

Tests must directly prove:

1. parameter namespace/inventory:
   - complete Local-Memory selected set;
   - no host param matches `keys_to_select=["local_memory"]`;
   - expected Edge Local trainable count = 165,312 when hidden_size=2048.

2. non-zero first-step gradient:
   - synthetic native loss through Memory Prefix gives non-zero gradient to local_memory2llm input and a representative upstream TTT slow parameter;
   - zero/no-grad projector fixture demonstrates the test would fail if the path were detached.

3. packing invariance:
   - with vs without Local, native sequence length/split_lens/attn_modes/mRoPE/loss indexes are unchanged.

4. sample isolation:
   - B>=2 mixed S0/non-S0 prefix cannot cross samples.

5. K/V semantics:
   - memory K uses generator K projection + K norm;
   - memory V uses generator V projection;
   - no RoPE is applied to memory K;
   - no Local Q exists.

6. no-Local parity:
   - exact ordinary attention path is taken when all prefixes are None.

7. fail-closed:
   - wrong K/D, duplicate Local authority, unsupported attention mode, CP enabled, CUDA graphs or inference route reject before mutation/forward.

8. B0/B1 regression tests remain PASS.

## 9. Implementation scope

Expected child files are limited to the native Local seam and direct tests, likely:
- new `mot/memory_prefix.py` + tests;
- `mot/cosmos3_vfm_network.py`;
- `mot/unified_mot.py`;
- `mot/attention.py`;
- `sequence_packing/sequence.py`;
- `sequence_packing/packers.py`;
- `model/generator/utils/data_and_condition.py`;
- `omni_mot_model.py`;
- the Edge/Model config fields needed to instantiate the Local subsystem;
- focused tests.

Do not port V2 active driver, trainer integration, inference, checkpoint, telemetry, launch callbacks or schedulers in B2-A.

## 10. Next Gates

Only after B2-A fresh approval:
- B2-B: B1 producer + B0 transaction + native loss/backward/commit semantics.
- B2-C: RTX4090 S1 real GPU smoke under TTT/Local-only trainable profile.
- H100 matched smoke and formal training remain later Gates.
