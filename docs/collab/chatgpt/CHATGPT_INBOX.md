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

- immediate prior live blob SHA: `be42508d16141b8a9b55679f86fcbb17ccbb28de`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root PASS Linearization CPU/static Implementation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `885b94fe8ed4c859014410dd7f53abb4550f3dc1`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:790)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_pass_linearization_cpu_static_implementation_885b94f_93a89ba.md`

Canonical review commit:
`494dbc0e30147321f9045972fb326dbf56276fcb`

Current blockers: `4 HIGH`.

1. `publish_candidate(finalizer=None)` still returns a `PublicationWitness` while the new terminal cell is PENDING and preserves both candidate refs without the accepted terminal transition. Existing tests explicitly rely on this path and one then enters the collection executor, so PENDING publication is still treated as valid success. No witness may return and no refs may remain preserved while PENDING.
2. The v0.10-approved authority-private opaque `AcceptedPass` capability is not implemented at all. The approved design retained this capability as pre-bound, non-copyable/non-pickle/replay-safe, internal-only acceptance machinery sharing the terminal cell. It cannot be silently optimized away in implementation.
3. `_AuthorityTerminalState` is not immutable. It is a normal writable `__slots__` object, so the shared global PENDING/ACCEPTED singleton fields can be mutated in place, bypassing the required single semantic `cell.state = ACCEPTED` pointer transition and reintroducing split-state risk.
4. The approved A/B/C crash/restart fail-stop contract and CPU/static acceptance matrix are missing. The adapter still only has generic fresh-absent evidence preflight; there is no exact A/B/C restart classification/recovery-Gate handoff or direct process-loss / guard-success-before-swap / post-swap interruption matrix. The submitted suite adds only the post-final-observation ref-drift regression.

The submitted implementation does correctly move `EvidenceCommit.committed` onto a shared terminal cell and preserves the approved observation-only historical ref behavior after the final exact observation. Those improvements are retained, but they do not close the implementation Gate.

Formal root/tree is independently valid: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`; the child commit is independently reachable.

Remediation remains strictly limited to the already approved four root tooling/test files and temporary directory/local bare-remote CPU/static tests. This does not authorize real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.