# Stage-1 v1.7 live-plan continuity CPU/static implementation design v2.5

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`。
**依据**：V24 三方同 pair 批准的 continuity model。

## 范围

只在现有 `tools/psm_wma/stage1_v17_pre_c_rehearsal.py` 与其 stdlib unittest 中增加纯内存的 `LivePlanSessionV1`、opaque continuation lease 和 resume-only entrypoint。不得新增真实 host capability、文件 I/O、subprocess、网络或 pair 写入。

## 最小 contract

- session 创建时接收唯一 sealed plan，并以不可复制 object token 绑定 plan/lease/session identity 和 binding digest；
- pending 状态仅可读取 audit record，直接 consume/resume、copy/serialize/rebind 全部 fail-close；
- approve 后 entrypoint 只接受同一 live lease 与 exact approval identity；验证三元 binding 后把原 plan object 交给既有 `consume_once_v05`；
- revoke、identity mismatch、session close 或异常均 terminal invalid，不能创建替代 plan 或从 record 回填；
- tests 证明 same-instance handoff、foreign lease/plan 拒绝、pending direct-consume 拒绝、loss terminal、C 不接收 reconstruction input。

## 验收

stdlib unittest、py_compile、diff-check 全通过；只证明内存 contract。真实 pre-C/C、request pair、materialization/source-evidence、child/runtime/config、GPU 和训练仍禁止。

Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
