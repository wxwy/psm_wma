# Stage-1 v1.7 request projection preflight design v0.3

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`。
**状态**：仅 docs-only v0.2 HIGH 整改；其余 v0.2 约束保持不变。

## Bootstrap argv / contract 精确预像

`parser_argv_items` 是已解析的完整 canonical parser JSON 字符串数组。helper 必须精确计算：

```python
bootstrap_argv_raw = json.dumps(
    ["--", *parser_argv_items],
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")
```

这不是`parser_argv.raw`。冻结 identities：

```text
parser argv:     2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333
bootstrap argv:  2341 / 85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d
contract:         182 / bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702
```

`bootstrap_contract.raw`必须恰为sorted-key/compact UTF-8 JSON：`{"bootstrap_argv_sha256": sha256(bootstrap_argv_raw), "bootstrap_raw_sha256": sha256(bootstrap.raw)}`。结果schema增加`bootstrap_argv: ProjectedBytes`，位于`parser_argv_items`之后、`bootstrap`之前。

CPU/static tests必须直接断言上述三条identity，并以漏`"--"`前缀、parser bytes代替bootstrap argv、重排parser items及bootstrap raw drift证明fail-close。保持无I/O、无request构造、无authority恢复，仍须三方重新批准后才可实现。

Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
