# ChatGPT review — Stage-1 v1.7 request-instance recovery design v1.1

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN`
- Formal root: `7b528dc2fb754d9f27cab6ae157c15abaec654bc`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`
- Blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence: `0`; child/runtime: `0`.

## Formal target / Gitlink

This is a fresh formal pair/Gate relative to the prior approved request-instance design `9c8b4adc71b92caad5ecaf6fb044f5c01a4f9d9a / 93a89ba61306d840a008813f62f26a34d54850f4`.

The formal root tree independently resolves `cosmos-framework` as a mode-160000 Gitlink exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is reachable in `wxwy/cosmos-framework`.

The formal-root delta is one commit and is limited to `SESSION.md`, `TODO.md`, and the new docs-only recovery design `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.1.md`. No project production code or child code changes in this target.

## Prior authority consumption

The previously approved v1.0 contract explicitly made P0/P1 non-consuming and made C begin immediately before the first freshness observation, with one-shot/no-retry semantics. The reported post-P1 output-path enumeration is therefore conservatively inside C. Treating that authority as permanently consumed is the fail-closed interpretation; this review does not depend on reclassifying that operation as P0/P1 and does not reuse the prior approval.

v1.1 explicitly records the old authority as exhausted and prohibits retry, continuation, reinterpretation, or conversion into materialization authority. This preserves the prior lifecycle contract rather than weakening it.

## Recovery path authority

v1.1 freezes one and only one future sibling pair as design literals:

- `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.md`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json`

Both paths are absent from the exact formal root tree. Existing historical v0.1/v0.2 request pairs are explicitly excluded as candidate/template/input/output authority, and future construction is forbidden from discovering or selecting an output path after P1.

This closes the failure class that consumed v1.0: output naming is now frozen by the reviewed design before any future P0/P1/C attempt.

## Inherited construction contract

The design preserves the prior authority chain rather than silently refreezing unrelated rules:

- P0 remains limited to the v1.0 closed immutable-object allowlist and complete literal `ReplayBinding`.
- P1 remains the previously closed injected-byte projection helper only and performs no Git/path/network/environment/output I/O.
- C begins immediately before its first live freshness observation, consumes the new one-shot authority, and any subsequent failure is terminal/no-retry.
- The v0.5–v1.0 same-round zero-mutation closure is explicitly retained without weakening, including formal/base/replay identity, `.git`/config/local-ref state, exactly two timeout-protected remote queries, inherited absence requirements, exact v0.3 output-pair absence, closure bytes/argv/environment/FD/replay/target identities, and detached canonical JSON/Markdown whole-file binding.
- A successful construction only produces the docs-only request pair and then hard-stops for independent exact-pair review.

No materialization, launcher/materializer execution, source/checkpoint/manifest/data/cache I/O, collection/receipt/record/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this approval.

## Verdict

`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

No current blocker remains for this exact recovery-design pair.
