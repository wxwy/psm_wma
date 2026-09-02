# R09-B2 P4-v4 Execution Request `environment` v0.1 design review

## Verdict

`REQUEST_CHANGES`

Target:
- design: `2421b486bb468b1edf1446dc67ccfe455fba0f97`
- request: `7da25e375715732b8b8d731e87f41ab6087ead02`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- prior closed interpreter review: `a966fa9979dde85d03c2be47c032016dcabe4efc`

## Accepted direction

The design is aligned with the existing P5 empty-parent environment model on the following points:
- exact `effective_environment` / `native_loader_environment` objects with self-SHA;
- `inherit_allowlist=[]`;
- native-loader `set={}`;
- `unset` exact-order binding to `P5_FORBIDDEN_ENVIRONMENT`;
- no ambient `os.environ` inheritance;
- `PYTHONPATH` excluded from effective environment;
- final P5 locale injection as `LC_CTYPE=C.UTF-8` after request projection;
- pair comparison requires the P3-owned `PSM_R09_B1_TTT_ENABLED` difference with recurrent=`0`, ttt_fast_weight=`1`.

Those are the correct invariants to preserve.

## HIGH 1 — D005 projection rule conflicts with the frozen pair-difference rule

The design says `effective_environment.set` is obtained from the already verified D005 `environment.set` by removing forbidden keys and otherwise retaining the remaining fixed key/value pairs. It simultaneously says that the **only** allowed recurrent-vs-TTT difference is `PSM_R09_B1_TTT_ENABLED`.

Those two rules are not simultaneously satisfiable against the frozen D005 evidence currently in the repository.

The committed D005 records have another backend-specific value:

- recurrent `IMAGINAIRE_OUTPUT_ROOT=/disk/rl/data/psm_wma_p4_d005_outputs/recurrent`
- ttt_fast_weight `IMAGINAIRE_OUTPUT_ROOT=/disk/rl/data/psm_wma_p4_d005_outputs/ttt_fast_weight`

`IMAGINAIRE_OUTPUT_ROOT` is not in `P5_FORBIDDEN_ENVIRONMENT`, so the current v0.1 projection rule would retain it. The resulting pair would therefore differ on both `IMAGINAIRE_OUTPUT_ROOT` and `PSM_R09_B1_TTT_ENABLED`, and must fail the design's own section 3 rule / the existing P5 pair-difference contract.

### Required remediation

Freeze one exact projection policy rather than saying “retain all non-forbidden D005 keys”. In particular, classify backend/run-owned keys explicitly.

A valid remediation could, for example:
1. define an exact frozen set of environment-owned keys copied from D005;
2. explicitly exclude `PYTHONPATH` as runtime-sys-path-owned;
3. explicitly exclude `IMAGINAIRE_OUTPUT_ROOT` as `run`-section-owned, with its later value cross-bound by the run contract;
4. require all remaining common keys to be byte-identical across backends;
5. allow only `PSM_R09_B1_TTT_ENABLED` to differ inside the environment section.

Do not silently drop arbitrary future differences. The excluded-key set and ownership must be frozen and tested.

## HIGH 2 — `effective_environment.set` has no machine-verifiable D005 source binding

The design calls `environment` the future candidate's unique environment authority and says the set “must come from already P4-D005-verifier-verified `environment.set`” and “must not introduce new keys”. But the proposed section schema contains only:

`{effective_environment,native_loader_environment,identity_sha256}`

and the validator requirements described in v0.1 only constrain shape, forbidden keys, pair differences and locale projection. There is no D005 record/hash/projection digest or other exact authority input that lets the section validator prove that a candidate set is actually the approved D005 projection.

As written, a request can add an arbitrary non-forbidden key such as `UNREVIEWED_ENV=x`, recompute the section SHAs, keep the same value in both backends, and satisfy all stated environment-section rules.

The sentence that a “later section” will independently re-check source/asset binding is not sufficient to freeze this contract: it does not name the authority section, exact fields, digest, projection function, or mandatory cross-section comparison.

### Required remediation

Freeze the source binding now, either directly or as an exact mandatory cross-section contract. For example:
- bind each backend to an exact reviewed D005/environment authority digest and independently recompute the normalized projection; or
- define a verifier-owned canonical projection digest supplied by a named later `authorities` section, and require `environment` validation to receive and exactly match it before the full execution request can pass.

Whichever route is chosen, permanently test:
- added non-forbidden key -> FAIL;
- removed expected key -> FAIL;
- changed expected value -> FAIL;
- wrong D005/backend authority -> FAIL;
- run-owned excluded key leaking back into `environment.set` -> FAIL.

## Minor design wording

The sentence “all key/value are strings” should be narrowed: `set` entries are string→string; `unset` / `inherit_allowlist` are ordered lists of strings; digest fields are strings. This is not an independent blocker once the schema is stated precisely in implementation requirements.

## Scope

Only environment design/static remediation is authorized.

Still forbidden:
- real P4-v4 preflight
- staging/materialization/candidate generation
- record/refreeze/evidence publication
- P5 authority population/export/compose
- torchrun/GPU/CUDA
- model/data/checkpoint I/O
- training/eval/inference
- B2-T / Local Memory training

Next requested verdict after remediation should remain:
`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_ENVIRONMENT_STATIC_TOOLS` or `REQUEST_CHANGES`.
