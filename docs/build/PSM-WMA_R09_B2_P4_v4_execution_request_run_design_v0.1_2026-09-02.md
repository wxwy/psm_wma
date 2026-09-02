# R09-B2 P4-v4 Execution Request `run` 静态合同 v0.1

**状态**：draft。本版只申请 root request parser/validator tooling 与 stdlib CPU fixtures；不申请真实 P4 preflight、目录创建、staging/materialize、candidate、record/refreeze、P5 export/compose、torchrun、GPU/CUDA、模型/数据/checkpoint I/O、训练/评测/推理或 B2-T。

## 1. 前置与边界

`entry`、`source`、`interpreter`、`environment` 与 `authorities` static section 已分别关闭。`run` 只冻结未来一次 preflight 的计划身份；它不是已经创建的 run root，不能提前生成 roster、staging tree、candidate 或任何 P5 evidence。最终 P5 v0.8/v0.9 handoff 已固定读取 `p4_run={identity,run_token,roster_sha256}`；本版不得改变该已冻结 key set。

未来真实 preflight 仍须独立三方 `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY` 和用户执行授权；本静态批准绝不替代该 Gate。

## 2. 精确语法

request 的 `run` 精确为：

```text
{
  "identity": {
    "root": "<absolute lexical future run root>",
    "resolved_root": "<same absolute lexical future run root>",
    "kind": "run_root",
    "identity_sha256": "<canonical SHA256 of the first three keys>"
  },
  "run_token": "<64 lowercase hexadecimal characters>",
  "roster_sha256": "<64 lowercase hexadecimal placeholder>"
}
```

三层 key set 必须 exact，无额外、缺失或类型替代。`identity_sha256` 使用既有 `canonical_sha256()` 对删除自身字段后的对象独立重算；`run_token` 与 `roster_sha256` 都只允许 lowercase 64-hex。`root`/`resolved_root` 必为相同的 absolute normalized lexical path，禁绝空、`.`、`..`、相对、symlink alias 与不同 spelling。因为该 root 在真实 preflight 前必须不存在，本 static parser 不得用 `resolve(strict=True)` 将不存在误作格式失败，也不得创建它。

## 3. 静态交叉约束

给定已关闭的 `source.root`，future run root 必与 source root、source `cosmos-framework` 子模块及其任一祖先/后代路径非重叠；不得位于任何 Git trust root 内，也不得等于现有 staging/candidate/evidence/exporter path。该静态 section 只验证 request 已声明的路径关系和 lexical grammar；实际不存在性、首次 mkdir 消耗 identity、双 backend 原子候选、readonly roster、manifest、native closure 与最终 `roster_sha256` 一致性均归后续独立 execution/preflight Gate。

两 backend 的 `run_token`、run-root identity 与 roster SHA 必彼此不同；backend 与 P3 selector、environment 或 P5 payload 的跨绑定不属于本 section。

## 4. CPU 验收与禁止行为

若获准实现，仅可新增/修改 root `tools/g0/r09_b2_p4_v4_execution_preflight.py` 与其 stdlib tests。永久 CPU fixtures 至少覆盖正例，以及 run/schema/identity/path/token/roster digest drift、uppercase/non-hex/长度错误、source/submodule/trust-root overlap、backend token/root/roster reuse 和 ambient path/环境不影响结论。fixtures 使用临时目录和 mock；不得调用 project entry、subprocess、网络、torch、GPU 或创建真实 staging/candidate/run root。

本版请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_RUN_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
