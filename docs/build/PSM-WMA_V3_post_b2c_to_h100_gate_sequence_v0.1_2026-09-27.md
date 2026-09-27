# PSM-WMA V3 — Post-B2C to 8xH100 Formal Training Gate Sequence v0.1

- Date: 2026-09-27
- Status: planning authority only; **no implementation or GPU/training authorization**.
- Hard prerequisite: B2-C RTX4090 S1 must close first.
- Current 4090 Local-only serial relay is a smoke mechanism only and is forbidden as the formal H100 joint-training path.

## Why a separate H100 path is required

The 4090 S1 serial relay deliberately detaches each Local prefix at the frozen-host boundary and manually relays only the prefix gradient back into TTT. That is exact when host parameters are frozen.

Formal 8xH100 training restores trainable Edge generation/action parameters. Reusing the detached 4090 relay would omit host gradients across the Local-prefix/native-host boundary and would therefore train a different objective.

The H100 path must use ordinary joint autograd through:
- Edge generation/action trainable parameters;
- LocalEvidenceEncoder;
- ContinualTTTLocalMemoryCore slow parameters;
- local_memory2llm;
- local_memory_modality_embed.

Frozen algorithm constants remain T=16, K=4, local_dim=32, evidence_dim=256, ttt_dim=64, fast_hidden=256, inner_lr=0.1, raw15, policy chunk32 / consumer33 frames.

## Gate H3-A — Joint-autograd native Local path, CPU/static

Goal: prove the same native policy loss produces gradients simultaneously on the formal host trainable set and the complete Local slow set without detached prefix relay.

Required:
- ordinary native autograd from policy loss through K/V Memory Prefix into Local slow parameters;
- host generation/action grads finite/non-zero on representative parameters;
- Local grads finite/non-zero;
- reasoner/frozen inventory remains frozen according to recipe;
- no Local inner loss enters outer objective;
- no duplicate /GA scaling;
- no serial leaf-detach path on this formal profile;
- 4090 S1 path remains isolated as smoke-only.

No GPU.

## Gate H3-B — RoboCasa grouped persistent producer/driver, CPU/static

Goal: replace fixed CloseFridge ep0/single-slot smoke source with a deterministic persistent training stream.

Freeze before implementation:
- task catalog scope (initially target-atomic 18 task classes unless separately changed);
- number of stable slots;
- episode assignment and rebind policy;
- per-slot cursor semantics;
- cross-slot same-index batching semantics;
- T=16 segment construction;
- terminal remainder / next-episode binding;
- category/task balancing;
- rank sharding ownership under 8 ranks;
- exact source/provenance identity.

Acceptance:
- long deterministic chronology across episodes;
- S0 only on fresh episode;
- continuation uses previous committed fast state;
- no duplicate/skip consumer;
- terminal rebind clears old fast state exactly once;
- rank partitions are disjoint and deterministic;
- failure does not advance catalog/frontier.

No GPU.

## Gate H3-C — Trainer transaction + optimizer/GA integration, CPU/static

Goal: connect persistent Local transactions to the actual ImaginaireTrainer backward/optimizer lifecycle.

Required ordering:
- grouped segment preparation;
- one native joint-autograd forward/backward per formal training microbatch geometry;
- native trainer GA scaling exactly once;
- finite-gradient/scaler-skip decision;
- optimizer step;
- only after successful step: publish every participating slot fast-state/frontier atomically.

Fail closed on:
- forward/backward exception;
- nonfinite loss/gradient;
- GradScaler skip if enabled;
- partial member failure;
- optimizer exception before mutation.

No fast-state publish may occur on a failed optimizer step.

## Gate H3-D — Slow checkpoint + persistent runtime resume

Goal: make long training resumable without changing the learning trajectory beyond documented numerical tolerance.

Checkpoint authority must define:
- model slow parameters;
- optimizer/scheduler;
- Local fast-state sidecar per stable slot;
- slot→episode binding;
- segment cursor/frontier;
- catalog permutation/epoch/position;
- RNG state required for deterministic data/prompt transforms;
- geometry/profile identity.

Acceptance:
- interrupted vs uninterrupted next-identity equality;
- restored fast states match;
- no duplicate or skipped segment;
- next loss/gradient within frozen tolerance;
- source manifest/config mismatch hard-fails.

CPU/static first, then short H100 resume witness later.

## Gate H3-E — 8xH100 matched integration smoke

Only after H3-A/B/C/D closure.

Formal trainable set:
- moe_gen
- time_embedder
- vae2llm
- llm2vae
- action2llm
- llm2action
- action_modality_embed
- complete local_memory namespace.

Required Evidence:
- exact 8-rank topology/FSDP profile;
- parameter inventory by rank/global;
- finite native loss and representative host+Local gradients;
- persistent state progression;
- optimizer/commit ordering;
- memory peak by rank;
- throughput;
- one checkpoint save/reload/resume witness.

This Gate is a short integration smoke, not the long run.

## Gate H3-F — Formal RoboCasa Local-TTT training authorization

Only after H3-E fresh review.

The formal long-run command, max steps, save/eval cadence, task mixture and output namespace are frozen here.

No 4090 smoke setting may silently override this profile.

## Current hard stop

B2-C run04 GPU Evidence is still required before any H3 implementation starts.

This document may be used for planning and review decomposition only.
