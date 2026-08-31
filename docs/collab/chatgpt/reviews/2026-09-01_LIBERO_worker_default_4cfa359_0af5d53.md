# LIBERO launcher worker default help-text review

- Review target root: `4cfa359c4fda78f228473cdb6f640b949505cfb0`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Verdict: **APPROVE**

## Findings

No blocking issue found.

The submodule change is documentation-only: `examples/launch_sft_action_policy_libero_edge_all.sh` changes the help comment for `LIBERO_NUM_WORKERS` from `default: 32` to `default: 12` and does not modify executable shell logic.

Independent source checks confirm the actual runtime defaults were already `12` before this help-text correction:

- `examples/launch_sft_action_policy_libero_edge_all.sh`: `${LIBERO_NUM_WORKERS:=12}`
- `cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py`: `os.environ.get("LIBERO_NUM_WORKERS", "12")`
- `examples/tmux_launch_sft_libero_edge_all.sh`: `${LIBERO_NUM_WORKERS:=12}`

Therefore this commit only removes stale documentation and does not change runtime behavior, environment override semantics, dataloader construction, training, GPU usage, or any R09/P3 gate contract.

## Scope

Approval applies only to this launcher help-text consistency fix. It does not authorize GPU execution, training, evaluation, inference, B2-T, P4/P5, or any other pending gate.
