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

- immediate prior live blob SHA: `3e0e3d147fcac4510827d43e2069682f2d3e7c1a`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 request projection preflight design v0.1 REQUEST_CHANGES

Formal pair:
- root design SHA: `c4c2d7c66b50a829dccbec811d670cc8f470c5f2`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_projection_preflight_design_v0.1.md:24)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_request_projection_preflight_design_v01_c4c2d7c_93a89ba.md`

Canonical review commit:
`a4d94fd3b73f2aa6b88478da52ae166b30762709`

Current blockers: `2 HIGH`; Design/Authority: `2 HIGH`; Production implementation: `0`; Evidence-only: `0`; child/runtime: `0`.

Positive disposition:
1. Formal root Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime bytes are unchanged.
2. Formal scope is docs-only: projection-preflight design plus `SESSION.md` / `TODO.md`.
3. The design correctly separates pure projection preflight from construction authority and explicitly does not revive/retry the consumed v0.5 construction authority.
4. AST-only, non-executing parsing and the no Git/remote/filesystem/subprocess/request-output boundary are appropriate.
5. Embedded frozen fixtures or explicitly injected bytes are the correct CPU/static evidence model, and preflight success correctly does not grant construction authority.

HIGH 1 — outer-only input cannot project bootstrap raw bytes:
- proposed API accepts only `outer_payload_bytes`;
- the design requires complete raw projection including bootstrap raw bytes;
- the frozen launcher's `boot(s)` does not embed bootstrap raw as a constant: its final return is `return raw.decode()`, where `raw` is obtained after dynamically reading/parsing the frozen adapter source's `bootstrap_payload`;
- the outer source carries only bootstrap identity guards, not the bootstrap raw itself;
- therefore a no-I/O helper cannot reconstruct complete bootstrap raw from outer bytes alone.

Required remediation:
- preserve no-I/O, but inject a second independently identity-checked authority input containing the frozen adapter source or verified bootstrap raw bytes;
- statically extract/verify bootstrap payload from that injected authority;
- fail-close missing/wrong/drifted adapter/bootstrap authority before any projection result;
- do not ambiently read Git/path/filesystem to fill the missing bytes.

HIGH 2 — blanket duplicate argv-item rejection contradicts canonical argv:
- the design says parser argv duplicates are rejected and asks for a `duplicate argv item` negative;
- canonical v1.7 argv legitimately repeats value `/proc/self/fd/8` for both `--cwd` and `--bootstrap-project-root`;
- this was already the duplicate-value case that motivated flag/position-aware launcher replay authority;
- a blanket duplicate-item rule would reject the canonical positive fixture.

Required remediation:
- allow repeated values;
- reject duplicate/missing/extra flags and malformed flag/value adjacency/structure instead;
- require all argv elements to be strings;
- validate the whole parser against exact canonical compact JSON bytes/SHA and/or the frozen ordered flag/value table;
- replace the duplicate-value negative with duplicate-flag / malformed-structure negatives while preserving the canonical repeated `/proc/self/fd/8` positive.

Still NOT authorized:
- projection helper implementation under the current design;
- request construction or any new construction authority;
- Stage-1 materialization/execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
