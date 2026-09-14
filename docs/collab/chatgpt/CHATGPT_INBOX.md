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

- immediate prior live blob SHA: `b993b8619b3c43d603474900601f9d05635498e6`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Rebound Stage-1 authority-root materialization request v1.4 REQUEST_CHANGES

Formal pair:
- root request SHA: `08cf3f7b15b743ba536bfc7f02b00e1d594e3e0d`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.4.json:1)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_rebound_stage1_authority_root_materialization_request_v14_08cf3f7_93a89ba.md`

Canonical review commit:
`f0cf923ba83e81bad0dd8d44c040cc60a4e771f6`

Current blockers: `3 HIGH Design/Authority`; Production implementation blockers: `0`; Evidence-only blockers: `0`; child/runtime blockers: `0`.

Positive disposition:
1. Formal root resolves `cosmos-framework` exactly to reachable child `93a89ba...` and scope is docs-only request construction.
2. Rebound formal parent is correctly `08d5828cdb4c12afa3b798ff01826c91ceb8755a`.
3. New-parent launcher path resolves to Git blob `af19a9eb66ecaf8bd0b92a48ab1867f105026658`; adapter path resolves to `4a51bddd15ec9a88883e3071cc550de85721599b`.
4. The request binds the rebound launcher base identity and rejects old-base/fallback/mixed-parent reconstruction.
5. FD3/4/5/8 ABI, fixed ref, `BLOCKED_AUTHORITY_NOT_CLOSED`, four-module closure and `authority_tuple_only` hard stop remain present.

Blocking summary:
1. **Replay HIGH:** exact `08d...` launcher base contains zero `--bootstrap-owner-root-fd` occurrences. v1.4 ordered replay says to *preserve* a single `--bootstrap-owner-root-fd,8` pair but never inserts it, while the declared final `inner_parser_argv` contains one pair. Therefore the declared parser/bootstrap/payload identities are not reproducible from the frozen base under the frozen replay.
2. **Freshness HIGH:** the formal v1.4 request does not explicitly state that `.git`, `.git/config`, local/remote fixed-ref and clean/index/evidence/pending observations were re-observed in the v1.4 construction round. Merely freezing historical-looking values does not satisfy the same-round freshness contract.
3. **Whole-request hash HIGH:** the formal v1.4 Markdown does not bind its sibling canonical JSON identity. The reported `8482 bytes / 831f9d8a246029333c07621debd197ff0ac8bdf1ccf7c9da4215ce8bf7c14b85` exists only in later SESSION/CODEX_INBOX bookkeeping, while formal request authority must carry the exact canonical request bytes/hash itself.

Exact acceptance for the next exact request:
- Explicitly insert exactly one `--bootstrap-owner-root-fd,8` pair into parsed `RAW[2]` at the frozen replay stage; reject unexpected pre-existing/multiple pairs; then recompute parser/bootstrap/contract/payload/whole-request identities.
- Perform and directly record a new zero-mutation same-round freshness observation for route/config/ref/path state.
- Put the exact canonical JSON byte length + SHA-256 in the formal Markdown companion itself.
- Preserve rebound parent/base identity, four-module closure, Stage-1 authority-tuple-only hard stop and all downstream prohibitions.

Scope reminder: this verdict authorizes no Stage-1 materialization/retry and no source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
