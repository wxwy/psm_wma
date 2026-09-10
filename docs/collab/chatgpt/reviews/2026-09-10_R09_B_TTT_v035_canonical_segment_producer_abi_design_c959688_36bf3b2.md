# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer ABI Design

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-ABI-DESIGN`  
**Formal root:** `c9596881eea09962ecaccc8d0b2b14eb57e6c8fa`  
**Formal child/Gitlink:** `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.1.md`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.1.md:17)`

## 1. Repository-truth lock

- `origin/V2` was locked at request/bookkeeping HEAD `ccb1e81be720787366703741aeba2ccad7fb623a`; its parent is the declared formal root `c9596881eea09962ecaccc8d0b2b14eb57e6c8fa`.
- The `cosmos-framework` gitlink stored by the formal root is exactly `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`.
- That child commit is reachable/readable in `wxwy/cosmos-framework`.
- The prior approved source-ABI authority was inspected only as provenance. Because the child changed from `3a078f2...` to `36bf3b2...`, this review independently rechecked the live producer/packer seam that matters to this Design Gate.
- The current and prior `cosmos_framework/data/generator/joint_dataloader.py` relevant collate region have the same blob (`69929967b8e4c9b0bd2c4fefdb069189f90d7f1e`), so the child increment did not silently move that seam.

## 2. Incremental conclusion

The proposal correctly preserves several frozen invariants: stream-major `flat(b,t)=b*T+t`, PAD exclusion, S0 counted with `None` Local prefix, exact count checking, no fallback to legacy row-wise/active/v0.5 sidecar routes, and a docs-only boundary that does not authorize production/GPU/runtime work.

However, the new producer ABI freezes the native materialization at the wrong lifecycle boundary. This is a Design blocker, not merely an Evidence gap.

## 3. Current blocker

### HIGH — upstream `CanonicalNativeRow` incorrectly owns model-generated native materializations

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.1.md:17,25,45`  
**Relevant live source:**
- `cosmos_framework/data/generator/joint_dataloader.py:128-205` (`custom_collate_fn`)
- `cosmos_framework/model/generator/omni_mot_model.py:_prepare_training_data`
- `cosmos_framework/model/generator/omni_mot_model.py:_get_training_inputs`
- `cosmos_framework/model/generator/omni_mot_model.py` normal training path immediately before `_pack_input_sequence()`
- `cosmos_framework/model/generator/omni_mot_model.py:_pack_input_sequence`
- `cosmos_framework/data/generator/sequence_packing/packers.py:pack_input_sequence`

**Root cause**

The design says the producer input is already prepared by an upstream collate/segment builder and freezes every non-PAD row as already holding `sequence_plan`, a clean generation payload, tokenized text indexes, and input timestep metadata. It then asks the next source audit to show how `joint_dataloader` retains those values.

That is not the live production lifecycle:

1. `custom_collate_fn` preserves per-sample list-aligned raw/native fields such as `text_token_ids`, `sequence_plan`, and sparse `local_memory=None`; it does **not** produce `GenerationDataClean` or diffusion input timesteps.
2. `_prepare_training_data()` runs inside `OmniMoTModel`: it calls `_load_and_tokenize_text_data(...)`, `build_sequence_plans_from_data_batch(...)`, and `get_data_and_condition(...)`, and only there constructs the `input_text_indexes` and `GenerationDataClean` consumed by training.
3. `_get_training_inputs()` may additionally own/cache/broadcast that processed payload for context-parallel training.
4. Only **after** `_get_training_inputs()` returns does the normal model path sample `timesteps_vision` through `_get_train_noise_level_vision(...)`; the actual packer call receives `timesteps_vision.cpu()`.
5. The native packer ABI therefore consumes a mixture of post-training-preparation objects and a dynamically sampled model-owned diffusion timestep. Those values cannot truthfully be described as immutable fields already retained by an upstream dataloader/collate row.

Freezing the current v0.1 shape would force a later implementation either to move/reconstruct native tokenization/`GenerationDataClean`/noise-schedule semantics in the producer, or to violate the declared upstream ownership while pretending the ABI is unchanged. Both contradict repository truth and the design's own prohibition on implicit conversion/redefinition.

**Violated frozen contract**

- Design authority must match the live production ABI before a downstream Gate is authorized.
- Producer/adapter must not reconstruct or silently redefine native decode/tokenization/noise/timestep semantics.
- No hidden collate/dataset/packer authority expansion.
- One native Cosmos forward must consume native semantics without duplicating or moving the model-owned preparation/noise schedule.

**Exact closure condition**

Revise the design so the producer/materialization boundary matches an actual live seam. The revised design must, before source-audit approval:

1. distinguish **pre-model row data that truly exists after collate** from **model-generated materializations** (`input_text_indexes`, `GenerationDataClean`, and diffusion timesteps);
2. keep diffusion timestep generation at the current model-owned noise-level seam unless a separate design explicitly re-authorizes that semantic move;
3. freeze one source-accurate ordering, for example either:
   - gather exact stream-major valid raw/native rows first, then invoke the existing model preparation + timestep sampling + packer chain once on the gathered native batch; or
   - place an explicitly model-side capture/materialization seam after native preparation, while keeping dynamically sampled timesteps owned by the current model path rather than by upstream rows;
4. rewrite source-audit question 1 so `joint_dataloader` is only required to prove fields it actually owns/preserves, and separately map the model-side creation of `GenerationDataClean`, tokenized indexes, CP payload handling, and diffusion timesteps;
5. retain the already-correct S0/PAD/order/count/fail-closed and legacy-route exclusions.

The subsequent source audit may decide which exact concrete seam is viable; this Design Gate must not pre-freeze a seam already contradicted by the live source.

## 4. Blocker lifecycle / scope

- Previous P1/P2 gap (“opaque segment payload is insufficient to feed the native packer”) remains a valid motivation.
- This v0.1 does **not** close that gap because the proposed replacement source object has incorrect lifecycle ownership.
- No additional blocker is raised here against S0, PAD, stream-major gather, count, legacy fallback, or Gate-scope text.
- Current blocker count: **1 HIGH**.

## 5. Authorization

`REQUEST_CHANGES` authorizes only narrow **docs-only producer-ABI design remediation** for the blocker above.

Not authorized by this review: source-audit closure, producer implementation, new child production writes under this Gate, dataloader/collate/packer changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, training, evaluation, inference, runtime sidecar, distributed execution, or LIBERO4IN1.

## 6. Exact verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.1.md:17)`
