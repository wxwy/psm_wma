# Stage-1 v1.7 request-instance recovery design v2.1

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V21`。
**状态**：docs-only；本版不执行 pre-C、C、request-pair 写入或下游操作。

## 1. 覆盖范围

v2.1 只收口 V20 审核指出的 C-time freshness 原子性缺口，取代 V20 的第 4 节 C-time freshness 表述；V20 的 v1.8 authority 已消费、C995 `ContractV05`/C01--C15、唯一 opaque consumer、canonical bytes、one-shot/no-retry 和 hard stop 均保持不变。

这不是字段或路径 Gate：同一个 future v0.5 pair 的全部 freshness inputs、唯一 guard ABI、C 调用序列和静态负例在本版一次性冻结。v0.3/v0.4 永久禁止，不能作为本版输入、输出、readback、cleanup 或 retry 对象。

## 2. Freshness 分类与 pre-C sealing

`rehearse_v05()` 仍是唯一可做 provenance/query/discovery 的 non-consuming phase。它除 C995 的 typed `ClosureV1` 外，只能注入一次不可复制、不可序列化的 host-owned `FreshnessGuardV1`：

```text
provider, module, path, blob_sha256, callable_qualname, abi,
guard_opaque_v1(sealed_lease, descriptor, expected_identities) -> FRESH | STALE | UNKNOWN
```

其固定 ABI 为 `psm.stage1.request-freshness-guard/v1`，transport 为 `opaque-sealed-freshness-guard/v1`。pre-C 验证其 provider/module/path/blob/callable/ABI/transport identity，并执行纯内存 no-call ABI probe；它不可由 PATH、dynamic import、tool name、shell、临时文件或任意 `ClosureV1` 替代。

pre-C 按以下类别封存 `FreshnessLeaseV1`，并将 guard object、lease object、descriptor 和 exact identity tuple 原样置入同一 `SealedPreCPlanV1`：

| 类别 | C-time 规则 |
| --- | --- |
| immutable ContractV05 P0/P1/ReplayBinding、six-key environment、canonical bytes、consumer identity | 不重观察；仅随 sealed identity tuple 传给 guard 比较。 |
| mutable local `.git`/config/local-V2 与 designated local absence/output absence | pre-C 由 host 建立 exact handle、predicate、path 和 identity 的 opaque lease；C 只让已验证 guard 对该 lease 做 `FRESH/STALE/UNKNOWN`，不接收路径或 Closure。 |
| remote V2 与 remote authority-ref queries | 仅 pre-C truth；C 不重发 remote query，也不把远端变化伪装为 local freshness。其 pre-C raw/argv/predicate identity 仍是 sealed plan 的一部分。 |
| post-write pair | pre-C 封存 pair paths 与 expected bytes；C 后只调用已验证的 sealed readback verifier，不产生/推断路径。 |

`FreshnessLeaseV1` 和 `FreshnessGuardV1` 均为 host opaque object：计划、调用者和 consumer 看不到可用于重建观测的 raw path/query/closure，也不能复制、pickle、替换或重新绑定。lease 的 comparison domain 必须逐项等于 C995 的 local mutable records；缺项或额外项均为 pre-C fail-close。

## 3. 唯一 C ABI 与原子序列

production contract 不再暴露 `consume_once_v05(plan, current_closure)`，因为任意外部 `ClosureV1` 没有 provenance。后续 CPU/static 实现唯一允许的签名是：

```text
consume_once_v05(plan: SealedPreCPlanV1) -> HARD_STOP_PENDING_INDEPENDENT_REVIEW
```

该函数不可接受 `ClosureV1`、raw path、query argv、callable name 或任何可重建 closure 的参数。C 固定为：

```text
1. guard_opaque_v1(plan.freshness_lease, plan.descriptor, plan.freshness_identities)
   == FRESH；STALE/UNKNOWN/exception 均在 consumer 前 terminal。
2. 一次 plan.capability.apply_opaque_v1(plan.descriptor, plan.patch_text)。
3. plan.post_write_verify(plan.json_raw, plan.markdown_raw, sealed_pair_paths) 的 byte-for-byte readback。
4. hard stop，等待 future v0.5 exact-pair independent review。
```

第 1 步是唯一被生命周期显式许可的 C-time operation；它是对 pre-C 建立的 opaque lease 的 host guard check，不是 remote/local discovery、字符串查找、路径推断、schema 补全、import、格式生成或外部 `ClosureV1` reconstruction。guard result 不是 freshness source；其唯一合法输入已由 pre-C sealing 冻结。任何 guard 结果或后续步骤失败都先消费 authority，禁止第二 call、repair、cleanup 或 retry。

## 4. 后续一次性 CPU/static 直接证据

在另行获 implementation authority 后，只修改已有纯内存 `stage1_v17_pre_c_rehearsal.py` 与其 unittest，并一次性证明：

1. `ContractV05` 必须携带 identity-verified guard；`rehearse_v05()` 产生不可复制/不可序列化 lease，且 capability/lease/domain drift 在 apply 前 fail-close。
2. `consume_once_v05(plan)` 没有 `current_closure` 或任何 reconstruction argument；静态签名检查拒绝旧 ABI。
3. fake guard 仅接收 sealed lease/descriptor/identity tuple；mutable-local drift 返回 `STALE` 且 `apply_opaque_v1` 调用数为零，`UNKNOWN`/exception 亦相同。
4. fake remote query 不在 C 调用；sealed remote raw 不会被 guard 输入替代为 query argv。
5. `FRESH` 时仍只调用 consumer 一次，readback byte mismatch 与所有 terminal outcomes 均不可 retry。

这些测试仍为标准库、纯内存；不调用真实 guard/consumer、Git/network/source/data/cache、child 或 CUDA。

## 5. 验收与边界

- C-time freshness 不再接受任意外部 `ClosureV1`，并能在 apply 前检测预封存 mutable-local drift；
- 固定/remote/pre-C-only/local/output/readback 的归类逐项明确，C 无 query/discovery；
- pre-C 覆盖 C 会用到的 capability、lease、bytes、paths、environment、identity 和 readback verifier；
- C 始终仅为 guard → one opaque write → exact readback → hard stop；
- 本版获三方设计批准后，才可申请一次上述 root CPU/static implementation authority；不直接授予真实 construction。

Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_FRESHNESS_GUARD_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

仍禁止：真实 pre-C/C、future request pair、materialization、source-evidence、真实 guard/consumer/Git/network/source/data/cache I/O、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。
