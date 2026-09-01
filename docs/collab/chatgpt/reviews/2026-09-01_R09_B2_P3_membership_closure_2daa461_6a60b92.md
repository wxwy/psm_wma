# R09-B2 P3 row-level selector membership closure review

- Request: `2daa4617f47800407cbf71b4621a8ae9d2072092`
- Implementation: `6a60b929757b803db4c7aa6d18a4303b9230dfd5`
- Attempt-6 collection root: `269540e3ac6b25be8c1f3549f58d9ed28147cb2e`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_CLOSE_B2_P3_GPU_ONLY**

## Independent review

No blocking finding remains from ChatGPT review `9b9d72a`.

### 1. Production selector semantics are reproduced exactly

At Gitlink `21d064f`, `cosmos_framework/utils/generator/optimizer.py:205-214` builds the trainable parameter dictionary from `model.net.named_parameters()` and applies the production selector with:

```python
if len(keys_to_select) > 0 and not any(key in pn for key in keys_to_select):
    p.requires_grad = False
    continue
```

The new verifier implements the same substring membership rule in `tools/g0/verify_r09_b2_p3_gpu_inventory.py:177-184` and independently derives the expected set from every recorded `model_parameters[*].name` rather than trusting `selected_by_*` booleans.

The verifier then requires both artifact selector membership and actual optimizer-object membership to equal that independently recomputed set exactly (`verify_r09_b2_p3_gpu_inventory.py:187-220`). Existing optimizer reverse-map, duplicate, group, state, DCP membership/schema and TTT exclusion checks remain in force.

Production first filters pre-existing `requires_grad=False` parameters before applying the substring selector. The verifier's recomputation over all recorded model parameter names is therefore at least as strict: any selector-matching parameter omitted by the actual optimizer due to pre-existing frozen state would make `optimizer_membership_exact` fail. Attempt-6 passes this stricter check.

### 2. Frozen selector lists match the reviewed production recipes

At Gitlink `21d064f`:

- `action_policy_libero_all_nano.py:76-87` defines the inherited selector keys `moe_gen`, `time_embedder`, `vae2llm`, `llm2vae`, `action2llm`, `llm2action`, `action_modality_embed`.
- `action_policy_libero_edge_all.py:205-217` appends `local_memory2llm`, `local_memory_modality_embed`, and `local_history_runtime` for the recurrent configuration.
- `action_policy_libero_edge_all.py:225-230` replaces the TTT selector with exactly `local_history_runtime.encoder`, `local_memory2llm`, `local_memory_modality_embed`.

These are the verifier-owned `EXPECTED_RECURRENT_SELECTOR_KEYS` and `EXPECTED_TTT_SELECTOR_KEYS` in `verify_r09_b2_p3_gpu_inventory.py:13-20`, with recipe source SHA binding retained.

### 3. Recurrent-vs-TTT optimizer/DCP differences are now exact-set checks

`verify_r09_b2_p3_gpu_inventory.py:279-345` independently computes `expected_recurrent` and `expected_ttt`, derives both exact set differences, and requires:

- resolved-selector recurrent-only / TTT-only sets to equal that exact difference;
- actual optimizer recurrent-only / TTT-only sets to equal that exact difference;
- optimizer-DCP schema owner differences to equal that exact difference.

The previous broad substring allow path that could confuse `local_history_runtime` with `local_history_runtime.encoder` is removed.

Structural model/buffer/DCP-model differences remain restricted to the reviewed recurrent-backend prefix.

### 4. Required negative regression is present

`tools/g0/test_verify_r09_b2_p3_gpu_inventory.py:606-625` leaves the frozen selector lists untouched, adds `local_history_runtime.encoder.visual_proj.weight`, and consistently marks it unselected by both selector and optimizer. The test requires:

- `selector_contract_exact == true`;
- TTT `selector_membership_exact == false`;
- TTT `optimizer_membership_exact == false`;
- verifier status `FAIL`.

This directly closes the false-PASS case identified in `9b9d72a`.

### 5. Attempt-6 evidence was not rerun or rewritten

The diff from ChatGPT anchor `9b9d72a` to request `2daa461` does not modify the original attempt-6 aggregate, recurrent worker, TTT worker, or D005 artifacts. It changes the verifier/tests and updates only the derived selector-review verifier JSON.

The original D005 remains bound to collection root `269540e`, Gitlink/submodule `21d064f`, one visible GPU, the reviewed Python interpreter + collector argv, offline/local processor environment, run token, and the frozen run path.

The collection-root tree independently confirms Gitlink `cosmos-framework -> 21d064f`.

The re-verification artifact `artifacts/g0/r09/b2/p3_gpu_inventory_attempt6/p3_gpu_inventory_verifier_selector_review.json` reports:

- recurrent `selector_membership_exact=true` and `optimizer_membership_exact=true`;
- TTT `selector_membership_exact=true` and `optimizer_membership_exact=true`;
- optimizer/DCP membership/schema checks true;
- all provenance/source/Gitlink/clean-worktree checks true;
- all matched-diff checks true, including `selector_contract_exact`;
- `record_valid=true`, `status=PASS`.

No GPU rerun is required; this is exactly the verifier-only revalidation allowed by the previous ChatGPT review.

## Gate decision

**APPROVE_TO_CLOSE_B2_P3_GPU_ONLY**.

This closes only the R09-B2 P3 GPU-only optimizer inventory gate and resolves the P0 actual optimizer-membership blocker addressed by P3.

It does **not** authorize P4, P5, B2-T, training, evaluation, inference, closed-loop execution, multi-GPU, long training, backend freeze, Global Memory, Agent, RL, or any additional GPU run. Those remain subject to their own gate/review requirements.
