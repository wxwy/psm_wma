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

- immediate prior live blob SHA: `0ee41cbfcc4208df235dfcee53db9a204423a5a3`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Production Runtime Integration Design REQUEST_CHANGES

Formal pair:
- root design SHA: `bd6ea801367efc88e569c2cd4f9f62ebce2cdaeb`
- child/Gitlink SHA: `f49f568923555fe15efe546925cbe6cc9140170e`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-PRODUCTION-RUNTIME-INTEGRATION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_production_runtime_integration_design_v0.1.md:25)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_production_runtime_integration_design_bd6ea80_f49f568.md`

Canonical review commit:
`d6f108aafb711d3a4e87026d69df44cbab53d029`

Current blockers: `1 HIGH`, Design-only.

Required remediation:
- do not silently replace the previously approved mandatory progression. The inherited contract requires: runtime implementation design -> CPU/static implementation -> feature/config/optimizer/checkpoint refreeze -> single-GPU smoke design/approval -> single-GPU smoke -> runtime-sidecar design -> CPU/static verification -> resume smoke -> LIBERO4IN1 matched-smoke design/approval -> matched smoke -> formal-training design/command approval -> formal training.
- current v0.1 instead places durable sidecar/checkpoint resume before single-GPU smoke and omits multiple mandatory intermediate Gates. Either restore the inherited progression verbatim, or explicitly create/refreeze an independent superseding contract with equivalent or stronger acceptance for every reordered/omitted stage.
- stale `root=42fcfce...` reading-anchor text should be updated to avoid confusion with the formal review root; this is not a separate blocker.

No child modification or real execution is authorized by this verdict.

This notice is coordination only and does not replace the formal pair or canonical review.
