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

- immediate prior live blob SHA: `f5c3f4d15f6f4a5510d23c972e830a0093256a50`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v1.7 request-instance design v0.6 REQUEST_CHANGES

Formal pair:
- root design SHA: `76307bb65c08c1f9f35e3832be89c9cc617953eb`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.6.md:27)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_request_instance_design_v06_76307bb_93a89ba.md`

Canonical review commit:
`c00ac2e3ba88d119ffe15759d95127d141bdbcab`

Current blockers: `2 HIGH`; Design/Authority: `2 HIGH`; Production: `0`; Evidence: `0`; child/runtime: `0`.

Positive findings:
1. Formal root immediate delta is docs-only: v0.6 design plus `SESSION.md` / `TODO.md`.
2. Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime bytes are unchanged.
3. v0.6 correctly treats the v0.5 construction authority as permanently consumed and does not revive/retry it.
4. Closed projection implementation `079167743685247d6aae62a671436e834411a3cb / 93a89ba...` is correctly a prerequisite, not request/materialization authority.
5. Detached canonical JSON / Markdown sidecar identity, two-query allowlist, one-request/no-retry goal and independent exact-pair request review remain directionally correct.
6. Non-conflicting v0.5 rules remain applicable, including moving remote `V2` as construction provenance rather than runtime equality.

HIGH 1 — Phase C start / authority-consumption boundary is contradictory:
- §2 says Phase C begins only after Phase P succeeds **and all same-round zero-mutation observations are completed**;
- §3 defines those Git/.git/local-ref/two-remote-query/path-absence/environment observations as **Phase C reads**, and says observation failure is non-retry because Phase C has already begun;
- therefore the same observation is simultaneously before and inside the consuming attempt.

Required remediation:
- freeze one unique consumption point consistently in all sections;
- recommended: `P0 input acquisition -> P1 pure projection -> C consuming construction`; entering `C` occurs before the first freshness/remote/path/env observation and consumes the authority; any failure thereafter permanently exhausts it and forbids retry.

HIGH 2 — Phase P has no authorized source for its formal-tree outer/adapter bytes:
- Phase P requires injected frozen outer/adapter bytes but forbids Git/filesystem/path/subprocess I/O;
- the only explicit permission to read formal Git commit/tree/blob and outer/adapter bytes is in Phase C;
- Phase C cannot begin until Phase P succeeds, creating a circular authority dependency.

Required remediation:
- add a closed, non-consuming Phase-P input-acquisition substage that allows only immutable reads needed to obtain and independently verify exact frozen formal outer/adapter objects/bytes, with no network, mutation, output or request construction;
- or freeze those bytes as externally supplied invocation inputs with a mechanically verifiable source/identity contract.

Recommended structure:
`P0 immutable local formal-object acquisition (non-consuming) -> P1 pure projection (non-consuming) -> C one consuming construction attempt`.

Still NOT authorized:
- request construction under v0.6;
- revival/retry of v0.5 construction authority;
- Stage-1 materialization/execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O outside any future explicitly approved construction allowlist;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
