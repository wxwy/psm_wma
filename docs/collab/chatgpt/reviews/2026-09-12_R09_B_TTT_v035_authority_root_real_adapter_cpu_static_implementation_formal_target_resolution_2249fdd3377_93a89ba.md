# ChatGPT Review — Authority Root Real Adapter CPU/static Implementation Formal-Target Resolution Failure

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Requested exact formal pair

- requested root SHA: `2249fdd3377f82d037d85b7f3ed854cf90472303`
- requested child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

## Resolution result

The requested root SHA does not resolve to a commit object in `wxwy/psm_wma` through either the repository commit API or the low-level Git commit-object API. Therefore its tree cannot be read, its `cosmos-framework` Gitlink cannot be independently verified, and no exact-pair technical review can validly be issued against this requested root.

The live `CODEX_INBOX.md` nevertheless names this nonexistent SHA as the formal root in the current review request.

A nearby but different reachable commit exists:

- reachable root: `2249fdd3f7503d7e4c2be89bdd102cb4daf5aa49`
- message: `fix: close authority failure evidence paths`
- parent: `0b77d2d11c39a179266d2c6de073eff94e1853dd`
- tree: `6cc036c120cf1c447a157310a2ed9e381d327326`

That reachable commit's tree contains `cosmos-framework` as mode `160000`, type `commit`, SHA `93a89ba61306d840a008813f62f26a34d54850f4`. However, the reachable commit is **not** the requested root: the two full SHA-1 values differ after the shared `2249fdd3` prefix. ChatGPT will not silently substitute one exact formal root for another.

## Current blocker

### HIGH-1 — the requested formal root SHA is nonexistent / does not match the reachable implementation commit

**Location:** `docs/collab/chatgpt/CODEX_INBOX.md:603`

The current request declares:

`2249fdd3377f82d037d85b7f3ed854cf90472303`

but the reachable implementation commit in the V2 history is:

`2249fdd3f7503d7e4c2be89bdd102cb4daf5aa49`

Because the exact pair itself is an authority input to the review, this is not bookkeeping that can be inferred away. Until the canonical request is corrected and pushed with the exact reachable full root SHA, any technical verdict would bind the wrong object.

**Exact acceptance:** update the canonical `CODEX_INBOX.md` request (and any associated delivery bookkeeping that claims the same wrong full SHA) to the intended reachable full root SHA, push it, then resend the corrected exact pair to the frozen reviewers. ChatGPT should then perform the fresh technical remediation review against that corrected root without inheriting MM/Kimi conclusions.

## Technical review status

No technical review of `2249fdd3f7503d7e4c2be89bdd102cb4daf5aa49` is issued in this document. The code changes visible at that commit are not treated as the current formal target until the canonical request names that exact full SHA.

## Blocker summary

- formal-target resolution blockers: `1 HIGH`
- production/contract blockers assessed: `0` (technical review not started)
- total blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/collab/chatgpt/CODEX_INBOX.md:603)`

This verdict binds only the requested exact pair `2249fdd3377f82d037d85b7f3ed854cf90472303` / `93a89ba61306d840a008813f62f26a34d54850f4` and does not authorize any real materialization, selection/config creation, candidate/ref/origin mutation, source/collection I/O, child/runtime change, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
