# V3-PHASE6-ENCODE1-THRESHOLDED-VALIDATION — ds Evidence r3 / E 系列（authority finalizer）

- 日期/时间：2026-10-05 16:18–16:19 CST
- 角色：**ds（执行/取证 only）**。本 E 系列**只读**三个输入文件，**未**重跑 VAE/编码，**未**改 repo / cache / source / VAE / 任何已有 Evidence 文件，**未** commit / push。
- 目的：在不新增数值判据的前提下，对已有证据做一次**证据级 authority 终局核对**，把「pairlock 文本锚点」「probe 实际字节」「D1 判定字段」三者钉在一起。
- **最终结果：`FINALIZER_RC=0`，`status=PASS`，`33/33` 检查通过，`failures=[]`**

## 1. 输入边界（严格三文件）

`E0_authority_finalizer.py` **只允许读取**：

| 输入 | 路径 | sha256 |
|---|---|---|
| pairlock | `A1_pairlock.txt`（corrected） | `db2e52d2ead4281760caeaf08478045db8344d5a643833f45c55d34c3ec193fc` |
| probe 实际字节 | `B0_probe.py` | `a07e7fd1cbc96d855785708e0e9c6eccf7ec89240f0fae045ed9bbd34942a3fcb` |
| 阈值判定 | `D1_threshold_validation.json` | `7e0f8b0df7075309c1ea4c6af0582904c7ffbc4704ebc7c500311d68f74ad571` |

不读 `C0_observational.json`、不读 cache/source/VAE、不导入 probe、不重跑 VAE。

## 2. 硬编码期望（无任何 CLI 覆盖参数）

| 常量 | 值 |
|---|---|
| `EXPECTED_SCRATCH` | `8c3800565f66cfbce2929264f1c2a7854137482e` |
| `EXPECTED_PROBE_SHA256` | `a07e7fd1cbc96d855785708e0e9c6eccf7ec89240f0fae045ed9bbd34942a3fcb` |
| `EXPECTED_REVIEW_COMMIT` | `b6c42088ae41904c0667d1066983c2829ae61c36` |
| `EXPECTED_V3_HEAD` | `3f0d5e20a29922b40054c7d348eaba77675531f2` |
| `EXPECTED_CHILD_GITLINK` | `b673ceda5a9ff058abb31224b7006f2d87771ad2` |
| `KNOWN_STALE_SHA`（仅允许出现在 stale 标签行） | `89e62662adde2c0f1f8c0e3605e0f99007632659` |
| D1 契约 | `status=PASS` / `threshold=0.0` / `exact_required=true` / `checks_failed=0` |

**常量形状前置校验**：任何硬编码 SHA 的长度/字符集不符（`^[0-9a-f]{40}$` / `^[0-9a-f]{64}$`）时，脚本以 `FATAL_CONSTANT_SHAPE` 立即退出，不产生 PASS/FAIL 判定——防止把「常量笔误」误报成 Gate 失败。

## 3. 判定内容（33 项）

1. **pairlock 包含且一致**
   - 必需键存在且取值等于期望：`phase6a_scratch_target`、`threshold_freeze_review_commit`、`current_V3_bookkeeping_head`、`production_child_gitlink`、`probe_sha256`
   - 派生行（出现即须一致）：`scratch_HEAD`、`r3_B0_probe_sha256`、`r1_B0_probe_sha256`、`pinned_in_review`、`gitlink@origin/V3`、`gitlink@b6c42088`、`superseded_by`
   - stale 行只能承载 `KNOWN_STALE_SHA`
   - **anchor 行不得出现期望集合之外的任何 40-hex**（防止 pairlock 内部自相矛盾）
   - 5 个权威 token 必须字面出现（防空/截断文件通过）
2. **probe 实际 sha256** 与冻结值一致；且 pairlock 自报的 `r3_B0_probe_sha256` 与实际**互相一致**
3. **D1 字段**：`status=PASS`、`checks_failed=0`、`threshold=0.0`、`exact_required=true`；附加健全性 `checks_total>0`、`failures=[]`、`source_observational_sha256` 为合法 sha256、`exit_code_semantics` 存在

## 4. 结果

```json
{
  "schema": "robocasa_phase6_encode1_gate_validation_v1",
  "status": "PASS",
  "checks_total": 33,
  "checks_failed": 0,
  "failures": []
}
```

- `observed.probe.actual_sha256 = a07e7fd1cbc96d855785708e0e9c6eccf7ec89240f0fae045ed9bbd34942a3fcb`（与冻结值、pairlock 自报值三方一致）
- `observed.d1 = {status: PASS, threshold: 0.0, exact_required: true, checks_failed: 0, checks_total: 435, failures: [], source_observational_sha256: dce68c34b82167a00ded963268f491d5ae0a62e0ec44391280ec7c1aaaddad90}`
- 退出码 `0`（`0=PASS` / `1=FAIL`）

## 5. finalizer 自身一轮缺陷（非 Gate 判据失败，已留存原始证据）

| 轮 | rc | 失败项 | 原因 | 处置 |
|---|---|---|---|---|
| attempt1 | **1** | 6/33（`pairlock.key_value[probe_sha256]`、3 个 derived、`pairlock.contains`、`probe.actual_sha256_matches_frozen`） | ds 在 E0 中**硬编码的 `EXPECTED_PROBE_SHA256` 手打多一字符**（65 字符） | 用 `sha256sum` **实测值回填**该常量（不再手打），并新增常量形状前置校验；原始输出留存 `E0b_attempt1_finalizer_stdout.txt`、`E1_attempt1_gate_validation.json`（sha256 `a208da05…`） |
| attempt2 | **0** | — | — | 正式证据 `E1_gate_validation.json` |

attempt1 的 6 项失败**同源于一处常量笔误**，不是 pairlock/probe/D1 的真实不一致：失败详情里 `offending` 列出的正是**正确**值。根因与 Owner 先前指出的同一类问题（手打 64 位十六进制）。

## 6. 产物

| 文件 | sha256 |
|---|---|
| `E0_authority_finalizer.py`（attempt2 正式版） | `fe492501f546444e0d8a0a469b5fe857504d517d883527a17f91ac5f51391356` |
| `E1_gate_validation.json` | `af80778d7937e86abd867b4ca5a332da4644cf35bc934d5a8adb6a06eaf278ae` |
| `E1_attempt1_gate_validation.json`（留存） | `a208da05900d488b18a984d94beed4132b4b9553b6d327c6b4ebf38041588b2f` |

另：`E0a_finalizer_sha256.txt`、`E0b_finalizer_stdout.txt`、`E0b_attempt1_finalizer_stdout.txt`、`E0c_finalizer_stderr.txt`（空）、`E1a_attempt1_sha256.txt`、`E1b_sha256.txt`、`E_pre_baseline_sha256.txt`、`E2_summary.md`

## 7. 未修改证据（机械校验）

运行 finalizer 前记录基线，运行后 `sha256sum -c` 校验：**`A1_pairlock.txt`、`B0_probe.py`、`D1_threshold_validation.json`、`C0_observational.json`、`D0_threshold_validator.py` 全部 `OK`（BASELINE_UNCHANGED: ALL_MATCH）**。

- repo root：HEAD `3f0d5e20…` 不变，dirty 仅 4 个既有未跟踪 `.__dpc…`（非本次产生）
- scratch：HEAD `8c380056…` 不变，status **0 行**
- 本轮唯一新增写入为 `E0*` / `E1*` / `E2_summary.md`（均在 `/tmp` 证据目录内）
- **未**重跑 VAE、**未**执行任何编码/推理

## 8. 边界

本 E 系列**不**新增任何数值判据、**不**改变 D0/D1 结论，只做证据级 authority 终局核对；其 PASS 含义是「pairlock 文本锚点、probe 实际字节、D1 判定字段三者与硬编码 authority 一致」，**不**等于生产提升，**不**关闭 Phase3.5 production Gate，**不**构成任何后续 Gate 授权。

结果须回 GPT/Owner 裁定后再定下一步。