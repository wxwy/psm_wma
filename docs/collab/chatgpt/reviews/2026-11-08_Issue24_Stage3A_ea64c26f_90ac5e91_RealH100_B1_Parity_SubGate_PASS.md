
# Issue #24 — Stage3A 真实 H100 Wan/DCP B1 数值等价性独立审核

**Formal verdict: PASS_REAL_H100_DCP_B1_FIXED_INPUT_PARITY_SUBGATE**

2026-11-08。Reviewer: GPT，Owner 已明确授权本轮真实 H100 固定输入功能验证。此结论不是整个 Stage3A/P0 或真实闭环 SR 的通过。

## 1. 严格绑定正式代码和模型身份

- **Formal Root**：ea64c26f7738f2efba5c33c78f18eab475230a61。
- **Formal Child/Gitlink**：90ac5e91c5919cdb1d228aebd797e40327900981。两仓在真实测试前、后 git status 均 clean。
- **PR**：wxwy/psm_wma #25 与 wxwy/cosmos-framework #7 均 Draft、未合并；所有后续仅归档文档的 Root commits 不能代替 Formal Root。
- **真实 checkpoint L**：/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/packed128_droid_fresh_g1_20261019/checkpoints/iter_000015000；使用同目录 config.yaml。
- **Wan weights**：/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth。
- **实际物理资源**：H100 GPU6 为完整 Policy DCP，GPU4 独立加载真实 Wan BF16 eager Encoder；无 CUDA OOM，GPU0–3 的其他作业未触碰。

## 2. 上轮 H1 OmegaConf 生产启动阻塞在真模型下关闭

实际 GPU6 ActionModelService 已载入真实 iter15000 LocalTTT checkpoint，调用已修复的 loaded_vae_identity()，不再发生原 ListConfig → invalid canonical JSON 错误。独立 GPU4 Wan2.2 VAE 真实加载后，其 loaded VAE identity 与 Policy 实际模型逐项一致：权重 SHA、config SHA、preprocess SHA、Visual96 SHA、backend=eager、dtype=BF16。32段输入和额外一帧当前图像的真实 RoboCasa RGB SHA256 对应一致。

**H1 REAL-MODEL STARTUP/LOADED-IDENTITY：PASS。**

## 3. 真 Wan Encoder B1：Policy Boundary + Worker 15+1 exact parity

- 原始数据：33 张连续 RoboCasa365 v3 target-atomic left+wrist RGB 合成 256×512，取32帧历史与第33帧作为生成条件。
- GPU6 的 Legacy Policy 原生 B1 Encode1 得到32×96 reference Visual96。
- source_step=0、16：真实 Policy model._encode_vision_item 的既有 current Encode1 前向过程，在完整 pre-crop latent 处通过 Stage3A capture_policy_boundary 捕获 Visual96。与独立 Legacy Reference 对应96个 float32，两个边界的 max_abs=0、bit exact。为形成独立数值 reference，测试脚本另做过 reference encode，不能将总模型调用次数解读为生产一次 Replan 的真实调用次数。
- GPU4 独立 LoadedWanEncode1 逐帧 B1 真 Encode1：真实 source_step=1..15、17..31（30帧，无虚假重编号），与 GPU6 Legacy Visual96 全部数值一致，max_abs=0，bit exact。
- 合成 C 15+1 的32×96=3072 float32与 B reference 全部 bit exact，max_abs=0。

**REAL-WAN B1 VISUAL96：PASS exact0。**

## 4. 真实 DCP T16 vs 16×T1 FastState / Prefix / Action

同一真实 L checkpoint，固定 raw15 synthetic 控制证据、30步 UniPC与 seed=[0]，分别用 T16 一次扫描和16×T1逐帧扫描两个真实模型分支。两组独立16帧 [0,16)、[16,32) 各自核对：
- Visual96 max_abs=0。
- 每段四组 FastState tensor，合计24864个fp32元素，max_abs=0。
- Local Prefix 128维/段 max_abs=0。
- 最终生成 Action [16,15]（每段240标量）max_abs=0。
- B1 原输入重复生成 Action 差异 max_abs=0，排除本测试采样随机性。

**REAL-DCP SINGLE-CHUNK T16-vs-T1：PASS exact0。**

## 5. 连续两段持久 MemoryStateStore 事务补验

独立启动两份原生产 OnlineLocalMemory（共享同一个真实 checkpoint 的 encoder、core 和 model-owned scan，但分别存储 B 和 C 的私有 FastState），严格使用 OnlineMemoryRequest：
- B：stream_t1=False；C：stream_t1=True；两个 Store 各自 reset、prepare、commit。
- 第一段 source0..15 更新后，两个 Store 真实 commit；第二段 source16..31 **保留第一段已提交的 FastState**，再次 prepare、Policy native Action generation、commit。
- 两次持久提交前后，B/C FastState 四组张量 max_abs=0，Prefix max_abs=0，原生动作 max_abs=0；consumer_step 分别推进至16和32。
- 再对已提交相同历史请求调用 prepare/commit，真实 Replay 命中，adapted_steps=0，原 FastState和Prefix不变。

**REAL-DCP TWO-CHUNK PERSISTENT ONLINE-MEMORY：PASS exact0，REPLAY PASS。**

## 6. 原始证据、独立失败恢复和资源后检查

所有原始结果留在授权 data 服务器，隔离目录：

/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue24_h1_newpair_real_B1_parity_20261108/

- policy_features.{json,log,exit} 和 visual_policy_B.npy；
- worker_features.{json,log,exit}、visual_worker_C15.npy；
- policy_compare.{json,log,exit}；
- real_online_memory_two_chunk_parity.{json,log,exit}；
- 独立 probe scripts 与 independent_subgate_summary.json，后者持有所有脚本/结果原始 SHA256；汇总 SHA256：77e8785283bd16fe14edc7122884896d2e5cb140475f151dced96fce69df87df。

**透明披露 Reviewer harness 两次错误**（原失败文件保留，不能算生产 defect）：
1. 初版 Frame.create 的 Episode 与 Job Deadline 用两次 monotonic_ns 单独计算，后者大于前者，生产协议正确拒绝。更正为复用同一绝对 Deadline。
2. 初版 T1 scan 将 ContinualTTTFastState NamedTuple 转普通 tuple，生产 state validator 正确拒绝。更正调用真实 core.detach_state()，未修改生产源码。
修正后所有最终子实验均 exit0，原始失败证据留档而未覆盖。

审计完成后 Formal Root/Child 两仓 clean；GPU4、5、6、7 显存均0MiB、无残留 probe PID；未训练、未写 checkpoint、未启动真实 Sim/SR。

## 7. Gate boundary 与下一步

**唯一 Formal verdict：PASS_REAL_H100_DCP_B1_FIXED_INPUT_PARITY_SUBGATE。**

它证明真实 Wan2.2和本次真实 DCP 固定输入下的15+1 B1 Visual96及跨两段 persistent LocalTTT/Action数值等价；**没有**证明完整生产 Unix IPC/Run Registry/HTTP/实际 env.step Action provenance 路径的 1 Server×1 Sim 操作。Worker 这次是直接运行真实 Wan Encoder/LoadedWanEncode1 而非完整 Worker daemon IPC，动作证据是固定 synthetic raw15 而非仿真器实际执行 raw15。本结果不能推断任务 SR、真实 Replan p95、Episode/h或整个 C Profile 可用。

后续需独立权限和 Gate：实际1×1 B/C post-step、Worker Unix IPC/Owner/ACK/End、P0 A/B/C延迟与 paired SR。Stage3B B4/B8 Action exact0未通过，仍然禁止默认接入。PR25/PR7均保持Draft，正式V3/Gitlink/训练不变。

本 Review/Inbox 的后续 docs-only commits 不改变 Technical Formal Pair。
