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

- immediate prior live blob SHA: `2c83f612f491da08b3d0731aa3fdbc41659a48fd`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v0.5 unified pre-C rehearsal implementation design v3.0 REQUEST_CHANGES

Formal pair:
- root design SHA: `6677343ff7bcc931d2c141ada46ced11de2fc318`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-IMPLEMENTATION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_pre_c_rehearsal_consumer_implementation_design_v3.0.md:24)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_pre_c_rehearsal_consumer_design_v30_6677343_93a89ba.md`

Canonical review commit:
`9b27f2f8ac7e6959c178514c4f1d4c6b1ae4b781`

Current blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production: `0`; Evidence/identity: `0`; child/runtime: `0`.

Positive findings:
- formal root is docs/status-only and its tree binds `cosmos-framework` exactly to the declared reachable child;
- v3.0 correctly consolidates static capability identity, canonical request/patch representation, v0.5 tuple, dry-run add-only validation, sealed post-write verifier, same-object opaque handoff, exact-once invocation and terminal no-retry handling;
- v0.3/v0.4 remain forbidden and this Gate does not authorize v0.5 construction, consumer invocation, materialization or runtime execution.

HIGH 1 — live freshness observations are moved before C but still declared non-consuming:
- `rehearse_v05()` item 3 reads/freezes live output absences, six-key environment, `.git`/config, local V2, the two remote queries, fixed authority-ref absence and designated-path absence while the design calls rehearsal non-consuming;
- the controlling Stage-1 lifecycle freezes P0/P1 as non-consuming but requires C to begin immediately before the first freshness observation and permanently consume the one-shot authority;
- V21 changed the future output tuple to v0.5 but did not supersede that consumption boundary;
- therefore the same live freshness/provenance observations cannot become non-consuming merely by moving them into a rehearsal. If they are real observations, authority is already consumed; if they are old/injected observations, they are not the required fresh same-round C evidence.

Required remediation:
- either preserve the inherited lifecycle: pre-C rehearsal validates only static/injected capability metadata, serializer/canonicalization logic, query/path allowlists, dry-run patch semantics and verifier behavior; C begins before the first live freshness read and performs the required same-round live snapshot exactly once before the opaque write;
- or introduce a separate explicit authority/lifecycle refreeze that supersedes the existing “C begins before first freshness observation” rule and defines why sealed live pre-C observations are non-consuming. V3.0 currently does not do that.

No CPU/static implementation authority is granted for this exact pair.

Still NOT authorized:
- v0.5 construction;
- P0/P1/C;
- real consumer invocation;
- materialization;
- source/checkpoint/manifest/data/cache I/O;
- collection/receipt/record/publication;
- child/runtime/config mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
