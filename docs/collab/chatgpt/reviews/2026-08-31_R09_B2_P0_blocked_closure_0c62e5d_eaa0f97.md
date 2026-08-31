# R09-B2 P0 blocked preflight review — root 0c62e5d / submodule eaa0f97

## Verdict

**APPROVE_TO_CLOSE_B2_P0_BLOCKED**

This approval closes the current B2-P0 preflight as an honest BLOCKED result. It does **not** authorize B2-T matched training, GPU, evaluation, inference, or any submodule/model change.

## Findings

The P0 collector/verifier correctly records that the currently available evidence is insufficient to freeze a valid matched-training run. The artifact is intentionally `BLOCKED`, while the verifier `PASS` means only that the unresolved blockers were recorded consistently and machine-readably.

Confirmed blockers:
1. no enforceable per-window stream manifest / exact data-stream identity contract;
2. no non-mutating Normal/Zero/Shuffle capture implementation with before/after hashes for model, optimizer, RNG, dataloader cursor and local runtime state;
3. no actual parameter + optimizer-state membership inventory (name/trainable/numel/state membership);
4. no frozen exact argv + sanitized environment + world size + explicit 100-optimizer-update launch contract/D005;
5. only selected config fields are compared; no complete resolved-config machine diff yet.

The existing selected fields are internally consistent: recurrent and TTT use the same precision, seed, batch/accumulation and max_iter, while the visible selected differences are limited to backend/selector fields. However this is not sufficient for B2-T because the complete resolved configuration has not yet been machine-compared.

## Required next implementation scope

A subsequent independently reviewed root-only implementation may add tooling/artifacts needed to close those five blockers. At minimum it must:
- generate and hard-gate an exact consumable ordered stream manifest with stable window identity;
- implement non-mutating intervention capture and prove state hashes/cursors/RNG/model/optimizer are unchanged;
- instantiate the actual model/optimizer read-only and record exact parameter names, numel and optimizer-state membership for both backends;
- produce exact launcher argv/environment/world-size/100-update budget and D005 paths without launching training;
- emit a complete resolved-config diff and hard-fail on any difference outside the approved backend-specific allowlist.

If implementation requires loading model/config/dataset metadata on CPU, that is acceptable only as read-only preflight work; it must not execute optimizer updates, GPU training, evaluation, inference, or closed-loop runs. Any need to modify `cosmos-framework` must return to REVIEW first.

## Gate state

B2-P0 current artifact: CLOSED as **BLOCKED**.

B2-T remains **NOT AUTHORIZED**. After the five blockers are implemented and a new P0 artifact/verifier is generated, submit the new root SHA + unchanged/updated Gitlink for independent three-party review. Only a later explicit run approval may authorize matched training.
