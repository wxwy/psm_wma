# PSM-WMA V3 — M0 历史运行模式与 S0 前瞻性随机数值方案增量审核

**Date:** 2026-10-12
**唯一既定 Formal Implementation Pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` / Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Result:** `M0_HISTORICAL_DENSE_MODE_SUPPORTED`; **`S0_DESIGN_REQUEST_CHANGES`**; **`D1_PRESTEP_NOT_PASSED / C1_CLOSED / FORMAL30K_STOPPED`**.
**Evidence:** owner-relayed DS M0/S0 in `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_M0_S0/DS_PRO_2026-10-12_M0_S0_mode_and_stochastic_design_owner_relay.md` and immutable prior frozen D1 FAIL. No full code re-review because the current Formal Pair has not changed; only narrow historical and configuration identities independently verified.

## M0 — 历史 Dense/Reference 模式：有较强证据，接受模式判断但不接受“已可 Resume”

GitHub 直接确认：`71e03c8`（2026-10-09 14:57 UTC）的 `robocasa_exact_window_cached_sft.py` 输出 `torch.zeros(_COMPOSITE_SHAPE)`，尚无 `cached_pixel_geometry` 和 shared episode reader，旧 `local_memory_grouped.py` 没有异步预取；优化功能在 `d41be4f`（2026-10-10 08:54 UTC）才出现。结合 DS 报的 Oct09–Oct10 formal window，此时效果为 **Dense / Reference** 而非后来可选的 1/1；默认 env 值 1 和 digest 不应替代运行时源代码证据。接受本轮针对**模式识别**的主要结论。

**但存在不能合并的 SHA 身份：** 今天当前 Formal Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` 的 GitHub commit 创建于 **2026-10-10 11:32 UTC**，晚于 DS 报的原 Formal30k 训练结束 `2026-10-10 02:09 UTC`；它的 Gitlink 指向 `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` 而非历史 Child `71e03c8501c94a2ad5fed60955af657d3f945b85`。因此“原训练真正 root/child SHA”尚未完整见证，不能用今天 Formal Pair 假称 Oct09 已经运行的完全相同 Executable Pair。这不推翻 Dense 模式判断，却阻止把历史版本切换说成无须重新验收。

### 正式恢复路线的选择

**优先候选 B（当前已审核 Child `e9b8a41` + 显式 OFF/OFF + `--num-workers=0`）**：当前 C1 已实际严格恢复 iter800，D1 Reference 当前版本曾完整跑过 GA0/GA1 Forward/Backward，没有执行 optimizer step；可复用这些 Gate，当前 Formal Pair 不变。旧数据路径 dense，两个新 env flags 显式设为0，以避免默认1造成实际静默切换。注意旧 `dataloader.num_workers=4` 和新 raw prefetch `num_workers=0` 不是同一项；不要反向改写旧 config.yaml。不能由这项选择推出跨历史版本 Grad/Optimizer 数值逐位一致，也不能偷偷启用1/1。

**备选 A（回到历史 Child `71e03c8`）**：可追求更强历史字节一致性，但会与当前 root Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` 不一致，属于**新的执行/正式 Pair**；不得直接继承今日对 `e9b8a41` 的 C1 结论，也不允许 DS 自行 checkout/reset 当前工作树或降低 Gate。只有 B 出现真实 blocker 且独立授权 A 新 Pair 审核，才考虑。

**M0 Verdict:** `HISTORICAL_DENSE_MODE_SUPPORTED / RESUME_NOT_YET_AUTHORIZED`. Prefer B subject to narrow CPU-only original-run SHA/env/asset guard and specific same-job strict resume decision. **不要求先证明 OFF/ON 跨模式随机数值等价才能恢复保持 0/0 的正式训练**；但正式恢复仍须单独批准。

## S0 — 新随机数值一致性 Gate：REQUEST_CHANGES（设计层面）

**积极结果已接受：** 正确澄清4个运行而非v2同模式重复；完整映射 296 captured/314 selected（漏 action modality1 + generation bridge8 + local noncore9；w0重复计算4）；找到零/空 shard `grad==weight` 的 Comparator 证据口径缺陷。旧冻结 D1 8 Rank 数值 FAIL 保留，NCCL-only 假说仍未证实。

### S0-F1 — Frozen profile/digest 直接冲突（HIGH）

- **位置：** DS M0/S0报告 §5.3，`S0_2026-10-12.md:166–167`（报告正文）；实际代码 `cosmos_framework/examples/psm_wma_robocasa_corrected_phase5.py:205–231`，固定 Child `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`（路径以 `examples/` 为准）。
- **根因：** S0 将 `save_iter=500,warmup=100` 写成 shared frozen profile；本 Formal profile `save_iter=100,warmup=500`。实际 `config_digest()` 中 `schedule.warm_up_steps` 和 `schedule.save_iter` 都参与 SHA256。
- **违反合同：** same iter800 必须在同 digest/原优化器 scheduler 轴下恢复和测试，不允许为了 diagnostic 重写训练 schedule 后还声称 digest 不变。
- **验收：** 恢复冻结 T16/B8/GA2/K4/world8/max30000/**warmup500/save100**；每次 mode 必须在 PRE-GPU 复算与迭代800一致的完整 digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`，明确退出失败而不是绕过预检。

### S0-F2 — Wilcoxon 差异检验不能证明“等价”（HIGH）

- **位置：** DS §5.6–5.7（第184–194行），Wilcoxon `alpha=0.05` + median(cross/same)<=2 + any field>10×family p90。
- **根因：** 普通双侧差异显著性检验“不拒绝差异为0的零假设”不代表两模式在预期工程 margin 内等价；FQN/Rank 同属一组分布式训练而强相关，R=3每模式不能靠声称“effective N = family×rank”代替独立 launch 复制数。
- **违反合同：** 新 stochastic Gate 必须 prospectively 冻结 **真正的等价/非劣效检验目标** 和独立统计单位，不能对已观察FAIL引入事后无依据接受边界。
- **验收：** 明确若仅 3/模式则标为工程 smoke、绝不宣称统计等价；如果要求统计意义，设计事先非劣边界 + run-level CI/TOST/其它适合推断方案与足够 run 数/power；`≤2` 和 `10×` 的工程 margin 需要独立精度/训练敏感性来源而不是从先前 D1 噪声量级倒推。若没有来源报 `D1_S_DESIGN_BLOCKED` 而不是冻结可执行的 PASS。

### S0-F3 — 输入/参数覆盖及 Runtime身份对齐需要预先验收（MEDIUM）

- **位置：** DS §5.2、§5.5–5.6（第157–188行），旧 `no_step_harness.py` 的 SELECTED_MARKERS，缓存输入 0/0 vs 1/1。
- **根因：** 296 old Gradient fields 不代表314完整 selected；全场 `video` dense zeros 与 shape proxy 不应按序列化容器、storage_nbytes 或 stride 不同误报输入不一致；真实 logical semantic input and RNG/CFG/slot identities 才可比。
- **违反合同：** `same-data`、全 Optimizer allowlist 及真正跨模式输入身份预先确认；一些 Tensor 为空/零时 `grad==weight` 不得作为伪造梯度的充分证据。
- **验收：** 在 /tmp 外部 v3 验证真实 production allowlist的314 selected FQN 和每 rank 的 local shard，区分重复4 w0和真实缺梯度；按视频**逻辑值+geometry+latent+actions+text+mask** 做 canonical input fingerprint（同时独立记录 storage/stride 等效率指标）；`param.grad` 来源经实际对象路径而非与 weight 值是否相等证明；provenance 全记录。不要直接授权六次 GPU。

## 最终边界

**原 D1 冻结数值 Gate `REQUEST_CHANGES / D1_PRESTEP_NOT_PASSED` 永远保留。** M0 支持历史 Dense，不改变正式 Resume HOLD。当前不批准 S0 六次8×H100 GPU，不批准直接训练或版本回退。

**授权下一步：** 仅 `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_next_parallel_same_mode_resume_readiness_and_S0_design_rework_444c232b_e9b8a41.md` 的两个并行 CPU-only 小工作流：R0 同模式正式恢复的最后身份/命令 Guard；S1 S0 设计整改+v3仅CPU静态验收。不要再重复 C1/旧D1/Dataset/Index/VAE。一次报告后由 GPT 决定能否直接授权当前 e9b8a41 OFF/OFF 原 Job Resume；D1-S 可选独立推进，不能以它强行阻止已证实同模式的恢复。
