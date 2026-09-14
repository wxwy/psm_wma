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

- immediate prior live blob SHA: `852516a7bb646207252eae529c8a5c6969769679`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 request projection preflight design v0.3 APPROVED

Formal pair:
- root design SHA: `d9e4be0e990c2847f402c6e9913ea42a662ddb4c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_request_projection_preflight_design_v03_d9e4be0_93a89ba.md`

Canonical review commit:
`0a15846743bf396aca0dcd874bf38d39cfbcdd62`

Current blockers: `0`; Design/Authority: `0`; Production implementation: `0`; Evidence-only: `0`; child/runtime: `0`.

Closure summary:
1. v0.3 closes the sole v0.2 HIGH by freezing the exact bootstrap argv preimage used by the launcher: `json.dumps(["--", *parser_argv_items], separators=(",",":"), ensure_ascii=False).encode("utf-8")`.
2. Exact identities are frozen and mutually distinguished: parser argv=`2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`; bootstrap argv=`2341 / 85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d`; bootstrap contract=`182 / bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702`.
3. `bootstrap_argv: ProjectedBytes` is added to the frozen result schema between `parser_argv_items` and `bootstrap`.
4. Direct CPU/static tests must assert all three exact identities and fail-close omission of the `"--"` prefix, substitution of parser bytes for bootstrap argv, parser-item reorder, and bootstrap raw drift.
5. Previously closed v0.2 controls remain unchanged: independently verified injected outer/adapter bytes; strict AST-only bootstrap extraction; flag-aware argv validation allowing canonical duplicate values; frozen module/test paths and dataclass schema; no partial results; embedded/injected fixture-only tests; no Git/path/network/subprocess/request-output I/O.
6. Formal root immediate delta is exactly the v0.3 design file; Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime production bytes are unchanged.

Authorized consequence:
- implement only `tools/psm_wma/stage1_v17_request_projection.py` and `tools/psm_wma/test_stage1_v17_request_projection.py` under the frozen CPU/static design;
- implementation must then receive an independent close review.

Still NOT authorized:
- any new request construction authority;
- revival/retry of the consumed v0.5 construction authority;
- Stage-1 materialization/execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
