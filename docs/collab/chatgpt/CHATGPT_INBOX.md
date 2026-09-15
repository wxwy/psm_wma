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

- immediate prior live blob SHA: `f128c03b9b3a2395afb33af37a41e01a8ddd8bd2`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v1.7 request-instance consumer recovery design v1.9 APPROVE

Formal pair:
- root design SHA: `13efbfde19a848aa44cfb5f0bfa0373523902ae4`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V19`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_RECOVERY`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_request_instance_recovery_design_v19_13efbfd_93a89ba.md`

Canonical review commit:
`d194425576dd5d66b64859c83168784632199847`

Current blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence/identity: `0`; child/runtime: `0`.

Closure summary:
- the V18 one-shot C is treated as permanently consumed after the sole consumer-name resolution failure; no second invocation, retry, repair, or completion of the absent v0.4 pair is authorized;
- the V19 formal target is docs/status-only and the formal tree binds `cosmos-framework` exactly to the declared reachable child;
- V19 authorizes only a future consumer-recovery design, not construction or execution;
- any later construction design must close consumer capability before C begins: explicit injected capability, frozen invocation ABI, exact producer `patch_text` object identity, result schema, no-extra-I/O behavior, and pre-C availability probe;
- if governance requires orchestration-level `apply_patch`, the future design must freeze an opaque orchestration handoff instead of treating `apply_patch` as an executable name;
- PATH inference, shell redirection, Python writes, temporary files, stdout/context reconstruction, and manual patch copying remain prohibited.

Still NOT authorized:
- reuse, repair, retry, or completion of the consumed V18 C;
- a new v0.4 construction attempt under this pair;
- materialization or launcher/runtime execution;
- real source/checkpoint/manifest/data/cache I/O;
- collection/receipt/record/publication;
- child/runtime/config mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
