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

- immediate prior live blob SHA: `636b0acfc328bb5d2b41ed52772ec04769358995`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Acceptance Authority / Sticky-B Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `a18d178877c192fdc9682033acbd36c4184b3639`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:135)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_pass_linearization_cpu_static_implementation_a18d178_93a89ba.md`

Canonical review commit:
`e2a49e443e0ca5a757a26a39bb442410daa2c81c`

Current blockers: `1 HIGH`.

Closure/progress:
- prior callback-writeable final-ref observer / binding authority inputs are CLOSED by private `_AcceptanceAuthority`;
- prior callback-swallowable B recovery is CLOSED by sticky authority-owned `recovery_required` checked after callback return;
- stale terminal-key / AcceptedPass identity protections and restart preflight classification remain closed.

Remaining HIGH:

1. **`_commit_exact_guard()` can return `False` without proving the public guard is restored.** After public→private handoff, post-handoff failure can call `restore_if_public_absent()`, ignore a failed restore, and still return `False`. Example: parked unlink fails, restore rename also fails. Then final evidence exists, public `.pending` is absent, terminal remains PENDING and refs remain candidate — a durable B/recovery state. `consume_by_unlink()` currently treats `guard_committed == False` as ordinary `AuthorityRootError`, so `publish_candidate()` may enter ordinary `_rollback`. Every non-success guard-helper outcome must either prove the exact original public guard is restored (ordinary A) or latch `recovery_required` / surface stable `PASS_CLOSURE_RECOVERY_REQUIRED` (B). Add direct unlink-failure + restore-failure coverage, including swallowed immediate error, proving refs preserved, no delete events, and restart recovery routing.

Formal root/tree is independently valid: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`; child commit is independently reachable.

Reported `78/78` CPU tests and static checks are auxiliary evidence only.

Remediation remains strictly limited to the already approved four root tooling/test files and temporary directory/local bare-remote CPU/static tests. No real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 are authorized.

This notice is coordination only and does not replace the exact formal pair or canonical review.