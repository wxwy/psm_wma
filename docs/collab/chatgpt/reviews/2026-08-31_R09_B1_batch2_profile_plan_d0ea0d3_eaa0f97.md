# R09-B1 bounded profile failure rework review — root d0ea0d3 / submodule eaa0f97

## Verdict

**APPROVE_B1_BATCH2_PROFILE_REWORK**

This approves only the root-side implementation of the proposed phase-specific bounded smoke profile. **It does not authorize GPU execution.**

## Review

The failure description is internally consistent with the bounded-smoke objective: Gate-A batch1/accum1 completed 2/2 finite steps and saved the replacement DCP; B1 then model-only loaded that checkpoint but failed on the first backward because the B1 optimizer contains only Local parameters while the first deterministic causal window (`start=0`) carries no Local-history evidence. With no selected trainable parameter participating in the loss graph, `loss.backward()` can legitimately raise `element 0 of tensors does not require grad and does not have a grad_fn`.

Changing only the B1 phase from `max_samples_per_batch=1` to `2`, while keeping Gate-A at 1, `grad_accum_iter=1`, 2/5 optimizer steps, the same checkpoint handoff, model, cache, environment, history mode and TTT contract is an appropriately narrow smoke-profile repair. It remains bounded/noncanonical and must not be interpreted as a formal training recipe or performance result.

## Required implementation contract

The root-only implementation may proceed, subject to all of the following hard requirements:

1. The launcher must encode a **phase-specific** profile: Gate-A=`max_samples_per_batch=1`, B1=`max_samples_per_batch=2`, both with `grad_accum_iter=1`; no submodule/model/recipe changes.
2. D005 must record the phase-specific profile and structured argv exactly, and reject phase/profile mismatches.
3. The verifier must hard-gate Gate-A=1 and B1=2 independently rather than accepting one global smoke profile.
4. Do **not** rely solely on the assumption that batch size 2 implies useful Local history. The implementation/evidence path must machine-prove that the first B1 training batch contains at least one sample with effective Local history (`history_present` or equivalent runtime evidence) before treating the repair as valid. If exact window indices are available, record them and confirm the intended `start=0` + `start=1` coverage; otherwise an equivalent direct Local-present assertion is sufficient.
5. Preserve all existing GPU binding, source/Gitlink provenance, cache-only/no-online-VAE, exact model-only checkpoint handoff, optimizer membership/gradient, TTT state/reset/detach, checkpoint, clean-tree and bounded/noncanonical warning gates.

After implementation, submit the new root SHA with unchanged submodule/Gitlink for a separate `APPROVE_TO_RUN_*` review. Until that review and the matching Kimi/MM approvals complete, GPU remains blocked.

Any later run failure must stop and preserve evidence; no automatic retry, larger batch, submodule change, formal recipe change, eval/inference, multi-GPU, long training, matched SR, backend freeze, Global/Agent/RL expansion is authorized here.
