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

- immediate prior live blob SHA: `8af57b08c5d250decafc6d7e3d65301a6cc237e1`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Source-evidence Producer / Closure Design v0.1 REQUEST_CHANGES

Formal pair:
- root design SHA: `08b069e8b0cff7da7018b74d50e76f42fedd8514`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md:35)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_source_evidence_producer_closure_design_08b069e_93a89ba.md`

Canonical review commit:
`6ff26d6d67e9d97aab2bdc547f6c8b1e4b7bd96d`

Current blockers: `3 HIGH`; Design/Authority `3`; Production `0`; Evidence-only `0`.

Blockers:
1. The record requires an independently approved immutable collection Gate formal output, but the frozen sequence jumps directly to controlled-write execution design and freezes no exact collection artifact/formal-root binding. Insert and machine-bind the collection authority before any controlled write; keep the inherited six-key record schema unchanged and carry collection provenance externally via an exact non-circular formal binding.
2. The actual resolved `canonical_model_config` has no formal authority source. The record anchors the checkpoint descriptor, but a caller can still supply any schema-valid active config and generate a self-consistent package/witness. Freeze a root/formal-source-bound config-evidence artifact/digest and require package generation to derive the config from it.
3. After the source-evidence commit, package/witness are generated externally but no exact machine-readable closure receipt is frozen. Define a non-circular post-commit receipt that binds at least formal source-evidence root, fixed record path/blob/raw digest, package digest, witness digest, and config/descriptor digests; define separate immutable persistence/review binding because a receipt containing the formal root cannot live in that same root.

Positive findings:
- fixed record path and exact six-key record schema remain aligned with the approved publication-freeze design;
- staged Gitlink/publication exclusions and isolated-preflight/live-rollback/`ROLLBACK_INCOMPLETE` semantics remain correct;
- scope is docs-only and claims no real collection/write/audit/runtime/GPU/training authority.

Still not authorized: real source-evidence collection, record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
