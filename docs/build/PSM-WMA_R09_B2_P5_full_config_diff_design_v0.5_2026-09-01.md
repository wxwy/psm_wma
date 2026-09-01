# R09-B2 P5 Full Resolved-Config Diff 静态设计 v0.5

**状态**：draft。v0.5 继承 v0.4 三根隔离合同，仅补充 P4 D005 v2 已冻结的绝对生产
worktree 身份，处理 review `2026-09-01_R09_B2_P5_v0.4_three_root_design_9814202_fc2124e.md`
的唯一 HIGH。

`production_root` 不是任意 tracked-clean `ddb4e0e` checkout。parent 必须从两份 verified P4
D005 的 `command.cwd` 各自推导 root（`Path(cwd).parent`），要求二者逐字相同，并要求
`production_root.resolve()` 精确等于该值；当前唯一允许值为 `/disk/rl/psm_wma_p4_d005_retry`。
禁止 symlink alias、relocation、cwd/PYTHONPATH/stream-manifest root 的 remap。

parent 还必须逐条检查所有 D005 应位于 production worktree 的绝对路径均在这个 exact root 下：
`command.cwd`、`environment.set.PYTHONPATH`、`PSM_R09_B2_STREAM_MANIFEST_ROOT` 与 stream-manifest
external asset。模型、数据、VAE 和 checkpoint 等外部资产仍只能匹配其 D005 冻结 absolute path，
不能借 production-root containment 放宽。

永久 CPU 负例：在不同绝对路径创建相同 `ddb4e0e`/Gitlink 的 clean checkout 必 FAIL。若未来要
relocate，必须新建 D005 schema/launch contract 并独立审核；P5 不重新解释已关闭的 P4 v2 pair。
v0.4 的 evidence_root/exporter_root、自包含 child、immutable staging、精确信封和独立 provenance
合同全部不变。当前仍不授权任何 compose/export/CUDA/GPU/训练。
