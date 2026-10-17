# PSM-WMA V3 Packed128 DROID Fresh — S0 DS+Codex Readiness / Evidence Gate 审核

**日期：2026-10-17**  
**审核者：GPT — 独立 Design / Code / Evidence / Gate 审核**  
**S0 只读 Evidence Gate formal verdict：`APPROVE_TO_CLOSE` (S0 READ-ONLY EVIDENCE ONLY)**。  
**训练/G0 执行发布门：`BLOCKED`**，直到 Owner 明确选定/批准新 OUTPUT_ROOT 与 GPU 资源预算、目标卷小型FS witness、实时容量与确切 G0 执行身份；本报告本身 **不授权 GPU、torchrun、Fresh、Resume、真实DCP读写或数据清理**。**不是**条件性或等价的 GPU approval。

### 身份与来源
- 精确且未变化、此前已通过 F0/F1 CPU Gate 的 **Formal Implementation Root** `6ebf8998a7935f2ad690bb547c5db5e5a4322e6d`；**Child/Gitlink** `2d128ed5a07601cdd424974f99b67832eafeeb41`；隔离实施分支 `v3-f1-checkpoint-rng-20261016`，其文档 HEAD `ccfd900bc35fcd39ca9953aa7aa55b85398300ad` **不是** formal Root。
- 审核时 `origin/V3` docs HEAD `cb7c607c8d32f9dc844ac74cdab377719660b2fc`，生产Child仍旧 `1d56320c08c56b0f8dd248919d152d81ae12ea7b`；尚未Promote F1。GitHub F1 formal root tree精确含上述Child Gitlink，已核验。新V3文档提交不得取代training identity。
- **DS独立材料**：Owner本轮粘贴的 `DS_PRO_V3_S0_Packed128_Fresh_readiness_2026-10-17.md` 及机读JSON；报告指向CPU证据 `/tmp/psm_v3_s0_20261017/preflight_world8.log`, `c_old_breakdown.json`, `s0_readiness.json`。GPT无训练服务器权限，**未独立读取DS远端raw日志与磁盘**，容量/运行结果明确归类为DS独立报告，不能伪称GPT实测。
- **Codex只读材料**：`docs/collab/codex/reviews/CODEX_V3_F1_Packed128_GPU_gate_launch_readiness_READONLY_2026-10-17.md`, **docs-only commit `40a0f8b053a627a390dbc96a635bdb02e15fbec1`**（父提交 `ccfd900...`，仅新增一份文档；正式Root/Child及V3主线生产代码均未改变）。通过GitHub直接读取全文。
- **本轮仅新S0 Evidence/方案审核**，没有再重复审查F1同Pair代码、F0/F1 CPU Gate、B0数据、旧B1 r2 NUMERIC FAIL、旧iter1300 migration。

## 一、S0-CONFIG — PASS（CPU Read-only）；真实GPU初始化未PASS

| 冻结需求 | DS结果/代码引用 | 审核 |
|---|---|---|
| 正式启动路径 | Root `scripts/train_v3_packed128_staged.sh`，F1 exact Root；唯一调用 corrected Phase5，非H3F；world8/B8/T16/GA2/K4、workers0、no full segment prefetch、`max_iter=30000,warmup=500,save_iter=100`。无OOM自动Index8 fallback | **S0-PASS** |
| Packed128 默认 | Child `NATIVE_BATCH_LAYOUT=v2_a2_member_packed_slot_major_v1`；Index8显式训练选择**尚未实现**，仍作为P1兼容合同，**不能宣称双路径当前完整** | **Packed-only PASS, P1 open** |
| 实际world8只读preflight | DS用完整V2依赖真实F1 Child，RC0，episodes=9126、offline已验收Index、verify_files=False、`execution_stop_after_iter=100`、no Job dir。world8 digest **`65ad8bce52aed0feaecbf399828667683f7a461487f870e0493dad8766abd01f`**，与world2 `c6c733...`因world_size进入identity而合法不同。CPU数据源创建~191.9s，总体wall时间不得误认为训练速度 | **S0-PASS as reported** |
| Action/Optimizer/Local身份 | raw15/state15/Action64/H_pred16/17 frames、left_wrist、BF16、FusedAdam LR5e-5 WD0.05、selected Generation+Action+Local、Local K4/T16/dim32/ttt_dim64、DROID-model-only Fresh、SafeLocal `psm_v3_sync_local_v1` sync/local/strict、transform RNG legacy_global、scheduler 30000/500/100；real model/loss/mask/action causal GPU尚无 | **CONFIG PASSED; runtime/GPU PENDING** |
| `Config.validate()` | CPU禁止CUDA，与生产 `Config.validate`内部CUDA world-broadcast不兼容 | **BLOCKED_IN_CPU**；未来8GPU Gate **HARD_P0**，不是CPU PASS |

## 二、S0-STORE — DS测量可信层级PASS；现有目标输出地点选择仍待Owner

**旧真正分布式 DCP测量**：`iter_000001300`，latest也指向此Iter，apparel bytes `24,897,732,763 B = 23.1878206 GiB`：model12.5611GiB、optimizer10.6183GiB、scheduler~0、trainer~0、8Rank dataloader0.0082GiB；这些是实际8份`.distcp`各组件+共享metadata和8份Local sidecar，**不是B1的`8×4.7GB rank*.pt`数值证据文件**。只读stat/du，未加载旧DCP内容。

**报告时的卷容量（DS-reported, 非live承诺）：**
- `/mnt/data`：**104.57 GiB**可用，99%满；**拒绝**作为新完整Packed128训练序列的优选输出。
- `/mnt/data1`：**337.33 GiB**可用，`/mnt/data1/data_v2_0617/`已验证可写，**推荐Owner指定为新G0/G1/G2的`OUTPUT_ROOT`所在独立目录**。挂载ext4；F0之前原子/fs锁验证在`/mnt/data`，**仍需在新目标`/mnt/data1`做小型mkdir/flock/fsync/rename探针**（不可拿一个挂载上验证当另一个挂载）。
- `/`：45.72GiB free；不作为新大DCP输出。
- Quota工具缺失、无mount quota flags !=证明全部配额不存在，保留UNCONFIRMED。

**容量预算，实际新C未知：**令C_old=23.188GiB、W=50GiB（日志/视频/基础缓冲工程假设，非实测）、R=2*C_old（失败staging或orphan额外缓冲）。
- **3个启动、两个Namespace**：G0 bounded3 **1份**诊断DCP + G1/G2正式iter100、200、300、400、500共**5份**（不会自动删除）；至少 **6*C_old + W + R ≈235.50GiB**。DS测得`/mnt/data1` free337.33GiB，按旧C估算剩余101.83GiB；`/mnt/data`失败。
- **更稳的Resume硬停方案（额外一个启动）**：G2a Resume100→101会按当前正式Trainer在非整百执行终点额外保存**iter101**；G2b Resume101→500。G0 1份 + 正式iter100、101、200、300、400、500共6份，**7*C_old + W + R ≈258.69GiB**；按DS报告data1仍余约78.64GiB。此方案牺牲一次启动+一份DCP换取101后真实人工Gate；不在本S0自动授权，G1后依据C100和Owner决策。
- **重点：保存1次本身会留下完整文件**；正式G2恢复100→500不会自动在101暂停。若坚持3启动且无人值守，只能外部监控并承认无法零延迟在101硬停，不能将“检查101”说成自动守卫。
- 本次可以允许**规划到500、所有DCP保留不删**；未来30k最多300个整百正式Checkpoint约`300*C_old`，**现有代码无自动retention**，长期训练不得在没有Owner授权的实际保留/扩容计划下发布。任何未来cleanup只能限新Job、complete/latest已完成且不被pin/引用的旧版本，旧595GB B1 PT证据、旧iter1300/DROID/cache绝不可自动移动或删除。
- **必须测新C**：G0 iter3和G1 iter100的真实DCP字节数与高峰写盘、fsync延迟需分别实测；如果实际C或共享卷变化使后续不满足批准的W+R，G1/G2需阻断，不能基于旧DCP估算默认继续。

## 三、S0-SEMANTIC — 证据边界明确，未冒充GPU PASS

- Native Payload/Prefix/Mask按slot-major；每GA member Full B8×T16=128 Consumer、GA2；每完整update **2个Native forward/backward per rank**，三次更新合计每Rank6次；全GA共8Rank预计`8×3=24`份rank×iteration missing-grad报告；实际每member和Terminal Partial必须按真实n_member/n_window，非固定各0.5。三步未出现partial则保持`NOT_COVERED`，不人为重跑B1。
- `--audit-missing-grads`仅可`fresh + bounded_* --stop-after-iter 3`，不能与formal`--formal-execution-until 100`混用。Stock G0 `AUDIT_OK`只表示审计采集/迭代协议无故障：**即使eligible nonempty FQN仍然grad=None也可能报告AUDIT_OK**；必须逐项检查JSON missing字段和rank/local_numel、FSDP placements，而不是以8Rank进程RC0、rank0 Loss下降、`AUDIT_OK`代替全Rank真实数值更新。
- G0现有observer在其他Rank主要提供梯度**存在性**，Rank0分片数值norm，**不能单凭G0关闭全部Rank nonzero Slow gradient/optimizer moment或Local→Action因果干预**。`numel=0`合法空DTensor分片、all-continuation W0合法zero均需按实际FQN角色例外排除。缺失Action有效mask与Prefix chronology证据的子门必须诚实标`GPU_PENDING`/ `BLOCKED`，不要假造Passed。
- 真正 DROID load、`Config.validate`/NCCL+Gloo、FSDP8 optimizer/init、实际Action/Vision/Aux Loss、raw15/state15→env12真实Controller ABI、CUDA RNG和strict Save100→Resume、下次consumer Identity、短Simulator两次Replan和E1评测可靠性皆为未来独立Owner GPU或Eval Gate。旧V2 LIBERO成果只证明架构方向，旧B1 iter1300数值FAIL不构成本Fresh需重跑的等价前置。

## 四、方案裁决 / 后续硬阻塞

**优先选A**：**G0独立bounded3**，既有F1代码、无需变SHA、独立diag-only Job + iter3 DCP；随后按独立授权 G1正式新Namespace Fresh0→100，G2同NamespaceResume→500。Codex只读报告认可该方案，GPT采纳；单纯降低一GPU启动以加新生产观测代码属可选B方案，成本/回归/正式Root改变不值得眼下采用。

**仍需Owner决策的两项：**
1. 把两个新Job的唯一`OUTPUT_ROOT`授权指定到`/mnt/data1/data_v2_0617/`下的**未创建全新Namespace**；并在该卷完成小型FS原子、flock/fsync和即时df复测、给出容量门的真实状态。
2. 明确单次GPU Gate G0运行预算、8×H100、精确F1 Formal Pair、独立日志/产物保存范围；**本S0不代表Owner已授权**。在G0结束后手动Review 24份审计/诊断DCP后，再独立授权G1；G2启动/是否分拆101应在G1后新C实测与严格恢复证据采集计划完成时定。

**Formal S0 verdict definition:** `APPROVE_TO_CLOSE` 的范围**仅限 S0 READ-ONLY EVIDENCE 收集与设计/配置/容量方案**；此Gate可关闭是因为 DS/Codex 已交付约定的所有只读证据且对GPU需求和条件真实标注。独立 `G0_GPU_EXECUTION_RELEASE`仍`BLOCKED`，直到Owner授权、target-FS原子探针+current capacity、8GPU设备/运行环境、外部停机机制就绪；不能称为CONDITIONAL_APPROVE GPU。**本 verdict 只关闭当前 Gate，不授权后续 Gate 或生产行为。**
