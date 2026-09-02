# R09-B2 P4-v4 Execution-Preflight v0.2 design review

## Request / design

- Request commit: `1c56c2bdcce41c0ddc9307f6b91845a16f2fe94c`
- Design commit: `b29edb2ef9ded7577be0d80d07ff285d9da99088`
- Previous ChatGPT review: `7933e3baa71322ed071efe190590630aee4cc72d`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

`APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_STATIC_TOOLS` is not authorized.

## Findings

### HIGH — the newly frozen P4-provenance trust anchor is not a real commit

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_preflight_design_v0.2_2026-09-02.md:7` freezes `P4 provenance design=f362b827dc9b4c9c21d2af4f54f17e0ccba20278`.

Independent lookup finds no such commit in either `wxwy/psm_wma` or `wxwy/cosmos-framework`. A provenance Gate cannot start from a non-resolvable SHA; otherwise the builder/verifier can later substitute whichever source is convenient while still claiming to implement v0.2.

Required fix: replace this with the exact real, already-approved P4 interpreter-provenance design/implementation/review anchors. Do not infer or shorten the identity. Static tests must fail if the frozen anchor cannot be resolved or if the implementing tooling is not derived from the approved source identity.

### HIGH — the requested implementation approval contradicts the design's own unmet prerequisite

`...design_v0.2_2026-09-02.md:9` says that **before this Gate implementation/execution**, the P5 consumer must first receive an independently reviewed static remediation adding full-clean Git evidence-root authority, tracked fixed-file discovery, and `git show HEAD:<path>` bytes == current bytes checks.

That prerequisite is not closed. The current P5 consumer still accepts `evidence_root.resolve()` and calls `load_p4_v4_preflight()` without first proving the evidence root/submodule full-clean or proving the three fixed evidence files are tracked HEAD bytes. No P5-consumer remediation commit exists between ChatGPT closure `ea73612b...` and this v0.2 design/request; the branch delta contains only the new design and request ledger.

Required sequence:
1. submit the P5 consumer Git-authority remediation as its own static implementation request;
2. independently review and close it;
3. only then request authorization to implement P4-v4 preflight static tooling.

Until then, `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_STATIC_TOOLS` would violate the design's own prerequisite.

### HIGH — candidate -> committed evidence publication identity is still ambiguous / potentially self-referential

`...design_v0.2_2026-09-02.md:13` says the refreeze step copies a PASS candidate into the fixed Git evidence paths, commits it, and records `evidence revision/Gitlink/three-file blob+current SHA`; line 9 also requires root revision/Gitlink to equal the record binding.

The design does not state where the **post-commit evidence revision** is stored. If it is embedded into any of the three files contained by that same commit, the commit identity becomes self-referential. If it is external/verifier-owned, its schema/discovery/authority is not defined.

Required fix: freeze a non-circular publication contract. For example, the three P4 files may bind their own content/source/run/staging identities while P5 independently derives `evidence_root HEAD`, Gitlink, tracked blob bytes and current bytes; the final evidence commit itself is then pinned by a later review/closure artifact rather than embedded inside the commit that it identifies. Any alternative is acceptable only if its SHA chain is explicitly non-self-referential and verifier-owned.

### MEDIUM — PASS/FAIL candidate file-state grammar is not exact yet

`...design_v0.2_2026-09-02.md:13-17` introduces `candidate_root/<attempt-id>/{request,result,verification,failure}.json` and failure poisoning, but does not define the exact file set/schema for PASS versus FAIL.

Freeze at least:
- exact PASS candidate files and statuses;
- exact FAIL candidate files and prohibition on PASS `result/verification` publication after failure;
- attempt-id/token binding;
- failure stage/error schema;
- how refreeze proves a candidate was never poisoned/partially retried.

This is necessary for the proposed `candidate/refreeze schema` CPU tests to have a single contract rather than implementation-defined behavior.

## Positive observations

v0.2 materially improves v0.1 in the right direction:

- candidate execution output is separated from the Git evidence trust root;
- P5 is explicitly forbidden from consuming candidate files;
- final-path staging is used before manifest/native-closure/roster recomputation;
- first mkdir consumes the run/token identity;
- failure leaves an immutable poisoned attempt and forbids cleanup/repair/retry/reuse;
- a new attempt requires a new run root/token;
- real preflight, refreeze, P5 export/compose, GPU and training remain separately gated.

These points should be retained.

## Gate decision

Allowed now:
- revise the design only;
- submit the prerequisite P5-consumer Git-authority remediation for independent static review.

Not authorized:
- P4-v4 preflight static-tool implementation under this design;
- real staging/materialization;
- candidate execution;
- record/refreeze or evidence publication;
- P5 export/compose or `load_experiment_from_toml`;
- torchrun/CUDA/GPU;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- P5 runtime closure or B2-T.
