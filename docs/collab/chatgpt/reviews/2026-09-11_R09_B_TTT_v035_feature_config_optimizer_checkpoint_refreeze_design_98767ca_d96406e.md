# ChatGPT Independent Review — R09-B TTT v0.3.5 Feature / Config / Optimizer / Checkpoint Refreeze Design v0.1

- Date: 2026-09-11
- Formal root design SHA: `98767ca5a2b67d2b8e7d21e1df1bf2ecb34503af`
- Child/Gitlink SHA: `d96406e3b273d35e328c88142b36ef2eae895d2c`
- Gate: `G0-R09-B-TTT-V035-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-DESIGN`
- Design authority under review: `docs/build/PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_refreeze_design_v0.1.md`
- Prior closed technical pair: `d29889522994fdc947ef59e8ee9cd173c3c196b5 / d96406e3b273d35e328c88142b36ef2eae895d2c`

## Verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_refreeze_design_v0.1.md:70)`

## Current blockers

`2 HIGH + 1 MEDIUM`

The direction of the refreeze is materially correct: it supersedes the old `local_history_runtime.encoder/recurrent_backend` selector authority, freezes the v0.3.5 config identity, preserves per-token `[B,K,32] -> [B,K,2048]`, keeps runtime `W_fast` out of the slow checkpoint, and does not authorize real checkpoint I/O/GPU/runtime/training. The blockers below are design-contract gaps exposed by the current child ABI; they must be frozen before an implementation design can safely choose behavior.

## HIGH-1 — Restore is strict but not frozen as an atomic transaction

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_refreeze_design_v0.1.md:70` (§5 restore validation).

### Root cause

The design requires key/shape/dtype/config/base-model/optimizer membership checks and says any drift must fail closed, but it does not define the mutation boundary: it never requires all fallible restore validation/staging to finish before the first mutation of registered slow tensors, optimizer state, scheduler state, or global iteration, and it does not define rollback if a later validation fails.

This omission is not theoretical. The current child `config_checkpoint_contract.strict_restore_into()` first loads `local_memory2llm`, then copies `local_memory_modality_embed`, then loads the Local module, and only afterwards calls `validate_slow_inventory()`. A late destination/owner failure can therefore occur after earlier live objects were already mutated. The current tests prove successful same-object round-trip but do not prove zero mutation on a late reject.

### Violated frozen contract / reviewer requirement

- This Gate is explicitly refreezing a **strict**, fail-closed slow checkpoint/restore authority.
- The independent-review contract requires Design Gate review of failure semantics and atomicity; rejected checkpoints cannot leave partially restored live state while still reporting failure.

### Exact acceptance

Freeze an explicit restore transaction with one of the following equivalent semantics, with the first form preferred for this CPU/static Gate:

1. decode/stage the entire in-memory payload and validate **all** fallible identity/contracts before the first live mutation: exact config serialization, base-model identity, exact ordered/name-bound slow inventory key/shape/dtype, exact optimizer parameter-object/group schema needed by restore, scheduler compatibility/state schema, global optimizer iteration/resume identity, and absence of forbidden runtime-state keys;
2. only after that preflight succeeds may the existing registered objects be mutated; no replacement Local module/parameter objects may be created;
3. any rejected restore must leave canonical slow tensors, projector/modality tensors, optimizer state/groups, scheduler state, global iteration, registered object identities, and runtime authority unchanged byte/object-for-object;
4. if the implementation intentionally permits a fallible operation after the first mutation, the design must instead freeze an all-or-nothing rollback transaction and direct Evidence proving rollback of every affected component.

The next CPU/static design must require a direct late-failure witness (for example, a valid tensor payload with a deliberately invalid late optimizer/scheduler/owner condition) proving zero live mutation after rejection, not merely that an exception was raised.

## HIGH-2 — Slow-only restore has no admission rule against live `W_fast` / frontier / pending authority

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_refreeze_design_v0.1.md:72` (§5 excluded runtime state / no-mid-episode-resume).

### Root cause

The design correctly excludes `W_fast`, frontier, cursor/ownership, pending capabilities and suffix-recovery state from the slow payload and declares `slow_only_no_mid_episode_resume`, but it does not define the runtime-state precondition for performing the restore itself.

The current canonical child has a process-local `CanonicalProductionAdapter` with a persistent `CanonicalProductionFastStateFrontier._states` plus live scan/commit/native-forward/retry/suffix capability registries. The adapter is cached on the model and is object-bound to the registered encoder/core. Therefore a slow restore into a process that already owns committed frontier state or pending authority can change `W_bar_0`/other slow parameters while retaining stale pre-restore `W_fast`/transaction authority. That is neither a fresh slow-only resume nor an exact mid-episode resume, and the current design does not say whether to reject, clear, or rebind it.

### Violated frozen contract / reviewer requirement

- §2 freezes `local_runtime_resume_mode=slow_only_no_mid_episode_resume`.
- §5 explicitly says runtime state is not restored and mid-episode resume is unsupported.
- A design-level lifecycle/admission rule is required so implementation cannot silently choose incompatible behavior.

### Exact acceptance

For the first CPU/static rollout, freeze one unambiguous admission policy before any restore mutation. The minimal acceptable policy is:

- slow restore is legal only on a fresh/quiescent canonical runtime with no committed frontier/continuation state, no pending scan/native-forward/commit/retry/suffix capability, no open canonical transaction/recovery receipt, and no other live runtime authority derived from pre-restore slow parameters;
- if any such authority is present, restore fails before the first slow/optimizer/scheduler/iteration mutation and preserves both slow and runtime state unchanged;
- after a successful restore, the canonical adapter/frontier used for subsequent work must be demonstrably empty/fresh while remaining bound to the exact registered encoder/core objects.

If the project instead wants an in-process reset that destroys live fast/runtime authority, that reset semantics is new lifecycle authority and must be explicitly designed (and, if it widens this Gate's scope, split into a separate design Gate) rather than inferred inside checkpoint code.

The next CPU/static design must include a direct witness that seeds live frontier/pending authority and proves slow restore is rejected pre-mutation under the chosen first-rollout policy.

## MEDIUM-1 — Semantic `W_bar_0 / theta_K,V,Q` roles are not bound to the child’s concrete checkpoint keys

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_refreeze_design_v0.1.md:47-49` (§3 exact inventory).

### Root cause

The design says `W_bar_0`, `theta_K/V/Q` and slot queries must be in the exact slow inventory while runtime `W_fast` must be excluded, but the current child does not expose parameters under those mathematical names. `ContinualTTTLocalMemoryCore` registers:

- `w0_fast_in_weight`, `w0_fast_in_bias`, `w0_fast_out_weight`, `w0_fast_out_bias` — these are the learned slow seed that `initial_state()` clones into runtime fast state;
- `key_proj.{weight,bias}`, `query_proj.{weight,bias}`, `value_proj.{weight,bias}`;
- `slot_queries`.

The actual runtime `W_fast` is instead an unregistered `ContinualTTTFastState` carried by the adapter frontier. In particular, the slow `W_bar_0` seed keys themselves contain the substring `fast`, so a name-based implementation can accidentally classify the wrong state unless this semantic-to-concrete mapping is frozen.

### Exact acceptance

Add an explicit role-to-concrete-ABI mapping for the existing `ContinualTTTLocalMemoryCore` and make it normative for the next implementation design/test matrix. At minimum distinguish the four registered `w0_fast_*` **slow seed parameters** from runtime `ContinualTTTFastState`, bind `theta_K/Q/V` to the existing projection parameters (including their registered bias parameters), and bind the slot-query role to `slot_queries`. The exact checkpoint/selector inventory may then be generated from `named_parameters()`, but tests must prove those concrete objects are the semantic slow roles and that no runtime frontier state is represented by a registered parameter alias.

## Existing-ABI feasibility notes (non-blocking once the above is fixed)

- The current model still registers the canonical core under `net.local_history_runtime` and `_canonical_production_adapter_from_model()` retrieves `runtime.encoder` / `runtime.recurrent_backend`. The proposed new `local_memory_runtime.evidence_encoder` / `.ttt_core` owner is feasible, but the next implementation design must atomically migrate model registration **and** this adapter lookup to the new same-object authority without leaving a trainable legacy alias/copy.
- The current `LocalHistoryRuntime` also owns a `StatelessLocalReplayReadout`; the new exact inventory correctly intends to supersede that legacy trainable owner rather than silently exclude an otherwise registered duplicate.
- The design's `[B,K,32] -> [B,K,2048]` per-token projector contract is consistent with the no-slot-concatenation requirement; no blocker found there.

## Pair / scope verification

- Formal root `98767ca5a2b67d2b8e7d21e1df1bf2ecb34503af` resolves `cosmos-framework` exactly to `d96406e3b273d35e328c88142b36ef2eae895d2c`.
- Child is unchanged from the prior closed canonical-native runtime CPU/static pair; this is a root docs-only Design Gate.
- The formal root commit adds the design document plus SESSION/TODO bookkeeping; no child implementation is part of this target.
- No MM/Kimi verdict is used as technical authority.

## Evidence / execution scope

This review is a source/design audit. I did not run project tests or project code. No real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, real optimizer/scheduler step, runtime sidecar, training, evaluation, inference, distributed execution, matched smoke, or LIBERO4IN1 was executed or authorized.

## Authorized next action

Docs-only remediation of this same refreeze design to freeze restore atomicity, slow-only restore admission relative to live runtime state, and the semantic-to-concrete slow inventory mapping; then submit a new formal root/child pair for fresh incremental Design Gate review.

Not authorized by this verdict: child implementation, public runtime activation/hard-stop removal, real checkpoint I/O, GPU, optimizer activation/step, sidecar, training, evaluation, inference, distributed execution, matched smoke, or LIBERO4IN1.
