# Stage-1 v1.7 ContractV05 完整需求矩阵 v1.0

**目的**：落实 2026-09-15 user convergence directive。此矩阵不新增执行 Gate；它将现有 v0.5/v1.7/V18/V21/V31 与三方已生效审查意见收敛为下一次 construction 前唯一的 pre-C 验收清单。

| ID | exact frozen expected | 来源/实现 | positive witness | foreign-self-consistent negative witness | 状态 |
|---|---|---|---|---|---|
| C01 | `P0_OBJECTS`三项与`P0_IDENTITIES`三项 literal tuple；`blob(raw)==blob_oid` | v1.0 §P0；`SourceObjectV1` | fixture exact P0 | `test_foreign_self_consistent_sources...` P0×3 | PASS |
| C02 | `P1_IDENTITIES`八项 ordered literal `(name,length,SHA)` | v1.0 §P1；`_validate_closure` | fixture exact P1 | 同测试 P1×8 | PASS |
| C03 | `P0_IDENTITIES[0]` base SHA、FD flag/value、`PARSER_ROWS`/`SOURCE_ROWS`、parser raw JSON items | v1.0 §binding；`ReplayBindingV1` | fixture exact binding | base SHA/items/rows drift | PASS |
| C04 | `DescriptorV1()`、`PATHS`双输出、`CANON`、`_expected_patch` | v3.1；`_validate_*` | canonical fixture | canonical witness 负例 | PASS |
| C05 | `ENV`精确六对 key/value | v3.1；`rehearse_v05` | fixture `ENV` | environment drift | PASS |
| C06 | sealed `RawFactV1` exact git/config/local-V2 bytes+length+SHA | v3.1；`ClosureV1` | fixture observation | sealed freshness git/config/local-V2 drift | PASS |
| C07 | `REMOTE_V2_ARGV`、`AUTHORITY_ARGV`、30/0、predicate及sealed raw identities | v3.1；`QueryFactV1` | fixture queries | query identity/freshness drift | PASS |
| C08 | `AUTHORITY_REF=refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`、`authority_absent`、`PATHS`与`DESIGNATED_ABSENCES` | V18/v3.1；absence validators | fixture exact absence targets | local+remote authority foreign target/raw；output/designated drift | PASS |
| C09 | `FROZEN_TARGETS`五项 literal cwd/index/evidence/json/md paths | V18/v3.1；`ClosureV1` | fixture targets | target/order drift | PASS |
| C10 | host capability exact provider/module/path/blob/callable/ABI/transport | V21/v3.1；`OpaquePatchCapabilityV1` | fixture capability | mutation/copy/pickle | PASS |
| C11 | verifier qualname与`ReadbackV1(json_raw,markdown_raw)` exact bytes | v3.1；`consume_once_v05` | APPLIED/readback | bad readback | PASS |
| C12 | one `_RetirementV1`、freshness equality before opaque apply | v3.1；`consume_once_v05` | exactly-once APPLIED | terminal/retry/freshness drift | PASS |
| C13 | sealed plan only；C无query/import/path/schema/bytes generation | directive §5；`consume_once_v05` | public API path | freshness rejects prior apply | PASS |
| C14 | in-memory `REPLAY_HELPER_GZIP_B64`=`5582/8f55dc32...d5e82`；无 source/Git/network/data/cache/consumer I/O | v3.1/ChatGPT 6c4；test fixture | fixture SHA assertion | frozen bytes raw mismatch rejected | PASS |
| C15 | 当前`ClosureV1`必须完全等于 sealed `ContractV05.closure` | directive §3--5；`consume_once_v05` | sealed plan | git/config/local-V2/query/P0/P1/binding/target drift | PASS |

## ContractV05 收口判据

`ContractV05` 必须成为 `rehearse_v05()` 的唯一输入；它把 C01--C11 所有输入与最终 JSON/Markdown/patch bytes 一起密封为不可复制的 `SealedPreCPlanV1`。`consume_once_v05()` 只能做 C12--C13 的固定四步，且不得补全任何矩阵字段。

本矩阵的 `PASS` 只代表当前纯内存 CPU/static 覆盖；它不授权 construction、C、materialization、source-evidence、GPU 或训练。下一次申请前，所有行必须重新运行并保持 PASS。
