# 仿真环境入口

本目录只保存指向实际仿真代码和资源位置的软链接，不复制第三方包或大资源。

- `libero` → `/root/venvs/psm_wma/lib/python3.13/site-packages/libero`
- `robosuite` → `/root/venvs/psm_wma/lib/python3.13/site-packages/robosuite`
- `mujoco` → `/root/venvs/psm_wma/lib/python3.13/site-packages/mujoco`
- `cosmos_libero_adapter` → `/gemini/code/psm_wma/cosmos-framework/cosmos_framework/simulation/libero`

LIBERO 入口已包含 `libero_10`、`libero_90`、`libero_goal`、`libero_object` 和 `libero_spatial` 的 BDDL 与 init files；robosuite 入口已包含 arenas、assets、robots 和 tasks。
