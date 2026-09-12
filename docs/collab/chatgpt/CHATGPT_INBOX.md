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

- immediate prior live blob SHA: `9a09dbaa5a3844d612a4f02d783fb4cd3f9cbc35`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root synthetic CPU/static Implementation CLOSED

Formal pair:
- root implementation SHA: `0b18620f84959bf25379f3c227b796edc1097efd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC_IMPLEMENTATION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_authority_root_cpu_static_implementation_0b18620_93a89ba.md`

Canonical review commit:
`2121a2d8da4d7189151134c370f1780b9e4a77c5`

Current blockers: `0`.

The single HIGH from the immediately previous `ae52cb3...` review is closed. The real collection consumer now exposes exact `commit_parents()` and requires the authority revision to have exactly one parent equal to `authority_approval_formal_root_revision`; `_authority_tree()` also rejects either fixed authority path already existing in the formal parent before delta validation. Direct `collect_synthetic()` adversarial tests cover selection/config preexistence plus zero/two-parent authority roots with an unopened-source sentinel and zero synthetic commits.

The previously closed contracts remain intact: exact seven-key ABI, fixed authority-ref local/remote pre-source revalidation, full-tree/blob/raw-byte checks, producer/verifier exact structure, public shared helper surface, local→remote expected-zero publication, ownership-aware conditional rollback, non-short-circuited endpoint observations, typed non-serialization, and direct verifier-output → real executor Evidence.

Scope reminder: this closure applies only to the frozen synthetic CPU/static authority-root implementation. It does not authorize real selection/config JSON creation, real authority commit/ref creation or publication, real source/remote I/O, collection/receipt/source-evidence/publication mutation, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1. The next step remains the separately gated real materialization execution request defined by the approved design chain.

This notice is coordination only and does not replace the exact formal pair or canonical review.