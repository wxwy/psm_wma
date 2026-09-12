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

- immediate prior live blob SHA: `655f67e14fe64add288ce057be066d014810df64`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Materialization Snapshot Preparation APPROVED

Formal pair:
- root docs SHA: `15e665576c8af37dbbbaf15cd05d2b4bf6af2f63`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_SNAPSHOT`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_materialization_execution_request_v02_runtime_authority_15e6655_93a89ba.md`

Canonical review commit:
`69cefb741dcb62619c46c8337f2bd691d1914428`

Current blockers: `0`.

Closure:
- prior competing-runtime-authority HIGH is CLOSED;
- v0.1 now contributes only one-shot transaction, evidence, PASS/FAIL, rollback and prohibition semantics;
- v0.1 runtime paths/tool identities/remote/environment/metadata/input/bootstrap/argv declarations are explicitly non-authoritative;
- §4 annex is the sole runtime authority for its enumerated fields and cannot override v0.2 §2 formal parent/Gitlink/fixed ref/four-module identities or §3 routing-authority contract;
- stale `remote=origin` is explicitly superseded: the annex must freeze an exact credential-free canonical HTTPS endpoint string plus SHA-256; aliases are forbidden;
- annex must freeze fresh absolute paths, Python/Git identity, canonical sanitized environment bytes/digest, endpoint, metadata, exact selection/config bytes+raw SHA+native blob OID, bootstrap bytes/SHA, complete argv bytes/SHA, and all current FD/open/inheritance ABI semantics;
- annex values become immutable after annex approval.

Scope reminder: this approval permits **only** preparation of the read-only snapshot annex. It does not authorize JSON/worktree/index/candidate/ref/evidence/source-handle creation, project-code/materialization execution, source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.

The annex and complete execution command still require a separate exact three-party `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` before execution.

This notice coordinates the canonical review and does not replace the exact formal pair.