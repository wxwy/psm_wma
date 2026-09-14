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

- immediate prior live blob SHA: `337e808b612a137da7355d0891b9d22254fe302e`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static final-path-continuity remediation APPROVED

Formal pair:
- root implementation SHA: `d806a9c8bcd04a57fe705c5716fe79e554e4d590`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_immutable_source_collection_real_adapter_cpu_static_d806a9c_93a89ba.md`

Canonical review commit:
`aa2b21714c28af95b1b5e2978cd9b866aef6dc4e`

Current blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. The retained staging-inode authority, snapshot/source continuity, native composition/rollback/mode/type matrix, link-time relocation handling, foreign-final cleanup, visible-preflight rollback, and cleanup-time parent-relocation protections remain closed from prior pairs.
2. The final remaining blocker from pair `77564a85... / 93a89ba...` is closed: after `.pending` cleanup and final retained-parent destination inode+canonical-byte verification, `AtomicFileEvidenceSink.emit()` now performs one final global frozen-parent pathname identity check as the last authority validation before success.
3. The new direct temporary-directory witness relocates/replaces the parent after the second/final destination leaf open and proves `emit()` raises with no accepted evidence at either the replacement frozen pathname or relocated old parent.
4. Reported supporting suite evidence for this pair is `56/56 PASS`, plus `py_compile` and `git diff --check` PASS.

Scope reminder: this approval closes only exact formal pair `d806a9c8bcd04a57fe705c5716fe79e554e4d590` / `93a89ba61306d840a008813f62f26a34d54850f4` for the CPU/static real-adapter Gate. It does not authorize real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication execution, execution-request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write.

This notice coordinates the canonical review and does not replace the exact formal pair.
