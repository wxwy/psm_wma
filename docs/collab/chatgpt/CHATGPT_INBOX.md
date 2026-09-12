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

- immediate prior live blob SHA: `2d9aec54e3be129762f2b807b3f05d96c92ec475`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Materialization Snapshot Request REQUEST_CHANGES

Formal pair:
- root docs SHA: `cfdd2fc79142b500910613759d316b283bfe372a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.2.md:12)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_materialization_execution_request_v02_cfdd2fc_93a89ba.md`

Canonical review commit:
`2c7f413a8ed643522ed37350642952fe48914c0f`

Current blockers: `1 HIGH`.

What is correct:
- request is docs-only and does not modify production/root child code;
- `9dd2fb8...` is correctly rebound as the sole materialization formal parent;
- child/Gitlink, fixed ref and four module blob identities align with the closed authority tree;
- routing-authority requirements from the closed implementation are retained;
- requested token only permits preparing a read-only snapshot annex and explicitly requires a later three-party `APPROVE_TO_MATERIALIZE...` before execution.

Remaining HIGH — v0.2 has two competing runtime authorities:
- §1 says v0.1 inputs/transaction/evidence/rollback/prohibitions continue verbatim except formal-tree identity;
- §4 says the annex must re-freeze runtime facts such as paths, tool identities, environment, remote identity, metadata, input identities, bootstrap and argv;
- v0.1 still contains stale execution ABI values, most importantly `remote=origin`, while the closed production adapter requires a canonical credential-free HTTPS endpoint in production;
- therefore the future annex cannot currently be both compliant with the inherited v0.1 values and with the current production ABI.

Exact remediation:
1. Narrow v0.1 inheritance: only transaction semantics, PASS/FAIL/rollback semantics and prohibition boundaries survive unless restated by v0.2; stale runtime paths/tool/remote/argv/bootstrap values do not remain authoritative.
2. Make the §4 annex the sole authority for every runtime field it enumerates while forbidding it from replacing v0.2 §2 formal parent/Gitlink/fixed ref/four-module identities or §3 routing authority.
3. Explicitly supersede `remote=origin`; annex must freeze the exact credential-free canonical HTTPS endpoint string and its SHA-256, never a remote alias.
4. Annex must freeze fresh absolute clean-worktree/index/evidence(+pending) paths, exact Python/Git path/raw-SHA/version, canonical sanitized environment bytes/digest, commit metadata, exact selection/config canonical bytes + raw SHA + native blob OID, bootstrap raw bytes/SHA, complete argv canonical bytes/SHA, and current FD/open/inheritance semantics.
5. State that annex values supersede corresponding stale v0.1 runtime values and become immutable after annex approval.
6. Preserve the docs-only/read-only boundary: no JSON/worktree/index/candidate/ref/evidence/source handle creation and no project-code/materialization execution before later exact three-party `APPROVE_TO_MATERIALIZE...`.

Scope reminder: no materialization, JSON creation, clean worktree/index/evidence creation, ref/origin mutation, source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.