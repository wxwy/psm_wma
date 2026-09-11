# ChatGPT Independent Review — R09-B TTT v0.3.5 Feature / Config / Optimizer / Checkpoint Refreeze Design v0.2

- Date: 2026-09-11
- Formal root design SHA: `ca08bebfaec0e63beee653fcbc3997ecee7fb476`
- Child/Gitlink SHA: `d96406e3b273d35e328c88142b36ef2eae895d2c`
- Gate: `G0-R09-B-TTT-V035-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-DESIGN`
- Design authority under review: `docs/build/PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_refreeze_design_v0.2.md`, read together with the non-superseded portions of v0.1 exactly as v0.2 states.
- Prior review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_feature_config_optimizer_checkpoint_refreeze_design_98767ca_d96406e.md`

## Verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC`

## Current blockers

`0`

The v0.2 remediation closes all `2 HIGH + 1 MEDIUM` blockers from the prior formal pair. No new Design-Gate blocker was found in the root-only remediation. The child is unchanged, so this is an incremental review of the new design contract against the already-inspected concrete child ABI rather than a re-review of unrelated child implementation.

## Prior HIGH-1 — CLOSED: restore is now preflight-first and mutation-free on rejection

The prior review required an explicit atomic restore contract because current child `strict_restore_into()` can mutate some live objects before a later validation failure. v0.2 now freezes one allowed order:

`decode/stage -> validate every fallible contract -> validate fresh/quiescent runtime admission -> apply existing registered objects exactly once`.

Before the first live mutation, the design requires validation of config serialization, base-model identity, ordered/name-bound inventory, tensor shape/dtype, optimizer parameter-object/group schema plus staged state, scheduler schema/state, global iteration/resume identity, and forbidden runtime keys. It also forbids creating/replacing Local modules or Parameter objects during preflight.

Most importantly, every rejection must occur before any registered slow tensor, projector/modality tensor, optimizer state/group, scheduler state, global iteration, registered-object identity, or runtime-authority mutation, with byte/object-for-object preservation after rejection. v0.2 explicitly forbids choosing post-mutation rollback semantics for this first CPU/static implementation. This removes the implementation ambiguity identified by the prior HIGH.

The required witness is also direct: a tensor/config-valid payload with a deliberately late optimizer/scheduler/owner defect must prove that tensors, optimizer groups/state, scheduler, iteration and object identities are unchanged after rejection. An implementation that still invokes a fallible validation/load step after its first live mutation would violate this frozen design even if its happy-path round trip passes.

## Prior HIGH-2 — CLOSED: slow-only restore has a frozen fresh/quiescent admission rule

v0.2 makes `slow_only_no_mid_episode_resume` operational rather than descriptive. Restore must reject pre-mutation if any of the following authority is live:

- committed continuation `W_fast` in the frontier;
- pending scan/native-forward/commit/retry/suffix capability;
- open canonical transaction, recovery receipt, or pre-restore scheduler/runtime ownership;
- other nonterminal/uncommitted adapter state derived from the pre-restore encoder/core.

The design forbids checkpoint code from implicitly clearing, rebinding or destroying such live authority. A successful restore must leave the adapter/frontier provably empty/fresh while remaining `is`-bound to the exact registered encoder/core; only a subsequent fresh episode may clone the restored `W_bar_0` seed. This is compatible with the current child adapter/frontier model and closes the stale-runtime-authority ambiguity from v0.1.

The required CPU/static evidence now includes both live-authority rejection with unchanged slow/runtime snapshots and fresh/quiescent successful admission with exact object binding.

## Prior MEDIUM-1 — CLOSED: mathematical roles are bound to concrete child keys

v0.2 normatively maps the mathematical slow roles to the current `ContinualTTTLocalMemoryCore` ABI:

- `W_bar_0` -> `w0_fast_in_weight`, `w0_fast_in_bias`, `w0_fast_out_weight`, `w0_fast_out_bias`;
- `theta_K` -> `key_proj.weight`, `key_proj.bias`;
- `theta_Q` -> `query_proj.weight`, `query_proj.bias`;
- `theta_V` -> `value_proj.weight`, `value_proj.bias`;
- slot-query bank -> `slot_queries`.

The unchanged child registers exactly those projections, `slot_queries`, and four `w0_fast_*` values as `nn.Parameter`s; `_w0` then exposes the four seed Parameters through `ContinualTTTFastState`, while runtime episode state is cloned/carried separately. The design therefore correctly distinguishes the registered slow seed parameters whose names contain `fast` from unregistered runtime fast-state carriers.

The new witness requirement also prevents a purely naming-based implementation: each concrete key must be proved to have the intended semantic slow role and selector/checkpoint membership, while `ContinualTTTFastState`/frontier must have no registered alias.

## Composite authority / no new blocker

v0.2 expressly supersedes the v0.1 restore, runtime-admission and semantic-inventory portions while retaining the remaining v0.1 config identity, per-token `[B,K,32] -> [B,K,2048]` contract, prohibited scope and acceptance rules. Accordingly, the existing unique-owner / selector requirements that are not contradicted by v0.2 remain part of the Gate authority; the next implementation design must carry this composite contract forward rather than treating v0.2 as permission to reintroduce legacy recurrent ownership or a second trainable Local copy.

No new blocker was found in the remediation. In particular, `apply ... exactly once` does not authorize a fallible post-mutation validation phase: v0.2 already requires *every fallible contract* to have passed before apply. The implementation design/Evidence must preserve that stronger meaning.

## Pair / scope verification

- Formal root `ca08bebfaec0e63beee653fcbc3997ecee7fb476` resolves the `cosmos-framework` submodule exactly to `d96406e3b273d35e328c88142b36ef2eae895d2c`.
- That child commit is reachable and unchanged from the prior v0.1 Design-Gate pair.
- The formal root remediation is docs-only: the technical change is the v0.2 design plus session bookkeeping; it does not contain a child implementation change.
- No MM/Kimi conclusion is used as technical authority.

## Evidence / execution scope

This is a source/design review. No project test execution, real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, real optimizer/scheduler step, runtime sidecar, training, evaluation, inference, distributed execution, matched smoke, or LIBERO4IN1 is authorized by this verdict.

## Authorized next action

Despite the requested verdict literal containing `APPROVE_TO_IMPLEMENT`, the request's explicit scope controls: this approval authorizes only creation/submission of the next CPU/static **implementation design** for this frozen feature/config/optimizer/checkpoint contract.

Not authorized by this verdict: child implementation, public/real runtime activation or hard-stop removal, real checkpoint/filesystem/DCP/remote I/O, CUDA/GPU, optimizer activation/step, runtime sidecar or mid-episode resume, training, evaluation, inference, distributed execution, matched smoke, or LIBERO4IN1.
