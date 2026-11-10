# Issue #31 — Prefix-aware Text KV Cache 独立增量审核（GPT）

- 审核日期：2026-11-09
- 正式 implementation Root：`5b89f3eddbfe27ee72c173696a386e0b756d7866`
- 正式 Child / Root Gitlink：`4446be0f6dad9b6dc887ef90af52d0af754d4682`
- 上一审核基线：Root `53b5273c7907e2d7a8fb1831ac0e0ec8b9fa973a` / Child `4cd5fc8c43d6793745dbc4cac51c59ee8a020dbe`
- Root Draft PR #32、Child Draft PR #10。后续 Codex evidence/Inbox/本审核记录 commit 均为非正式 bookkeeping，**不得替代以上 formal implementation pair**。
- **独立 verdict：`APPROVE_CODE`，仅限 Issue31 第一阶段 B1 / single-sample / two_way / guidance=1 的 Prefix-aware Text KV 代码及同权重 model-only GPU P50 Evidence。**
- **不批准**：P99/尾延迟改善、真实 Sim/Episode/SR、multi-B、线上 SLA、训练、V3 合并或第二阶段 Pack/Attention 优化。

## 1. Frozen contract 与增量范围

原始 frozen contract：<https://github.com/wxwy/psm_wma/issues/31>。审查对象是 Text-KV 复用，不是降低历史采样 K、关闭 Prefix、绕过 `validate_model_mode` 或修改原生生成动作合同。

独立读取精确 Git commit，核验 Root Gitlink 与 Child HEAD 完全相同。Root formal delta 限于 Gitlink、SESSION/TODO、模型内测试用 benchmark 与测试；Child 相对4cd5仅六个文件：`omni_mot_model.py`、`mot/inference_text_kv_memory.py`、`mot/attention.py`、`mot/unified_mot.py`、`mot/cosmos3_vfm_network.py` 和新增 `mot/prefix_text_kv_memory_test.py`。没有修改 Local Fast Weight/训练、VAE、仿真、Worker、EvalV2 Session/Resume、checkpoint mode 校验。

代码审查要点：

1. `omni_mot_model.py:4067+`：可选缓存仅在已有 Local Prefix、B1兼容、two_way、guidance=1、无 postprocess、无DP/CFG并行时开启；NoPrefix/NoTTT维持既有路径。Prefix下 pack-template 复用仍关闭。
2. `omni_mot_model.py:4150+`：现在 Prefix ON 即使不启用 pack-template，也可把当前请求独立的 `InferenceTextKVMemoryState` 传入生成；`finally` 释放部分填充缓存并恢复原 dispatch。请求结束不把 KV 缓存在 Model/Session 上。
3. `cosmos3_vfm_network.py:1574+`：只允许明确的 Prefix-aware、单样本、非 grad、two_way MemoryState 与 Local Prefix 并存，其它不受支持情形继续 fail-closed。
4. `unified_mot.py:1506+`：gen-only 后续步骤仍把**当前 Prefix**传给每层 Attention。非缓存路径保持原行为。
5. `inference_text_kv_memory.py`：首步从真实 native GEN K/V materialized buffer 提取 UND K/V；后续补齐真实 UND padding、构造 GEN-only 输出，并继续按每层 current Prefix K/V 调用原 two_way/varlen 注意力。非 prefix cache path 保留。
6. `attention.py:424+`：缓存首步捕获发生在 native GEN K/V materialization 之后，避免前一次候选在 Inductor BF16 rounding 边界造成的 Action/Vision 差异；不修改 Attention backend、精度和 compile limit。

**以上符合首阶段设计，不存在本轮已证实的新 production blocker。** 不把尚未启用的第二阶段 Pack/Dense 复用当成缺陷。

## 2. CPU / regression evidence

- 作者 exact Pair 定向测试：187 passed、1 deselected、0 failed/error/skipped within selected set；来源 `docs/collab/codex/evidence/2026-11-09_issue31_prefix_kv_native_precision/raw/author06/`，已检查 gate、focused log 与 frozen scope。作者证据不直接继承为独立通过。
- **GPT独立在服务器 exact `root5` / `child4446`、CUDA禁用，重新运行新增 `prefix_text_kv_memory_test.py`：25/25 PASS（14.61s）**。覆盖 FP32/BF16、native padding、30步 Prefix、编译 fullgraph 静态/动态、请求边界与失败复原、NoTTT/cold-start 分流。
- 作者排除的旧 `local_evidence_test.py::test_model_owned_all_continuation_never_initializes_w0`，GPT对旧 Child4cd5 和新Child4446 **分别独立复跑**，同在原测试328行触发 `AssertionError: all-continuation 不得读取 W0`，旧4.43s、新4.81s。属于**相同的 inherited baseline failure**，不能纳入187 PASS，也不是Issue31引入。建议另案跟踪，不能宣称全仓绿色。
- 3个 scoped Ruff I001 旧 import-order 例外有作者基线对照；其余 scoped静态/格式检查为作者 PASS。未独立跑全仓测试，因此 Gate范围限于指定代码增量。

## 3. H100 原始 Evidence 独立复核

正式原始文件位于授权服务器：
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue31_prefix_kv_20261109/gpu05/`。
非隐私派生索引：`docs/collab/codex/evidence/2026-11-09_issue31_prefix_kv_gpu_derived/`。**GPT直接读取服务器原始JSON/PT；没有外传原始文件。**

独立复核结论：

- Root5b89/Child4446/Gitlink精确匹配、两个仓库 clean；56/56 GPU原始文件的 SHA256、bytes 与公开 `gpu_statistics.json` 索引逐一匹配。
- 原始 `measurements.jsonl`：**30个AB/BA均衡配对、60次计时**；无舍弃异常。每次 Vision/Action `errors_from_baseline` max_abs 均为0。
- GPT直接 `torch.load(weights_only=True,map_location='cpu')` 比较真实保存的 Action/Vision 输出张量：baseline＝optimized **逐元素完全相同**；baseline＝repeated-original 也完全相同；换 Prefix 后 Action max_abs=**1.9608675**、Vision max_abs=**0.6929022**，因此 Prefix 确实作用于动作路径，不是缓存屏蔽。
- 独立读取28层 audit：旧每层30完整前向/30 Prefix 注入；新每层30步中1次填充+29次gen-only，且 **30/30步均保留 Prefix context / Prefix K/V投影**。Audit hooks 在计时前移除，基准有独立重热身。
- H100同一 Local iter15000 DCP，固定合成 Obs/历史/FastState/Prefix(4×32)，B1、30步UniPC、guidance1，计时排除 FW 更新；`current_frame_vae` 是包含于 native generation 的子计时，不可重复相加。

| GPU event generation，30次/模式 | 原 Prefix ON | Prefix-aware KV | GPT 复算 |
|---|---:|---:|---|
| P50 | 991.5513ms | **825.5335ms** | 减少16.7432%，1.2011× |
| P95 | 997.1945ms | **829.1916ms** | 改善 |
| Mean | 990.4186ms | **843.0906ms** | 改善 |
| P99（30样本插值） | 1000.0608ms | **1225.2732ms** | **退化，不能宣称尾延迟改善** |
| Max | 1001.1876ms | **1386.7728ms** | pair-2离群，原样保留 |
| 当前VAE P50（已包含） | 4.3396ms | 4.3489ms | 基本不变 |

30组中29组优化更快；唯一 pair-2 较原基线慢389.47ms。原始核验可复现以上全部数字。显存峰值 8.302GB allocated / 8.452GB reserved，作者记录未变化；profiler launch 数从53,706降至39,667（属单次 profiler 样本，不能当作30次统计）。

## 4. 风险与 Gate 限制

- **P99 降速原因尚不明**。30样本的 P99 不能作为严谨的尾延迟 SLA 估计；既不能据此宣布稳态尾延迟更好，也不能把单一离群当作已经定位的代码缺陷。后续若要发布生产，需要多种 Prefix/真实Obs/长时运行及尾延迟专门复验。
- 这次 **model-only合成输入**不是 RoboCasa 真机或 Sim 带证据 Session 的完整端到端评测，不包含网络/历史Worker/仿真、多样化任务输入或 SR。不能承诺 Episode 加速16.7%，更不能声称达到了 No-TTT 历史约608ms。
- 目前缓存复用优化保留 varlen 与每步打包，825ms距离历史 No-TTT 608ms 仍有差距。若需要进一步优化，另起**第二阶段 Prefix-safe pack reuse**的独立差异、数值等价与性能审核，勿混在本 Gate。
- 没有发现违反本 Issue 首阶段冻结范围的 formal blocker；前述旧 W0 失败和 P99 风险均须记录，**不阻止严格限定的 code / model-only P50 Gate**。

## 5. Formal verdict

**`APPROVE_CODE` — 仅 Issue #31 第一阶段 Prefix-aware Text KV 复用、B1/single-sample/two_way/guidance1、同一 Local checkpoint model-only 数值/性能 P50 验收。**

本 verdict **不批准** Root PR32/Child PR10 及上游 PR29/30/Child8/9 合入 V3，不批准 real EvalV2、训练、生产部署、多Server/多Sim/B2或后续 Pack/Attention 优化。正式 Root 是5b89，不是 PR review/evidence HEAD cab44 或任何后续文档 SHA。

本次独立服务端复算仅落盘在：`.../_gpt_independent_gates_20261104/issue31_prefix_kv_review_20261109/`，包含 `independent_reduction.json`、`reviewer_cpu_prefix_test.log`、`w0_old.log` 和 `w0_new.log`；源码未被修改。 
