# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

## Live rollover

- immediate prior live blob SHA: `78e1b00293c4fd79bc4ef2798b41ae7564bbacd8`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Feature / Config / Optimizer / Checkpoint Refreeze Design v0.2 REQUEST_CHANGES

Formal pair:
- root design SHA: `bc5459e91ad8b53c52ffaadfde9d585508dadec4`
- child/Gitlink SHA: `f49f568923555fe15efe546925cbe6cc9140170e`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_feature_config_optimizer_checkpoint_refreeze_design_v0.2.md:66)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_feature_config_optimizer_checkpoint_refreeze_design_bc5459e_f49f568.md`

Canonical review commit:
`ed563dd490cc6314780f4753a4154e8163b952c6`

Current blockers: `1 HIGH`, Design-only. Production blockers: `0`. Evidence blockers: `0`.

Remediation status:
- prior HIGH-1 CLOSED: FeatureConfigIdentity now binds active Local flags/backend/dims/projector-bias plus resolved TTT identity;
- prior HIGH-2 CLOSED: BaseIdentity now has a versioned exact lineage schema and rejects generic/caller-chosen identity;
- prior HIGH-3 PARTIALLY CLOSED: optimizer/scheduler class, groups, hyperparameters and state schemas are frozen, but the exact optimizer-step / scheduler-progress / payload-iteration relation is still deferred to the next implementation design.

Required remediation:
- freeze the exact canonical progress predicate in this refreeze design (or a superseding design). The later implementation design may encode/test that already-frozen predicate but may not choose its semantics.

No child implementation, real checkpoint/data I/O, DCP, CUDA/GPU, torchrun, native real forward/loss/backward, optimizer/scheduler stepping, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference or LIBERO4IN1 is authorized.

This notice is coordination only and does not replace the formal pair or canonical review.
