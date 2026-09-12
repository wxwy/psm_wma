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

- immediate prior live blob SHA: `f7e2bebb4366eeabb13d829f61ef9d1403158de9`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Real Adapter / Execution Request Design v0.5 REQUEST_CHANGES

Formal pair:
- root design SHA: `066de7052310dc889074632981cc3cdec880ab41`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.5.md:22)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_execution_request_design_066de70_93a89ba.md`

Canonical review commit:
`dc0d668445143346922815a84c59d3f3be60f1ab`

Current blockers: `1 HIGH`.

Closed from the prior `be833f8...` review:
- rollback reachability now matches production closely enough: `rollback.entered` is distinct from owned-endpoint `required`; `pre_publication` and `local_cas` no-ownership final-proof paths are representable; `post_publication` requires all six local/remote create/succeeded/owned bits.

Remaining HIGH:
- `commit.consume_by_unlink()` is the PASS linearization point, but it executes inside arbitrary finalizer code. After unlink succeeds and PASS is accepted, control returns to the finalizer, which can still raise before normal return. v0.5 only freezes the authority's non-throwing state dispatch for the normal-return path; it does not explicitly freeze the equally reachable post-commit callback-exception path. Without an outcome wrapper that first checks the authority-owned commit state, the inherited broad `publish_candidate()` exception boundary can still roll back refs after accepted PASS is visible.
- The same section is internally inconsistent about return semantics: item 5 says the finalizer may return any object and the return value is ignored, while item 6 / acceptance tests classify an ordinary return value as a possible post-commit capability violation. Choose one single-valued return contract.

Required same-Gate remediation:
1. authority must convert both finalizer normal return and exception into a single outcome dispatch keyed first by authority-owned `EvidenceCommit` state;
2. pre-commit callback return/exception may enter rollback; committed callback return/exception must always preserve exact candidate refs and accepted PASS, never rollback;
3. make the return-value rule internally consistent (ignored, or exact post-commit contract with preserve-refs fail-stop on mismatch);
4. test `consume_by_unlink()` success followed by callback raise, ordinary return, pre-commit callback exception, and wrong/replayed/unsealed commit; prove no accepted-PASS case ever invokes `_rollback`.

Latest repository delivery bookkeeping for this exact pair records MM entered review and Kimi received the request with no exact-pair final yet at that snapshot. Those are coordination signals only and do not supersede this independent ChatGPT verdict.

Scope reminder: remediation remains in the same design Gate. This verdict does not authorize implementation yet and does not authorize real selection/config files, candidate/ref/origin mutation, source read, collection/receipt/source-evidence/publication, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.