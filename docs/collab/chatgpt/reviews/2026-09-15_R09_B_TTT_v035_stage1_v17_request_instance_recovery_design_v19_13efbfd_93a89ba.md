# ChatGPT review — Stage-1 v1.7 request-instance recovery design v1.9

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V19`
- Formal root: `13efbfde19a848aa44cfb5f0bfa0373523902ae4`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_RECOVERY`
- Blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence/identity: `0`; child/runtime: `0`.

## Formal target / scope

This is a fresh formal pair relative to the approved V18 recovery-design target `6baadaf282bea673eb217c055bb7c837522e0267 / 93a89ba61306d840a008813f62f26a34d54850f4`.

The formal root resolves and changes only the root v1.9 recovery design plus `SESSION.md` / `TODO.md` coordination state. Its formal tree binds `cosmos-framework` as mode `160000` exactly to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit resolves in `wxwy/cosmos-framework`. No child/runtime implementation change is in scope.

## Chronology / authority finding

The V18 construction authority was one-shot. The current formal design records that after the same-pair multi-review approval, P0/P1 passed and C began, then the sole consumer attempt failed because the frozen six-key environment could not resolve an `apply_patch` executable. No second consumer invocation or retry occurred, both designated v0.4 output paths were subsequently absent, and the design treats the V18 C as permanently consumed.

That treatment is consistent with the inherited one-shot/no-retry contract: the failure does not reopen V18 authority, does not permit repair of the missing v0.4 pair, and does not authorize alternate shell/Python/temp-file write paths.

## Recovery-design finding

V19 is deliberately one level narrower than a new construction authorization. It authorizes only a future consumer-recovery design and correctly requires that any later construction authority first close the consumer capability before C begins:

- the consumer must be an explicit, verifiable injected capability rather than ambient PATH resolution;
- the invocation ABI, input object identity, success/failure result schema, and no-extra-filesystem/network/Git behavior must be frozen;
- consumer availability must be probed before C and before freshness/output-path/`.git`/environment/ref/remote observations;
- if governance requires an orchestration-level `apply_patch` tool rather than an executable, the future design must freeze an opaque orchestration handoff preserving the producer `patch_text` object;
- ambient PATH inference, shell redirection, Python writes, temporary files, stdout/context reconstruction, and manual patch copying remain prohibited.

This closes the only issue in the reviewed delta: V19 does not attempt to reinterpret the V18 failure as recoverable execution authority. It only authorizes designing a new capability-closed path for later independent review.

## Verdict / boundary

`APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_RECOVERY`

This approval is bound only to exact formal pair `13efbfde19a848aa44cfb5f0bfa0373523902ae4 / 93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V19`.

It does **not** authorize a new v0.4 construction attempt, reuse or repair of the consumed V18 C, materialization, launcher/runtime execution, real source/checkpoint/manifest/data/cache I/O, collection/receipt/record/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.
