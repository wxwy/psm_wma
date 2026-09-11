# ChatGPT Independent Review — R09-B TTT v0.3.5 Feature / Config / Optimizer / Checkpoint CPU/static Implementation Design v0.1

- Date: 2026-09-11
- Formal root design SHA: `93529fb3762efa8425f50f8a214615310fe6e388`
- Child/Gitlink SHA: `d96406e3b273d35e328c88142b36ef2eae895d2c`
- Gate: `G0-R09-B-TTT-V035-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-CPU-STATIC-IMPLEMENTATION-DESIGN`
- Design under review: `docs/build/PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_cpu_static_implementation_design_v0.1.md`
- Frozen composite authority: refreeze v0.1 plus v0.2 remediation, with prior ChatGPT approval at `ca08bebfaec0e63beee653fcbc3997ecee7fb476` / `d96406e3b273d35e328c88142b36ef2eae895d2c`.

## Verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC`

## Current blockers

`0`

The six-file implementation whitelist is sufficient for the synthetic CPU/static Gate as designed. The child is unchanged from the approved refreeze design pair, so this review is a fresh incremental Design-Gate audit of the new implementation plan against the frozen composite contract and the concrete child ABI.

## 1. Six-file whitelist is feasible

The main feasibility question was whether owner migration and canonical adapter binding would require an out-of-scope runtime/adapter edit. Direct source inspection shows they do not.

At child `d96406e...`, active TTT registration is currently performed in `cosmos_framework/model/generator/omni_mot_model.py`: the TTT branch constructs `ContinualTTTLocalMemoryCore`, then registers a legacy `net.local_history_runtime = LocalHistoryRuntime(...)` containing `LocalEvidenceEncoder`, `StatelessLocalReplayReadout`, and the backend. The same whitelisted file also owns `_canonical_production_adapter_from_model()`, which currently looks up `net.local_history_runtime.encoder` and `.recurrent_backend` before binding `CanonicalProductionAdapter`.

Therefore the approved implementation may atomically migrate the active-TTT registration to one registered `net.local_memory_runtime` with exact children `evidence_encoder` and `ttt_core`, and update the canonical adapter lookup to those exact registered objects, without changing `local_evidence.py`, `canonical_segment_production_adapter.py`, scheduler, trainer, packer, producer, or checkpoint backend. The design correctly limits the no-legacy-owner rule to active TTT; it does not require deleting unrelated legacy recurrent support.

The current `Cosmos3VFMNetwork` already registers `local_memory2llm = nn.Linear(local_memory_dim, hidden_size)` and `local_memory_modality_embed` when Local Memory is enabled, so the 32→2048 projector/modality assertions can be enforced from the whitelisted config/model-registration surfaces without modifying the network implementation file.

## 2. Config identity and inventory preserve the frozen refreeze contract

The design removes the old `runtime_evidence_steps` identity, narrows `k_local` from the legacy `{1,4,8}` acceptance to exact first-rollout `1`, and freezes the approved feature-version, fp32 fast-state dtype, and slow-only/no-mid-episode-resume mode. This matches the composite v0.1+v0.2 authority rather than the current child helper, whose `LocalMemoryConfig` still uses `inner_lr`, permits `k_local in (1,4,8)`, and carries `runtime_evidence_steps`.

The exact slow key space is also correct: evidence encoder parameters, concrete core slow seeds/projections/slot query, per-token projector, and modality embedding. The design correctly keeps the four `w0_fast_*` values in the slow inventory despite their names, while excluding runtime `ContinualTTTFastState`, frontier, pending capabilities, transaction/receipt state, cursor/queue/RNG and partial graph/grad state.

The four frozen selector prefixes exact-cover this inventory and explicitly reject overlap, omission, alias, non-trainable, foreign and legacy keys. This is consistent with the prior refreeze approval.

## 3. Preflight-first restore remains atomic in the design

The implementation plan retains the approved order:

`decode/stage -> validate all fallible payload/config/base/inventory/tensor/optimizer/scheduler/iteration contracts -> validate runtime admission -> mutate existing registered objects once`.

This closes the defect in the current child `strict_restore_into()`, which presently loads projector/modality/module state before the final owner validation and therefore can partially mutate on a late failure. The implementation design explicitly forbids post-mutation rollback as the first-rollout semantics and requires late optimizer/scheduler/owner defects to reject with parameter bytes, optimizer groups/state, scheduler, iteration and object identities unchanged.

At implementation closure, “apply exactly once” must continue to mean that no fallible validation or fallible ownership decision remains after the first mutation. A passing happy-path round trip alone is not sufficient.

## 4. Fresh/quiescent runtime admission is implementable without expanding scope

The current `CanonicalProductionAdapter` already owns the actual encoder/core references, `CanonicalProductionFastStateFrontier`, pending scan/native-forward/commit/retry/suffix authority collections, and active suffix-recovery state. `CanonicalBatchScheduler` and `CanonicalBatchWindowTransaction` expose the frozen-transition/transaction state needed for direct CPU/static witnesses.

Accordingly, the config/checkpoint contract can require the exact live adapter/scheduler/transaction authority as mandatory in-memory preflight inputs and reject before mutation when any frontier, pending capability, frozen/open transaction, recovery receipt or other nonterminal authority is present. No public runtime integration is authorized in this Gate, so adding a production checkpoint/backend call site is neither necessary nor permitted here.

However, implementation evidence must use the real existing authority objects. A test-only mirror such as a boolean `is_quiescent`, a synthetic state dictionary not derived from the actual adapter/scheduler/transaction objects, or a witness that checks only adapter pending sets while omitting an open-but-unscanned transaction/recovery authority will not satisfy this design at closure.

## 5. Acceptance matrix is adequate

The nine required CPU/static witnesses cover the critical contract→behavior→evidence chain:

- exact versioned config identity and invalid legacy/drift cases;
- one registered active-TTT owner and exact adapter object binding;
- exact concrete inventory and four-selector coverage/no-alias rules;
- semantic inclusion of `w0_fast_*`, K/Q/V, slot, evidence/projector/modality and exclusion of runtime fast authority;
- legal in-memory round trip preserving tensor/config/base/optimizer/scheduler/iteration/object identities;
- late preflight defect proving zero mutation;
- each real live-runtime authority rejecting before mutation plus fresh/quiescent success;
- forbidden runtime/sidecar key rejection and no false mid-episode-resume claim;
- preservation of public hard-stop / disabled-first behavior with no native forward/loss/backward or optimizer step.

The requested three targeted CPU/static test files plus Ruff, `py_compile`, and child/root `git diff --check` are appropriate for this design Gate. Their later pass count will be evidence for this synthetic scope only, not checkpoint/training evidence.

## Pair / scope verification

- Formal root `93529fb3762efa8425f50f8a214615310fe6e388` resolves `cosmos-framework` exactly to `d96406e3b273d35e328c88142b36ef2eae895d2c`.
- Child commit `d96406e3b273d35e328c88142b36ef2eae895d2c` is reachable.
- The formal root is docs-only for this Gate; child code is unchanged.
- MM/Kimi conclusions were not used as technical authority.

## Evidence / execution scope

This is a Design Gate. No project tests were executed for this ChatGPT review. No real checkpoint/filesystem/DCP/remote I/O, public runtime activation, native forward/loss/backward, optimizer/scheduler step, CUDA/GPU, `torchrun`, runtime sidecar, training, evaluation, inference, matched smoke, distributed execution or LIBERO4IN1 is authorized by this verdict.

## Authorized next action

This approval authorizes only the exact six-file synthetic CPU/static implementation described by the design, followed by a new formal root/child pair and fresh implementation review.

Still not authorized: any file outside the six-file whitelist, real checkpoint I/O, checkpoint backend wiring, public runtime/hard-stop removal, real native forward/loss/backward, optimizer/scheduler stepping, CUDA/GPU, `torchrun`, runtime sidecar or mid-episode resume, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1.
