# V3 Matched No-TTT — DS_PRO 独立 CPU Gate 正式 Evidence 验收

日期：2026-10-25（CST）。
**FORMAL EVIDENCE VERDICT：`APPROVE` — 只关闭精确 Formal Pair 的 DS_PRO independent synthetic/config CPU Gate。**
**不授权**真实资产 S0、模型加载、GPU/FSDP、训练、DCP Save→Resume、真实 Action Server、RoboCasa Evaluation、任何 G1 工作树与历史 checkpoint 修改。

## 1. 本次 Gate 与 Formal Pair

- **Formal Root:** `7c083215e9f39ed4b5b3ff64010e415ad62dfdf4`（parent `48d1eb7f21f26be459bf78259d9678a8118e27c1`）。
- **Formal Child/Gitlink:** `20b5fa639c405a515933da109529e3e2c04de88d`（parent `813a550dab5d6b5b5e3be90d38bb97527956b4dc`）。
- **上一 GPT 独立代码/作者 Evidence APPROVE：** `docs/collab/chatgpt/reviews/2026-10-25_V3_Matched_No_TTT_7c083215_20b5fa63_incremental_review.md`。Root/Child 未变，按审核规范**不重新审核设计/代码**，只验收本轮新的 DS 独立 CPU 执行 Evidence。
- **Codex 作者 Evidence commit** `0f70fe8a6a58761b2d5c9c369627b001c08656a5`，不是 implementation root。当前查询实际远端 `V3` HEAD `d6e16aba0113ef7ebe9d32ebfe2111050ce94f92`，其 Root Tree Gitlink 已是 `20b5fa639c405a515933da109529e3e2c04de88d`；`7c083215` → `V3` 的增量不涉及 `scripts/`、`tools/`、`configs/` 或 Child Gitlink。DS 报告称 V3 尚处于旧 Child `813a550d`、HEAD `1d3b4358`，此状态**与最新 GitHub V3 不符，属于过期分支观察，不是当次 detached formal pair 失配**。无需再重复将同一个 implementation 合并进 V3。

## 2. DS_PRO 独立验收报告（现场独立执行）

- DS 报告的 detached clean 根仓/子仓来源：`/mnt/data1/data_v2_0617/dspro_matched_no_ttt_20261025/root`，锁定上述精确 Root/Child/Gitlink；Root/Child均 clean，没有修改源代码或测试。
- DS 原始 Evidence 原位保存：`/mnt/data1/data_v2_0617/dspro_matched_no_ttt_20261025/run1_20261025_092447/`。
- 运行环境：Python3.13.11、pytest9.0.2、torch2.10.0+cu128，**CUDA_VISIBLE_DEVICES 为空，整个 Gate 仅 CPU**；`--noconftest -c /dev/null`、offline缓存及独立 PYTHONPATH，与冻结作者命令同测试清单。
- **DS 汇总：** 16组测试 **439 顶层 case 收集，434 PASS，5 SKIP，0 failed/error；42 successful subtests；21.15 s**（作者 final_after_c0 为434 PASS、5 SKIP、42 subtests、23.66s）。`439=434+5`，JUnit/收集口径不把 subtest 再当作顶层case，统计内部一致。
- **16模块 testcase 分布与冻结一致：** `28,19,35,61,28,19,27,31,14,16,27,70,26,7,11,20`，合计439；新增文件三组 28+19+35=**82**。DS 报告显式将82个 `--collect-only` node IDs逐一对应其独立JUnit：`missing=0`、`present-but-not-pass=0`、`skipped=0`；未凭总量掩盖新增跳过。
- **明确5项历史可选真实资产 SKIP，且与已核查作者 JUnit 相符：** `test_optional_real_strict_snapshot10_preflight`、`test_optional_strict_real_data_grouped_smoke`、`test_optional_real_data_debug_smoke`、`LocalEdgeAssetsTest.test_local_hf_and_dcp_metadata_contract`、`LocalEdgeAssetsTest.test_local_processor_without_hub_fallback`。这些是被保留的未执行真实资产 Gate，**不是PASS，更不能据此声称真实资产已经验证**。
- **Source / 静态见证：** 冻结 `source_sha256.json` 所列 24/24 files均匹配、无缺失；Ruff0.12.7 check/format9、`bash -n scripts/train_v3_matched_no_ttt.sh`、Root/Child `git diff --check` 全PASS；DS未改正式 launcher、model、存储或 Gitlink。
- **直接相关 contract→behavior→test Evidence：** 新 Trainer 未创建Local模块或调用TTT inner-loop/private prefix；测试覆盖相同 G1 `ExactWindow` Consumer顺序、完整/尾部样本加权、Generation toy gradients、raw15/state15/H16、No-TTT checkpoint frontier身份/错误中止、训练配置/隔离namespace、G1 default路径回归、off-mode server CLI profile；新增82个case全部执行。此前 GPT 已独立检查这些实际 frozen 源码/测试断言，DS此次独立执行报告与之对应。

## 3. 证据强度与局限

- GPT **确实独立获取**远端当前 Formal Root/Child/Gitlink、已完成 GPT 代码审核报告及作者冻结 JUnit/测试合同，并核对 DS 的精确 case数、模块数、Skip清单、代码哈希与测试范围一致。
- GPT **没有**进入 DS 主机重新运行测试，也**没有**实际读取 DS 服务器上此次 `junit.xml`/pytest stdout 等原始字节。本次 CPU Evidence closure 采用 **DS_PRO 独立现场执行者提供的详细验收报告 + 原位保留的可追溯原始 Evidence**；是对该 Gate 冻结验收责任与执行结果的接受，**不表示 GPT 对 DS 原始日志字节做过独立取证**。
- 不要求 DS 上传原始 Evidence：此前已按冻结 Owner 规范确认“将现场原始文件上传到 GPT/GitHub”不是额外硬前置。若未来原位 Evidence 与此报告相矛盾或丢失，应重开 Evidence Gate并对账。
- 作者 CPU 使用 torch CPU build，DS使用可支持CUDA的torch但可见GPU为空；此次仅 CPU 执行且结果相同，不把这个差异当作 GPU kernel 或FSDP验证。
- Root/Child Git commit的祖先关系及分支状态与该静态CPU Gate无冲突：Root formal SHA和Child exact Gitlink已冻结并现场校验，不依赖分支名承载技术 verdict。

## 4. Verdict / 后续 Gate

**`APPROVE` — DS_PRO Independent CPU Gate CLOSED，限新精确 Pair `7c083215e9f39ed4b5b3ff64010e415ad62dfdf4` / `20b5fa639c405a515933da109529e3e2c04de88d` 的 synthetic/config CPU 与静态证据。**
没有新的 Production Code blocker；无需重复代码审核、CPU重跑、再由Codex修改生产代码或上传报告到GitHub。

仍需单独 Gate，不得被当前批准混同：

1. **S0 Real-input Matched Parity（DS_PRO，只读独立验收，需Owner对应授权）**：固定同一 G1 参考，核对实际 `VerifiedIndex` receipt、Cache manifest/corpus/source-binding digest、官方DROID/Edge/VAE初始化、rank分片/slot/真实 Consumer trace、mask/native loss、Generation optimizer和scheduler一致性；拒绝 shape-only 假匹配、不同Real资产冒充；不得修改 G1。
2. **World8 CUDA/Real DCP Gate（Owner另授权）**：真实 Config.validate、模型装载/Generation梯度和无Local、DCP Fresh100→strict Resume101→500/F1，验证实际CUDA/FSDP/optimizer/scheduler/RNG/frontier连续性和数值有限。
3. **No-TTT off-mode RoboCasa Evaluation Gate（Owner另授权）**：G1同任务/split/场景随机源/horizon/num_steps/guidance/控制协议，Server及Client都off，独立output；不能将现有Required-TTT Queue直接用于No-TTT或复用/覆盖G1历史20 Episode。

此前生产 G1、iter12000和原历史20 Episode仍被保护，不得更新活动训练worktree、覆写checkpoint、自动启动训练、Server/GPU/仿真。
