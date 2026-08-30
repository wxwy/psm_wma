# ChatGPT Review — R09-B TTT B0 CPU contract closure re-review

- Date: 2026-08-30
- Reviewer: ChatGPT
- Request HEAD: `21b48f174d28ce218b243bb16a8985bbc2a1c558`
- Closure artifact commit: `1e1f051f8e7df2688fae48faca82a0b73d412d3b`
- Verifier/code provenance root: `9186e55c9e27df7544cf93985e63576027c083f5`
- Submodule/Gitlink: `cc848c333941f373e7e86d37e3ff500f9329c209`
- Verdict: **REQUEST_CHANGES**

## Summary

本轮已经实质关闭上一轮 4 个 blocker 中的大部分内容：

1. `cc848c3...` 已可通过远端 GitHub API 独立解析；root Gitlink 与该 SHA 一致。
2. verifier/artifact 已补齐绝大多数 frozen CPU contract 字段与 hard checks。
3. `N_valid=1,2,3,5,6,7`、`floor(N/4)`、N<4 zero-W/zero-token + present=true 已进入 machine-readable evidence。
4. unaligned two-segment 的 **state/token/present** 已以 tolerance=0 做 exact gate。
5. state member shape 现在确实来自实际 tensor，而不是 caller 提供的常量。
6. root diff 仍未引入 production `omni_mot_model.py` / runtime/config/training/GPU wiring。

但 B0 仍不能 close，因为上一轮要求中的两个 machine-readable hard-contract 还没有真正闭合，另有一个 partial-reset gate 覆盖不完整。都属于 verifier/artifact 小修，不需要重做 backend 算法。

## Findings

### HIGH-1 — 实际 state shape/dtype 已“派生”，但没有与 frozen composite schema hard-assert

上一轮 MEDIUM-1 的 Required fix 是：

> derive `shape_per_sample` from the actual tensor, **compare it to the frozen expected schema, and hard-fail on mismatch**.

当前 verifier 在：

- `tools/g0/verify_r09_b0_ttt_contract.py:38-48`

确实从实际 tensor 生成：

- `shape_per_sample = list(value.shape[1:])`
- `dtype = ...`
- `bytes_per_sample = actual numel * element_size`

这是正确进展。

但之后：

- `tools/g0/verify_r09_b0_ttt_contract.py:153-160`

只是把这些实际值写入 artifact，并把最终 PASS hard-gate 在：

- total logical bytes == 18,953；
- segment exact；
- `checks.values()`。

没有任何 `state_schema_pass` / expected-members comparison。

这意味着下面这种错误仍可能被 artifact 标成 PASS：

- `W` 从 `[32,256] bfloat16` 变成另一个 **same-numel / same-byte** shape；
- 某 bf16 member 变成同字节宽度的 float16；
- composite member layout 发生变化，但总 bytes 仍为 18,953。

而 frozen source-audit 明确冻结：

- `W [32,256] bfloat16`
- `pending_evidence [4,256] bfloat16`
- `last_evidence [256] bfloat16`
- `initialized [] bool`
- `segment_progress [] int64`

见 `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.1_2026-08-30.md:52-56`。

**Required fix**

在 verifier 中定义 frozen expected member schema，并对实际 `members` 做逐成员 hard comparison：

- name
- `shape_per_sample`
- dtype
- `bytes_per_sample`

例如增加 machine-readable：

```text
state.schema_expected
state.schema_actual
state.schema_pass
```

并把 `state.schema_pass == true` 纳入最终 PASS predicate。

### MEDIUM-1 — frozen runbook 要求的 `canonical_command_hash` 仍缺失

上一轮 HIGH-2 已明确要求完整 command provenance：

- argv
- cwd
- python
- output
- **canonical-command-hash**
- tool SHA

frozen runbook 也明确写了：

`docs/build/PSM-WMA_R09_B_TTT_preflight_runbook_v0.2_2026-08-30.md:55`

```json
"command": {
  "argv": [],
  "cwd": "",
  "python": "",
  "output": "",
  "canonical_command_hash": "",
  "tool_sha256": ""
}
```

当前：

- `tools/g0/verify_r09_b0_ttt_contract.py:158`
- `artifacts/g0/r09/b0_ttt_contract.json`

只有：

- argv
- cwd
- python
- output
- tool_sha256

没有 `canonical_command_hash`。

因此上一轮 HIGH-2 中“完整 command provenance”仍未完全关闭。

**Required fix**

按 frozen runbook 的 canonical-command 规则生成并序列化 `canonical_command_hash`，并确保 canonical artifact 中存在该字段。若项目已有统一 canonical-command hash helper，应复用，不要另造不兼容口径。

### MEDIUM-2 — `partial_reset` hard gate 只证明一个未 reset sample 保持不变

当前 verifier：

`tools/g0/verify_r09_b0_ttt_contract.py:130`

对 done mask：

```text
[False, True, False]
```

只检查：

- sample 0 未改变；
- sample 1 被清零。

没有检查 sample 2 也保持原 state 不变。

submodule CPU test 同样只显式验证 sample 0 preserved + sample 1 reset。

实现本身 `reset_mask()` 使用逐 sample `torch.where`，从源码看是正确的；因此这不是 backend algorithm blocker，而是 machine-readable contract 覆盖仍有洞：如果未来实现错误地同时破坏另一个 non-done sample，当前 `partial_reset=true` 仍可能通过。

**Required fix**

对所有 `done=False` 样本逐成员 exact-preserve，对所有 `done=True` 样本逐成员 exact-zero/reinitialize。建议 verifier 与 dedicated CPU test 同时补齐。

## Previous blockers status

### Closed

- **旧 HIGH-1 / unpushed submodule**：CLOSED  
  `cc848c333941f373e7e86d37e3ff500f9329c209` 当前可远端解析；root Gitlink exact match。

- **旧 HIGH-3 / tail + split token exact**：CLOSED  
  artifact 记录 N=1/2/3/5/6/7；observed update count 与 `floor(N/4)` 一致；N<4 zero fast W / zero token + present=true；unaligned split state/token/present exact=0。

- **旧 HIGH-2 的绝大多数 schema/check coverage**：CLOSED  
  deterministic、mask/padding/all-mask、batch/cross-sample、reset/boundary、detach、optimizer/checkpoint、segment fields、root/sub/Gitlink provenance、8 candidate fields 均已出现。

### Still open

- **旧 MEDIUM-1**：只完成“derive actual shape”，未完成“compare to frozen schema + hard fail”。
- **旧 HIGH-2 command provenance 子项**：仍缺 `canonical_command_hash`。
- partial reset machine-readable coverage 不完整。

## Accepted evidence

当前 canonical artifact 的以下内容可以接受并保留：

- `root_revision=9186e55...`
- `submodule_revision=gitlink_revision=cc848c3...`
- tracked-clean root/submodule + Gitlink exact
- logical payload = **18,953 B/sample**
- all eight candidate fields present
- tail cases N=1/2/3/5/6/7
- segment state max abs = 0
- segment token max abs = 0
- segment present exact
- graph detached
- no backend named parameters
- empty backend state_dict
- no production runtime/config/GPU scope expansion

无需重做 TTT objective、SGD math、tail Option A 或 backend state design。

## Required re-review package

只需做一个小的 B0 verifier/test closure patch：

1. hard-gate actual composite state schema against frozen expected shape/dtype/bytes；
2. 补 `canonical_command_hash`；
3. partial reset 对全部 done / non-done samples 做 exact assertions；
4. 从新的 pushed-clean root/submodule pair 重新生成 canonical artifact；
5. 保持 B1/runtime/GPU 全部不动。

然后再次申请 `APPROVE_TO_CLOSE_B0`。

## Gate state

```text
R09-B0 CPU contract = REVIEW / REQUEST_CHANGES
B1 production runtime wiring = BLOCKED
GPU / A1-style smoke = BLOCKED
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
RoboTTT/shared-MoT import = BLOCKED
Global / Agent / RL = BLOCKED
```
