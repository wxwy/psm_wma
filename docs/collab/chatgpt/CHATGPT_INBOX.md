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

- immediate prior live blob SHA: `a5bf495a78ca006537134fa633d4c1afd7a367e2`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v1.7 request projection preflight implementation APPROVED TO CLOSE

Formal pair:
- root implementation SHA: `079167743685247d6aae62a671436e834411a3cb`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC_IMPLEMENTATION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_request_projection_preflight_implementation_second_remediation_0791677_93a89ba.md`

Canonical review commit:
`eff72b5fd3cc98445636db7c8499133c1d1ec56f`

Current blockers: `0`; Production/Authority: `0`; Evidence: `0`; Design/Authority: `0`; child/runtime: `0`.

Closure summary:
1. The prior outer-RAW grammar HIGH is closed: `RAW[0]` / `RAW[1]` base64 arguments and `RAW[2]` parser JSON now use `_single_literal()` and accept only a single `ast.Constant(str|bytes)`; recursive `BinOp(Add)` remains isolated to the adapter `bootstrap_payload()` return expression.
2. The direct embedded-fixture matrix closes the prior evidence HIGH: all three outer concatenation variants fail, malformed base64 and malformed parser JSON fail, and the canonical public helper still runs directly against the frozen in-memory outer and adapter bytes.
3. Every returned `ProjectedBytes` field is directly checked for `byte_length == len(raw)` and `sha256 == sha256(raw)`.
4. Bootstrap argv remains frozen to exact `["--", *parser_argv_items]`; wrong no-prefix/parser-byte substitution is forced through the production identity guard and fails `projection_identity`.
5. Previously closed production controls remain intact: adapter native Git blob OID + raw SHA revalidation; exact ordered parser flag/value table and compact JSON; strict bootstrap signature/body/return AST; exact parser/bootstrap-argv/contract identities; no partial return path.
6. Formal delta from prior ChatGPT notification head is limited to the approved projection module/test plus `SESSION.md` / `TODO.md`; Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime bytes are unchanged.
7. Helper/tests remain pure stdlib, injected-byte-only and no Git/network/filesystem/path/subprocess/launcher/materializer/request/runtime I/O.

Authorized consequence:
- close only `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC` implementation.

Still NOT authorized:
- any new request construction authority;
- revival/retry of the consumed v0.5 construction authority;
- Stage-1 materialization/execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

A future request-construction attempt requires a new construction design/authority and a fresh exact-pair review chain.

This notice coordinates the canonical review and does not replace the exact formal pair.
