# Stage-1 v1.7 ContractV05 完整需求矩阵 v1.0

**目的**：落实 2026-09-15 user convergence directive。此矩阵不新增执行 Gate；它将现有 v0.5/v1.7/V18/V21/V31 与三方已生效审查意见收敛为下一次 construction 前唯一的 pre-C 验收清单。

| ID | 冻结事实 | 来源 | 实现位置 | 正向/foreign-self-consistent 负向验证 | 状态 |
|---|---|---|---|---|---|
| C01 | P0 三项 root/path/blob/raw length/SHA，raw blob OID 必须等于 frozen blob | v1.0 §P0、ChatGPT 6c4 | `P0_OBJECTS`/`P0_IDENTITIES`/`SourceObjectV1` | `test_foreign_self_consistent_sources...` P0×3 | PASS |
| C02 | P1 八项 ordered name/length/SHA | v1.0 §P1、ChatGPT/DS 1bf4 | `P1_IDENTITIES` | 同测试 P1×8 | PASS |
| C03 | ReplayBinding scalar、owner FD、parser argv items、8 parser rows、8 source rows | v1.0 §binding、DS 1bf4 | `ReplayBindingV1` | base SHA/items/rows drift | PASS |
| C04 | descriptor、v0.5 双输出路径、UTF-8 JSON/Markdown/patch inverse witness | v3.1 §rehearsal | `DescriptorV1`、`_validate_*` | canonical witness 负例 | PASS |
| C05 | six-key environment | v3.1 §rehearsal | `ENV` | environment drift | PASS |
| C06 | `.git`、config、local V2 raw observation identity | v3.1 §rehearsal、prior review | `RawFactV1`/`ClosureV1` | self-consistent drift 在 sealed freshness 前停止 | PASS |
| C07 | remote V2 与 fixed authority ref 的 argv/rc/stdout/stderr/advertised-V2 identity | v3.1 §rehearsal | `QueryFactV1` | 每个 query identity field drift | PASS |
| C08 | local/remote authority absence、双输出 absence、四个 designated absence | V18/v3.1 | `AuthorityAbsenceV1`/`AbsenceObservationV1` | absence 字段 drift | PASS |
| C09 | cwd/index/evidence/output targets | V18/v3.1 | `FROZEN_TARGETS` | target/order drift | PASS |
| C10 | consumer provider/module/path/blob/callable/ABI/transport，不可复制/序列化 | V21/v3.1 | `OpaquePatchCapabilityV1` | capability mutation/copy/pickle | PASS |
| C11 | post-write verifier identity 与 byte-for-byte readback | v3.1 §C | `ReadbackV1`/`consume_once_v05` | bad readback | PASS |
| C12 | exactly-once retirement；freshness 在唯一 consumer call 前 | v3.1 §C | `SealedPreCPlanV1`/`consume_once_v05` | terminal/retry matrix | PASS |
| C13 | C 内禁止 discovery、query、格式生成、schema repair | v3.1 §C、directive §5 | sealed plan only | public API exactly-once test | PASS |
| C14 | pre-C 测试不进行真实 consumer/Git/network/source/data/cache I/O | v3.1、ChatGPT 6c4 | test fixtures | frozen in-memory helper bytes identity | PASS |
| C15 | sealed observation 的每类外部身份在 C 前必须与 pre-C frozen truth 完全相等 | convergence directive §3--5 | `ContractV05`/`consume_once_v05` | git/config/local-V2/query/P0/P1/binding/target foreign drift | PASS |

## ContractV05 收口判据

`ContractV05` 必须成为 `rehearse_v05()` 的唯一输入；它把 C01--C11 所有输入与最终 JSON/Markdown/patch bytes 一起密封为不可复制的 `SealedPreCPlanV1`。`consume_once_v05()` 只能做 C12--C13 的固定四步，且不得补全任何矩阵字段。

本矩阵的 `PASS` 只代表当前纯内存 CPU/static 覆盖；它不授权 construction、C、materialization、source-evidence、GPU 或训练。下一次申请前，所有行必须重新运行并保持 PASS。
