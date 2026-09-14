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

- immediate prior live blob SHA: `6e0c1fc56157264665c1b2eac9885999f1563755`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v1.7 request projection preflight remediation implementation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `5580e20ca918ec3287f77c17cdfe485dd890b440`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`

Formal-SHA correction:
- prior expanded root `5580e20c7e406d7ceade9222353f355fe0a4a15d` is void and does not resolve;
- the sole valid corrected root is `5580e20ca918ec3287f77c17cdfe485dd890b440`.

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_request_projection.py:96)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_request_projection_preflight_implementation_remediation_5580e20_93a89ba.md`

Canonical review commit:
`a5181d98660cd1d90a6d41dacb57da726f0882f3`

Current blockers: `2 HIGH`; Production/Authority: `1 HIGH`; Evidence: `1 HIGH`; Design/Authority: `0`; child/runtime: `0`.

Closed from `b85584e...`:
1. adapter source now revalidates both native Git blob OID `4a51bddd...` and raw SHA-256 `87e22fac...` from injected bytes;
2. parser now enforces compact canonical JSON plus the exact ordered flag/value table, preserving canonical duplicate values while rejecting ordered-table drift;
3. bootstrap function signature/body/return AST checks and exact parser/bootstrap-argv/contract identities are production-enforced;
4. tests now embed the real frozen outer and adapter fixtures in memory and call `project_request_closure()` directly; the previous `_literal()`-only 3/3 evidence gap is closed;
5. formal Gitlink remains exactly reachable child `93a89ba...`; child/runtime bytes are unchanged; helper/test remain no-Git/no-network/no-path/no-subprocess CPU/static.

HIGH 1 — outer RAW literal grammar remains too permissive:
- approved v0.2 requires `RAW[0]` / `RAW[1]` base64 arguments to be a single ASCII str-or-bytes literal, and `RAW[2]` to be a single bytes/string JSON literal;
- implementation reuses recursive `_literal()` for those outer positions;
- `_literal()` accepts `BinOp(Add)`, so concatenated outer literals such as `base64.b64decode("a"+"b")` or a concatenated `RAW[2]` are accepted when test authority identities are adjusted;
- recursive `BinOp(Add)` was approved only for the injected adapter `bootstrap_payload()` return expression.

Required remediation:
- add/use a strict outer-only single-literal extractor for `RAW[0:2]` base64 arguments and `RAW[2]`;
- keep recursive `_literal()` only for adapter bootstrap-return projection;
- add direct concatenated-outer-literal negatives.

HIGH 2 — required direct CPU/static matrix is still incomplete:
- add malformed-base64 and malformed-JSON direct negatives;
- add v0.3's explicit fail-close witnesses for omission of the leading `"--"` from bootstrap argv and substitution of parser bytes for bootstrap argv;
- directly assert `byte_length == len(raw)` and SHA-256 consistency for every returned `ProjectedBytes`, including selection/config/bootstrap/outer/adapter_source, not only parser/bootstrap-argv/contract;
- add the required partial-result-failure witness.

Still NOT authorized:
- projection implementation close for this exact pair;
- any new request construction authority or revival/retry of consumed v0.5 construction authority;
- Stage-1 materialization/execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

Only remediation of the already-approved projection module/test (plus coordination records) and a fresh exact-pair close review are permitted.

This notice coordinates the canonical review and does not replace the exact formal pair.
