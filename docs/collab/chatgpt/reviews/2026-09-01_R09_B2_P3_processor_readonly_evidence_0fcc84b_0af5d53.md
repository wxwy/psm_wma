# R09-B2 P3 processor read-only evidence static implementation review

- Review request root: `0fcc84b9be8ac8a94bf7d937c1d4a7fad81b6f40`
- Reviewed implementation root: `d30c11c47ccbecc20250a4cae8be83736adff07e`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: root-side static helper/verifier work only; **no GPU / processor construction / model construction authorization**

## Verdict

**APPROVE_TO_CONTINUE_GPU_P3_IMPLEMENTATION**

This intermediate static step correctly closes part of the prior run-before hard requirements without crossing the execution boundary.

## Accepted

1. `tools/g0/collect_r09_b2_p3_gpu_inventory.py:23-43` now records a deterministic six-file local processor snapshot including canonical path, existence, size and SHA256.
2. `tools/g0/collect_r09_b2_p3_gpu_inventory.py:46-50` adds an explicit helper that applies the approved offline environment and reads back the observed values. This is the right mechanism for the future isolated worker, provided it is invoked before any HF/Transformers import.
3. `tools/g0/collect_r09_b2_p3_gpu_inventory.py:53-55` adds strict before/after record comparison for the approved processor package evidence.
4. `tools/g0/verify_r09_b2_p3_gpu_inventory.py:91-110` makes future PASS require the observed offline environment to equal the approved environment and requires `before_assets == after_assets == required_assets`.
5. Existing PASS-only optimizer/state/DCP/TTT and matched-diff hard gates remain intact; BLOCKED semantics are not weakened.
6. The reviewed root tree still points exactly to submodule/Gitlink `0af5d53900ec169f43104d4fdf1827ad6691600d`.
7. No processor/model construction, GPU, network, checkpoint I/O, VAE, dataloader/data, forward/backward or optimizer/scheduler step is introduced in this commit.

## Remaining hard requirements before any GPU/model-construction run approval

These are not blockers to continued static implementation, but remain blockers to `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`:

1. **Canonical asset-path binding must be verifier-owned.** For each frozen asset, the verifier must hard-require `asset.path == canonical_path / expected_filename`, not merely `set(assets)==REQUIRED_PROCESSOR_ASSETS` plus a non-empty SHA. It should also require a valid non-negative `size_bytes` and exact before/after size+SHA equality.
2. **Observed offline environment must come from the actual isolated worker.** The future artifact must make it unambiguous that `apply_offline_processor_environment()` ran before any HF/Transformers/model import. A self-declared JSON field is not sufficient. Prefer a worker phase/order record or equivalent machine-checkable evidence.
3. **Production processor binding remains required.** The recipe-resolved processor/tokenizer source must equal the approved canonical local `EDGE_POLICY_CHECKPOINT`; any repository/revision/remote-code resolution must BLOCK.
4. **Read-only proof should cover the actual load scope.** At minimum the six frozen files must be unchanged; if processor construction can touch additional local package metadata/cache files, the approved pre/post manifest must cover that relevant set or fail closed on any added/removed/modified file attributable to P3.
5. **Execution provenance must become a hard PASS gate.** Bind actual root/submodule/Gitlink, recipe SHA, collector/verifier SHA, relevant model/optimizer/serialization source SHAs, exact command/cwd/environment, GPU identity/world-size/resource cap, and the reviewed run authorization/D005 record.
6. **DCP production membership must be actual, not symbolic.** `dcp_state.production_binding.symbol` alone is insufficient. Future PASS must obtain the stable persistent schema through the approved production serialization/state-dict path and explicitly prove the five TTT runtime members are absent. If this cannot be done without forbidden save/load/checkpoint I/O/weight loading/forward/backward/step, return `BLOCKED`.
7. Preserve the verifier-owned recurrent-only prefix, empty selector exclusions, selector==actual optimizer membership, optimizer-state eligibility/materialization checks, TTT five-member exclusion, single-process/single-GPU scope, and <=24 GiB cap. No synthetic fallback.

## Scope ruling

This verdict authorizes only continued **root-side static implementation/tests/verifier work**.

It does **not** authorize:
- GPU execution;
- processor construction;
- model construction;
- checkpoint/model-weight/VAE/tokenizer-weight/data/dataloader loading;
- forward/backward/optimizer/scheduler step;
- DCP save/load or checkpoint write;
- B2-T, P4/P5;
- training, eval, inference, closed-loop, SR, multi-GPU, long training, backend freeze, Global/Agent/RL.

A later exact implementation review plus separate `APPROVE_TO_RUN_GPU_ONLY_P3_GATE` remain mandatory before any GPU/model-construction command.