# PSM-WMA V3 — R0 同模式正式恢复准备 + S1 随机数值设计整改：增量审核

**Date:** 2026-10-12
**Binding Formal Pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`, Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`（正式实现 SHA 未变）。
**Verdict by scope:**
- `R0_CPU_READINESS_PASS`：**同模式正式 Resume 的执行条件已充分界定，但 CPU --preflight 尚未执行**。
- `S1_REQUEST_CHANGES`：工程随机数值一致性设计未能形成有说服力的退化/噪声等价边界；全314参数组成解释有算术错误。
- 原冻结 `D1_PRESTEP_NOT_PASSED` 不变，`C1_RESTORE_PASS/C1_CLOSED` 不变。
- **Scoped execution authority:** `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_iter800_owner_manual_same_mode_resume_execution_authorization_444c232b_e9b8a41.md`，仅 owner 手动执行的原正式 Job Dense OFF/OFF Resume，前置 guard 全绿才可运行；本 Review 不声称当前已有 iter801 commit。

**Source:** user-relayed DS R0/S1 report `docs/collab/chatgpt/evidence/2026-10-12_V3_R0_S1/DS_PRO_2026-10-12_R0_S1_resume_candidate_owner_relay.md`. DS /tmp 原始结果未被 GPT 独立读取。GPT 直接检查了 current pinned Child `examples/psm_wma_robocasa_corrected_phase5.py::preflight/_resume_checkpoint/verify_root_child_lock/_execution_stop_iteration/main`, `cosmos_framework/trainer/__init__.py::train`、`examples/psm_wma_robocasa_formal_monitor.py::TelemetryJournal/read_train_records`、`examples/psm_wma_robocasa_corrected_telemetry.py::_gradient_group_names`，并核查历史 Child `71e03c8501c94a2ad5fed60955af657d3f945b85` 的 Dense zero-video 源行为。Formal code pair 未变，不重做一般技术审核。

## R0 closure: candidate is executable if live CPU preflight/owner guards pass

- 历史代码 `71e03c8501c94a2ad5fed60955af657d3f945b85` 只有 dense zeros，无 later compact/shared/prefetch；该路径认定成立。固定 Formal Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` 的 GitHub commit timestamp **2026-10-10 11:32 UTC** 晚于 reported original job 完成 **02:09 UTC**：原训练时 Root SHA 未获完整源证实，不能宣称历史/root字节同一。当前选择继续使用经 C1 和 D1 Reference GPU测过的 `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` + 显式0/0、raw prefetch0，避开历史版本更换 Gate；它是源码行为等价恢复，而不是 bytewise cross-version parity 证明。
- Original Job own `latest_checkpoint.txt` → iter800，five DCP components+8 sidecar。固定 `config_digest=70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`，`30000/500/100` schedule 和 action/Local profile。C1 已在物理独立 Shadow 进行 8-rank strict same-job full restore，D1 Reference在此当前 Child 8×H100完成了一整 GA Window pre-step；足以支持**原模式运行的受控恢复工程风险判断**，虽不能宣称 OFF/ON 梯度等价。
- **Checkpoint 时间线关键事实：** 原作业提交到**iter805**，但最后 DCP是**iter800**。恢复从800起，新的801–805为 checkpoint rollback replay，不是无缝从806继续；不得把历史 801–805 作为本次新提交模型状态。原历史 stdout/session 保留，建立新 attempt 日志；监控 `read_train_records()` 会在衍生视图中正确处理 iteration 回退而保留原 JSONL，不改写历史行。
- **R0 CPU preflight NOT RUN:** DS给出候选命令，但未实际执行。正式GPU的必要前置为：冻结 Root/Child/gitlink+Child clean、目标原 Job latest/五组件与 sidecar、真实0/0 + nw0、source/model/Index、`config_digest` 完整值、`report.checkpoint_load_path` 精确原 Job iter800、`execution_scope=full_formal`、`verified_index_hit=true`；任一失败 => BLOCKED **不能启动GPU**。需预先把正式输出 Job、rank日志、历史监控/原始Checkpoint manifest 小文件证据保护好；C1 Shadow备份已存在。Resume的 `GroupedLocalMemoryTrainer.__init__` 会重写 **原 Job** config.yaml/pkl、后续 iter900+会写原正式checkpoint——只有在经过执行授权、owner确认时才允许。
- 实际 pinned `_execution_stop_iteration` 限制 `--stop-after-iter` **仅 fresh bounded diagnostic**，不能用它把 Original Resume限制到801；只能原生 full job恢复并以iter801监控、iter900保存的健康门控制，中途首异常/非有限/资源冲突 fail-stop。当前固定 scheduler 和 selected inventory不会因关闭0/0的Cache flags被直接改变。
- **梯度指标口径纠正：** 之前 Gate B 的314参数是互斥 generation289/action5/local20；Telemetry `_gradient_group_names` 把 action同时计入 generation，故报告中出现 overlapping generation294/action5/local20，其互斥总数仍314，不能把294+5+20错加成319。检查iter801必须核对实际指标 schema（并非每个“计数”字段都在非 audit 模式逐步存在）；无 NaN/Inf、missing=0、selected set、Local candidate正常才是硬健康边界，loss范围与LR等仅作历史参考。
- GPU现时 free 与 robotwin进程/owner分享许可 **未由本次报告锁定**；历史瞬时值不得冒充实时。指定用户手动执行，DS仅准备CPU guard和现场监控；不自动由DS启动 30k run，也不驱逐其他任务。

**R0 disposition: `R0_CPU_READINESS_PASS` within evidence scope.** Approval for original job production execution is separate and explicitly conditional on its live preflight/guard, not an unconditional auto-resume. This is a new scope, not automatic inheritance from C1 or a reinterpretation of old D1. Failure after launch requires first-error preservation and new explicit authorization; no self-retry.

## S1 decision: REQUEST_CHANGES (does not block same-mode Resume)

1. **HIGH — weak fallback margin/noise identification.** Report §2.4 proposes if ε=0 fails (the old independent launches already show nonbitwise gradients), compare cross-mode per-field difference to only two Dense repeats (e.g. cross_max≤self_max). A maximum from one same-mode pair is unstable and not an independently supported engineering non-inferiority bound. It lacks matched independent Optimized repeats and a prospective sufficient run protocol. “Input tensors logically same therefore Grad bitwise same” assumes deterministic FSDP/CUDA; code/path identity and exact seeds are necessary but not sufficient for bitwise distributed backward. **Acceptance:** Freeze a defensible reproducible engineering *smoke* test with independently justified numerical metric/margin and both-mode repeats, or explicitly mark non-deterministic-gradient equivalence unverified and do not launch additional GPU.
2. **MEDIUM — inventory reconciliation wrong.** Report §2.5 says `13 gen +1 action+9 local=23` and claims a difference of 5 due to 4 w0 duplicate. The correct unique FQN difference is **8 non-action generation bridges +1 action modality +9 local noncore =18**; w0 are among the existing11 core params and only duplicated in a separate additional display count, not in unique296. **Acceptance:** Actual FQN keyed complete314 set and disjoint category mapping, no marker-based capture omissions.
3. **MEDIUM — historical D1 decision misstatement.** Report §3.1 says “旧 D1 数值结论整体作废”，invalid because the **clean v2** eight-rank full-tensor frozen comparator FAIL survived prior N1/N2 review; **only v1 rank-overwrite data-dependent old comparison** invalid. No retrospective PASS/retraction of clean v2 FAIL. **Acceptance:** Preserve original D1 strict `FAIL` and simply label future D1-S as an optional independent design.
4. **LOW — logical fingerprint scope:** pre-forward canonical video all-zero hash need include other actual native text/actions/masks/latents/CFG/conditioning and rank/GA identity, not just known 6.68MB zeros; storage/stride is separate efficiency witness. No new model task needed now.

**S1 result `REQUEST_CHANGES` remains strictly optional for OFF/OFF original mode and does NOT gate separately authorized same-mode Resume.** No D1-S GPU authorized. C1 CLOSED / old D1 FAIL permanent.

## Operational scope

Full owner-controlled manual formal resume authorized **only via** `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_iter800_owner_manual_same_mode_resume_execution_authorization_444c232b_e9b8a41.md` and after *executed* CPU preflight + real sharing permit + immutable evidence snapshots pass; no assistant/DS auto execution. This Review plus canonical Inbox are evidence of Gate determination for fixed Formal Pair; no merge/code changes.
