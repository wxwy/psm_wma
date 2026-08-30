# ChatGPT Review — R09-B0 closure bookkeeping / verifier rerun

- Date: 2026-08-30
- Reviewer: ChatGPT
- Latest reviewed HEAD: `4e85ba81a0514e3f93098eccdd45a41f1d5d5ce3`
- Parent closure-status commit: `f146bb761a83772d05f0927d4ce6371953992e5f`
- Prior approved canonical artifact commit: `f4ca0fc61d0d24d090bba1eaea466b57f4a2b512`
- Prior approved technical root: `a9b74434e6badfc33e5e817a4390318843b29c3d`
- Submodule/Gitlink: `ee1b78d532bad99ab29bcc1891c8e374eb960297`
- Verdict: **REQUEST_CHANGES — provenance hygiene only; B0 technical closure remains valid**

## Summary

这批提交没有引入新的 backend/runtime/GPU 技术变化：

- `f146bb7` 只将 R09-B0 状态回填为 DONE，并继续明确 B1/runtime/GPU 等未授权；
- `4e85ba8` 只重跑并覆盖 `artifacts/g0/r09/b0_ttt_contract.json`；
- rerun artifact 仍为 PASS，submodule/Gitlink 仍为 `ee1b78d`，所有 frozen B0 hard gates 仍保持通过；
- verifier/tool SHA 未变，技术实现未变。

因此，ChatGPT 上一轮 **APPROVE_TO_CLOSE_B0** 的技术结论不撤销，R09-B0 不需要重新打开。

但最新 HEAD 存在一个明确的 canonical-evidence provenance 不一致，需要清理后才能把这批 post-closure bookkeeping 视为完全收尾。

## Finding

### MEDIUM-1 — 当前 canonical artifact 路径已被 rerun 覆盖，但 TODO/SESSION 仍声明旧 artifact 是正式 canonical

`f146bb7` 明确写入：

- `SESSION.md`：正式 canonical artifact **仍为** commit=`f4ca0fc`，其证据 pair 为 root=`a9b7443` / submodule=`ee1b78d`；
- 同一段还说明 Kimi review rerun 的 working-tree artifact 是审查副产物，**未覆盖或提交**；
- `TODO.md` 的 DONE 行同样把 B0 canonical evidence 锚定到 root=`a9b7443` / submodule=`ee1b78d`。

但紧接着的 `4e85ba8` 又提交并覆盖了同一路径：

`artifacts/g0/r09/b0_ttt_contract.json`

当前 HEAD 中该文件已经变为：

- `root_revision=685ca9a...`
- `submodule_revision=gitlink_revision=ee1b78d...`
- argv 顺序变化；
- 对应新的 `canonical_command_hash=3e694e...`。

所以 HEAD 现在同时表达了两个互相冲突的口径：

1. 文档：正式 canonical 是 `f4ca0fc → root=a9b7443`；
2. 当前 canonical 路径内容：rerun evidence 是 `root=685ca9a`。

Git 历史当然仍能取回 `f4ca0fc` 的旧 artifact，但项目当前工作树中的 canonical path 已不再与 `TODO/SESSION` 的“正式 canonical”描述一致。这会让 fresh reviewer 不知道该以哪个 evidence pair 作为 frozen closure anchor。

这不是算法/contract failure，但属于 provenance hygiene blocker。

## Technical rerun status

我同时复核了 `4e85ba8` 当前 artifact。它本身仍满足 B0 frozen contract：

- status=PASS
- root/submodule tracked-clean=true
- Gitlink exact
- five-member schema exact PASS
- logical bytes=18,953
- tail N=1/2/3/5/6/7 PASS
- N<4 zero-W/zero-token + present=true
- mask/padding/all-mask PASS
- batch/cross-sample isolation PASS
- partial/full reset PASS
- boundary PASS
- detach / named-parameter / optimizer / checkpoint exclusion PASS
- unaligned split state/token diff=0
- present exact
- command/tool provenance present

因此，不存在理由撤销 B0 closure。

## Required fix

二选一，必须只保留一个明确口径：

### Option A — 保持原 closure artifact 为正式 canonical（推荐）

- 将当前 `artifacts/g0/r09/b0_ttt_contract.json` 恢复为 `f4ca0fc` 中已审核通过的 canonical 内容；
- 如果想保留 post-closure verifier rerun，将其另存为明确的非 canonical 路径，例如：
  `artifacts/g0/r09/b0_ttt_contract_postclosure_rerun.json`；
- 在 SESSION 中说明该 rerun 仅为 reviewer/post-closure sanity evidence，不替代 frozen closure anchor。

这样 `TODO/SESSION` 现有的 `a9b7443 / ee1b78d` canonical 口径无需改动。

### Option B — 正式提升 `4e85ba8` rerun 为新 canonical

若确实要让当前 rerun supersede 原 artifact，则：

- 更新 `TODO.md` 和 `SESSION.md`，明确新的 canonical evidence 是 committed artifact=`4e85ba8`，其 recorded clean root=`685ca9a` / submodule=`ee1b78d`；
- 删除/修正“正式 canonical 仍为 f4ca0fc”与“rerun 未覆盖或提交”的旧表述；
- 明确这是同一技术实现的 provenance refresh，不是新的 B0 implementation Gate。

本 review 已独立确认该 rerun hard gates 仍 PASS，因此若只做上述 provenance 口径同步，不要求重跑 B0 技术审查。

## Gate state

```text
R09-B0 technical CPU contract = CLOSED / remains valid
post-closure provenance bookkeeping = REQUEST_CHANGES
B1 production runtime wiring = BLOCKED / separate Gate required
GPU / A1-style smoke = BLOCKED
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
RoboTTT/shared-MoT import = BLOCKED
Global / Agent / RL = BLOCKED
```
