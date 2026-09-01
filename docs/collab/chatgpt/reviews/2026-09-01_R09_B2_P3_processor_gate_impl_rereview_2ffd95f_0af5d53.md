# R09-B2 P3 local processor hard-gate implementation re-review

- Review request: root `2ffd95f9c95bccd716d4a06e2745be2c6f6c64fb`
- Reviewed implementation root: `4c959422fcf5548725ed6d86069977c9abf425e6` (initial hardening `a67ed4372aa53cae954d7f209fb662bc7ce9d5e0`)
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: root-side static collector/verifier implementation only; **no GPU/model construction/runtime authorization**

## Verdict

**APPROVE_TO_CONTINUE_GPU_P3_IMPLEMENTATION**

The Kimi-requested BLOCKED-semantics fix is correct and safe for this intermediate static step.

## Accepted

1. `tools/g0/collect_r09_b2_p3_gpu_inventory.py:11-39` performs only a local, read-only canonical-path/asset audit before the run-token branch. It hashes the six frozen processor/tokenizer configuration assets without importing Transformers or constructing the model.
2. `tools/g0/collect_r09_b2_p3_gpu_inventory.py:49-79` correctly emits `status=BLOCKED` both when the separate run token is absent and when the local processor directory/assets are unavailable; it does not silently synthesize a processor or fall through into model construction.
3. `tools/g0/verify_r09_b2_p3_gpu_inventory.py:94-108` now distinguishes a valid BLOCKED record from a PASS claim. A missing local directory/asset may be the reason for BLOCKED and therefore does not itself convert the record into FAIL; all other static execution-contract checks must still remain valid.
4. For a future `status=PASS`, `local_processor_path` and `local_processor_assets` remain mandatory because `pass_ready` still uses the complete `checks` set. The optimizer/state/DCP/TTT and matched-diff PASS gates were not weakened.
5. The duplicated `checkpoint_loaded` entry in `NO_EXECUTION_FIELDS` was removed; semantics are unchanged.
6. The reviewed HEAD Gitlink is exactly `0af5d53900ec169f43104d4fdf1827ad6691600d`.

## Hard requirements before any `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`

These are **not blockers to continuing root-side static implementation**, but they are blockers to any GPU/model-construction run approval:

1. **Actual offline environment, not a declaration.** Current `local_processor_record()` records the required values but does not set or observe process environment. The run-enabled implementation must set `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and the approved local cache path **before any Transformers/HF/model import**, then record the observed environment used by the isolated worker. The verifier must hard-gate those observed values.
2. **Production processor binding.** The recipe-resolved production processor/tokenizer source must resolve to the same canonical path as the approved `EDGE_POLICY_CHECKPOINT`; an artifact-local self-declared path is insufficient. Any repository/revision/remote-code resolution must BLOCK.
3. **Read-only package proof.** Capture a deterministic before/after manifest for the approved local processor package (at minimum path, file set, size/SHA256 for the frozen assets; preferably the whole package metadata set relevant to processor loading) and hard-require no added/removed/modified files attributable to P3 construction.
4. **Provenance must become a PASS hard gate.** The future artifact/verifier must bind actual root revision, submodule revision, root Gitlink, recipe SHA, collector SHA, verifier SHA, relevant model/optimizer/serialization source SHAs, exact command/cwd/environment, world size/GPU identity/resource cap, and the reviewed run token/D005 record. The current static BLOCKED artifact is not sufficient evidence for execution provenance.
5. **DCP production membership must be actually inspected.** `dcp_state.production_binding` cannot be satisfied by a symbol string alone. Future PASS must record the stable persistent key/schema membership obtained from the approved production serialization/state-dict path and explicitly prove the five TTT runtime members are absent. If this cannot be obtained without DCP save/load, checkpoint I/O, weight loading, forward/backward/step, or other forbidden behavior, the only legal result is `BLOCKED`.
6. Keep the fixed verifier-owned recurrent-only policy, empty selector exclusions, selector==actual optimizer membership, optimizer-state eligibility/materialization checks, TTT five-member exclusion, single-process/single-GPU scope, and <=24 GiB cap. No synthetic fallback.

## Scope ruling

This verdict authorizes only continued **root-side static implementation/tests/verifier work** for the GPU-only P3 Gate.

It does **not** authorize:
- GPU execution or model construction;
- processor construction yet;
- model/checkpoint/VAE/data/dataloader loading;
- forward/backward/optimizer/scheduler step;
- DCP save/load or checkpoint write;
- B2-T, P4/P5;
- training, eval, inference, closed-loop, SR, multi-GPU, long training, backend freeze, Global/Agent/RL.

A separate exact implementation review and `APPROVE_TO_RUN_GPU_ONLY_P3_GATE` remain mandatory before any GPU/model-construction command.