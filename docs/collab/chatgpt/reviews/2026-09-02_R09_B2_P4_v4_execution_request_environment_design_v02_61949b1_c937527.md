# R09-B2 P4-v4 Execution Request `environment` v0.2 design review

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_ENVIRONMENT_STATIC_TOOLS`

Target:
- design: `61949b13b16310193466de0a2d60d031bd5fa9a8`
- request: `c937527d1fef5447422e26588c35502558dff85a`
- prior review: `c1f1f4ee029fb0a7ff9b03abfc49d4565fe9a59d`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Closure of prior blockers

1. D005 projection is now machine-verifiable rather than an unconstrained non-forbidden environment map.
   - `environment` adds exact `d005_projection` identity.
   - validator must consume the already verified D005 recurrent/TTT pair and reuse the frozen D005 verifier constants/contracts.
   - the source D005 `environment.set` key set is required to equal `set(REQUIRED_ENV) ∪ {PSM_R09_B1_TTT_ENABLED}` before projection.
   - added/removed/changed source keys, wrong backend/source digest, forged projection digest, or an unverified pair must fail.

2. The backend-specific output-root conflict is resolved explicitly.
   - `PYTHONPATH` and `IMAGINAIRE_OUTPUT_ROOT` are the only excluded D005 keys.
   - `PYTHONPATH` is delegated to the later runtime-sys-path authority.
   - `IMAGINAIRE_OUTPUT_ROOT` is delegated to the later run authority and must later cross-bind to fresh run-root identity and the original D005 value.
   - after those two exclusions, the remaining effective maps are required to differ only at the verifier-owned `PSM_R09_B1_TTT_ENABLED` key (`0` vs `1`).

This is consistent with the existing D005 verifier, whose `REQUIRED_ENV` includes both `PYTHONPATH` and `IMAGINAIRE_OUTPUT_ROOT` and whose `_env_ok()` requires the exact D005 set key universe plus the TTT key. It is also consistent with the current P5 empty-parent environment projection, which requires empty inherit allowlists, exact `P5_FORBIDDEN_ENVIRONMENT`, native-loader `set={}`, and injects `LC_CTYPE=C.UTF-8` only after projection.

## Implementation requirements

The approved scope is static/CPU only. Implementation should:
- use the existing verifier-owned D005 constants/verification path rather than copying their values into a second authority;
- validate exact inner/outer canonical identities and all declared projection digests;
- reject leakage of either excluded key into `effective_environment.set`;
- preserve exact P5 forbidden tuple ordering and empty-parent semantics;
- pair-validate recurrent/TTT and reject any third backend or any difference beyond TTT after projection;
- include the permanent CPU fixtures listed in v0.2, with outer identity recomputed for mutations so the intended branch is exercised.

## Scope

This approval authorizes only implementation of the `environment` root static parser/validator and stdlib CPU fixtures.

Still forbidden:
- real P4-v4 preflight
- staging/materialization/candidate generation
- record/refreeze/evidence publication
- P5 authority population/export/compose
- torchrun/GPU/CUDA
- model/data/checkpoint I/O
- training/eval/inference
- B2-T or Local Memory training

`run`, `candidates`, `backends`, and `authorities` remain separate unclosed sections.
