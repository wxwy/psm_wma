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

- immediate prior live blob SHA: `724523e95e54114109c2ddcf09f5857e7d955149`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation Design v0.2 APPROVED

Formal pair:
- root design SHA: `9468e10fec3e83a4754ced24b900def5478bd5f9`
- child/Gitlink SHA: `f49f568923555fe15efe546925cbe6cc9140170e`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_feature_config_optimizer_checkpoint_cpu_static_implementation_design_9468e10_f49f568.md`

Canonical review commit:
`d6ee3acd1c1f09dd25c9228bce20b55417ff8b1c`

Current blockers: `0`. Production blockers: `0`. Evidence blockers: `0`.

Closure:
- prior sole HIGH is closed;
- FeatureConfigIdentity is now frozen unambiguously as exactly 15 keys total: `schema` + 14 non-schema fields, with no 16th key;
- direct witness wording is aligned to the same exact 15-key schema;
- v0.1 remaining two-file whitelist, BaseIdentity, exact optimizer/scheduler identity, pristine-before-first-step progress predicate, preflight-first zero-live-mutation restore and fresh/quiescent admission remain binding.

Authorized implementation scope only:
1. `cosmos_framework/model/generator/mot/config_checkpoint_contract.py`
2. `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py`

Still not authorized: real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler stepping, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
