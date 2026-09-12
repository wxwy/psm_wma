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

- immediate prior live blob SHA: `d9df167a5ada201167afa4f2baf4caf87c3ba4ff`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Real Adapter CPU/static Identity-safe Unlink Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `153bf17b3755b20296e69d2f5790becd8520875d`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:77)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_153bf17_93a89ba.md`

Canonical review commit:
`31364d4a33f2ad5a4b6306ff5c9b096ce7f7efdf`

Current blockers: `1 HIGH`.

Prior `8879742...` closures remain accepted: activation lifetime/stale capability, authority-owned final ref recheck, verify/pre-input terminal evidence, cleanup-incomplete Evidence-v1, CAS ownership and deterministic metadata are closed.

Remaining HIGH:

**The new private-parking unlink handoff removes the public `.pending` guard before the exact-object deletion transaction is proven and before `EvidenceCommit.committed=True`.** `_unlink_exact_regular()` validates the public pathname, renames it into a private same-directory parking directory, only then re-validates the parked inode and unlinks it. Because verifier acceptance is defined solely by absence of the public `.pending` path, the `rename(public_guard, parking/owned)` already makes PASS externally visible. Failures after that rename can still return to pre-commit rollback. A foreign replacement moved during the lstat→rename race also creates a window where the public guard is absent before the mismatch is detected/restored. Conversely, after a correct handoff another actor can recreate `.pending`; the helper may still delete the parked owned guard and return success, causing `committed=True` while the verifier rejects PASS because a guard exists.

Exact acceptance: keep the public guard verifier-visible until a single exact-object authority-owned commit transition; prove object identity before that transition; once the public guard becomes absent, commit must already be irrevocable and no later exception may enter ref rollback. Raced foreign guards must never be moved/deleted/overwritten as part of a successful commit. Add direct concurrent-verifier/boundary tests for post-handoff failure, foreign replacement at handoff, and guard recreation during handoff.

Formal tree/Gitlink is independently correct for this exact pair and the child commit is reachable. Reported `61/61` tests and static checks remain auxiliary evidence only.

Scope reminder: remediation stays in the same four-file temporary CPU/static Gate. This verdict does not authorize real selection/config JSON creation, real candidate/ref/origin mutation, source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.