# ChatGPT Review — Stage-1 v1.7 request-instance design

- Formal root: `218f5f6254e7e926ae2d9ad8fb8206d037a9cadf`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`
- Requested positive verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

## Verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.1.md:5)`

Blockers: **1 HIGH**
- Design/Authority: 1 HIGH
- Production/Authority: 0
- Evidence/Scope: 0
- child/runtime: 0

## Pair / scope verification

- Formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Relative to the closed replay implementation root `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f`, the technical addition is the docs-only request-instance design plus SESSION/TODO coordination; child/runtime production bytes are unchanged.
- The design correctly records v1.6 authority as consumed and non-reusable.
- Frozen formal parent/base identities and the closed replay implementation root are consistent with the prior approved launcher-freeze closure.

## Positive disposition

1. The design correctly separates this Gate from an actual request instance: approval would only authorize construction of one future docs-only Markdown/JSON pair, which must then receive a fresh exact-pair three-party request review.
2. The frozen dependencies are explicit: formal parent `08d5828...`, launcher base blob/raw/bytes, replay implementation root `50b0bff...`, and canonical parser/outer identities.
3. The future request is required to use the frozen pure helper on verified injected formal-parent bytes, bind a same-round zero-mutation freshness snapshot, record canonical request bytes/SHA, and prohibit fallback/mixed-parent/stale/inferred/default/reordered/duplicate-owner-FD/request-byte drift.
4. The design keeps Stage-1 materialization, launcher execution, runtime artifacts, source/checkpoint/manifest/data/cache content, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference and LIBERO4IN1 outside this Gate.

## Remaining HIGH — construction authority contradicts the stated I/O prohibition

File: `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.1.md:5`

The opening authority statement says this design does not authorize materialization **or any real I/O**. But the construction contract later requires the approved constructor to obtain a fresh same-round snapshot by reading:

- the formal Git object / commit tree,
- local `.git` identity and config bytes,
- fixed local / remote refs,
- designated clean-root / index / ref / evidence / pending path absences.

Those operations are themselves real read-only Git/filesystem provenance/freshness I/O (and a remote-ref observation may involve network I/O). Therefore the exact positive verdict has no unique operational meaning: a literal reading of line 5 forbids the reads required to construct the request, while the later contract requires them.

This is not a production implementation defect and does not authorize any broader I/O. It is an authority-definition contradiction in the docs-only design.

## Exact remediation

1. Replace the blanket `不授权 ... 任何真实 I/O` wording with an explicit allowlist boundary for request construction.
2. State that, after unanimous same-pair design approval, construction may perform **only** the enumerated read-only provenance/freshness observations needed for the one docs-only request instance: exact formal Git object/tree bytes/identity, local `.git` identity/config bytes, the frozen local/remote ref observations, and the designated path-absence checks.
3. State explicitly whether the frozen remote-ref observation is allowed to contact the configured Git remote; if yes, limit it to that exact read-only ref query and bind the returned raw result into the request. If no network is allowed, define the exact non-network authority source instead.
4. Preserve zero mutation throughout construction and continue to prohibit source/checkpoint/manifest/data/cache content I/O, runtime/service I/O, directory/ref/artifact creation, launcher/materializer execution, child/runtime mutation, GPU/CUDA/torchrun, training/evaluation/inference and LIBERO4IN1.
5. Preserve the one-request-only rule: construction failure/drift does not authorize retry under this design; a newly constructed exact request must still receive an independent same-pair three-party request review before any single Stage-1 attempt can be authorized.

## Scope boundary

This verdict authorizes only remediation of the docs-only request-instance design. It does **not** authorize request construction, Stage-1 retry/materialization, launcher execution, source/checkpoint/manifest/data/cache content I/O, downstream collection/receipt/record/package/publication, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1. v1.6 authority remains consumed.
