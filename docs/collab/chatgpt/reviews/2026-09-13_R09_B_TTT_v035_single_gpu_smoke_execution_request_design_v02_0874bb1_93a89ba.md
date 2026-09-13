# ChatGPT Independent Review — R09-B TTT v0.3.5 Single-GPU Smoke Execution Request Design v0.2

Date: 2026-09-13

## Formal target

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`
- Root formal SHA: `0874bb153ba81ee29eee84f0bde311bbf2d1ebe0`
- Child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.2.md`

The root commit is reachable. Its formal tree contains `cosmos-framework` as mode `160000` at exactly `93a89ba61306d840a008813f62f26a34d54850f4`, and that child commit is reachable in `wxwy/cosmos-framework`.

## Prior blocker disposition

The two HIGH findings from the v0.1 exact-pair review (`86c3276f1f8a6071659316e8c190f97fd622c0a7 / 93a89ba...`) are **CLOSED**:

1. **Runbook §3 schema authority conflict — CLOSED.** v0.2 explicitly states that its versioned §3 replaces only the approved runbook §3 exact request key-set, while the runbook's other controlling sections remain authoritative. It also forbids accepting/generating the old flat schema in parallel.
2. **Current-Gate / next-Gate creation boundary contradiction — CLOSED.** v0.2 now makes the current Gate design-only and moves creation of exactly one request instance to a separately reviewed `INSTANCE-CONSTRUCTION-AND-REVIEW` Gate after receipt closure; the current Gate itself cannot create or execute the instance.

## Current findings

### HIGH-1 — the request's `approvals` field creates an impossible self-referential review/hash cycle

The v2 top-level ABI includes both `request_sha256` and `approvals`. `request_sha256` is defined as the SHA-256 of the canonical request with only the hash field removed, so `approvals` is inside the hashed request bytes. The same section then requires `approvals` to carry **this instance Gate's** formal root/child, three reviewer identities, same-pair final verdicts, and review evidence locators. Later, §4 says the exact request instance is created first and then re-reviewed by the three reviewers.

Those final verdicts/evidence locators do not exist until after the exact instance is reviewed. Adding them afterward changes the canonical request bytes and therefore `request_sha256`; if the request is committed, it also changes the root formal SHA, invalidating the pair whose verdicts were just embedded. Re-reviewing the changed instance repeats the cycle. There is no acyclic exact-pair construction under the frozen ABI.

Required remediation before approval:
- remove same-instance final review results from the hashed request payload, **or** make `approvals` refer only to already-final prior design authority;
- store the exact-instance review receipt externally (for example, canonical review/ledger keyed by immutable `request_sha256`) rather than inside the object being reviewed;
- if an `approvals` object remains in the request, freeze its exact nested key set/types and ensure every value is available before the request hash/formal pair is frozen.

### HIGH-2 — the future construction Gate is required to read the receipt but is simultaneously forbidden from reading request-external real input

§2 requires `authority_tuple` to be derived directly from the approved post-commit receipt via Git blob lookup and exact root/tree/Gitlink validation. Therefore constructing the request necessarily requires a read-only receipt/Git-object authority lookup before the request exists.

But §4 says the later instance-construction-and-review Gate may create the request while still not being authorized to read any real input other than the request itself. That makes the required authority derivation impossible: the request cannot be constructed without first reading the external receipt authority from which its tuple is derived.

Required remediation before approval:
- explicitly authorize the construction Gate to perform the **minimal read-only authority lookup** needed to read/verify the already-closed receipt blob and root/tree/Gitlink identity, while still prohibiting source/checkpoint/manifest/data/cache payload reads and all GPU/training actions; **or**
- define a previously approved immutable authority package that is the only allowed construction input and does not require any otherwise-prohibited external lookup.

## Non-blocking checks

- Formal Gitlink remains unchanged and exact.
- The v0.2 schema now restores `launcher="python"` in `fixed_runtime` and keeps the approved single-GPU/no-`torchrun`, no-resume, `num_workers=0`, bounded `1..100`-step, artifact and terminal-status constraints.
- No child/runtime/config implementation change is in this Gate.
- Reported diff-check evidence is auxiliary only; this verdict is based on contract closure and the exact formal design text.

## Blocker summary

- Current blockers: `2 HIGH`
- Prior v0.1 blockers: `2 CLOSED`
- Implementation blockers: `0` (not an implementation Gate)
- Evidence-only blockers: `0`
- Child/runtime blockers: `0`

## Verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.2.md:87)`

This review does not authorize creation/execution of a request instance, real source/checkpoint/manifest/data/cache I/O, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or formal training.
