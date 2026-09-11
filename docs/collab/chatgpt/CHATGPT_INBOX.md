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

- immediate prior live blob SHA: `c46ff43df7e819170219cc22ff77907903789778`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `1f5eb1cbf172893a1640008a15d23e878ca73ed3`
- child/Gitlink SHA: `11f9adf7fa209805ef6437145cf7a0dbf1625697`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract.py:46)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_feature_config_optimizer_checkpoint_cpu_static_implementation_1f5eb1c_11f9adf.md`

Canonical review commit:
`c24207af976dbc9ffb2873a0ac7d5e5d706e218b`

Current blockers: `3 HIGH`, Production. Authority/Design blockers: `0`. Evidence-only blockers: `0`.

Remediation status:
- prior HIGH-4 CLOSED: save/restore reconstruct detached pristine AdamW + ExponentialLR shadows; advanced-live scheduler matching payload is rejected;
- prior HIGH-5 CLOSED: request now uses the distinct implementation Gate without `-DESIGN`;
- prior HIGH-2 requested owner/core/projector dimensions and bias binding are implemented;
- prior HIGH-1 remains incomplete because BaseIdentity is still caller-authoritative: a syntactically valid arbitrary 40-hex child SHA is accepted, and the source descriptor is only `{schema, source_sha256}` rather than the frozen source-kind / immutable-source-id / source-manifest lineage descriptor;
- prior HIGH-3 structural fields are added, but optimizer/scheduler identities are still unversioned raw mappings without the frozen canonical-JSON/SHA-256 identity digest discipline;
- additional inherited FeatureConfig blocker: `local_evidence_feature_version=causal_visual96_executed_action10_v1` is not checked against the live encoder's visual/action input dimensions or canonical state/dt/age-disabled feature configuration.

Required remediation:
1. Make BaseIdentity owner-derived and bind the full frozen source descriptor plus actual child/manifest/source owner identities; syntactically valid foreign SHA/digest values must not pass.
2. Make optimizer/scheduler identities versioned exact mappings with canonical JSON/SHA-256 digests and exact schema/type/digest validation.
3. Bind the evidence feature-version identity to live encoder `visual96/action10` and canonical state/dt/age-disabled construction; add direct drift witnesses.

Positive findings retained:
- formal root resolves exactly to the requested child;
- implementation Gate authority is now correct;
- remediation remains within the approved two child files;
- detached-pristine progress check is source-correct;
- reported `14 passed` plus Ruff/py_compile/diff-check are supporting evidence only.

Still not authorized: real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler step, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
