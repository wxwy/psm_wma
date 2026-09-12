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

- immediate prior live blob SHA: `56625e2a4b0150f4650f0ac8711a8316781e8b39`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root CPU/static Implementation Design APPROVED

Formal pair:
- root design SHA: `ee0de157d337bc85bf3d8d1c9e4957c31aa03c07`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_authority_root_cpu_static_implementation_design_ee0de15_93a89ba.md`

Canonical review commit:
`5c48701c38116de4925d7d7cff325eb1bd600d1a`

Current blockers: `0`.

Closed from prior review:
1. HIGH-1 is closed: the frozen implementation allowlist now includes the existing collection executor/test, and the real `_bound_source_inputs()` / `collect_synthetic()` path must perform fresh local+remote fixed authority-ref observation to the exact `authority["root_revision"]` before any source open. Absent/wrong/disagreement/observation-error cases must fail before the source-open sentinel with zero ref/source mutation.
2. HIGH-2 is closed: publication is frozen local→remote with expected-absent→candidate CAS and per-endpoint activation-owned witnesses; rollback is remote→local and may only perform conditional exact-candidate→absent compare-and-delete on endpoints owned by this activation. Foreign/unreadable/unprovable endpoints are preserved and force `ROLLBACK_INCOMPLETE`; fresh two-endpoint re-observation is required for rollback success.
3. The prior non-blocking validator-reuse note is implementable inside the explicit four-file allowlist while preserving the existing collection executor's acceptance/rejection semantics.

Scope reminder: this approval authorizes only the frozen four-file synthetic CPU/static implementation and stdlib CPU/static tests after same-pair reviewer closure. It does not authorize real selection/config JSON creation, authority commit/ref creation or publication, real source/remote I/O, collection/receipt/source-evidence/publication mutation, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.