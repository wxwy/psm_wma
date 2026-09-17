# PSM-WMA Workspace Hygiene 方案 v0.1

- 状态：设计（回应 ChatGPT Gate 3 review HIGH-1，2026-09-17）。
- 目标：让 `git status` / formal diff / 自动 reviewer / 异常恢复可读，不再被 residue 淹没；**不删除任何来源不明的 residue**。

## 1. 问题

根仓工作区被三类 residue 污染（`git status --short` 数百项）：

1. **authority-root materialization worktree**：约 20 个 `.authority-root-materialization-*`（另有若干 `psm_wma_p*_*` worktree、`/tmp/psm_wma_p3_verify.*`），来自既往 Gate 的 materialization 流程；其中 `.authority-root-materialization-a1c4e80` 已被 git 标 `prunable`。
2. **runtime/evidence 产物**：`artifacts/g0/latent_cache_route_probe/rank_00/*.json`（上百个）、`artifacts/g0/resume_control/`、`resume_smoke/`、`active_soak45/`、`d8a_memcheck/`、`r09/authority_root_materialization_evidence_*.json`。
3. **临时/遗留文件**：`tmp_escape_link.json`、`tmp_escape_target.json`、`.authority-root.index`、`.local/`、`SESSION_HANDOFF_2026-09-16.md`、`outputs/`；子模块侧 `results/libero_closed_loop_*`、`examples/eval_*_4090.sh`、`uv.lock`（dirty）。

## 2. 原则与分类规则

不删除未知来源 residue。三类：

- **可安全 prune**：git 已标 `prunable` 的 worktree、明确一次性临时文件。
- **必须保留证据**：既往 Gate 的机器可读 evidence（JSON/checkpoint 侧产物），先归档到专用 evidence root 再决定。
- **用户遗留不可碰**：`.local/`、handoff 文档、`outputs/`、子模块 `results/`——默认不动，除非用户明确授权。

## 3. 方案（对应 GPT 4 点要求）

1. **materialization/worktree 默认落到项目外 scratch 根**：`/tmp/psm_wma_materialization/<id>`（或专用 scratch root），生命周期结束用 `git worktree remove` 自动 prune，不再 `rm -rf`。
2. **.gitignore 统一纳入 runtime/evidence 产物路径**：把上述未跟踪 residue 路径加入根仓 `.gitignore`（只影响忽略行为，不删文件）。
3. **只读 cleanup inventory**：`tools/g0/workspace_hygiene_inventory.json`，逐条标注 `prune-able / keep-evidence / user-owned-untouchable`。
4. **后续 Gate 不再在根目录生成 `.authority-root-materialization-*`**：materialization 输出路径改为 scratch root，见 §3.1。

## 4. 执行边界

- 本方案 v0.1 只冻结「分类规则 + .gitignore 忽略路径 + scratch root 策略」。
- `.gitignore` 更新是只读-safe（不改运行逻辑、不删文件）；实际 `git worktree remove` / 删除临时文件 / 归档 evidence 属**需用户确认**的操作，不在本方案内自动执行。
- 后续 materialization Gate 须在 runbook 中引用本方案的 scratch root 约定。

## 5. 初步 inventory（待确认，不在此删除）

| 路径 | 建议类别 | 处置 |
|---|---|---|
| `.authority-root-materialization-a1c4e80` | prune-able | `git worktree remove --force`（git 已标 prunable） |
| `.authority-root-materialization-*`（其余 19） | keep-evidence（暂） | 归档 `docs/collab/session_archive/` 或 evidence root 后按 Gate 决定 |
| `tmp_escape_link.json` / `tmp_escape_target.json` / `.authority-root.index` | prune-able | 删除（一次性临时） |
| `artifacts/g0/latent_cache_route_probe/`、`resume_control/`、`resume_smoke/` 等 | keep-evidence | 加入 .gitignore，保留磁盘 |
| `.local/`、`outputs/`、`SESSION_HANDOFF_*.md`、子模块 `results/` | user-owned | 不碰 |
