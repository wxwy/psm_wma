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

- immediate prior live blob SHA: `2375529d028780c39353ccc73f08464a50740d6f`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Real Adapter CPU/static PASS-linearization Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `e1d5e1115023caa0e18d80108f218a9f5d2382b6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:116)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_e1d5e11_93a89ba.md`

Canonical review commit:
`37de20b14445cfa6d204c124ad701e6ede43cb3b`

Current blockers: `1 HIGH`.

The previous public-guard handoff race is materially improved: writer and `verify_evidence_path()` now use exclusive/shared `flock`, parked failures restore the guard before writer unlock, and tests show a cooperating verifier blocks during the handoff.

Remaining HIGH:

**The sidecar `<evidence>.lock` pathname is itself not identity-bound, so writer and verifier can flock different inodes.** `_evidence_guard_lock()` opens the lock path with `O_CREAT|O_RDWR|O_NOFOLLOW|O_CLOEXEC`, but it neither requires a fresh owned lock object nor freezes/rechecks its `(st_dev, st_ino)`. If the lock pathname is replaced while writer holds old inode L1, a verifier opens replacement inode L2, takes a shared flock without blocking, observes `.pending` absent during the private-parking handoff, and can accept PASS while the authority commit is still pre-commit and may later roll refs back. A pre-existing foreign regular lock file is also silently accepted.

Exact acceptance: make the writer/verifier serialization primitive identity-safe. Prefer locking an already identity-bound stable object (such as the verified final evidence inode or a stable authority-owned directory object). If a sidecar lock remains, its exact object identity/lifecycle must be authority-owned and mechanically shared by writer and verifier; stale/pre-existing/replaced lock objects must fail closed. Add a direct race where the lock pathname is replaced after writer takes exclusive lock and prove a subsequently-started verifier cannot accept PASS on a different lock inode, plus a pre-existing foreign-lock negative. If this requires changing the externally frozen evidence/verifier ABI or adding a durable coordination artifact, return to a design Gate.

Formal root/tree and Gitlink are independently correct; `cosmos-framework` is `160000 / commit / 93a89ba...`, and the child commit is reachable. Reported `64/64` tests and static checks remain auxiliary evidence only.

Scope reminder: remediation stays in the same four-file temporary CPU/static Gate. This verdict does not authorize real selection/config JSON creation, real candidate/ref/origin mutation, source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.