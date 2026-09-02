# R09-B2 P4-v4 Execution Request `environment` 静态合同 v0.2

**状态**：draft；替代未批准的 v0.1，仅申请 root static parser/validator tooling 与 stdlib CPU fixtures。整改 ChatGPT/MM：D005 projection 必可机器验证，且 `IMAGINAIRE_OUTPUT_ROOT` 是 `run` section-owned，不能泄漏入 P5 environment pair。

`environment` 精确为 `{effective_environment,native_loader_environment,d005_projection,identity_sha256}`；前两个对象精确为 `{set,unset,inherit_allowlist,sha256}`，`d005_projection` 精确为 `{backend,d005_sha256,input_set_sha256,excluded_keys,projected_set_sha256,sha256}`。`set` 为 string→string map，两个列表为有序 string list，所有 digest 为 64 lowercase hex；所有内层/外层 SHA 均按删除自身字段后的 canonical JSON 重算，额外、缺失、类型或顺序漂移均 FAIL。

实现必须复用 `tools/g0/verify_r09_b2_p4_d005.py` 的冻结 `REQUIRED_ENV`、`RANK_ENV`、`SANITIZED_ENV`、P3 backend mapping及已经 `verify_pair()` 验证 PASS 的 D005 recurrent/TTT pair；不得维护第二份 allowlist，也不得读取 shell/tmux/`os.environ`。`validate_environment_pair()` 强制接收该 verified pair；完整 request 后续必须将同一 pair 作为 named `authorities.d005_pair` 输入，再由独立 authorities section 冻结路径/bytes/source identity。没有或未验证的 pair 立即 FAIL。

每 backend 的 `d005_projection` 必由 record 独立重算：backend=record backend；d005_sha256=record self digest；input_set_sha256=D005 `environment.set` canonical SHA；excluded_keys 精确有序为 `["IMAGINAIRE_OUTPUT_ROOT","PYTHONPATH"]`；projected_set_sha256=下述 projected set SHA。added/removed/changed non-forbidden key、错误 backend/digest、伪造 projection digest或不同源 authority 均 FAIL。

投影先要求 D005 set key 集合精确为 `set(REQUIRED_ENV) ∪ {"PSM_R09_B1_TTT_ENABLED"}`，再只删除 `excluded_keys`。`PYTHONPATH` 属后续 runtime_sys_path；`IMAGINAIRE_OUTPUT_ROOT` 属后续 run section，须由 fresh run-root identity 与 D005 原值 cross-bind；不得静默删除/改写/新增其他 key。拒绝 `RANK_ENV`、`SANITIZED_ENV`、P5 forbidden key及非字符串值。

effective/native 均 `inherit_allowlist=[]`，unset 精确逐项等于 P5 `P5_FORBIDDEN_ENVIRONMENT`，native set=`{}`；effective set 不含 forbidden key。P5 child 仅在 projection 后注入 `LC_CTYPE=C.UTF-8`，locale 不得写入 set/unset。两个 native object 必完全相等；effective 的唯一差异是 P3-owned `PSM_R09_B1_TTT_ENABLED`（recurrent=`"0"`，TTT=`"1"`）。

CPU fixtures：正例；每层 identity/digest drift；tuple/allowlist/native/ambient parent；未验证 D005 pair、added/removed/changed key、wrong backend/digest、两个 excluded key leak、P3 difference/third backend、locale ordering。每次 mutation 重算 outer identity。本设计请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_ENVIRONMENT_STATIC_TOOLS`；run/candidates/backends/authorities 仍需独立 Gate，禁止 preflight/staging/P5/GPU/训练。
