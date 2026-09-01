# R09-B2 P4 v2 interpreter-exception isolation review

- Request: `afa6957ed50da84f68eb5ff1e47e5aa84f114739`
- Implementation: `ddb4e0eae97fb545d5239c1ddb6d4387170f3780`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_REGENERATE_P4_V2_D005**

## Findings

No blocking findings for the requested fresh static regeneration.

The previous interpreter-exception leakage is closed:

1. Generic asset/output allowlists are restored to the repository root, `/localdisk-tmp/models`, and `/disk/rl/data`; the canonical interpreter parent is no longer admitted as a generic runtime/output root.
2. Interpreter handling is isolated in `_interpreter_asset_ok()`, which requires the asset path to resolve exactly to `<root>/cosmos-framework/.venv/bin/python`, and independently checks its canonical realpath and SHA256.
3. All non-interpreter assets continue through the generic `_asset_ok()` contract.
4. `external_assets.interpreter.{realpath,sha256}` is explicitly required to equal `command.interpreter`, so the two interpreter records cannot drift independently.
5. The permanent regression verifies that the interpreter parent is not an external runtime/output allowlist root and that replacing the interpreter asset with the base-checkpoint asset fails verification.

## Authorized step

`APPROVE_TO_REGENERATE_P4_V2_D005` is granted narrowly for one fresh retry:

- use a fresh clean source checkout of implementation `ddb4e0e` with submodule/Gitlink `21d064f`;
- read/hash only the already-approved local assets required to populate the records;
- generate exactly two fresh `r09_b2_p4_launch_d005_v2` records:
  - `artifacts/g0/r09/b2/p4_launch_d005/recurrent.json`
  - `artifacts/g0/r09/b2/p4_launch_d005/ttt_fast_weight.json`
- both records must remain `FROZEN_NOT_EXECUTED` and `command.executable=false`;
- run the standard-library static pair verifier once;
- preserve the earlier failed attempt separately; do not overwrite or reuse it as closure evidence;
- submit the successful pair plus verifier result for independent P4 closure review.

The two D005 paths and both future run roots must be fresh before regeneration. If this fresh attempt fails or leaves partial files, do not overwrite/retry again without a new review.

## Not authorized

This does **not** close P4 and does not authorize P5, B2-T, execution of either D005 argv, `torchrun`, GPU, model construction/execution, checkpoint loading for execution, training, evaluation, inference, closed-loop, multi-GPU, or broader scope.
