# R09-B2 P4-v4 Execution Request `environment` v0.2 remediation review

## Verdict

`REQUEST_CHANGES`

Target:
- remediation: `45d78e3dafd01177c7c8da1b2f189b16b51ead58`
- request: `98060e00dbff7c57ae15187196f7bdd7fbd52ae2`
- approved design: `61949b13b16310193466de0a2d60d031bd5fa9a8`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Accepted

The environment validator logic remains aligned with approved v0.2: verified D005 pair is a hard prerequisite; projection excludes only `IMAGINAIRE_OUTPUT_ROOT` and `PYTHONPATH`; P5 forbidden/empty-parent/native grammar is reused; D005 record backend is now cross-bound to the requested backend; the unrelated host-Git fail-closed regression was restored. No new environment code blocker was found in this narrow remediation.

The previous fixture gap is substantially reduced: inner/outer digest drift, forbidden tuple/order, allowlist, native set, forbidden effective key, D005 added/removed/backend/digest/projection/exclusion drift, both excluded-key leaks, P3 missing/reversal/additional environment difference, and ambient-parent independence are now represented.

## HIGH — three frozen fixture semantics are still not exercised exactly

### 1. D005 changed projected value is not actually tested

`tools/g0/test_r09_b2_p4_v4_execution_preflight.py` test `test_environment_rejects_d005_source_projection_and_pair_drift` labels one case `changed D005 fixed value`, but mutates `PYTHONPATH`.

`PYTHONPATH` is one of the two intentionally excluded keys and its `REQUIRED_ENV` authority is `None`, so this case only proves that `input_set_sha256` changes while the projected set excludes that key. It does not exercise the approved v0.2 requirement that a changed **non-excluded projected D005 value** is rejected.

Required permanent fixture: mutate a projected verifier-fixed key such as `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`, `CUDA_VISIBLE_DEVICES`, or another non-excluded D005 value, while keeping the request section bound to the original projection, and require fail-closed on the D005/projection branch.

### 2. `third backend` is not tested

The approved v0.2 fixture matrix explicitly includes `third backend`. Current case named `third difference` only inserts an additional environment key into `ttt_fast_weight`; it does not mutate the top-level pair backend roster.

Required permanent fixture: add an unexpected third top-level backend entry (or otherwise mutate the pair key set away from exactly `{recurrent, ttt_fast_weight}`) and require `execution request environment pair schema differs`.

### 3. Locale ordering has only the negative half

Current `locale request` fixture proves `LC_CTYPE` cannot be present in the request `effective_environment.set`. The frozen design also requires the ordering semantic: `LC_CTYPE=C.UTF-8` is injected only **after** environment projection by the P5 child environment projection.

Required static/CPU fixture: keep `LC_CTYPE` absent from both request sections, run the already-frozen P5 environment projection helper on the validated pair, and assert the resulting backend-specific child environment contains exactly `LC_CTYPE=C.UTF-8` without ambient-parent influence. No export/child execution is needed.

## Scope

Only the three missing permanent CPU fixtures above are required. Do not expand `authorities.d005_pair` here; v0.2 explicitly leaves its path/bytes/source identity to the independent `authorities` section.

Still forbidden: real preflight, staging/materialization/candidate generation, record/refreeze/evidence publication, P5 authority population/export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training.
