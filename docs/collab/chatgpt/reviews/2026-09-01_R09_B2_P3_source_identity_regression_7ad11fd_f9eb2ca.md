# R09-B2 P3 frozen Python recipe identity regression review

- Review request root: `7ad11fd872707142354955eca2e822c82341f9fd`
- Reviewed implementation root: `f9eb2caed4673eebe46429198bbbf5fb28be2958`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: root-side static verifier regression only; no GPU/processor/model construction authorization.

## Verdict

**APPROVE_TO_CONTINUE_GPU_P3_IMPLEMENTATION**

The permanent negative regression requested in the prior review is now present and correctly targets the production Python recipe identity rather than the TOML entrypoint.

## Accepted

1. `tools/g0/test_verify_r09_b2_p3_gpu_inventory.py` constructs a minimal artifact that first passes the existing P3 verifier hard gates.
2. The regression leaves the TOML identity unchanged and mutates only the frozen production Python recipe `action_policy_libero_edge_all.py`.
3. After that mutation, the verifier must report `source_hashes_valid=false` and final `status=FAIL`; therefore a Python recipe/config drift cannot be hidden behind an unchanged TOML.
4. The test restores the exact original source bytes and removes its temporary D005 fixture in `finally`.
5. The reviewed implementation root Gitlink is exactly `0af5d53900ec169f43104d4fdf1827ad6691600d`.
6. No model/processor construction, GPU, checkpoint I/O, forward/backward, optimizer/scheduler step, data/VAE loading, or runtime execution is introduced by this change.

## Non-blocking run-precondition note

The regression intentionally mocks `_tracked_clean` so that the test isolates source-identity behavior while it creates a temporary D005 and mutates a source file. This is acceptable for the dedicated regression. It does not replace the real run-time cleanliness hard gate.

Before any `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`, keep the previously required real root/submodule cleanliness and source-blob checks active. Prefer a fully isolated temporary worktree for future mutation-style regressions if additional cases are added, so an externally terminated test cannot leave a production checkout dirty.

## Scope

This verdict authorizes only continued root-side static collector/verifier/test implementation.

It does not authorize GPU execution, processor/model construction, checkpoint/model-weight/VAE/data/dataloader loading, forward/backward/optimizer/scheduler step, DCP save/load, B2-T, P4/P5, training, eval, inference, closed-loop, SR, multi-GPU, long training, backend freeze, Global/Agent/RL.
