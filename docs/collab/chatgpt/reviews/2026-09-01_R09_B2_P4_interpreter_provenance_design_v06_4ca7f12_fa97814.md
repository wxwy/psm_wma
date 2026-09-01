# R09-B2 P4 Interpreter Provenance design v0.6 review

- Request commit: `4ca7f1220f57e3935d466b165c1d6270e0af46f0`
- Design commit: `fa97814782264ac1c71f775173c42d8576e3f8c5`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.6_2026-09-01.md`
- Verdict: **REQUEST_CHANGES**

## Scope

Design-only review. This review does not authorize implementation, P4 record regeneration, P5 compose/export, torchrun/distributed execution, GPU, model/data access, training, evaluation, inference, P5 closure, or B2-T.

## Findings

### Previous v0.5 HIGH blockers closed

The v0.6 architecture correctly closes the three v0.5 execution-boundary blockers and should retain these changes:

1. the shell worker hop is removed; PyTorch `--no-python` workers execute the exact lexical venv Python directly with `-I -S -B -c <FROZEN_STDLIB_LOADER>`;
2. the root bootstrap file is no longer executed by Python's file loader before identity checking; verifier-owned inline loader code reads the bootstrap bytes once, verifies the reviewed bytes, then `compile`/`exec`s those same bytes;
3. child stdlib/lib-dynload are no longer silently trusted from only the base executable path/SHA: an external parent TCB must verify the child Python installation manifest before spawning any lexical child.

These changes resolve the prior shell, bootstrap-before-identity, and base-stdlib findings.

### HIGH — request identity still lacks an out-of-band verifier-owned digest at the child boundary

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.6_2026-09-01.md:10-18,24-30` freezes the child shape as roughly:

`<lexical-python> -I -S -B -c <FROZEN_STDLIB_LOADER> -- <request-json> <mode>`

and says the inline loader verifies the request canonical-JSON SHA before executing the root bootstrap.

However, the design does not specify where the **expected** request SHA comes from at the child boundary. The current argv carries only request path and mode. A digest contained in the request itself is caller/self-owned; recomputing the current file digest is only observation, not a binding to the parent-approved request.

False-PASS / TOCTOU scenario:

1. the parent verifies request A at path P;
2. before the child opens P, P is replaced with request B;
3. the loader reads B and can recompute B's SHA, but without an independently supplied expected SHA for A it has no verifier-owned value against which to reject B.

Required fix:

- make `expected_request_sha256` an out-of-band immutable part of the frozen child argv/request contract, e.g. `... -- <request-path> <expected-request-sha256> <mode>`;
- parent/verifier must independently canonicalize the request and derive this digest before child spawn;
- loader reads the request once and compares the read bytes to the argv-bound expected digest before trusting any request field;
- for P4 workers, the agent must bind both worker-request path and digest into the exact torchrun `--no-python` command, and the pair verifier must re-derive both;
- add a permanent negative that replaces request bytes at the same path after parent preflight; loader must reject before bootstrap side effects.

This does not require redesign of the inline-loader approach; it only closes the missing trust anchor.

### MEDIUM — native runtime below the child Python executable is not yet explicitly inside or outside the TCB

`...design_v0.6...md:34-39` defines the child Python-installation provenance as the base executable plus `<base-prefix>/lib/python3.13` and `lib-dynload` manifests. That covers Python source/extension payload visible through `sys.path`, but a Python process can execute native code **before `-c` loader code runs** through the ELF loader and shared-library dependencies of the interpreter and native extensions.

The design must choose an explicit boundary:

- either declare the host dynamic loader/system native libraries (and any base-prefix native `.so` dependencies outside `lib/python3.13/lib-dynload`) as part of the external execution-request TCB; or
- expand parent pre-spawn provenance to bind the relevant child native runtime dependencies.

Do not describe the child Python installation as fully bound while leaving this layer implicit. A design statement plus a permanent negative for an in-scope base-prefix native dependency is sufficient; this does not require turning OS-wide libraries into project evidence if they are explicitly declared host TCB.

## Positive observations

- direct lexical worker execution under PyTorch `--no-python` is the right closure for the worker process tree;
- `-I -S -B` is consistently carried across agent/worker/P5 paths;
- inline verifier-owned loader plus verified-bytes `compile/exec` preserves the previous pre-import trust boundary;
- the external parent TCB is now explicitly acknowledged rather than being inferred from the child executable SHA;
- v0.5 copy-only mode-specific staging, P5/D005 output isolation, no-pyc policy, source provenance and tracked+untracked cleanliness remain intact;
- Gitlink remains `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Gate decision

**REQUEST_CHANGES**.

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is not granted yet.

No architectural rollback is requested. Keep the v0.6 `--no-python` direct lexical worker, `-I -S -B -c` loader, pre-spawn child-Python manifest and copy-only staging. A narrow v0.7/addendum only needs to make the request digest externally anchored and make the native-runtime TCB boundary explicit.

Still unauthorized:

- root P4/P5 tooling implementation;
- creating/modifying any Gate venv or source checkout;
- P4 static record regeneration;
- P5 export/retry/compose or `load_experiment_from_toml`;
- torchrun/distributed execution;
- CUDA/GPU;
- model/dataloader/optimizer/checkpoint construction;
- weights/data/MP4 access;
- training/evaluation/inference;
- P5 closure;
- B2-T or any later gate.
