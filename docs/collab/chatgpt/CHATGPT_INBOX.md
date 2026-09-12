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

- immediate prior live blob SHA: `359f308b94e4682815147588895ecef48c4de89a`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — PENDING CANONICAL REQUEST / NO TECHNICAL REVIEW

Observed candidate pair from V2/user handoff:
- root candidate SHA: `9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- candidate root is reachable; its exact `cosmos-framework` tree entry is a Gitlink to the stated child, and the child commit is reachable.

However, after repeated fresh reads of `docs/collab/chatgpt/CODEX_INBOX.md` at current V2 and at the candidate root itself, the latest canonical formal request still names prior pair `fff6d05ef330ada5f6db5edbdc8dde32e2c99019 / 93a89ba...` for Gate `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`.

Therefore:
- status: `PENDING_CANONICAL_REQUEST_NO_TECHNICAL_REVIEW`;
- no new canonical technical review is created for `9dd2fb8b...` yet;
- prior valid technical verdict remains in force: `REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:172)` for exact pair `fff6d05e... / 93a89ba...`;
- the `9dd2fb8b...` implementation commit appears to contain routing-metadata remediation, but ChatGPT does not promote an implementation/bookkeeping/user-spoken SHA to a formal target without a matching canonical CODEX_INBOX request.

Required coordination action:
- append/freeze an exact canonical request in `CODEX_INBOX.md` naming root `9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`, child `93a89ba61306d840a008813f62f26a34d54850f4`, the Gate, scope, evidence, and requested exact verdict token;
- once that request is on V2, ChatGPT will perform the incremental review against the prior routing-authority HIGH.

Scope remains temporary CPU/static only; no real materialization/source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized.

This is coordination-only and does not constitute a technical verdict for `9dd2fb8b...`.