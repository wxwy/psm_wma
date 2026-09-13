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

- immediate prior live blob SHA: `ff8e29b6580d80268dc2678be6ecbc69112547e5`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static REQUEST_CHANGES

Formal pair:
- root implementation SHA: `34cedc9ff227c35b387666ae824d282b14d2b1f5`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:300)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_immutable_source_collection_real_adapter_cpu_static_34cedc9_93a89ba.md`

Canonical review commit:
`c88a38672eba26657de9a68e6e7d959fbcf208d9`

Current blockers: `3 HIGH Production/Authority + 1 MEDIUM Production/Evidence`; `0 child/runtime`.

Blocking summary:
1. `NativeCollectionGit.preflight()` mutates the same temporary index that `snapshot()` hashes, while canonical `_commit_candidates()` requires snapshot equality immediately after preflight. The native adapter therefore cannot pass through the unchanged production algorithm. Existing tests call native `commit()`/`rollback()` directly and do not witness `collect_synthetic(..., git=NativeCollectionGit(...))`.
2. `NativeRootFd.open_regular()` uses one `os.open(..., O_NOFOLLOW, dir_fd=root_fd)`, which protects only the final component; intermediate symlink traversal can escape the retained source-root capability. The native tests do not cover this kernel-level nested-symlink case.
3. `NativeCollectionGit.snapshot()` does not implement the frozen `target_snapshot_v1` semantics: it hardcodes present mode `100644`, accepts untracked-present allowlist files, ignores out-of-allowlist porcelain residue, and lacks descriptor-anchored/no-follow worktree evidence. Rollback equality can therefore be asserted over an incomplete snapshot.
4. `AtomicFileEvidenceSink` checks destination freshness only at construction and publishes via overwrite-capable `os.replace`; a destination created before final publication can be overwritten instead of causing fail-close.

Exact acceptance:
- make native preflight observationally non-mutating to canonical `snapshot()` and add a direct full production-object witness through `collect_synthetic()` with actual `NativeCollectionGit`;
- implement component-by-component no-follow traversal (or equivalent beneath/no-symlink primitive) for `NativeRootFd`, with intermediate/final symlink and replacement witnesses;
- implement exact native `target_snapshot_v1` semantics, including tracked mode, untracked/porcelain rejection and no-follow type checks, with direct rollback equality witnesses;
- publish evidence with a no-replace atomic primitive and witness the destination-appears-after-construction race.

Formal-pair verification:
- root formal commit is reachable;
- formal tree resolves `cosmos-framework` exactly to `93a89ba61306d840a008813f62f26a34d54850f4`;
- child commit is reachable in `wxwy/cosmos-framework`;
- unique production executor remains `tools/psm_wma/immutable_source_collection.py`; the prior design-path blocker remains closed.

Scope reminder: remediation remains limited to the approved two-file CPU/static allowlist and temporary fixtures. This review does not authorize real source/checkpoint/manifest/data/cache I/O, live authority/collection/receipt/publication execution, request execution, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write. A new formal pair must receive fresh review.

This notice coordinates the canonical review and does not replace the exact formal pair.
