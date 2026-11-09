> **审核更正（2026-11-09）**：本文件所记 `REQUEST_CHANGES` 是当时把作者自设 `1.05×` Benchmark 阈值误作 Owner 必须达成的强制验收门槛所作结论，现已被新的限定范围 `APPROVE_CODE` 取代。原始性能门槛未达、Shell exit2 和数据仍真实保留。正式更正见 [同一 Formal Pair 的更正报告](2026-11-09_Issue31_Stage2_18be4a80_193627f4_PrefixPack_APPROVE_CODE_CorrectedGate.md)。本旧文保留为审核轨迹，不再作为当前结论。

# Issue #31 Stage 2 — Prefix-safe 输入打包复用：独立增量审核

**日期**：2026-11-09  
**Formal Root implementation**：`18be4a80a5ae4d97bc7d287034d24efab847c496`  
**Formal Child / Root Gitlink**：`193627f42f4cd1ba6d563aefb8fa8f9428ecb56d`  
**上一批准的 Stage 1 Pair**：Root `5b89f3eddbfe27ee72c173696a386e0b756d7866` / Child `4446be0f6dad9b6dc887ef90af52d0af754d4682`  
**当前 Root Draft PR**：[PR #33](https://github.com/wxwy/psm_wma/pull/33)；**Child Draft PR**：[PR #11](https://github.com/wxwy/cosmos-framework/pull/11)。PR33 HEAD `243f55fe…` 为后续 evidence/bookkeeping，不替代 Root Formal SHA。  
**正式 Gate Verdict：`REQUEST_CHANGES`** — Stage2 数值/代码增量无已确认的 production correctness blocker；**性能 Gate 未达到冻结阈值**，此 Gate 不得关闭。

## 1. 源码/Scope 独立审核

从固定 GitHub PR 及服务器干净 checkout 逐文件对比 Stage 1 → Stage 2，正式 Root Gitlink = Child `193627f4…` 一致。Child 相对前一 formal Child 只变更：
- `cosmos_framework/model/generator/omni_mot_model.py`（唯一变动的 production 函数 `generate_samples_from_batch`）；
- 新增 `mot/prefix_pack_template_test.py`；
- `mot/prefix_text_kv_memory_test.py` 的 Stage1 reference 测试显式选择 packOFF，不改变其先前计算断言。

`omni_mot_model.py:3998–4025` 在与 Stage1 一致的 Prefix-aware Text KV eligible B1/two_way/guidance1/no-postprocess/no-DP/CFG 条件下，启动本次请求专属 packed template；Prefix OFF/No-TTT 仍用原生既有模板条件。启用 `use_prefix_pack_templates=False` 回到 Stage1 Prefix-ON 缓存参考路径。原 `_update_inference_pack_template`、`_copy_timestep_to_template`、`_get_velocity` 无变更。Noise/timestep 每次更新，Prefix、条件 Mask、位置/动作等 metadata 原值保留。模板只存于一次 generate 调用栈中，失败或新请求不会复用上次模板；Stage1 text-KV 的请求清理仍保留。

此次**未发现**新 production 实现违反 Prefix / No-TTT / FailClosed 模式约束。此结论不推广到未测的 multi-B、分布式、真实 Sim。

## 2. CPU 与历史故障限定

作者正式定向测试：`201 passed, 1 deselected`，选定集 0 fail/error，`1487/1487` 文件指纹未变；三个既存 I001 import-order 例外保留。GPT直接读取原始 `raw/author02/gate.json` 和 `focused.log`，独立重跑**新 Child `prefix_pack_template_test.py`：14/14 PASS**，服务器 exact clean pair + CPU only，记录在独立审核目录。

原 `local_evidence_test.py::test_model_owned_all_continuation_never_initializes_w0` 已在 Stage1 审核中由 GPT 分别在旧/new Child 重跑出现同一失败，本次源码未修改该路径；保留为历史 baseline failure，未加入 201 PASS；不将其认定为本轮新回归，亦不宣称全仓 green。

## 3. H100 原始证据与独立重算

使用授权服务器 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue31_prefix_pack_20261109/gpu02/` 的原始测量与保存输出，没有外传敏感原始文件。GPT对 GitHub 公开的 hashes/bytes 索引与服务器文件逐一计算 **31/31 SHA256 完全匹配**。

- 固定同一 Local-TTT iter15000 DCP、固定合成视觉/历史/FastState/4×32 Prefix、B1、H16 raw15、guidance1、UniPC 30步；Baseline 与优化 **都启用 Stage1 text-KV**，唯一变化 packOFF / packON。变更不计 FW 更新。
- 原始 `measurements.jsonl` 正好60条、30对交错AB/BA，逐对结果均保留且 **30/30 优化更快**。输出 `audit/outputs_*.pt` 由 GPT直接 CPU `torch.load(weights_only=True)` 复核：优化前后 Vision和Action **逐元素 `torch.equal`，max_abs=0**，重复原请求也完全一致；改变 Prefix 时 raw15 Action `max_abs=1.9608675`，Vision `max_abs=0.6929022`，证明缓存没有消掉 Prefix 效果。
- 审核了28层×30步 audit：基线/优化均29次gen-only + 30次 PrefixContext/PrefixKV投影。Native pack总调用31→2（其中共享准备1，去噪过程30→1）。计时前 audit hooks 移除并重热身；源码身份、配置、源内 DCP 与 FW/PREFIX hashes 未变。

| H100 native-generation GPU events，30次/模式 | Stage1 packOFF | Stage2 packON | 审核结果 |
|---|---:|---:|---|
| P50 | 837.0812ms | 798.8678ms | **1.047834×，未达到1.05×** |
| P95 | 844.7195ms | 803.0262ms | 样本内改善 |
| Mean | 836.9260ms | 798.0850ms | 样本内改善 |
| P99（30次线性插值） | 846.2682ms | 805.8524ms | 样本内改善，非SLA |
| Max | 846.7140ms | 806.9632ms | 样本内改善 |
| 当前 VAE P50（已包含于生成） | 4.3394ms | 4.3290ms | 基本相同 |

独立复算P50/mean/P95/P99与作者一致；配对平均节省 **38.841ms**，每对最快至多约44.65ms。完整计时的 benchmark `status=CORRECTNESS_PASS_PERFORMANCE_NOT_MET`、`performance=NOT_MET`、**退出码2**，无过滤、无调低冻结阈值。Stage1旧 P99离群原因**仍未关闭**；此独立批次 P99看起来改善，并不等于已有尾延迟问题解决。

## 4. 当前唯一 Gate blocker

**Finding MEDIUM / PERFORMANCE-EVIDENCE-ONLY**

- **源码/判定位置**：Root `tools/v3/benchmark_local_ttt_prefix_kv.py:467–471`（冻结 P50 speedup`>=1.05`），相关生产变更在 Child `cosmos_framework/model/generator/omni_mot_model.py:3998–4025`。
- **根因**：Stage2 的打包复用有效减少了重复 pack（每请求从31到2次），但在同一冻结30步模型负载中**只获得1.047834×** 加速，没达到该独立性能 Gate 的下限；不能把“正确性PASS”或“所有30对都更快”当成达标。
- **违反的冻结合同**：本阶段 predeclared H100 model-only P50 performance `>=1.05×`；不能擅自降门槛或剔除样本/重复刷分。当前输出 `exit2` 是符合合同的失败行为，测试本身不是 Bug。
- **可验收条件**：如果继续推进这个性能 Gate，Codex须提交可归因的真实优化/诊断并给出**新的正式 Root/Child implementation pair**，继续执行同权重同输入固定Prefix/30步、缓存 ON 对比、AB/BA、所有样本保留、Action/Vision 等价、Prefix敏感和 tail 原始证据，实测 `P50 speedup>=1.05×`；或由 Owner 明确另行调整验收目标形成新独立合同（审核者不得自行改口径）。旧W0 failure 不作为此 blocker。**不建议为了跨线反复无代码重跑或调整统计。**

## 5. Formal verdict / 下一阶段

**`REQUEST_CHANGES`**：技术代码增量正确性无新的 confirmed blocker，**只有上述性能 Gate 未满足**。当前不合并 RootPR33 / ChildPR11，也不批准上游PR32/10/PR30/9/PR29/8 自动合入V3。NoTTT、真实Sim/Worker、900Episode、SR、多会话多Batch、尾延迟SLA及独立 Attention/Dense 改造均不在本次验收范围内。

若Owner认为这3.7–4.6%程度增益已足够业务用途，可以由Owner**明确调整**后续目标/路线；在冻结门槛未改之前，本 pair 的正式结论保持 REQUEST_CHANGES。

GPT 独立审核原始统计存于授权服务器 `.../_gpt_independent_gates_20261104/issue31_prefix_pack_review_20261109/`：包含独立 `independent_reduction.json`、CPU `reviewer_cpu_pack_test.log` 等。原始 GPU 张量/日志未外传。 
