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

- immediate prior live blob SHA: `b4dc3781c071a5d98bcbb8c117424b167dba1ebc`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Feature / Config / Optimizer / Checkpoint Refreeze Design REQUEST_CHANGES

Formal pair:
- root design SHA: `f890b72fe1ff27eaa5eca0eb7b185af2c6b75459`
- child/Gitlink SHA: `f49f568923555fe15efe546925cbe6cc9140170e`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_feature_config_optimizer_checkpoint_refreeze_design_v0.1.md:15)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_feature_config_optimizer_checkpoint_refreeze_design_f890b72_f49f568.md`

Canonical review commit:
`a3d24e63980f54e83ede209479cfce02dbd34627`

Current blockers: `3 HIGH`, Design-only. Production blockers: `0`. Evidence blockers: `0`.

Required remediation:
1. Expand/factor the versioned Local config identity so it explicitly binds the active Local activation/backend/dimension fields that determine the registered owner/projector ABI; do not define config identity as only the six TTT fields.
2. Freeze an exact versioned `base_identity` schema/owner that binds the slow payload to the intended model/config/source lineage; arbitrary caller-provided non-empty mappings or a generic schema tag are insufficient.
3. Freeze optimizer/scheduler identity, not just loadability: optimizer class, ordered groups/members/hyperparameters, allowed state-slot tensor semantics, scheduler class/config/state, and exact step/iteration consistency; all drift must reject pre-mutation.

Positive finding retained:
- current child correctly registers the Local projector/modality path (`local_memory2llm.*`, `local_memory_modality_embed`), and the proposed slow inventory includes it together with the registered evidence encoder and TTT core.

No child implementation, real I/O, GPU, sidecar/resume, single-GPU smoke, matched smoke, or training is authorized by this verdict.

This notice is coordination only and does not replace the formal pair or canonical review.
