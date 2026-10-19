# PSM-WMA V3 G0 bounded3 — DS CPU 补证增量 Evidence-only 复审

**审核日期：** 2026-10-19
**审核者：** GPT 独立 Code / Evidence / Gate Reviewer
**申请范围：** 只复审前轮 `G0-EVID-01/02/03`；无新 production 变更证据，无重新执行 G0，无重开 F0/F1/S0。
**Verdict：`REQUEST_CHANGES`（Evidence-only remaining blockers；G0 Gate 尚未正式 CLOSED，G1 Fresh100 GPU BLOCKED）**

## 0. 精确身份及已取得材料

- DS 本轮报表：`DS_PRO V3 G0 bounded3 — 精确源与 24 条 Rank×Iter 原始梯度证据（CPU-only 补证，2026-10-19）`。Owner 直接粘贴，完整约187行。其证据与五文件名称是 DS 主张、尚非 GPT 直接读取。
- As-executed Root `0d770dd03ef701d85e58751aa7f6df58dd1a8861`、Child/Gitlink `2d128ed5a07601cdd424974f99b67832eafeeb41`。原已核验两父 production merge Root `dd6e040ea8229fc3ce81259952444f82dd9897b2` / 同 Child。GPT 本轮从 GitHub 回读 `origin/V3` docs HEAD `904285837d39bf81b24c80e1eadee73caa908ea0`，`/commits/0d770dd0...` 仍 422 `No commit found`。
- DS 的 CPU-only 本地观察说明 0d 是 dd6e 后代，`git diff --name-status dd6e..0d` 仅 docs/ (M1+A9)，且本地 8 个未发布 docs commits、V3 主线另有 GPT docs HEAD；**这一解释与远端未找到 SHA 一致，但尚不能独立检查 0d Git object / diff 本身**。
- GitHub `V3` 上并不存在报告宣称的下列五个原始证据文件（逐个 GitHub contents 回读 404）：
  1. `docs/collab/chatgpt/evidence/g0_24_rank_iter_audit_raw.json`
  2. `docs/collab/chatgpt/evidence/DS_PRO_V3_G0_bounded3_evidence_2026-10-19.json`
  3. `docs/collab/chatgpt/evidence/robo15train_pane_history.txt`
  4. `docs/collab/chatgpt/evidence/extract_g0_24_audit.py`
  5. `docs/collab/chatgpt/evidence/assemble_g0_evidence.py`
- 训练主机 remote connector 离线，GPT 无法直接阅读本地 0d objects/原始 JSON/pane/小文件 manifest。报告表格中的 SHA256 为“见文件”，并未随本次粘贴携带原始哈希值。

## 1. 逐 blocker 增量结论

### EVID-01 — HIGH — Root provenance：解释合理，direct verification 尚未关闭

- **定位：** `examples/psm_wma_robocasa_corrected_phase5.py:670-705` 的 Root/Child/Gitlink 安全锁；DS报告 §A.1–A.6 的 as-executed `git` 证据。
- **Root cause：** 0d 的 Git objects 位于训练机本地，远端不可回读，DS摘要不能替代实树证据。DS报告称事后 Root 工作树有117个 untracked docs/artifacts，但尚缺运行时 `allowed_root_noncode_changes` 状态证据；不能把事后目录状态直接视为启动前通过证明。
- **Contract：** G0 必须绑定可核验的精确 implementation Root/Child 和 runtime Job Identity；已验收Child与 Root生产字节不可仅依据转述继承。
- **Acceptance：** 在不修改 V3 的独立证据分支/ref 或Git bundle交付完整 `0d...` Git objects及祖先，复核 `merge-base dd6e...0d`、`diff --name-status dd6e..0d`、全部 docs-only、`ls-tree cosmos-framework`、本地/远端身份，以及当次 `v3_job_identity.json`、launch root/child/digest、Job namespace、run时安全锁状态。如需将未发布 SHA 推远端，**先由 Owner 授权，禁止 force push/覆写 origin/V3**。若发现 production差异立即另开 scoped技术 Gate。

### EVID-02 — HIGH — 24 raw Rank×Iteration Audit：DS自证充分，direct raw 缺席

- **定位：** `examples/psm_wma_robocasa_corrected_telemetry.py:314-378,633-643`；报告声称的 `g0_24_rank_iter_audit_raw.json` 与 pane历史。
- **DS报告：** 24条 unique `{0..7}×{1,2,3}`；逐条 `AUDIT_OK`、`missing=0`、`present=314`、`selected=289+5+20`、空errors。Generation 294含Action5重叠（实际代码 `:263-279`）。这是**文本层补全**，无内部算术矛盾；不构成梯度实际非零/optimizer moment/Local→Action证据。
- **Root cause：** 原始 JSON/pane/提取脚本均未对审核方开放；无法核查 tmux 2432行历史的 JSON恢复方法是否遗漏、跨 run 混入或重复，尤其 DS指明历史2026-10-13 traceback与本次成功2026-10-19 run混存在同一pane。
- **Contract：** G0 已冻结 8 rank × 3 update 的真实行为证据，而非汇总文字。
- **Acceptance：** 同时提供脱敏原始 pane（或完整运行 stdout）、rank0原始日志、24 raw JSON、提取脚本及原始文件SHA256，抽样确认所有24条属于**本次04:01–04:07 G0 运行区间**，且 (rank, iter)唯一、逐条字段和训练rank0三步loss/grad/telemetry核对；对raw_decode行折叠处理做到可复现、不可默默丢弃格式错误事件。

### EVID-03 — MEDIUM — DCP publication：一致性陈述已齐，metadata raw 尚缺

- **定位：** G0 `checkpoints/iter_000000003/complete.v1.json`、`latest_checkpoint.txt`、`v3_job_identity.json`、`launch.json`、报告中 `partC_checkpoint_metadata.small_file_sha256_manifest`。
- **DS报告：** complete=true、world_size=8、iter=3、`psm_v3_sync_local_v1`、4个DCP组件.metadata/每组件8rank shard存在、8 dataloader sidecars SHA与complete一致、latest为iter3；输出树24GiB，data1剩余约314.05GiB，target FS T1–T5已成功。指标彼此兼容，但**仍属报告而非可复核原始数据**。
- **Contract：** 独立G0诊断DCP必须完整、原子发布、latest指向正确且 `diagnostic_only_do_not_resume=true`；禁止把iter3用于 G1/G2 resume。
- **Acceptance：** 提供脱敏的complete/latest/identity/launch、component metadata文件哈希与stat清单、sidecar对照和小文件哈希manifest、T1–T5/当前df结果、退出日志；**不读大 DCP shard body，不反序列化，不要求重跑GPU**。

## 2. 后续动作与最终边界

- **技术判断：** 没有发现新生产代码 blocker；上次三项 finding 的**解释/报告已完善**，但尚不能提升为正式 Verified/PASS，原因是原始文件仍只在训练机、本地 Git对象未被审阅。
- **Formal verdict：`REQUEST_CHANGES`**；这是 Evidence-only persistence，不触发新 technical review/新代码修改，不要求重跑 G0。
- **最小整改**：Owner授权发布隔离只读证据分支 `evidence/g0-bounded3-20261019`（推荐）或等效完整 Git bundle+小文件原文；仅保留原始Git链、脱敏小日志/JSON/script/manifest，无模型权重/DCP shard、凭据或敏感路径内容。V3 主线不移动。可由 DS 单次提交全部证据，减少轮询。
- **G0 Evidence Gate：OPEN；G1 Fresh100：BLOCKED**。G1必须另有Owner执行授权、全新Job namespace、实时候选OUTPUT_ROOT/容量、冻结其正式 Root/Child/config digest。不可用Moving V3 HEAD或G0 iter3做正式Resume。
- F0/F1/S0已关闭，不重审；旧B1 numeric FAIL不重跑。当前不授权任何额外 GPU、训练、真实Checkpoint读写或清理。

**DS最小交接指令：** `docs/collab/chatgpt/requests/2026-10-19_DS_PRO_V3_G0_minimal_evidence_publication_and_review_handoff.md`
