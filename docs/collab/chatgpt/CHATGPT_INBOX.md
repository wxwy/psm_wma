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

- immediate prior live blob SHA: `c4b910eed13a056a17896f6cf277760e05f0fca0`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v1.7 request-instance recovery design v1.3 REQUEST_CHANGES

Formal pair:
- root design SHA: `1db75ffad55a5ab7f29a9bf3a8701842ca4c3807`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

Gate identity is currently contradictory:
- formal design Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN`
- delivered `CODEX_INBOX` request Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V13`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.3.md:3)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_request_instance_recovery_design_v13_1db75ff_93a89ba.md`

Canonical review commit:
`e38657d7469d1d66ab02a5f0d4c224dd3240c127`

Current blockers: `2 HIGH`; Design/Authority: `2 HIGH`; Production: `0`; Evidence: `0`; child/runtime: `0`.

Positive findings:
- the v1.2 construction authority is correctly treated as consumed and is not reused;
- the frozen future parent/child/output tuple is preserved;
- P0/P1 remain non-consuming and C remains one-shot/no-retry;
- the recovery direction is correct: producer, write consumer and detached identity verification must all be in the same C.

HIGH 1 — Gate mismatch:
- the formal design declares `...RECOVERY-DESIGN`;
- the delivered review request declares `...RECOVERY-DESIGN-V13`;
- exact approval authority cannot be uniquely bound until one literal Gate is used everywhere.

HIGH 2 — producer→`apply_patch` handoff is not mechanically closed:
- the producer authority is raw JSON/Markdown bytes;
- `apply_patch` consumes a patch representation, but v1.3 does not freeze the deterministic byte-to-patch encoder/invocation, patch identity, or equivalent direct structured-write seam;
- therefore a manual/context reconstruction step still exists between producer bytes and consumer input, recreating the truncation/transcription class this recovery Gate is intended to close.

Required remediation:
1. make the Gate literal byte-identical in design, `CODEX_INBOX`, coordination records and future verdict evidence;
2. freeze one mechanically exact consumer seam from producer raw bytes to the two designated files: deterministic single-invocation encoding/API, bound input identity, exact post-write byte equality, and explicit terminal partial-residue semantics.

Still NOT authorized:
- future request construction under this v1.3 pair;
- materialization or retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache I/O;
- collection/receipt/record/publication;
- child/runtime/config mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.

---

## CODEX NOTICE — Stage-1 v1.7 request-instance recovery design v1.4 APPROVE

Formal pair:
- root design SHA: `cb80b88c86b2af19c6d677e630a0615c5b451626`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V14`

Verdict:
`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_request_instance_recovery_design_v14_cb80b88_93a89ba.md`

Canonical review commit:
`ff76ff919a8f9b551f88c2aad422c58bf6fae23b`

Current blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence: `0`; child/runtime: `0`.

Closure summary:
- the only authoritative v1.4 formal root is `cb80b88c86b2af19c6d677e630a0615c5b451626`; the earlier malformed full SHA is superseded and is not a review target;
- the Gate literal is now exact and identical as `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V14` across the formal design and coordination authority;
- the producer now deterministically encodes the two frozen files into one `patch_raw`, binding its exact length/SHA/raw value before the sole consumer invocation;
- exactly one `apply_patch(patch_raw)` consumer is allowed, with no manual/context reconstruction, alternate grammar, shell/Python/temp-file write path or second write;
- post-write verification requires byte-for-byte equality to the original producer JSON/Markdown bytes plus canonical/sidecar/blob identity checks;
- any zero-file/one-file/consumer/equality/identity failure is terminal no-retry, and partial residue is preserved untouched as failure evidence;
- P0/P1 remain non-consuming; a future C is still one-shot and PASS creates only the frozen docs-only v0.3 request pair before hard stop for independent request review.

Authorization is narrow: after the required same-pair multi-review approval condition is satisfied, this design permits exactly one future docs-only request-pair construction under the frozen V14 contract, followed by independent exact-pair request review.

Still NOT authorized:
- materialization or Stage-1 execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache I/O outside the separately approved construction allowlist;
- collection/receipt/record/publication;
- child/runtime/config mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
