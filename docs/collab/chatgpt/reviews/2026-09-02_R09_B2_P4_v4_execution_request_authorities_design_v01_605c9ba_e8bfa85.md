# R09-B2 P4-v4 Execution Request `authorities` v0.1 design review

## Verdict

`REQUEST_CHANGES`

Target:
- design: `605c9ba9229096a3d3f350b2c6d0b149ab625d40`
- request: `e8bfa856b23b6ada0101ac3741737ccd01472d3d`
- prior ChatGPT anchor: `f7c1cb9c849c8e4b06e19190cbe8f67bcbc64bee`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

The high-level direction is sound: `authorities.d005_pair` should be the named authority feeding the already-closed environment section; path bytes should be bound with no-follow single-fd reads; records should be re-verified rather than trusting a candidate-declared PASS; and no real preflight/staging/export/GPU/training is authorized here.

Two design blockers remain because the proposed contract is not satisfiable by the currently frozen D005 evidence/toolchain.

## HIGH 1 — canonical-raw requirement rejects the currently frozen verification artifact

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_authorities_design_v0.1_2026-09-02.md:9`

The design requires all three bound raws, including `verification`, to be compact canonical JSON (`sort_keys`, compact separators, one trailing newline).

The currently committed `artifacts/g0/r09/b2/p4_launch_d005/verification.json` is the verifier's pretty-printed `indent=2` JSON. The current verifier `main()` also writes `json.dumps(..., indent=2, sort_keys=True) + "\n"`.

Therefore the proposed validator would reject the existing frozen verification artifact before it can serve as authority. This cannot be closed by an implementation trick: either the contract must explicitly admit the exact frozen verification bytes while separately canonicalizing the decoded object for semantic checks, or a separately reviewed evidence regeneration/refreeze must be introduced. This design explicitly forbids record/refreeze and does not name such a prerequisite.

Required design remediation:
- distinguish **byte binding** (`sha256` over exact fd-bound raw) from **semantic canonicalization** of the decoded verifier object; or
- explicitly introduce a separately authorized canonical verification artifact/refreeze prerequisite.

Do not silently rewrite the existing verification evidence in this Gate.

## HIGH 2 — current D005 records/verifier/source cannot satisfy the proposed same-source contract

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_authorities_design_v0.1_2026-09-02.md:9-11`

The design simultaneously requires:
1. the fd-bound records to pass the **current** `verify_r09_b2_p4_d005.verify_pair(recurrent, ttt, root)`;
2. `authorities.d005_pair.source` to equal both record `source` objects; and
3. that same source tuple to equal the already-verified current execution-request `entry/source` revision/Gitlink/submodule revision, explicitly rejecting historical source.

The currently frozen pair under `artifacts/g0/r09/b2/p4_launch_d005/` is historical:
- record schema is `r09_b2_p4_launch_d005_v2`;
- record `source.root_revision` is `ddb4e0eae97fb545d5239c1ddb6d4387170f3780`;
- Gitlink/submodule remain `21d064f2...`.

The current `write_r09_b2_p4_d005.py` / verifier contract uses `SCHEMA = r09_b2_p4_launch_d005_v4`. The current `verify_pair()` therefore does not validate the existing v2 records as the current v4 pair. Meanwhile the execution-request source necessarily points at the later tooling revision containing the new request validators, not historical `ddb4e0...`.

So the v0.1 contract requires an authority object that does not currently exist and cannot be produced within this Gate because record/refreeze is explicitly forbidden.

Required design remediation: choose and freeze one coherent authority model, for example either:
- **historical D005 authority model**: bind the exact historical D005 record/verifier bytes and their own source/verifier identity, without pretending their root revision equals the current execution-request source; then define the precise compatibility/cross-binding needed to project those frozen records into the current request; or
- **current-source D005 refreeze model**: make generation/refreeze of a v4 D005 pair at the current source an explicit, separately reviewed prerequisite before `authorities` implementation/closure.

Whichever model is chosen, pin the verifier authority explicitly. Do not call an evolving ambient/current module `verify_pair()` to validate historical evidence without freezing which verifier revision/bytes define that evidence.

## Non-blocking positive findings

- exact `authorities={d005_pair,identity_sha256}` shape is reasonable;
- root-relative distinct bindings + `O_NOFOLLOW`/single-fd bytes are appropriate;
- environment cross-binding through `validate_environment_pair()` is the correct integration direction;
- keeping `IMAGINAIRE_OUTPUT_ROOT` and `PYTHONPATH` owned by later run/runtime sections is consistent with the closed environment contract;
- the proposed CPU fixture categories are broadly appropriate once the authority model is made satisfiable.

## Authorization

No implementation authorization is granted for authorities v0.1.

Allowed next step: design-only remediation of the two blockers above and resubmission for `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_AUTHORITIES_STATIC_TOOLS`.

Still forbidden: real preflight, staging/materialize/candidate, record/refreeze unless separately authorized, evidence publication, P5 authority/export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, and Local Memory training.
