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

- immediate prior live blob SHA: `e7bbb25864a76522da3249a8faa6a7f916f75788`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Real Adapter CPU/static Implementation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `166e5f5f6470bcc7c77f8c3326914e1281e922b6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:525)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_166e5f5_93a89ba.md`

Canonical review commit:
`5032ac720ff6a608a6113253be58f752cb17a166`

Current blockers: `4 HIGH`.

1. **Approved real adapter/CLI seam is missing.** The materializer module contains the evidence verifier/writer and `NativeAuthorityGit`, but no CLI/orchestrator, no readonly two-input-FD preflight, no exact frozen selection/config identity preflight, no tool/interpreter/Git identity preflight, and no direct `prepare_candidate → verify_candidate → publish_candidate` execution path. The next exact execution-request Gate therefore has no runnable/auditable argv surface to freeze.
2. **CAS ownership can be falsely attributed.** `cas_create_local/remote` and delete methods discard the Git mutation command return code and infer success from final ref state. A same-candidate create race can make an expected-zero CAS fail while the observed ref equals candidate, falsely yielding activation-owned success; a concurrent delete can similarly make a failed conditional delete appear successful. Success must require both exact command success and the mandated fresh post-observation. Add local+remote same-candidate race and concurrent-delete tests.
3. **Detached commit metadata is ambient/unfrozen.** `create_detached_commit()` calls `git commit-tree` without explicit author/committer/message/timestamp, and the adapter has no immutable metadata input. This cannot satisfy the frozen future execution request, which must bind those fields, without relying on repo config/current time or modifying the closed adapter later.
4. **Evidence failure ABI verifier is too permissive.** `_PHASES` incorrectly includes `rollback` as a primary phase, and ordinary `FAIL` may carry secondary rollback phase/code. Frozen v0.4/v0.5 requires primary phase to stop at `evidence_write`, ordinary FAIL rollback fields null, and only `ROLLBACK_INCOMPLETE` to carry secondary rollback failure.

Positive findings remain: v0.6 post-commit finalizer dispatch is implemented in the correct preserve-refs direction; guard cleanup/single-FD reread coverage is improved; formal Gitlink is unchanged and correct.

Latest repository coordination at review time showed MM exact-pair approval while Kimi was still reviewing; those signals do not supersede this independent ChatGPT verdict.

Scope reminder: remediation remains in the same CPU/static implementation Gate and within the approved four root files plus normal bookkeeping. This verdict does not authorize real selection/config JSON creation, real candidate/ref/origin mutation, source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.