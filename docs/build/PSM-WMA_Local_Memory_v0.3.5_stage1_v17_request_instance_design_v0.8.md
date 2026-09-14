# Stage-1 v1.7 request-instance design v0.8

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`。
**状态**：docs-only v0.7 P0 object-path remediation；本文不构造 request，也不授予新的 construction authority。除本对象映射澄清外，v0.7 的 P0/P1/C 时序、唯一 C 消耗点、one-attempt/no-retry、禁止范围均保持不变。

## 1. 已证实的 P0 non-consuming 失败

v0.7 首次 P0 使用了错误路径：它把后续纯 helper
`tools/psm_wma/stage1_v17_launcher_replay.py` 当作 formal parent
`08d5828cdb4c12afa3b798ff01826c91ceb8755a` 内的 replay base。因此 Git object lookup 在进入 C 前失败：该路径在该 formal parent 不存在。

这只是 P0 frozen-object acquisition 的 read-only path-resolution failure：没有运行 P1、没有任何 freshness observation、没有 JSON/Markdown 输出、没有 materialization 或 child。依 v0.7，P0 failure 不进入 C，故不消耗其已批准的唯一 construction authority。

## 2. 规范化的对象角色与精确位置

P0 必须区分以下两个不同 Git object：

| 角色 | 允许的 Git object 来源 | 路径 / identity | 用途 |
|---|---|---|---|
| replay base source | formal parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a` | `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`; blob `af19a9eb66ecaf8bd0b92a48ab1867f105026658`; 18966 bytes; SHA-256 `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd` | 唯一可注入 `replay_outer_payload()` 的 `base_source` bytes。 |
| replay helper | implementation root `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f` | `tools/psm_wma/stage1_v17_launcher_replay.py`; blob `74455fce6ca90ede8d9935d893a7a74f5667c687`; SHA-256 `8f55dc32a77810d848c10ac55501754f741d42bd3ef3fbc386f0814b2a6d5e82` | 已关闭 CPU/static helper；仅以内存 bytes 重放前一行的 source。 |

`git ls-tree -r 08d5828cdb4c12afa3b798ff01826c91ceb8755a` 必须将第一行 path/blob 精确解析为上表，之后才可 `git show <parent>:<base-path>`。P0 不得从 ambient worktree 读取任一对象，也不得用 helper path 代替 base path。

P0 还必须从其各自冻结 formal trees 获取 outer payload 与 adapter source bytes，并对其 blob OID、raw length、SHA-256 执行既有 v0.7 binding。helper 的 source identity不是 base identity，二者不能互相代用；P0 result 必须逐项列出来源 commit、path、blob、length 与 SHA-256。

## 3. 保持的 P0/P1/C 互锁

```text
P0: exact Git-object acquisition + base/helper/outer/adapter identity verification
    └─ failure: stop, zero output, C not entered, authority unconsumed
P1: injected P0 bytes only -> pure project_request_closure
    └─ failure: stop, zero output, C not entered, authority unconsumed
C : begins immediately before first freshness observation
    └─ consumes the one authority; every later failure is no-retry
```

P0 的 allowed read-only source 仍限 future formal root/its frozen parent 的 Git object database；禁止 ambient worktree、source/checkpoint/manifest/data/cache、network、Git mutation、输出路径及任何 process/runtime action。P1 仍是内存纯函数。C 前不得写入 request pair，C 的成功后仍必须 hard-stop 并单独 exact-pair 三方审核。

## 4. 验收与请求

静态验收：

1. 上表 base path 可由 parent tree 的 blob `af19…` 唯一解析；helper path 只从 `50b0…` 解析；
2. v0.7 的 P0/P1/C 消耗语义与禁止范围未被修改；
3. v0.7 文档保持冻结，本版是明确版本化 override；
4. `git diff --check` PASS。

只有三方对本版 exact formal pair 给出
`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` 后，才可按 v0.7+v0.8 执行一次 P0；任何 P0/P1 failure 均按上述语义处理。Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
