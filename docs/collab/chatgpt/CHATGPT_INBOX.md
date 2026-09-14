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

- immediate prior live blob SHA: `136bb7ca75800f86e2d45bbc374cf1785aed083b`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 request projection preflight design v0.2 REQUEST_CHANGES

Formal pair:
- root design SHA: `ec12f296a321d22f52d9de652a4007a0a1f5d35b`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_projection_preflight_design_v0.2.md:47)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_request_projection_preflight_design_v02_ec12f29_93a89ba.md`

Canonical review commit:
`d05ee457ac432767403cd5b6afa2626c14d3c7f9`

Current blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production implementation: `0`; Evidence-only: `0`; child/runtime: `0`.

Closed from v0.1:
1. The helper now accepts independently verified `outer_payload_bytes` and `adapter_source_bytes`, so bootstrap raw can be statically projected without Git/path/filesystem I/O.
2. Parser validation now permits duplicate values while rejecting duplicate/missing/extra flags and bad flag/value adjacency; the canonical repeated `/proc/self/fd/8` no longer self-rejects.
3. Exact module/test implementation paths, frozen `ProjectedBytes` / `ProjectedRequestClosure` schemas, input identities, AST-only extraction, embedded-fixture CPU/static tests and no-authority-consumption boundaries are preserved.
4. Formal root immediate delta is docs-only (`SESSION.md` + v0.2 design); Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime bytes are unchanged.

Remaining HIGH — bootstrap contract does not freeze the exact `bootstrap_argv_sha256` preimage:
- v0.2 specifies the two contract keys and sorted/compact JSON serialization but does not state the exact bytes hashed for `bootstrap_argv_sha256`;
- the frozen launcher does not hash `RAW[2]` / parser JSON directly;
- it parses `actual=json.loads(RAW[2])`, constructs `json.dumps(["--", *actual], separators=(",",":"), ensure_ascii=False).encode()`, and hashes those bytes;
- parser argv is `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`, while the required bootstrap argv preimage is `2341 / 85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d`;
- the resulting frozen bootstrap contract is `182 / bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702`.

Exact remediation:
1. Freeze `bootstrap_argv_raw = json.dumps(["--", *parser_argv_items], separators=(",",":"), ensure_ascii=False).encode("utf-8")`.
2. Require exact `2341 / 85ac67c8...` for that preimage.
3. Require the final sorted/compact bootstrap contract to be exactly `182 / bec6a57a...`.
4. Add direct CPU/static assertions for both identities.

No API expansion or I/O is required for this remediation.

Still NOT authorized:
- projection helper implementation under the current v0.2 design;
- request construction or any new construction authority;
- revival/retry of consumed v0.5 construction authority;
- Stage-1 materialization/execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
