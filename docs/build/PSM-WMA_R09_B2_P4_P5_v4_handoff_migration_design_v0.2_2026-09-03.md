# R09-B2 P4/P5 v4 Handoff Migration 静态设计 v0.2

**状态**：draft，替代未获实现授权的 v0.1。仅申请 root P4/P5 handoff grammar、loader/verifier 与 stdlib CPU fixture 的静态实现；禁止真实 request、P4 preflight、staging/materialize、candidate/run-root 创建、record/refreeze、P5 export/compose、torchrun、GPU/CUDA、模型/数据/checkpoint I/O、训练、评测、推理与 B2-T。

## 1. 前置与整改范围

前置 static closure 保持：P4-v4 full request=`8535a8c`、P4 materialization=`bda9737`、P5 full-config=`49e6ccf`、P5 evidence Git authority=`3e3a853`、P4 planned-lock=`4108eb6`（ChatGPT=`8169d9f`，Kimi/MM 同 SHA批准）；Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。

v0.1=`4ce8ad3` 的 ChatGPT review=`8f21b78` 仅留下两项 HIGH：嵌套 payload path 没有 filesystem-closed directory rows；且错误要求 P4 `staging_projection` 与 P5 roster 的完整对象字节相同。本版只关闭这两项，不重开 P4 lock、P5 evidence authority、P3 binding、lexical loader 或 exporter hard-stop。

当前 P5 v1 将 `preflight.json` 计入 run-root roster，而该文件包含 result/verification SHA，后二者又绑定 roster SHA，故 `preflight.json -> result/verification -> roster -> preflight.json` 无法构造。v2 仍永久排除 `preflight.json` 及一切 P4 evidence/pointer；三份 P4 payload 仅位于 P5 evidence-authority 固定目录。

## 2. 唯一 v2 derivation

定义唯一 pure verifier-owned 函数：

```text
derive_v2_roster_entries(payload_manifest, run_token) -> entries
```

先以与已闭合 P4 `_validate_payload_manifest()` 完全相同的 grammar 验证 manifest：entries 非空且 path 唯一、byte-lexical sorted、非空相对 path、无 absolute/`.`/`..`/空 component/repeated separator、type 仅 `regular`、SHA 为 lowercase 64-hex。P5 不得保留较弱的平行 manifest grammar；实现必须复用同一 pure validator，或以逐项 parity fixture 证明相同接受语言。

对每一合法 regular path，derivation 不改变该 path，也不要求其为单层 filename。它收集每个 path 的全部非根 ancestor，并与必备 `import_staging`、`import_staging/<run_token>` 合并为 directory set；run root 本身永不成 row。若一个 regular path 与任一 required directory path 相同，或任一 regular path 是另一 regular path 的 strict ancestor，立即 FAIL，因其为 file/directory collision。重复 regular identity在 manifest validator中 FAIL。

保留 P4 已冻结的相对-path语言：本 Gate 不把 manifest 静默收窄为 flat 文件名，也不强制所有 payload 文件位于 `import_staging/<run_token>/` 下。为避免把 handoff payload 误作 P4 evidence/pointer，以下 run-root 保留 exact paths 永久拒绝：`preflight.json`、`request.json`、`result.json`、`verification.json`、`candidate_link.json`；`import_staging` 及其 token directory 仅可作为必备 directory rows，不可为 regular manifest row。其余合法嵌套 payload path（例如 `import_staging/<token>/pkg/sub/mod.py`）由 ancestor closure 完整表示。

输出 `entries` 按 path byte lexical ascending。每个 derived directory row 精确为 `{path,type:"directory",mode:"0555",sha256:""}`；每个 regular row 精确为 `{path,type:"regular",mode:"0444",sha256:<manifest row SHA>}`。令：

```text
d = SHA256(P5 canonical_bytes({"entries": entries}))
```

v2 embedded P5 roster 的唯一外形仍是 `{entries,sha256}`，其中 `sha256=d`；不得新增版本字段或 caller digest。

实际 pre-P5 run-root 的递归 path 集必须 exact-equal `entries.path` 集；每个目录 `0555`，每个 regular `0444`、非 symlink、`st_nlink==1` 且 bytes SHA 相等。额外/遗漏 path、type/mode/SHA、token、actual-tree、reserved path 或任何 collision 均 FAIL。

## 3. 跨 schema P4/P5 binding

P4 planned-lock 的已闭合 wire object 严格保持：

```text
staging_projection = {entries, projection_sha256}
```

`STAGING_PROJECTION_KEYS`、planned-commitment outer key-set、`projection_sha256` 字段名和已有 commitment identity 均不得改动。P5 embedded roster 同样严格保持 `{entries,sha256}`。两 complete canonical objects 不要求也不可能字节相同。

本 Gate 的唯一跨 schema 绑定为：对同一 verified manifest/token，调用同一 derivation 得到 `entries,d`；P4 `staging_projection.entries == entries` 且 `projection_sha256 == d`；P5 roster `entries == entries` 且 `sha256 == d`；P4 request `p4_run.roster_sha256 == d`，P4 result `pre_p5_run_root_roster == {entries,sha256:d}`。任何一侧以 caller-provided rows/digest 替代 derivation均 FAIL。

## 4. 允许实现、fixture与禁止项

经三方 `APPROVE_TO_IMPLEMENT_P4_P5_V4_HANDOFF_MIGRATION_STATIC_TOOLS` 后，唯一可改：

- `tools/g0/export_r09_b2_p5_resolved_config.py`：实现/复用 pure v2 manifest validator与`derive_v2_roster_entries`，以该结果校验 P5 roster、request/result binding 和 actual tree。
- `tools/g0/r09_b2_p4_v4_execution_preflight.py`：仅使既有 planned projection 调用同一 pure derivation或作 exact semantic parity；不得改 P4 staging-projection schema、填 lock authority或输出 final request。
- `tools/g0/r09_b2_p4_v4_static_contract.py`、`tools/g0/verify_r09_b2_p5_full_config_diff.py`：仅将 temporary final validation 与 static verifier接到同一 v2 semantic contract；`AUTHORIZED_P4_V4_LOCK_SPEC`、`AUTHORIZED_P4_V4_EVIDENCE` 继续为 `None`，`run_parent_export()` 继续在任何输出前 hard-stop。
- 对应 P4/P5 stdlib tests：新增深层 path、ancestor/collision/reserved/parity regressions；不得修改 artifacts、历史 evidence、P5 export entry 或 Cosmos 子模块。

永久 fixture：深层 `import_staging/<token>/pkg/sub/mod.py` 正例及所有 ancestor rows；regular/ancestor collision；reserved exact path；duplicate；`.`/`..`/repeated-separator/absolute/malformed-SHA；actual-tree extra/missing；P4 projection key-set和outer wire key-set不变；P4/P5 entries+digest semantic equal、但完整对象字段名不同；既有 evidence Git/current/Gitlink、P3-only difference、lexical loader/bootstrap、exporter hard-stop不回归。

验证仅允许定向 stdlib P4/P5 unittest、`python -m py_compile`、`git diff --check`。不得运行 P5 child、Cosmos exporter、torch、torchrun、网络或创建真实 run-root/candidate/staging/artifact。

## 5. Verdict 与后续门

本版请求 `APPROVE_TO_IMPLEMENT_P4_P5_V4_HANDOFF_MIGRATION_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。实现后必须以新 implementation SHA 重获三方 closure。

即使 closure，仍须独立冻结 exact final request 与 P4 record/refreeze，再针对 exact raw/SHA、单一 CPU命令、资源、输出和停止条件申请 `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY`。P5 export/compose、GPU 与 Local Memory/Libero4in1 训练仍为独立后续 Gate。
