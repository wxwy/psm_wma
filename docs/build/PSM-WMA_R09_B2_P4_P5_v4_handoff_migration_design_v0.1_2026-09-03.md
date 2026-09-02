# R09-B2 P4/P5 v4 Handoff Migration 静态设计 v0.1

**状态**：draft。仅申请 root P4/P5 handoff grammar、loader/verifier 与 stdlib CPU fixture 的静态实现；不申请也不执行真实 request、P4 preflight、staging/materialize、candidate/run-root 创建、record/refreeze、P5 export/compose、torchrun、GPU/CUDA、模型/数据/checkpoint I/O、训练、评测、推理或 B2-T。

## 1. 前置、目标与唯一问题

前置 static closure：P4-v4 full request=`8535a8c`、P4 materialization=`bda9737`、P5 full-config=`49e6ccf`、P5 evidence Git authority=`3e3a853`、P4 planned-lock=`4108eb6`（ChatGPT review=`8169d9f`，Kimi/MM 同 SHA批准）；Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。这些 closure 不授权本迁移实现或任何真实执行。

当前 `tools/g0/export_r09_b2_p5_resolved_config.py:_validate_roster()` 的 v1 path set 强制包含 `preflight.json`。该文件包含 `result.json`/`verification.json` SHA；后二者又绑定 `pre_p5_run_root_roster.sha256`，形成 `preflight.json -> result/verification -> roster -> preflight.json` fixed point。P4 planned-lock 的 `_planned_projection()` 已冻结无此 pointer 的预执行 projection，但生产 P5 loader/verifier 仍采用 v1，故必须先完成本独立迁移。

本 Gate 的目标是将 P4→P5 handoff 的 readonly run-root grammar 唯一迁移为 **`r09_b2_p5_run_root_roster_v2`**，使 request 的 `p4_run.roster_sha256` 可在任何 P4 输出产生前由 payload manifest 与 run token 唯一确定。`v2` 是 grammar 名，不在已有嵌入式 roster object 新增版本字段；该 object 的 key-set 永远仍是 `{entries,sha256}`，避免静默扩大 P4/P5 payload schema。

## 2. 精确 v2 roster contract

对每个 backend，给定已验证 `run_token` 与 `payload_manifest={entries,sha256}`：

1. `entries` 必为按 `path` byte lexical ascending 的 array；每 row 精确为 `{path,type,mode,sha256}`。
2. exact path set 必为 `{import_staging, import_staging/<run_token>} ∪ {payload_manifest.entries[*].path}`；不得多、不得少。
3. 两目录 row 分别为 `{path:"import_staging",type:"directory",mode:"0555",sha256:""}` 与 `{path:"import_staging/<run_token>",type:"directory",mode:"0555",sha256:""}`。
4. 每个 manifest row 必映射为 `{path:<同一路径>,type:"regular",mode:"0444",sha256:<同一 SHA>}`；不接受路径、类型、mode 或 SHA 的 caller 选择。
5. `sha256=SHA256(P5 canonical_bytes({"entries":entries}))`。`request.p4_run.roster_sha256` 与 `result.pre_p5_run_root_roster.sha256` 必 exact-equal；后者的 `entries` 也必须 exact-equal request 的 v2 预期 projection。
6. `preflight.json`、`request.json`、`result.json`、`verification.json`、`candidate_link.json`、任何 evidence/pointer/额外 regular 或目录 row 均永久拒绝。run-root 实际递归 path 集必须与 roster path set exact-equal；目录 `0555`、regular `0444`、无 symlink、regular `st_nlink==1` 与 bytes SHA 约束保持。

该 grammar 只覆盖 P5 读取前的 run root。P4 request/result/verification 三份 payload 仍仅位于 `artifacts/g0/r09/b2/p4_execution_preflight_v4/<backend>/` 的 P5 evidence authority 固定路径；绝不写入 run root，也绝不成为 roster entry。

## 3. 允许的静态实现范围

获三方 `APPROVE_TO_IMPLEMENT_P4_P5_V4_HANDOFF_MIGRATION_STATIC_TOOLS` 后，唯一允许修改：

- `tools/g0/export_r09_b2_p5_resolved_config.py`：用 verifier-owned v2 derivation/validation 替换 v1 `preflight.json` 期望；`load_p4_v4_preflight()` 继续只消费 canonical 三 payload，并将 request/result roster equality 强化为完整 v2 projection equality。
- `tools/g0/r09_b2_p4_v4_execution_preflight.py`：仅复用或暴露已冻结的 pure planned projection，证明 P4 producer-side planned roster 与 P5 v2 derivation canonical-equal；不得填入 production lock authority、不得输出 final request。
- `tools/g0/r09_b2_p4_v4_static_contract.py`：只调整其对 final payload temporary validation 所复用的 v2 grammar；不得 materialize、publish或创建 candidate。
- `tools/g0/verify_r09_b2_p5_full_config_diff.py`：保持 `AUTHORIZED_P4_V4_EVIDENCE=None` 默认 fail-closed，继续精确绑定三 payload blob；仅更新对 v2 handoff 的静态验证/错误分流，不写 authority 常量。
- `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`、`tools/g0/test_r09_b2_p5_full_config_diff.py`：stdlib 临时目录/Git fixture。不得修改历史 evidence、artifacts、P5 export entry 或任何 Cosmos 子模块文件。

不得引入新依赖、CLI、child process、P5 export/compose 路径或 runtime 权限。`run_parent_export()` 的 hard-stop 必保持；`AUTHORIZED_P4_V4_EVIDENCE` 与 `AUTHORIZED_P4_V4_LOCK_SPEC` 必保持 `None`。

## 4. 静态验收与失败分流

CPU fixtures 必覆盖：

1. 对两个 backend，从相同 manifest/token 独立构造 P4 planned projection 与 P5 roster，字节及 SHA 相同；backend token 或 manifest SHA 漂移立即 FAIL。
2. 正例 fixture 不创建 `preflight.json`，P5 loader、P4 temporary final-payload validator 与 pair verifier static route 均可验证；生产 authority 未填时仍 fail-closed。
3. `preflight.json` 即使是 readonly regular、任何其他未列路径、遗漏 manifest path、额外目录、未排序 entries、类型/mode/SHA/token/staging-root/actual-tree/roster-SHA drift 均 FAIL。
4. request/result 的 `p4_run`/`p4_staging` 原有 exact-equality、P5 evidence三 payload Git/current-byte/Gitlink/clean-worktree authority、P3-only backend difference、loader lexical bootstrap 与 exporter hard-stop 不回归。
5. 断言不调用 `run_parent_export` 的后续代码、P5 child、Cosmos exporter、torch、torchrun或网络；临时 fixture 外无 run-root、candidate、staging或 artifacts 产生。

验证仅允许：对应 P4/P5 stdlib unittest、`python -m py_compile` 和 `git diff --check`。任何失败仅修静态 grammar/fixture；不得以创建真实 request、手工写 evidence、填充 authority、record/refreeze 或执行 preflight 规避。

## 5. 后续 Gate 与 verdict

本设计请求：`APPROVE_TO_IMPLEMENT_P4_P5_V4_HANDOFF_MIGRATION_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。实现完成后必须以新 implementation SHA 重新获得 ChatGPT、Kimi、MM 三方 closure。

即使该 static migration closure，仍必须先独立冻结并三方批准 exact final request 与 P4 record/refreeze；之后才能针对该 exact raw/SHA、精确命令、CPU资源、输出根和停止条件申请一次 `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY`。P5 export/compose、GPU 与 Local Memory/Libero4in1 训练继续是更后的独立 Gate。
