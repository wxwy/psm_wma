# ChatGPT Review — R09-B TTT B0 CPU contract closure second re-review

- Date: 2026-08-30
- Reviewer: ChatGPT
- Latest reviewed HEAD: `685ca9a78ca3421dc01d3cb7e8c440ef02615db7`
- Review request commit: `5578d22008a733ed609015858218e6b60d7f7317`
- Canonical artifact commit: `f4ca0fc61d0d24d090bba1eaea466b57f4a2b512`
- Verifier/code provenance root: `a9b74434e6badfc33e5e817a4390318843b29c3d`
- Submodule/Gitlink: `ee1b78d532bad99ab29bcc1891c8e374eb960297`
- Verdict: **APPROVE_TO_CLOSE_B0**

## Summary

上一轮 ChatGPT closure rereview 的 3 个剩余 blocker 已全部关闭。本轮没有发现新的 B0 CPU-contract blocker。

最新 HEAD `685ca9a` 仅追加一条 Inbox 顺序修正说明，不改变代码、artifact、Gitlink 或 Gate 证据，因此本 verdict 同时覆盖该最新 HEAD。

本批准仅关闭 **R09-B0 independent CPU contract**。它不授权 B1 production runtime wiring、GPU/A1-style smoke、多卡、长训、matched SR、backend freeze、RoboTTT/shared-MoT、Global/Agent/RL。

## Previous blockers

### CLOSED-1 — frozen five-member state schema now exact hard-gated

`tools/g0/verify_r09_b0_ttt_contract.py:21-27` 冻结了完整 expected composite schema：

- W: [32,256], bfloat16, 16,384 B
- pending_evidence: [4,256], bfloat16, 2,048 B
- last_evidence: [256], bfloat16, 512 B
- initialized: [], bool, 1 B
- segment_progress: [], int64, 8 B

实际 member 仍由 runtime tensor 派生，而不是人工回填。

`tools/g0/verify_r09_b0_ttt_contract.py:165` 写入 `schema_expected`、实际 `members` 和 `schema_pass = members == EXPECTED_STATE_MEMBERS`。

`tools/g0/verify_r09_b0_ttt_contract.py:174` 已把 `state.schema_pass` 纳入最终 PASS predicate。

Canonical artifact 中 `schema_pass=true`，实际五成员与 frozen schema 逐项一致；logical payload 仍为 **18,953 B/sample**。

### CLOSED-2 — canonical command hash now follows the established A0 command-hash contract

`tools/g0/verify_r09_b0_ttt_contract.py:171-173` 新增 `command.canonical_command_hash`。

我独立对照了 R09-A0 verifier：
`tools/g0/verify_r09_a0_contract.py` 对 `{cwd, python, argv, output}` 做 sorted-JSON SHA256。

B0 当前先构造 command 为 argv/cwd/python/output/tool_sha256，再在计算 hash 时排除 tool_sha256，得到的输入字段正好等价于 A0 的 command dict。因此“按 R09-A0 口径”成立。

Canonical artifact 已记录非空：
`canonical_command_hash=fbeb884e84b163995a207027693d7619b05a5bfccec9a982c6c8d0057b3574f9`。

### CLOSED-3 — partial reset now covers all done and non-done samples

Verifier:
- `tools/g0/verify_r09_b0_ttt_contract.py:116` 使用 `partial_done=[False,True,False]`
- `:138-141` 对 **全部 non-done samples** 逐成员 exact-preserve，同时对 **全部 done samples** 逐成员 zero。

Dedicated submodule test 同步加固：
- `cosmos_framework/model/generator/mot/local_evidence_test.py:164-167`
- 所有 `~done` sample exact preserved
- 所有 `done` sample zero

因此上一轮 partial-reset coverage 缺口已关闭。

## Reconfirmed B0 contract evidence

Canonical artifact `artifacts/g0/r09/b0_ttt_contract.json` 仍为 `PASS`，并记录：

- root revision = `a9b7443...`
- submodule revision = Gitlink = `ee1b78d...`
- root/submodule tracked-clean = true
- all eight candidate fields present
- exact five-member composite state schema PASS
- logical bytes = 18,953
- deterministic / finite / fast-state-updated PASS
- masked timestep / padding / all-mask PASS
- batch permutation / cross-sample isolation PASS
- partial/full reset PASS
- boundary isolation PASS
- graph detached / detach-value exact PASS
- no named parameters / optimizer exclusion / checkpoint exclusion PASS
- tail N=1,2,3,5,6,7 update-count = floor(N/4)
- N<4 zero-W / zero-token with present=true
- unaligned two-segment state max abs = 0
- unaligned two-segment token max abs = 0
- present exact
- tolerance = 0
- command provenance + canonical command hash + tool SHA

## Scope audit

Root implementation commit `a9b7443` changes only:

- SESSION.md
- TODO.md
- cosmos-framework Gitlink
- B0 verifier

Submodule `ee1b78d` changes only the dedicated `local_evidence_test.py` partial-reset assertions.

No `omni_mot_model.py`, production runtime/config, training entrypoint, GPU or multi-GPU path was modified.

Latest `685ca9a` changes only `docs/collab/chatgpt/CODEX_INBOX.md` to correct append ordering.

No scope creep found.

## Verdict

**APPROVE_TO_CLOSE_B0**

ChatGPT side has no remaining B0 CPU-contract blocker.

Project governance still requires the other independent reviewers, if that is the active three-party closure rule, before `TODO.md` should move this Gate to DONE or before any B1 authorization is inferred.

## Gate state after this review

```text
R09-B0 CPU contract = APPROVE_TO_CLOSE_B0 (ChatGPT)
B1 production runtime wiring = BLOCKED / requires separate authorization
GPU / A1-style smoke = BLOCKED
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
RoboTTT/shared-MoT import = BLOCKED
Global / Agent / RL = BLOCKED
```
