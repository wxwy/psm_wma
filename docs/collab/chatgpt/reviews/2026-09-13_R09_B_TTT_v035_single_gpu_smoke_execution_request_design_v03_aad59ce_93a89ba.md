# ChatGPT Independent Review — R09-B TTT v0.3.5 Single-GPU Smoke Execution Request Design v0.3

Date: 2026-09-13

## Formal target

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`
- Root formal SHA: `aad59ce762c694d77aab646ae72cfa8c6ef27cdd`
- Child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.3.md`

The formal root is reachable. Its formal tree contains `cosmos-framework` as mode `160000`, type `commit`, at exactly `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`.

## Prior blocker disposition

The two HIGH findings from the v0.2 exact-pair review (`0874bb153ba81ee29eee84f0bde311bbf2d1ebe0 / 93a89ba...`) are **CLOSED**.

1. **Same-instance approvals/hash self-reference — CLOSED.** v0.3 replaces only the `approvals` sub-contract. The hashed request now carries only prior design authority (`design_authority_root`, `design_authority_child`, `design_verdict`), whose values exist before instance creation. Exact-instance reviewer identities/final verdicts/evidence locators are explicitly forbidden from the request. The exact-instance three-party review receipt is external append-only evidence keyed by immutable `request_sha256`, so review no longer mutates the object being reviewed.
2. **Receipt lookup forbidden by construction scope — CLOSED.** v0.3 explicitly authorizes the later `INSTANCE-CONSTRUCTION-AND-REVIEW` Gate, after receipt closure, to perform only the minimal read-only Git-object authority lookup required to read/verify the published receipt blob, root tree and child Gitlink and derive `authority_tuple`. It continues to prohibit source/checkpoint/manifest/data/cache payload reads, runtime-config reads, GPU/CUDA, torchrun, execution, training/evaluation/inference, child modification and checkpoint writes.

The two still-earlier v0.1 blockers (runbook §3 schema authority conflict and current-vs-next-Gate instance-creation boundary contradiction) remain **CLOSED** through the unchanged v0.2 authority retained by v0.3.

## Current findings

No new blocker found in the v0.3 remediation scope.

The remediation is intentionally narrow: v0.3 replaces only the `approvals` and later construction-input authorization clauses, while retaining v0.2's versioned canonical request ABI, runbook-§3 supersession rule, single-GPU/no-`torchrun` constraints, bounded `1..100` steps, terminal ABI, artifact constraints and design-only current Gate.

The next Gate is now unambiguous: only after source-evidence receipt closure may one `INSTANCE-CONSTRUCTION-AND-REVIEW` Gate create exactly one request instance using the allowed read-only authority lookup, freeze its immutable request hash/formal pair, and obtain external three-party review. It still does not authorize execution.

## Blocker summary

- Current blockers: `0`
- Prior v0.2 blockers: `2 CLOSED`
- Prior v0.1 blockers: `2 CLOSED`
- Implementation blockers: `0` (not an implementation Gate)
- Evidence-only blockers: `0`
- Child/runtime blockers: `0`

## Verdict

`APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST_INSTANCE`

Scope reminder: this approval authorizes only the later independently reviewed `INSTANCE-CONSTRUCTION-AND-REVIEW` Gate, after receipt closure, to perform the explicitly allowed read-only authority lookup and create one exact request instance for review. It does not authorize instance execution, source/checkpoint/manifest/data/cache payload reads, runtime-config reads, child/runtime/config changes, GPU/CUDA/torchrun execution, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or formal training.
