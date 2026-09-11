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

- immediate prior live blob SHA: `fa941ff68f299877bca7e9a8ef34f1ba3626f1fb`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation Design v0.1 REQUEST_CHANGES

Formal pair:
- root design SHA: `a99b6b94777517b5d1ecf0fcd099524544ea3309`
- child/Gitlink SHA: `f49f568923555fe15efe546925cbe6cc9140170e`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_feature_config_optimizer_checkpoint_cpu_static_implementation_design_v0.1.md:24)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_feature_config_optimizer_checkpoint_cpu_static_implementation_design_a99b6b9_f49f568.md`

Canonical review commit:
`cf4fbd6762b01bd27ab7edb38b617f0f6a87c408`

Current blockers: `1 HIGH`, Design-only. Production blockers: `0`. Evidence blockers: `0`.

Required remediation:
- correct the exact FeatureConfigIdentity cardinality. Approved refreeze v0.2 defines **15 keys total including `schema`** (14 non-schema fields + `schema`). The implementation design currently says “15 active fields + schema”, which implies 16 keys, while its witness section calls the identity 15-field.
- replace this with an unambiguous exact 15-key statement or enumerate the frozen v0.2 §2 keys verbatim. No other design change is required by this review.

Positive findings retained:
- exact two-file child whitelist is appropriate;
- v0.3 pristine-before-first-step progress predicate is otherwise translated correctly;
- zero-live-mutation CPU/static witness plan is adequate;
- no real checkpoint/data I/O, optimizer/scheduler step, GPU/native workload, sidecar/resume, training/eval/inference or LIBERO4IN1 is authorized.

This notice is coordination only and does not replace the formal pair or canonical review.
