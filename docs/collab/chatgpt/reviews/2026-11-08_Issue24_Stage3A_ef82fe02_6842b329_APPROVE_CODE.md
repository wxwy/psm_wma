# Issue #24 / Issue #23 Stage3A — GPT 独立 CPU Code Gate

**正式审核结论：`APPROVE_CODE` — 仅限于新的 Stage3A B1/wait0 双仓增量代码与 CPU/静态合约。**

**不等于**真实 Wan/DCP 模型数值验证、H100/EGL 实际集成验证、P0 A/B/C 成功率/延迟、Stage3B B4/B8 Action 准入、官方 V3 Gitlink 合并或生产部署批准。

审核日期：2026-11-08；角色：GPT 独立 reviewer；作者：Codex。

## 1. 冻结的实现 Pair 与 diff 边界

| 对象 | 精确审核 SHA |
|---|---|
| Root formal implementation | `ef82fe02ee73e3c804b83ffbd68c5123c1377fa2` |
| Child / formal Gitlink | `6842b329f71fff8b9813b2d00b83edfc61e3e505` |
| Root 设计基线 | `afd0b21f1f994bdf2b21cfbaa4a260ced8eeaaf9` |
| 已批准 Stage1 Child 基线 | `0a2119782fb5078fee3359f9ef7383d788744458` |

原始 PR：
- Root Draft https://github.com/wxwy/psm_wma/pull/25 ，提交审核时 PR Head `00a57e1cb3a46ccb648c1ddd6449fb21c3ef8ca1` 为后续 docs/evidence successor，**不是** formal Root implementation SHA。
- Child Draft https://github.com/wxwy/cosmos-framework/pull/7 ，审核时 Head 即 `6842b329f71fff8b9813b2d00b83edfc61e3e505`。
- 采用两个**增量 diff**：Root design `afd0b21f..ef82fe02`（11 files），Child approved Stage1 `0a211978..6842b329`（29 files）；不将未合并的 PR4/PR5/PR6 或 Root PR25 对官方 V3 的完整祖先 diff 错作本次增量。
- 从 GitHub 原始 Git Tree 与独立本机 detached Git checkout 验证 Root Gitlink **确切等于** Child `6842b329...`；两源码工作树 `git status --porcelain` 为空。正式 V3 Root 在审核时为 `7b8b733e1f585bb44a0eac7c14ad545c29355a86`，其 Gitlink 仍为 `1ca308055fc41fb69efaeb9efaa23808f164a18e`；未合并。

## 2. 真实源码验证要点

1. **实际成功 env.step 后证据**：Child `simulation/robocasa/closed_loop_eval.py:434–490` 在 `env.step(env_action)` 前复制 pre-action composite RGB、canonical executed raw15 到 `prepare_step`，调用成功后才 `complete_step`；异常调用 abort，不产生成功证据。Child `sim_shared_vae_client.py:265–370` 限 source_step/Chunk/frontier、RGB SHA 与完整 session lease；Root `scripts/robocasa_eval_v2/shared_vae.py:265–453` 的 Actor relay 验证 scoped capability、committed native Action response 及真实 callback，而不向 Sim 暴露 Owner 全局 token/Worker 签名 key。此信任模型明确是 `registry_same_trust_domain`，不能宣称 Worker HMAC 能独自证明物理 env.step。
2. **原始真实步号 15+1**：Child `inference/robocasa_vae_worker.py:268–393` Owner-only `owner_boundary_skip` 要求 source_step%16==0、四 frontiers 严格相等、previous jobs 已 ACK/排空、Chunk/Lease/receipt/hash 匹配，原子前移并留有 bounded tombstone，**没有编码/签名一份伪 Worker boundary**。后续 `owner_issue` 的真实 source_start=1/count15，再走 16、17..31，不把 Worker 帧重编号。
3. **只从 Policy 原有 current VAE 抓取 full pre-crop**：Child `model/generator/omni_mot_model.py:4888–4940` 通过 `_encode_vision_item` 的原始 `self.encode` 后调用 observer；`inference/robocasa_boundary_capture.py:137–245` 校验原始 RGB、实际 fp32 当前像素、Model/BF16 identity、单次 Encode1、完整 latent、source/deadline，调用 full pre-crop `current_latent_to_visual96`。同时复核真实推理模型 `omni_mot_model.py:5021–5124` 的 causal prefix T1 路径：`get_data_and_condition` 条件 Vision0 只编码需要的首个条件帧；并没有添加第二次 current Encode1。代码合同合格，**真实模型/Wan 仍需单独硬件验收**。
4. **原有 Local-TTT 原子路径复用**：Child `inference/robocasa_feature_evidence.py:497–665` 要求权威 Root/Policy post-step 完成账本和 signed Worker receipt 同时对应 source0..15/16..31，校验 HMAC、Loaded VAE identity、Clock/Deadline、Lease/Worker Epoch、Action SHA；`robocasa_local_memory_policy.py:230–369,387–474` 仅生成既有 `OnlineMemoryRequest([N,96],[N,15])`、复用 `OnlineLocalMemory.prepare` / Model-owned scan + `MemorySnapshot` 单次 atomic commit/abort，Boundary 随 Response/FastState 同时 publish，失败不发布。未重建记忆体系。
5. **Policy Native READY 与模式隔离**：Child `robocasa_batch_transactions.py` 的新模式先在原有 model executor prepare，Feature READY 后方入 Native Batch，避免未齐历史参与 generation；`action_policy_server_robocasa.py:631–745` 强制 Single ABC profile PolicyB1、C required 和 `wait0`。Child `robocasa_feature_evidence.py:351–382` 强制 Worker B1/wait0；B4/B8 对 Action Path **拒绝**。A/off 仍 0 History Worker；B/server VAE 仍保留16次 Encode1/T16/旧 schema。
6. **Root 生命周期/EGL**：Root `scripts/robocasa_eval_v2/shared_vae.py:535–896` 以 run-level Registry peer 启动唯一 Worker、私有继承 FD bootstrap、实际加载模型/配置/物理设备 identity proof、Actor scoped relay、Session End 与 owned-only group 清理；`runtime.py` C opt-in 独立定位 GPU、资源预留，并仅为 Sim 子进程设置 NVIDIA-only EGL ICD，保留严格物理 PCI/current context 验证，不修改系统全局 Vendor 列表。Worker restart/uncertain drain 后仍 fail closed。
7. **可审计 Trace 与 Deadline**：Child `robocasa_feature_trace.py` 原始 bounded monotonic CPU spans 与 CUDA events（未在 CPU 测试里虚构 GPU 时序）、overflow/incomplete标记，第一 action / steady Replan 单独定义；`sim_shared_vae_client.py:201–239` 将 Replan 开始时间与原 Episode Deadline 取 min，历史等待/HTTP/TTT/ACK 不刷新原 deadline；End 另有 bounded cleanup deadline。未改 M/B Resume 权威身份。

## 3. 作者原始 CPU 证据核验（不是 reviewer 的独立测试）

作者正式归档：`docs/collab/codex/evidence/2026-11-08_issue24_stage3a/`，Root docs successor `3c796fbb4ee214b3e9dafda596b04ab8745bf0fd`；
作者 handoff：`docs/collab/codex/reviews/2026-11-08_Issue24_Stage3A_ef82fe02_6842b329_CPU_Code_Review_Request.md`。

| 原始 JUnit | XML <testsuite tests> | XML <testcase> | 失败/错误/跳过 |
|---|---:|---:|---|
| Stage3 focused | 566（包括207 subtests）| 359 | 0/0/0 |
| Root lifecycle/config | 152 | 152 | 0/0/0 |
| Legacy protection | 143 | 143 | 0/0/0 |
| 合计 | **861** | **654** | **0/0/0** |

这里的 **654 是真实顶层 testcase 数，另有207 subtests**，不能宣称861个完全独立顶层测试。作者最终 `author-04/gate.json` 为 PASS，`author_result.json` 记录原始3轮失败的最终修复、Shell0、36个改动 Python Ruff check/format PASS、`source_unchanged=true`。核查未将先前失败轮次覆写或误计为本轮通过。Root Registry OS child/FD、外部进程未杀、Stage1 Unix IPC End/Close 和 synthetic Trace complete/overflow-negative 有原始证明；全部为 CPU synthetic，不代表真实 H100/Wan/Sim。

## 4. GPT 独立 CPU 复验和环境差异

**非作者原始环境：**独立 `data` 服务器，真实 GitHub clone detached Root ef/Child684，Python3.13.11 / torch2.10.0+cu128 **CUDA_VISIBLE_DEVICES=''**、Ruff0.12.7，未使用 GPU、真实 Policy 模型、真实 Sim 或训练。为避免项目独立 `.pytest.toml` 默认插件需求与 reviewer 环境不同，pytest 显式 `-c /dev/null -p xdist.plugin`（无生产代码变更）。

- **6个 C 核心与 Root Worker 测试文件**：独立结果 **119 passed +22 subtests passed**，Exit0，零失败。
- **6个 A/B 和旧事务保护测试文件**：独立结果 **114 passed**，Exit0，零失败。
- **合计独立执行：233 个顶层 tests +22 subtests**，而不是宣称全部作者654项重新执行。
- 独立 9 个关键代码文件 `ruff check` PASS，6 个 `ruff format --check` PASS。
- **透明披露 reviewer 自己的失误**：首次 legacy 运行设置 `MUJOCO_GL=disable`，Root legacy CLI 要求 `egl|osmesa`，导致 7 个 CLI 配置测试在被测逻辑之前失效。保留失败原始 `legacy_v1.log`；立即用合法 **`MUJOCO_GL=osmesa`** 对完全相同的测试文件重新运行 **114/114 PASS**。该首次失败不是生产代码回归，也未改源码/测试以通过。
- 复核前后 Root、Child `git status --porcelain` 均空；GPU4–7 显存全为0MiB。

原始 GPT 独立 CPU 证据只留授权数据主机，未上传真实模型/图片：
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue24_stage3a_independent_review_20261108/independent_cpu_targeted/`
其中 `targeted_v3.{log,exit}`、`legacy_v2.{log,exit}`、`legacy_v1.{log,exit}`、`independent_ruff.log` 与 `independent_gate_result.json`。
独立 summary SHA256：`d899623bcade247b6d81e8ed6cbfb3b9f2e3d2e250863021160138422816f1fe`。

## 5. Gate 判定与不许继承的工作

**`APPROVE_CODE`**：仅指 Stage3A 这对 exact SHAs 的 **CPU/static 合同、两仓增量和独立审计未发现代码级阻断项**。允许保留隔离 Draft PR 并发起下一项独立硬件验收申请，但**不自动批准启动真实 GPU/Policy/RoboCasa、SR、V3 合并或生产策略接入**。

仍然未完成：
1. 实际 H100 单卡/Policy 的 loaded Wan 参数与 Worker 物理身份比对、当前帧完整 pre-crop Visual96 B1 与 legacy 真实数值严格等价、实际 DCP Local-TTT T16 vs 16×T1 FastState/Prefix/Action、真实温启动/超时/End。
2. **P0 Single 1 Policy Server ×1 Sim**：A Native NoTTT N / B LocalTTT L server_vae / C 同 L sim Worker B1/wait0，需 Owner 新授权正式 GPU Gate；分 cold/start/steady/partial 及资源拓扑、实际总 Replan/首 Action 延迟 P50/P95/P99、paired SR/CI。A 与 B/C 权重不同，不可直接把 A-B SR 因果归结为 TTT 增益；B-C 是同权重工程对照。
3. Stage3B B4/B8：先前 B8 BF16 B1 严格 exact0 **仍未通过**；Owner 仅通过8帧重建人眼质量，Stage2 16Sim无Policy性能子门通过；实际 DCP B8 造成 Action非零差异 maxabs0.0301193（合成 raw15 3例），**没有 matched closed-loop SR**。Stage3A B8 Action 准入仍禁用，不可反向修改原数值标准。
4. Root V3/Gitlink / PR7 / PR25 不合并，任何 Source Resume/在跑训练与 GPU0–3 未触碰。

下一步由 Owner 显式选择是否授权 **isolated P0 Single real-GPU functional smoke**，不得以此 Code verdict 直接跳到18×50或900EP。

**正式受审核的对象始终是 Root ef82fe02 / Child 6842b329；本审核文档和 CODEX_INBOX 后续 docs-only commits 不能替换本 Pair。**
