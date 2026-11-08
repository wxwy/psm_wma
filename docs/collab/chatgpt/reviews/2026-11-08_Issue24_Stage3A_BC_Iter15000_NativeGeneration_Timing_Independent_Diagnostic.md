# Issue24 Stage3A — B/C 同 DCP、固定输入的 Native Generation 时延复核

**性质：独立硬件性能诊断，`DIAGNOSTIC_EVIDENCE_COMPLETE`。不是代码改动、Code Gate 批准或新的性能加速 Gate。**

2026-11-08 UTC。Reviewer/GPT 独立执行；无生产代码修改、无900EP重跑、无真机/模型训练。

## 1. 冻结受测身份与旧硬件试验

- 正式实现：Root `8a17c3db6a2e571b67e6a149638f9d7922a704d5` / Child+Gitlink `00f30235da6ffb085a9304ef6501ede509203092`；Root PR25/Child PR7 继续 Draft，官方 V3 Gitlink 不动。Review/Inbox 文档提交不能替换这对实施 SHA。
- 真 DCP：RoboCasa LocalTTT `iter_000015000`，B 为 Policy-side history Wan 16帧 + T16 Local-TTT，C 为 Sim shared-VAE B1 + Policy 15+1 Visual96 +16×T1 Local-TTT。
- 真实完全闭环 B 和 C：CloseFridge、seed4603、1 Policy GPU6×1 RoboCasa Sim GPU4、horizon16、30步 UniPC，均900动作、57次 Replan、`valid=1,invalid=0`、task failed 0/1。**两组原始逐动作比较确认全部900×15维 `predicted_raw15`、全部900×12维 `submitted_env12`、57×16×15 Policy Chunk 完全逐位相同（max_abs=0）**。这不是推测同输入模型行为，而是完全相同已执行动作的独立原始日志比对；并未存储/逐帧配对所有观察RGB的Hash，不能额外宣称全部原始RGB字节相同。

## 2. 原始闭环时延状态非平稳

| 统计口径 | B：原始 LocalTTT | C：优化版 C-B1 |
|---|---:|---:|
| Episode 900步耗时 | 164.964s | 144.256s |
| 稳态 Replan P50 / P95（去掉前2次，N55） | 1269.938 /1324.536ms | 1517.911 /1540.513ms |
| 原始完整运行中前段快档（Replan index3..12、17..21） Native Generation P50 | 982.696ms | 993.856ms |
| 同快档完整 Replan P50 | 1285.612ms | **1126.571ms** |
| C慢档（index13..16、22..56） Native Generation P50 | 970.510ms | **1359.738ms** |
| C慢档完整 Replan P50 | 1267.906ms | **1521.068ms** |

- C 的 Native Generation 在第13..16次出现慢档、第17..21次又恢复快档、第22..56次再长期慢档；**B 没有对应的大幅跳变**。
- 因此原来认为 C 生成算法比 B 固有慢约381ms 的推断不成立；真实运行记录具有条件相关的两个吞吐档位。
- 原始 B 在 Policy history VAE 侧16次Encode1，`history_payload_prepare` P50约164.7ms，T16 Fast Weight P50约32.9ms；C真实闭环 feature_prepare约89.9ms、T1 Fast Weight约84.9ms。在 C 快档，**完整 Replan 实际比 B 快约159ms（约12%）**；慢档时反而慢约253ms。C真实Episode总耗时比B少约20.7s，但不能仅归因于 Native Generation 或VAE差异，因为双方其他调度/环境阶段耗时不同。

## 3. 真 GPU6 冻结输入交替微型 Profile：消除时序与模型差异

隔离 reviewer script `fixedinput_real_dcp_alternating_profile.py` 使用**同一个真实训练 checkpoint**、相同33张 recorded RoboCasa left+wrist RGB（与既往已验证输入 SHA 一致）、相同16×96 Visual96、固定随机 raw15、30步 UniPC/seed及同一 Policy action batch。每一组 B-T16 与 C-16×T1 创建的真实 FastState 4张量和4×32 Prefix **逐元素/bit exact**，所生成的 Action也完全相同。单 GPU6，交替测试，正式源码和模型参数无任何修改。

| 单纯计算（严格同期） | B-T16 | C-16×T1 |
|---|---:|---:|
| Fast Weight 更新 P50（各24次） | **35.292ms** | **46.692ms** |
| Native Generation P50（各30次） | **995.294ms** | **995.323ms** |
| Native Generation Mean（各30次） | 996.283ms | 996.328ms |

同一循环30组成对 Native C−B时延差值均值 **0.0455ms**；无可观测固有 Native Generation慢档。模型在60次真实采样期间的 GPU6 H100时钟250ms被动采样；落在生成区间的**239/239采样均1980MHz**。源码无补丁，不依赖假Policy、fake Tensor或网络服务。**此结果证明给定相同输入和持续高时钟状态，模型 Native Generation 本身不因T16/T1配置变慢。**

## 4. 900ms空闲间隔／历史Wan预热小样本控制

另一隔离脚本 `idle_gap_real_dcp_profile.py` 对同一个真正Wan/DCP和完全相同的 Policy batch/Prefix/Action，以4种前置条件各8次真实30step UniPC测量；条件顺序跨轮轮换：

- HOT_NO_GAP
- GAP_900MS_NO_PREWORK
- GAP_900MS_PLUS_HISTORY16_WAN（生成前实际 GPU6 Wan Encode1×16，前置约68.6ms）
- GAP_900MS_PLUS_LOCALTTT_T1（生成前实际Local TTT 16×T1，前置约66.0ms）

最初各条件 Native Generation 约0.94–0.95s，**第7–8轮再度出现约1.25–1.30s的慢档**。每个条件晚期慢样本数（阈值 >1200ms）：HOT 2/8，GAP 2/8，T1 2/8，历史Wan预热 **0/8**。因此历史Wan前置核可能有预热/缓存/调度效果，但单次实验仅后段2个慢样本，**不能宣称历史Wan是已证实因果根因，也不能据此增加无谓的VAE计算到生产 C**。

重要的是，在这个复现慢档的实验里，**所有生成过程的250ms GPU6 SM时钟样本仍为1980MHz，快档GPU利用率NVML采样大致33–34%，慢档约24–25%**；没有监测到GPU SM降频。原来C完整900step运行时未记录GPU时钟，故不能回填该运行的物理因果。现有证据更符合运行时执行/供给/缓存/调度状态变化的方向，但不排除其它未观测协变量。必须避免将GPU频率、CPU线程或某个缓存机制当作已证实根因。

## 5. 原始证据目录和真实性约束

授权 data 主机完全隔离文件（不改训练权重，不改两Git worktree）：

- `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue24_stage3a_BC_sameDCP_fixedinput_profile_20261108/`
  - `profile_result.json` SHA256 `805382f0e8a70c3f379b21ca176b4e6174c3fd0c3113a791d57b22be253d6f73`
  - `BC_900step_regime_reanalysis.json` SHA256 `cffb3bb2aa141c722d5aa97449fe84af7d1fe20d48e92bcd9e588c5cc1bb407d`
  - `independent_combined_findings.json` SHA256 `58840fb5bc98f7c0d03ca8dba423788e0ea5e6d960603f14197058b21d193f1b`
  - 原始脚本、stdout、exit0和250ms GPU6时钟+功率/利用率CSV。
- `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue24_stage3a_GPU6_idle_history_clock_profile_20261108/`
  - `idle_gap_profile.json` SHA256 `18f0d19a11050bfbaafa30196821ab36ed7bc126774af6d77f8daa5b95115052`
  - 原始审阅脚本、stdout/exit0和单独GPU6 250ms NVML监视记录。

完整退出后GPU4/5/6/7均0MiB、无隔离实验进程；Root+Child检出均clean，未合并PR、官方V3与训练/900EP均未动。所有 Profile 计算耗时为直接实际观察，不能把不同时间的阶段P50相加来虚构关键路径。

## 6. 当前决策与边界

**`DIAGNOSTIC_EVIDENCE_COMPLETE`，不形成 Code Gate blocker / Production patch authorization。**

- 目前无需修改 Local-TTT/Native Generation模型结构；它在固定输入交替测量下 B/C完全一样快。
- C的16×T1在同GPU固定条件下多约 **11.4ms**，是真实独立的小计算开销；历史VAE移出Policy时，在未进入慢档的原真实闭环前段 C Replan比B快约12%。
- 需要进一步定位非平稳slow regime（可考虑一个**非侵入**单GPU定向Profile中测CPU kernel enqueue/dispatch间隙、CUDA Event持续时间、Host调度和 GPU active utilization，和是否有真实Wan先行缓存效应），但**不要从这组证据推出降频已证实或要在C中增加16次历史编码**。
- 没有必要重新测试900EP；下一工作如果只聚焦单Server×单Sim，则应坚持等源B/C与阶段耗时证据，而不是用早期 VAE B8 Worker microbenchmark代替系统性能。
