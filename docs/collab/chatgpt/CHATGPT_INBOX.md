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

- immediate prior live blob SHA: `04c59bc1e23781301bb2a22f5509c24c54e8f4d2`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Executor CPU/static implementation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `fb9c5e04e811865247e2ed44072af59acc8b93c9`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:70)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_controlled_execution_cpu_static_implementation_fb9c5e0_93a89ba.md`

Canonical review commit:
`1d9d3c40d7c6681c0cd4bbd33bd5e5991e650f19`

Current blockers: `5 HIGH`; Evidence-only `1`; Design/Authority `1`; Implementation `3`.

Blockers:
1. The implementation emits a six-key toy `{schema_version,phase,status,authority,candidate,snapshot}` record instead of the approved exact `immutable_source_collection_execution_evidence_v1` outer/nested schema, FAIL branches and `evidence_sha256`.
2. `_exact_authority()` replaces the reviewed seven-field execution-authority root tuple and target-lineage tuple with `{formal_root,formal_child,base,target}`; authority parent/path/blob/raw-byte and child-Gitlink drift are not witnessed, and `formal_child` is never verified.
3. `read_regular()` called twice is not the approved descriptor-safe same-opened-FD lifecycle: there is no rooted component traversal/symlink rejection witness, pre/post fstat identity/size/mtime/ctime, rewind or second hash on the same FD.
4. `OneShotHandoff` can wrap any mapping/final record and lacks same-activation producer ownership, ordered entry results, five artifact/config bindings and `candidate_handoff_sha256`; candidate derivation is only raw hashes, not the approved canonical artifact chain.
5. `GitTransaction` exposes only `resolve()`: there is no isolated temporary index/tree, exact five collection + one receipt path transaction, commit-parent/post-check logic, exact `target_snapshot_v1`, actual rollback, or `ROLLBACK_INCOMPLETE` transaction witness. Real execution would still require executor source changes and invalidate the CPU/static identity.

Positive / unchanged:
- the formal implementation stays within the approved two technical file paths and does not modify the child;
- the module remains stdlib/CPU-static and does not access real source/checkpoint/cache/network/GPU/model/training resources;
- explicit DI is directionally compatible with the approved design, but the production semantics behind the interfaces are incomplete.

Still not authorized: authority-root materialization, real source selection/read/hash, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler/scaler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
