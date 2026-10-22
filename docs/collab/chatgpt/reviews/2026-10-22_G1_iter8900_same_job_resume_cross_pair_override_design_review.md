# PSM-WMA V3 — G1 iter8900→30k Same-job Resume 跨版本校验解除申请：设计 Gate

日期：2026-10-22
类型：**Owner 请求变更严格 Same-job Resume 身份合同的独立设计审核**；不是旧 Formal Pair 代码重审，也不是实际训练或生产资产操作授权。

## 0. 对象、证据级别与已锁定事实

**当前已从 GitHub 回读的公开远端**：Root `wxwy/psm_wma` V3 docs HEAD `a2252a378335af2e0ec90d6b0243ac04df5ea375`；最新此前已验实施 Root `ba91ebb7de2555cd1ff2a290d0af5ee43a8a3ee6`，Child/Gitlink `35b0ea1ccee9ee26653ed6589c484f0997d1c586`。注意 docs HEAD 不是 formal implementation。申报称**训练服务器本地** Root HEAD `8610ad88...`，GPT 暂无法在远端据此解析完整 40 位 Git SHA，亦未取得该本地 Commit 的 tree。二者不能混为一个已经核实的新 pair。

**G1 的源冻结身份来自 DS/Owner 提交的报告，尚非 GPT 从原训练机直接提取的文件**：
- Root `e0121d34592d10323ede480eb3409468a07371ba`；
- Child/Gitlink `2d128ed5a07601cdd424974f99b67832eafeeb41`；
- `v3_job_identity.json` Config/Semantic Digest 申报 `757de96f...` / `bd4e6d78...`，canonical config.yaml SHA256 `f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e`；
- SIGTERM 后 latest checkpoint `iter_000008900`（申报 complete=true，仍需证明训练恢复所需全部组件，不能只看 model shards）；
- 本地备份 ref `backup/V3-diverged-e0121d34` 据 DS 声称指向 Root `e012...`，但 GPT 未能访问目标机或读取该 ref。
**Github 公开 API 对 Root `e0121d34592d10323ede480eb3409468a07371ba` 的 Commit 和 Git Tree 返回 Not Found**；这不证明目标机本地 Commit 不存在或训练资产无效，仅说明不能凭 remote GitHub 完成这一段历史的来源闭合。

**已直接核对的生产代码**：固定旧 Child `2d128ed5...` 与新 Child `35b0ea1c...` 的 `examples/psm_wma_robocasa_corrected_phase5.py`，以及当前 Root `scripts/train_v3_packed128_staged.sh`（新版本 Shell 仅用于说明需要显式 EXPECTED_ROOT/CHILD；实际旧 launcher 必须取冻结旧 Root）。

## 1. Verdict：REQUEST_CHANGES — 不批准跨 pair 解除/重算/绕过 Same-job Resume 身份

**`REQUEST_CHANGES`** for the proposed design “drop Root HEAD strict comparison, accept new Child and recalculate/override semantic in the *old G1 same-job namespace*”.

不批准的精确范围：
- 不批准在 `verify_root_child_lock()` 中全局删掉 Root SHA 身份作为 G1 Same-job Resume 的解锁方式；
- 不批准将 G1 旧 `v3_job_identity.json` 的 Child SHA 或 Semantic Digest 通过临时 override、弱比较、重算覆盖到当前新 Child；
- 不批准在同一个原始 namespace 中对新/旧 Child 跨版本进行隐式模型/优化器/加载器身份迁移，同时继续宣称这是一条相同冻结合同的 G1；
- 不批准修改 G1 冻结 Config/Job Identity/Checkpoint 来压平来源差异。

**支持的安全替代**：保留 G1 严格一致性合同，使用目标机**本地存在且 SHA 已核实的原 Root `e012...` / 原 Child `2d128...`** 的隔离工作树进行旧 G1 Resume。当前 V3 主线保持新 Child 和 Config-truth/Queue 修复，不回滚，不动原主线。只有源身份、checkpoint training-state 与 CPU read-only preflight 全绿且 Owner 再次明确手动授权训练，才能真实启动 8×H100 torchrun。

## 2. 当前拟议方案的 blocker

### HIGH-RESUME-01 — 跨 Parent/Child 放宽身份会破坏不可变 G1 Same-job 来源约束

- **File/lines**（旧 Child `2d128ed5...`）：`examples/psm_wma_robocasa_corrected_phase5.py:158-205` `check_job_namespace()` 对 `record.root/child/semantic_digest/semantic`、canonical Config sha等 fail-closed；`:219-265` `training_identity()` 将源 SHA、模型/optimizer/scheduler/trainer、数据来源、随机性及 chunk/T 等纳入 identity；`:677-713` `verify_root_child_lock()` 把 `actual_root/child/gitlink` 与 expected 精确比较且检查 Child clean；`:855-884` preflight 计算 semantic，进入 all-rank agreement；`:292-360` JobLifecycle 仅保持 Frozen Namespace/Config/Identity 的 Same-job publication 语义。
- **Root cause**：申报者将“新旧 Root 某些训练代码的 diff 为空”当作可跨 Root/Child 恢复的充分条件。然而 new Child `35b0ea1c...` 的 `overlay_config` 会同步 legacy chunk32→16，并在 lifecycle 增加 live/YAML config-truth 校验和 launch provenance，实际不是同一个源实现。Root 当前本地 `8610ad88...` 和原冻结 `e012...` 不相同；仅删除一处 Root 校验不能解决 Child+semantic，继续删其他校验则掩盖了真实 source change。
- **违反 frozen contract**：`corrected_phase5_f0_v1` same-job Root/Child/Layout/semantic/canonical config strict identity；不得把跨源码 Pair Resume 伪装成 same-job exact restore。
- **可验收修复**：**不改这三处严格校验**；先在独立工作树找回 G1 原 `e012...` 的 Git 对象及其 Gitlink `2d128...`，检验旧 Child 工作树及 snapshot SHA、source/env identity，从 `iter_000008900` 执行旧 Pair CPU read-only `--preflight` 并形成 gate.json/日志；Owner 再单独批准真实 resume。若原源码确实不可恢复，应另开“实验 fork/migration”设计/实施 Gate，要求新独立 Job Namespace 和不可变来源映射、对 model/optimizer/scheduler/RNG/loader/TTT 更新规则的逐项兼容证明，而**非**旧 G1 身份覆写/弱校验。

### EVIDENCE-RESUME-02 — 当前归档证明不足以认定 full training checkpoint 可严格恢复（Read-only 前置，非代码缺陷）

- **File/lines**（旧 Child `2d128ed5...`）：`examples/psm_wma_robocasa_corrected_phase5.py:618-639` `_resume_checkpoint()` 必须检查 `model/optim/scheduler/trainer` **每个组件**的 `.metadata`，以及 `dataloader/rank_0..rank_7.pkl`。还校验 `latest_checkpoint.txt` 和不可接受的 symlink。真实 Same-job training Resume 与此前 **model-only inference** 不同：之前的“推理不需要 optim/”勘误不能推导出“训练恢复不需要 optim/”。
- **Root cause**：申报称 `complete=true` 和 model 8×DCP，但没有在本轮提交 `optim/scheduler/trainer/rank sidecars` 的精确训练态只读证据，也未提供完整 local SHA/tree/current worktree 证明。
- **证据 Gate 条件**：由 DS 读取实际 `latest_checkpoint.txt`→`iter_000008900`、无 symlinks，逐个 full training state metadata/rank sidecar nonempty、canonical config/identity 完整 sha、旧 source SHA/Gitlink和环境身份。不可修改/补造/清理现有 DCP。如原 checkpoint 缺任一必要组件，报 `BLOCKED`，不尝试只加载 model 来进行 Same-job Resume。
- 这是后续 read-only readiness checklist，当前**不能凭用户描述断定 checkpoint 损坏**，也不作为“必须修改优化器”的请求。

## 3. 建议 DS_PRO 下一轮（不用 GPU、不改代码、不动任何现存 Job）

第一阶段：**纯只读对象/文件核验**，不运行 torchrun、无 checkpoint 写入：
1. `git -C <original root repo> rev-parse backup/V3-diverged-e0121d34^{commit}` 应精确得到 `e0121d34592d10323ede480eb3409468a07371ba`；`git -C ... ls-tree <that sha> cosmos-framework` 应为 mode160000、Gitlink `2d128ed5...`。确认 Git child 本地仓库仍含该 commit（`git cat-file -e`），不通过网络下载改仓库。不接受仅比对 `0bffaa5b` 的训练目录差异作为身份替代。
2. 现有 G1 frozen job identity：解析 `v3_job_identity.json` 的 source Root/Child、semantic sha、自身 hash、canonical Config SHA / job namespace；比较源路径、T16/B8/GA2/K4、world8、30k/500/100及数据/index/cache/transform RNG等语义。不写回。
3. latest `iter_000008900` 的训练态 model/optim/scheduler/trainer metadata + 8个 dataloader Sidecar，逐一 read-only stat/hash/路径等，检查是否有同 Job 活跃 PID/独占 launch lease；SIGTERM 造成的 noncompleted step不宣称已提交。保留所有原始资产和报告。
4. **仅在源和文件前置全绿后**，可提出/准备旧 Pair **独立 clean detached worktree**：将 old Root `e012...` 和 Child `2d128...` 放入**新的路径**，保证旧训练 runner/python `PYTHONPATH` 从 old Child import，不覆盖当前 V3 mainline。不得 `git reset --hard`、force、clean 现运行仓库；禁止修改原 Job namespace 和原 config。先通过旧 Child 的 **read-only CPU `--preflight`**（打印 old same-job identity 和 checkpoint path），未通过先报结果，不碰 GPU。
5. `--preflight` PASS 后给 Owner 具体的旧 Pair、hash和恢复边界、实际后续会写新 launches/Checkpoints 的计划。**仍不启动 GPU**。Owner 单独批准后才允许从 checkpoint8900 恢复迭代9000 onward；`--formal-execution-until=30000` 和原 schedule30000/warmup500/save100 不变（如 Owner 另选 bounded formal stop，应符合 `_execution_stop_iteration` 原合同）。不得改变 Job Identity，也不得拿当前 V3 的推理/Config-truth改动启动旧训练。

## 4. 若 Owner 坚持“新代码继续训练”

那属于 **explicit new-job fork/migration** 而不是 strict Same-job Resume。应先设计并评估新独立 namespace 和不可变 provenance edge `old(root,child,config,step8900)→new(root,child,config)`、CPU/GPU parity、Optimizer/sharded state、dataloader resume cursor、TTT fast weight state、random generator and memory components、实际训练损失/梯度 continuity 证据；不允许在旧 G1 identity 上静默重算 digest，亦不允许通过跳过检验直接让新 job 写旧 checkpoint 目录。

## 5. 执行授权边界

**本 Gate Verdict `REQUEST_CHANGES` 只拒绝“当前新 Pair 放宽 Resume 身份”这项设计方案；不否定安全恢复 G1 的目标。** 不授权任何修改生产代码、解锁检查器、修改已存在的冻结 Job/Checkpoint，也不授权 GPU、torchrun、真实训练、回滚主线或停止其他实验。此轮审核代码依据旧 Child与新 Child当前公开版本，原 Root`e012...` 与本地 `8610ad88...` 原始 Git对象仍待 DS 只读提供，这些未知不能凭猜测填补。
