# ChatGPT Independent Review — R09-B TTT v0.3.5 Single-GPU Smoke Execution Request Design v0.1

Date: 2026-09-13

## Formal target

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`
- Root formal SHA: `86c3276f1f8a6071659316e8c190f97fd622c0a7`
- Child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Reviewed design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.1.md`

The root commit is reachable. Its tree contains `cosmos-framework` as mode `160000` at exactly `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`. The earlier malformed request root `86c3276f5fd08c9a028e549c27ce7fe2989d0f4d` is therefore not the technical target; the corrected pair above is the sole pair reviewed here.

## Controlling prior contract

The immediately preceding approved runbook-design pair is `5053ed40065bfa0b8e1d755756b0565bd2d5ef31 / 93a89ba61306d840a008813f62f26a34d54850f4`, with ChatGPT verdict `APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST`.

That approved runbook freezes, among other things:

1. the smoke request as canonical JSON with an **exact top-level key set** containing `run_id`, top-level `world_size`, `launcher`, `num_workers`, `resume`, `sidecar_resume`, `B_stream`, `ttt_tbptt_steps`, `K_local`, feature flags, dtypes, `checkpoint_write`, `evaluation`, `inference`, `torchrun`, and `resolved_config_path`;
2. fixed single-GPU/no-torchrun/no-resume/no-sidecar/no-checkpoint-write/no-eval/no-inference semantics;
3. receipt-derived authority, bind-before-read admission, bounded `1..100` steps, write allowlist, and the terminal ABI `PASS|FAIL|BLOCKED|MANUAL_STOP`;
4. approval of the runbook Gate only for preparation/review of the later receipt-bound execution-request design, not execution.

## Formal delta

The formal design is docs-only. It introduces the execution-request design and task record; the child/Gitlink is unchanged. No GPU/runtime/source/checkpoint execution is part of this formal target.

## Findings

### HIGH-1 — New exact request schema conflicts with the already-approved runbook exact schema without a supersession/compatibility rule

Anchor: `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.1.md:39`.

The new design freezes a different exact top-level key set:

`schema_version, authority_tuple, request_id, request_sha256, output_root, cuda_visible_device, max_steps, resolved_config_path, command, environment_allowlist, fixed_runtime, expected_artifacts, terminal_taxonomy, approvals`.

The approved runbook §3 already froze a different exact request key set with `run_id` and the runtime fields at top level. The new design moves those runtime fields under `fixed_runtime`, renames/removes other keys, and adds new keys, but does not say that this exact schema explicitly supersedes runbook §3, nor does it define a compatibility/version transition that makes both contracts simultaneously satisfiable.

Therefore a future request can satisfy this design while violating the approved runbook, or satisfy the runbook while violating this design. Because both are declared exact/canonical contracts, the next Gate has no unique authority.

Required remediation: refreeze one canonical request ABI. Either (a) preserve the approved runbook §3 exact key set and add only explicitly permitted nested/derived data without contradicting it, or (b) explicitly supersede runbook §3 with a versioned replacement and state which earlier clauses remain controlling. The result must leave exactly one canonical schema for the future request instance.

### HIGH-2 — The authorization boundary contradicts itself on whether the next request instance may be created

Anchor: `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.1.md:100`.

The design states that approval permits preparing / “新建并审核” a receipt-bound request instance, but the same approval clause immediately says “不允许创建或执行该实例.” Section 1 has the same contradiction: approval allows preparing a concrete request for review while saying request creation is not authorized.

A concrete request instance cannot be both authorized to be newly prepared and simultaneously forbidden to be created. This ambiguity directly controls the next action, so it cannot be deferred to implementation/operator interpretation.

Required remediation: choose one boundary and use it consistently. If the next Gate is an **instance-construction-and-review** Gate, explicitly authorize creation of exactly one docs/data request instance under the frozen receipt-bound rules while continuing to prohibit execution/GPU/training. If the next Gate is still **design-only**, do not authorize a concrete instance and rename the requested verdict/next action accordingly.

## Non-blocking observations / preserved constraints

- Receipt-only authority derivation, exact root/child/receipt matching, no caller/CLI/environment/path authority substitution, and `AUTHORITY_DRIFT` fail-close remain directionally consistent with the approved runbook.
- The non-shell argv grammar, one-GPU/no-torchrun/no-resume restrictions, bounded steps, and terminal taxonomy remain consistent in intent.
- The child/Gitlink is unchanged; no child/runtime implementation is reviewed or authorized here.
- No real source/checkpoint/manifest/data/cache I/O, request execution, GPU/CUDA execution, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized by this review.

## Blocker summary

- Current blockers: `2 HIGH`
- Design / authority-contract blockers: `2`
- Implementation blockers: `0`
- Evidence-only blockers: `0`
- Child/runtime blockers: `0`

The prior `world_size` contradiction and prior `MANUAL_STOP/failure.json` terminal-status contradiction remain CLOSED; neither is reopened by this review.

## Verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.1.md:39)`

This verdict applies only to the exact formal pair above. It does not authorize creation or execution of a request instance, real I/O, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or formal training.