# ChatGPT Review — R09-B0 post-closure provenance hygiene re-review

- Date: 2026-08-30
- Reviewer: ChatGPT
- Latest reviewed HEAD: `b5df815981c523cc4c78be23885e6036ea33a30d`
- Provenance-fix commit: `4204408375ec2493229eed114e4357d624bbfe5a`
- Current canonical artifact commit: `4e85ba81a0514e3f93098eccdd45a41f1d5d5ce3`
- Canonical artifact recorded clean root: `685ca9a78ca3421dc01d3cb7e8c440ef02615db7`
- Submodule/Gitlink: `ee1b78d532bad99ab29bcc1891c8e374eb960297`
- Verdict: **APPROVE_PROVENANCE_HYGIENE**

## Summary

上一轮 post-closure provenance blocker 已关闭。

当前 HEAD 上，canonical artifact 路径、TODO、SESSION 已统一采用 Option B：

- 唯一 current canonical artifact：commit `4e85ba8` 中的 `artifacts/g0/r09/b0_ttt_contract.json`
- artifact recorded clean root：`685ca9a`
- submodule/Gitlink：`ee1b78d`
- 历史 `f4ca0fc / a9b7443` 已明确降为 initial-generation provenance，不再称为 current canonical。

因此 fresh reviewer 现在可以从项目当前状态唯一解析 B0 closure evidence，不再存在双 canonical 口径。

R09-B0 技术 closure 继续保持有效，不需要重新打开或重新执行 CPU contract。

## Evidence

### Canonical anchor is now unique

`TODO.md:64` 明确：

- current canonical artifact = commit `4e85ba8`
- recorded clean root = `685ca9a`
- submodule/Gitlink = `ee1b78d`
- provenance refresh 不是新 Gate。

`SESSION.md:755` 同样明确：

- 唯一 canonical artifact 已提升到 `4e85ba8`
- `f4ca0fc/a9b7443` 仅为历史 initial-generation provenance
- 不再称 current canonical。

当前 `artifacts/g0/r09/b0_ttt_contract.json` 与上述文档一致：

- `root_revision=685ca9a...`
- `submodule_revision=gitlink_revision=ee1b78d...`
- `status=PASS`
- root/submodule clean=true
- all frozen B0 hard gates 保持 PASS。

因此上一轮 MEDIUM-1 已完全关闭。

## B1 ordering / separate finding

本轮历史中曾出现 `4aa52be` 的 B1 implementation-review request，但最新协作状态已经明确纠正顺序：

- `TODO.md:65`：`G0-R09-B1-RUNTIME-PREFLIGHT = BLOCKED`
- `SESSION.md:757`：B1 runtime preflight = BLOCKED
- `CODEX_INBOX.md:2360`：明确“本条不请求 B1 实现 verdict，也不会发送给 MM/Kimi”。

因此我**不把旧的 4aa52be 条目视为当前有效 B1 implementation request**，本 review 不给 `APPROVE_TO_IMPLEMENT_B1`。

不过 future B1 正式重提前，有一个文档一致性小项必须先修：

`docs/build/PSM-WMA_R09_B1_TTT_runtime_preflight_runbook_v0.1_2026-08-30.md:5`

仍写：

> canonical B0 artifact ... code provenance root=`a9b7443` ... review rerun artifact 在 `4e85ba8`

这已落后于刚批准的 Option B current-canonical 口径。未来重新发起 B1 review 前，应改为：

- current canonical artifact commit=`4e85ba8`
- recorded clean root=`685ca9a`
- submodule/Gitlink=`ee1b78d`
- `a9b7443/f4ca0fc` 仅作为 historical initial-generation provenance。

该问题**不阻塞 B0 provenance hygiene closure**，因为 B1 当前本来就是 BLOCKED；但它会阻塞未来 B1 preflight 的正式审批。

## Scope audit

本轮用于关闭 provenance blocker 的 `4204408` 只修改：

- `SESSION.md`
- `TODO.md`

没有修改：

- B0 backend
- CPU test
- verifier
- artifact
- production runtime/config
- GPU path。

后续 merge / Inbox request 也没有改变 B0 technical evidence。

## Verdict

**APPROVE_PROVENANCE_HYGIENE**

B0 post-closure provenance bookkeeping 可以关闭。

## Gate state

```text
R09-B0 technical CPU contract = CLOSED
R09-B0 post-closure provenance hygiene = APPROVED / may close
R09-B1 runtime preflight = BLOCKED
  - before future review: update runbook line 5 to current canonical provenance
B1 production wiring = NOT AUTHORIZED
GPU / A1-style smoke = BLOCKED
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
RoboTTT/shared-MoT import = BLOCKED
Global / Agent / RL = BLOCKED
```
