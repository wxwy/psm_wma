# ChatGPT Review — PSM-WMA Current Build / Gate 3

- Date: 2026-09-17 CST
- Scope: project-level build health + current Gate 3 implementation review
- Formal root: `54aa90a03b60e05e00324b50e127926e7ba1f8cd`
- Formal child/Gitlink: `827c1cbda912de90d6d6a34696d40214dcae78b3`
- Reviewer: ChatGPT
- Verdict: **REQUEST_CHANGES_BEFORE_LONG_RUN**

## Executive conclusion

项目技术主线已经从“设计/静态合同堆叠”进入真正可训练状态：Gate 1 slot-rotation 已闭合，Gate 2 resume 已完成 save→kill→auto-resume 实证，Gate 3 catalog epoch-reuse 已落地并有成体系 CPU 测试。这是实质进展。

但我不建议当前直接进入 D8b / 5000-step 正式长跑。主要原因不是 Gate 3 核心逻辑明显错误，而是**工程治理和训练前验收仍有几个高价值缺口**，其中一项会直接影响可重复性和长期维护。

## HIGH-1 — 仓库工作区污染已影响审计可靠性

根仓当前存在大量 `.authority-root-materialization-*`、worktree、`artifacts/`、`outputs/`、临时 JSON、dirty submodule；`git status` 已被数百项 residue 淹没。当前还存在约 20 个 authority-root materialization worktree。

这会让后续 `git status`、formal diff、自动 reviewer、异常恢复时的“哪些是本 Gate 改动”越来越难可靠判断。即使 AGENTS.md 已规定 formal diff 不能依赖 dirty worktree，这种污染仍会持续放大人为误判和自动化成本。

**要求**：不要直接删除已有 residue；新增一个显式的 workspace hygiene 方案：
1. materialization/worktree 必须默认落到项目外独立 scratch 根目录，或生命周期结束自动 prune；
2. runtime/evidence 产物路径统一纳入 `.gitignore` 或专用 evidence root；
3. 建立只读 cleanup inventory，区分“可安全 prune / 必须保留证据 / 用户遗留不可碰”；
4. 后续 Gate 不再继续在根目录生成新的 `.authority-root-materialization-*`。

## HIGH-2 — Gate 3 需要一次 production-seed 的真实边界/恢复交叉验证

当前 Gate 3 单测覆盖很好，本次我独立执行相关五套测试：**73 passed**。实现中 production `queue_seed` 由 `sha256(manifest|config|source)[:16]` 派生，逻辑方向正确。

但现有主要容量探针历史上使用过固定 seed；而生产代码现在以 catalog-derived seed 为权威。正式长跑前至少补一份机器可读 evidence，使用**真实 production queue_seed**同时验证：

- 第 113 个 window 能越过旧 catalog exhaustion 边界；
- 至少一次 terminal-slot rollover 与至少一个 non-terminal-slot continuation；
- `_slot_epoch` 与重放后的 `_by_slot` 一致；
- save → kill → resume 跨越一次 epoch-reuse 边界后，首窗 identity 与不中断对照一致；
- `cumulative_valid_consumer_exposure` 单调且不归零。

这里不是要求再做大规模训练，只需要一个刻意跨 rollover boundary 的短 GPU/production-path witness。

## MEDIUM-1 — `SESSION.md` 已经失去“短期状态入口”的作用

`SESSION.md` 当前超过 11k 行，包含大量已经失效的历史轮询、旧 Gate 和被 supersede 的判断；而 `AGENTS.md` 明确写着它应“只保留最新事实”。当前事实源和历史审计日志实际上混在一起。

建议把 SESSION 改成真正的 rolling state：只保留当前目标、当前 Gate、最近有效 formal pair、dirty residue、正在运行的 process、下一步与 blockers。旧内容按日期移动到 `docs/collab/session_archive/` 或类似 archive。这样新 builder 接手时不需要先解析上万行历史。

## MEDIUM-2 — TODO 中存在大量 zombie / duplicate / stale Gate

`TODO.md` 同时存在旧 v0.3.2 路线、已被 v0.3.5 supersede 的 Gate、重复 ID（例如 writer implementation design 同名 IN_PROGRESS/DONE）、以及已经由后续路线实质覆盖但仍标记 IN_PROGRESS/REVIEW 的项目。

建议做一次**不改变技术语义的 task ledger normalization**：每个旧 Gate 标注 `SUPERSEDED_BY=<new gate>` 或关闭为 DONE/CANCELLED，而不是继续保持 IN_PROGRESS。当前真正应该阻塞正式训练的任务最好缩到 3–5 个。

## MEDIUM-3 — 测试入口需要收敛成 builder 可一键执行的 acceptance command

当前相关测试是分散的 pytest 文件、静态 probe、GPU smoke、artifact JSON。虽然证据很多，但没有一个“训练前最终验收入口”把它们串起来。

建议新增一个只读/验证型 acceptance 脚本，例如 `tools/g0/verify_active_local_memory_pretrain_gate.py`，统一检查：

1. Gate 1 slot coverage；
2. Gate 2 resume checkpoint/witness；
3. Gate 3 capacity/epoch-reuse；
4. production seed；
5. required artifacts freshness 与 formal child SHA；
6. 相关 CPU tests；
7. 输出单一 `PASS / FAIL / BLOCKED` JSON。

这样未来 builder 不需要从 SESSION.md 猜“到底哪些证据才算训练 ready”。

## Gate 3 code observations

本次复核未发现足以推翻 Gate 3 核心实现方向的代码错误：

- `_maybe_rollover()` 在 window boundary 判断剩余容量；
- `_rollover_slot()` 区分 terminal reuse 与 non-terminal continuation；
- `_reordered_by_slot()` 使用 category-level permutation，并保留 string episode ordering；
- `slot_epoch` 已进入 checkpoint state；
- load 路径继续保持 two-phase stage/validate → apply；
- terminal slot 的 sidecar carry 有显式 discard；
- production `queue_seed` 已由 catalog identity 派生。

我独立运行：
`pytest active_local_memory_driver_test.py active_local_memory_launch_test.py canonical_segment_runtime_test.py local_memory_segment_test.py local_memory_segment_adapter_test.py`
结果：**73 passed in 55.18s**。

因此当前 Gate 3 更接近“需要补 production-path closure evidence”，而不是“算法实现需要重写”。

## Recommended execution order for builder

1. 完成 Gate 3 当前 DS/MM/Kimi closure review；若有 REQUEST_CHANGES，先按 exact-pair 合并处理。
2. 补 production-seed + rollover-boundary + resume cross-boundary 的短 witness，并生成机器可读 JSON。
3. 把 Gate 1/2/3 与关键 artifact 汇总为一个 pretrain acceptance command。
4. acceptance PASS 后，再批准 D8b / 5000-step 正式训练。
5. workspace hygiene、SESSION/TODO 收敛可并行做，但不得删除未知来源 residue。

## Final verdict

**REQUEST_CHANGES_BEFORE_LONG_RUN**

- Gate 3 implementation 本身：**无重写级 blocker，方向可继续 closure**。
- 正式长跑：**暂不建议启动**，先补 production-seed + epoch-boundary resume witness 与统一 pretrain acceptance。
- 项目工程性：优先治理 workspace residue、SESSION 膨胀、TODO zombie Gate；这些不会改变算法，但会显著降低后续自动 builder 的错误率和接手成本。
