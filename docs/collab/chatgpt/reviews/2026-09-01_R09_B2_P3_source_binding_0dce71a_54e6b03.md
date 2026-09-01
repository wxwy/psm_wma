# R09-B2 P3 source-binding re-review

- Review request root: `0dce71ac9be7fa69663170af302632d3655ffa3d`
- Reviewed implementation root: `54e6b03cf30bc22eb28a552d9c2fbe5f89dc9877`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: root-side static verifier/provenance hardening only; no GPU/processor/model construction authorization.

## Verdict

**REQUEST_CHANGES**

The previous worktree/source-cleanliness blocker is substantially closed: source hashes are now recomputed from commit blobs, filesystem bytes are compared to those blobs, root/submodule tracked-clean and submodule HEAD/Gitlink are checked, and D005 containment is resolved before reading.

However one HIGH provenance gap remains.

## HIGH — `recipe_sha256` binds only the TOML launcher config, not the production Python recipe that determines P3 behavior

`FROZEN_SOURCE_PATHS["recipe_sha256"]` currently points only to:

`cosmos-framework/examples/toml/sft_config/action_policy_libero_edge_all.toml`

That TOML merely selects `experiment = "action_policy_libero_edge_all"` and supplies top-level runtime overrides. The production Python recipe:

`cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py`

actually determines P3-critical behavior, including:
- `vlm_config.tokenizer.tokenizer_type = ${oc.env:EDGE_POLICY_CHECKPOINT}`;
- `local_history_backend` selector;
- A1/B1 mutual exclusion;
- exact optimizer `keys_to_select` for recurrent vs TTT;
- dataloader/history settings.

Therefore the current verifier can still PASS when the TOML is unchanged but this Python recipe has changed at the reviewed submodule revision/worktree. The same issue applies to direct inherited config dependencies that determine model/optimizer construction (at minimum `edge_model_config.py` and the inherited `action_policy_libero_all_nano` recipe), unless the verifier instead binds a machine-readable resolved recipe/config snapshot produced from the exact production config path.

### Required fix

Before calling recipe provenance closed, do one of the following:

1. **Preferred:** bind a canonical resolved production recipe/config snapshot used by the worker, with SHA256 and exact source revision, and verify the snapshot is produced from the reviewed `action_policy_libero_edge_all` config path; or
2. Bind the complete minimum source set that determines P3 model/processor/optimizer construction, including at least:
   - `examples/toml/sft_config/action_policy_libero_edge_all.toml`
   - `cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py`
   - `cosmos_framework/configs/base/experiment/sft/models/edge_model_config.py`
   - `cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_all_nano.py`

All must be commit-blob-derived and current-filesystem-equal under the exact submodule revision.

Add a negative regression where TOML stays fixed but the Python recipe/config source identity is altered; provenance must FAIL.

## Accepted from this round

- root/submodule commit-blob source hashing and filesystem equality;
- root/submodule tracked-clean checks;
- submodule HEAD == Gitlink == artifact submodule revision;
- D005 relative-path and resolved containment protection, including symlink escape rejection;
- BLOCKED artifacts do not need invented run provenance;
- no GPU/model/processor/runtime scope creep.

## Scope

Still not authorized:
- GPU execution;
- processor/model construction;
- checkpoint/model-weight/VAE/data/dataloader loading;
- forward/backward/optimizer/scheduler step;
- DCP save/load;
- B2-T, P4/P5, training/eval/inference/closed-loop/SR/multi-GPU/long training/backend freeze/Global/Agent/RL.
