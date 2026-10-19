# V3 G0 bounded_3step — GPU 执行 DS 报告独立 Evidence Intake Review

**日期：** 2026-10-19
**审核身份：** GPT — 独立 Code / Evidence / Gate 审核
**Verdict：`REQUEST_CHANGES`（G0 Evidence-only，**生产代码未判定存在缺陷**；正式 G0 closure 与 G1 Fresh100 release 仍 BLOCKED）**
**证据来源：** Owner 在会话中转交《DS_PRO V3 G0 bounded_3step — GPU 真实执行报告（2026-10-19）》；GitHub remote repo live read；未直接访问训练主机或诊断 DCP。
**本审核不重新打开已关闭的 F0/F1 CPU / S0 只读 Gate，不要求重跑 GPU G0。**

## 1. 精确 Git 身份核对

- DS 声称实际执行 Root `0d770dd03ef701d85e58751aa7f6df58dd1a8861`、Child/Gitlink `2d128ed5a07601cdd424974f99b67832eafeeb41`，G0 `v3_job_identity.json`、launch 均声称匹配。G0 `config_digest=61c69bbc265fed40bae2a8c41bd09c77cc8027a024f29611321b5cd8433ee326`，`semantic_digest=9ceaaf306d2c0b5edf0a348029741230864343dd68a433cef7bb77ddc49cd495`，目前仅来源于 DS 文本。
- 本轮 GitHub `refs/heads/V3` 读取为 `b268f1b8b0907f8717ab59f3525792daeed46133`（docs-only successor）；已独立核验的双父 F0/F1 promotion implementation Root `dd6e040ea8229fc3ce81259952444f82dd9897b2`；该远端树 Gitlink 仍是 `2d128ed5...`。
- 直接 GitHub REST `/commits/0d770dd03ef701d85e58751aa7f6df58dd1a8861` 返回 422 `No commit found for SHA`；Git Tree 同SHA请求失败，`compare dd6e040e...0d770dd0` 返回 404。**0d Root 当前无法在远端独立回读或审计 Diff**。该事实并不证明现场执行虚假，但不能把 G0 绑定为已核验 implementation pair。
- 训练主机 remote agent 离线；原始 `launch.json`、`v3_job_identity.json`、`config.yaml/pkl` 指纹、完整 rank logs、`complete.v1.json`/latest 指针未提供可核验内容。
- Child 2d128ed5 中 `examples/psm_wma_robocasa_corrected_phase5.py:670-705` 要求实际 Root HEAD / Child HEAD / Root Gitlink 均等于 expected；本轮仅能确认该校验在源码存在，不能独立证明 G0 当时的 Root Git object 内容。

## 2. DS 报告中暂可接受的事实与边界

- **DS_REPORTED_SUCCESS，尚非 GPT_VERIFIED_SUCCESS：** torchrun 8×H100、RC=0，iter1~3 outer 14.9908/15.0315/14.7833，action 1.2184/1.2351/1.2346，vision 0.2807/0.2680/0.2437；rank0 peak_reserved 28.59~29.26 GiB；`bounded_stop.completed_iteration=3`；G0独立 diag only `iter_000000003` F1 DCP、`complete=true` / world8 / 16.219s save 均是 DS 报告，尚未审读 raw。
- **Audit 计数口径解释，不是 bug：** `selected_by_group=action5+generation289+local20=314`，`present_grad_tensors_rank_local=314`、`missing_by_group=0` 在算术上相容。`generation_grad_tensor_count_rank_local=294` 可含 action 的5个重叠计数（`examples/psm_wma_robocasa_corrected_telemetry.py:263-280`）。`native_batch_layout=v2_a2_slot_major_packed_member` 是遥测标签（同文件:549），正式 Job 身份用 `v2_a2_member_packed_slot_major_v1`（Phase5:132），应核对原始身份，不因标签不同误判实现漂移。
- **审计语义：** 源码 `examples/psm_wma_robocasa_corrected_telemetry.py:314-378` `AUDIT_OK` 只检查 snapshot / iteration 和 rank0 count consistency；它**不自动拒绝** selected trainable grad=None，也不检查数值非零/Optimizer Moment/Local→Action 因果；即使 `AUDIT_OK` 和`missing=0` 全成立，也不授权宣称 Local Slow全rank更新、moment非零或因果已证实。合法FSDP空分片应基于 `local_numel` 分类。此为既有 S0 预定限制，不是本次新 production finding。
- G0 `--phase fresh --stop-after-iter 3 --audit-missing-grads` 与 Child Phase5:707-741 的 bounded/diagnostic contract 相符，正式 `--formal-execution-until 100` 必须独立 new namespace，不可复用 iter3 诊断 DCP。
- `Config.validate()` / 实际 DROID Fresh loading / native packed invocation / 完整F1 DCP发布均是本报告中的 **DS-reported** 结果，需直接 Evidence 验收才能关门。

## 3. 当前 Blockers（全为证据/身份，无已确认生产故障）

### G0-EVID-01 — HIGH | Root 来源无法独立追溯

- **定位：** `examples/psm_wma_robocasa_corrected_phase5.py:670-705`（Root/Child/Gitlink 守卫）；诊断产物 `v3_job_identity.json` 的 `root` 字段。
- **根因：** 现场报告所用 `0d770dd0...` 未在 GitHub Root repo 找到；无法检查 `dd6e040e..0d770dd0` 的实际变更属于 docs/bookkeeping 还是 production。
- **违反合同：** GPU Gate 必须绑定可回读的**精确 implementation Root/Child + 原始执行配置身份**；过去已批准版本不可直接继承到无法核验的新 Root。
- **可验收修复：** DS 只读回传 `git rev-parse HEAD` / `git cat-file -t` / `git show --no-patch` / `git merge-base` / `git diff --name-status dd6e040e..0d770dd0` / `git ls-tree HEAD cosmos-framework` / root+child clean/status 和 `launch.json`、`v3_job_identity.json`、`config_digest` 相互比对。若 0d 确是本地未发布 commit，先由 Owner 决定非覆盖方式提供完整 Git object/受控 evidence ref，再独立检查变更；严禁 force-push 或直接用 moving V3 HEAD 冒充当时的 SHA。若涉及生产代码变化，必须新 scoped formal review。

### G0-EVID-02 — HIGH | 缺乏可核验的全 Rank×Step 原始审计

- **定位：** `examples/psm_wma_robocasa_corrected_telemetry.py:314-378,620-646`；诊断 `rank*.log` / 8×3个 `[CorrectedV3][missing_grad_audit]` JSON events。
- **根因：** DS报告了“24条、AUDIT_OK、全部missing=0”，但实际仅有汇总，没有可核查的24份原始记录、事件唯一性、rank/iteration覆盖与错误数组。
- **违反合同：** G0 A 方案冻结的 8rank × iter1..3 存在性审计必须以真实 `contract → behavior → evidence` 证明；不能以汇总字段及 rank0 Loss 代替。
- **可验收修复：** 不重跑GPU。提交原始无改写24个审计JSON及来源日志、清单SHA256，证明 unique `(rank, iteration)` = `{0..7}×{1,2,3}`，逐条 `AUDIT_OK`、`audit_errors=[]`、`missing_grad_tensors_rank_local=0`、`missing_by_group={action:0,generation:0,local:0}`、selected/present一致，列出全部实际 `selected_by_group` 和合法 DTensor 空 shard 口径；附 rank0 原始train3 records，`nonfinite`、telemetry_errors 和 step/plan/norm evidence。仅按实际覆盖范围验收。

### G0-EVID-03 — MEDIUM | Checkpoint 及运行完整性仍为文本级声明

- **定位：** 诊断 `checkpoints/iter_000000003/complete.v1.json`、`checkpoints/latest_checkpoint.txt`、`v3_job_identity.json`、`launches/*/launch.json`。
- **根因：** 完整 F1 DCP 的 8-rank 文件/sidecars/metadata、原子完成标志、latest pointer、原始RC及盘占用未提供可核验的小型元数据。
- **违反合同：** G0 diagnostic-only、F1 `complete` 和 latest 的一致性以及无正式 Resume 权限都必须由 direct metadata/log witness 证明。
- **可验收修复：** 不读DCP tensor/shard body，提供 `complete.v1.json`、`latest_checkpoint.txt`、`v3_job_identity.json`、`launch.json`（脱敏）、`rank0.log` 中启动/Config.validate/commit/save/结束片段、保存时序、小体量 `stat/find` 8 rank shard/sidecar/metadata listing 和实时 `df`。确认 `diagnostic_only_do_not_resume=true`，孤立 G0 不迁移至 G1。

## 4. 精确裁决与 DS 下一动作

- **G0 runtime DS assessment：** `DS_REPORTED_RC0 / PLAUSIBLE_SUCCESS`，无日志说明发散或CUDA失败，不据3步 Loss变化推断训练收敛。
- **GPT formal G0 Evidence verdict：`REQUEST_CHANGES`** — 证据/identity-only，不声明训练失败，不要求重跑3步，F0/F1/S0 CLOSED 保持。
- **G0 完成后 G1 Fresh100：`BLOCKED`**。须修复 EVID-01/02/03，完成后针对原始证据做 evidence-only 复审；另外单独复核 `/mnt/data1` target FS/capacity 与 G1 的新 Root/Child/config digest、全新 Job Namespace；另取 Owner G1 GPU 单次授权。
- **当前不授权：** 新GPU/torchrun、G1、G2、Formal30k、Simulator/E1、诊断 DCP Resume、自动/手动清理 checkpoint、修改生产代码。实际 H100 事后被其他作业占用仅为 DS 当时报告，非实时判断。

**请求：** `docs/collab/chatgpt/requests/2026-10-19_DS_PRO_V3_G0_bounded3_identity_and_raw_evidence_CPU_only.md`
