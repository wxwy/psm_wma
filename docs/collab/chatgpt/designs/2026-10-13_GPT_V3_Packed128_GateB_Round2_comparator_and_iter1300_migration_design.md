# GPT 设计草案 — V3 Packed128 Gate B Round2 Comparator / iter1300 跨布局迁移

**日期：**2026-10-13  
**作者：**GPT（基于 DS_PRO 只读证据，设计起草；Owner 决策）  
**状态：**DESIGN_PROPOSED / OWNER_REVIEW_REQUIRED / GPU_NOT_AUTHORIZED / MIGRATION_NOT_IMPLEMENTED  
**引用：**docs/collab/chatgpt/requests/2026-10-13_DS_PRO_V3_GateB_round2_design_remediation.md（R1–R7）；docs/collab/chatgpt/reviews/2026-10-13_V3_Packed128_owner_decision_and_gradient_semantics_contract.md；DS_PRO 2026-10-13 Gate B Round2 只读证据清单（Owner 会话提供，未声称 DS 已提交仓库）。  
**目的：**验证真实 Cosmos3-Edge/FSDP8 的纯 Packed128 执行布局等价，同时让训练从旧 Index8 iter1300 继续前先完成独立、安全、可追溯迁移。**本文不是技术 Gate APPROVE，也不是可直接执行的 GPU 命令。**

## 1. 正式对象与不变量

| 身份 | Root implementation | Child/Gitlink | 用途 |
|---|---|---|---|
| SOURCE Index8 | b159f45906f7261d028aecc226ab7f2bb9807eb9 | 937066ffd90f2bf783ad4fbb4909e9c0b8922982 | iter1300 真正生产方、数值参考 |
| TARGET Packed128 | c4731bca1a590663db88bd6cd74dbcf9fd513a85 | c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686 | Gate A CPU 已通过、Gate B 待验证 |
| 非本 Gate FSP | d45712a37318357ba2f57bde3d0f1f448aabbbd9 | 8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1 | C0 CPU 已关闭；不得混入验证 |

必须绑定精确 Root/Child/Gitlink、解析的 Python 模块实际 __file__、真实 source checkpoint、真实 source/target config_digest 和配置/数据集指纹。旧 iter_000001300 只读，iter1400 排除；正式 Formal30k worktree、latest_checkpoint.txt、源 DCP 绝不改动。

Owner 冻结几何：B=8、T=16、GA=2，每 rank 每 full member 有128个有效 Consumer，full step 256；8 rank full step 2048；Packed 每 GA Member **恰好1次 Native Forward 和1次 Backward**，两 member 即2/2；每完整 GA2 且 optimizer 成功只更新一次 optimizer/scheduler。Terminal partial 的实际 n_member<=128、n_window<=256，不可填补、丢弃或隐式缩小原定配置。

## 2. 两个绝不合并的 Gate 与依赖关系（R1）

Gate B：**Transient Numerical Comparator**，只读旧 Checkpoint，进程内加载模型/optimizer/调度器/Trainer RNG/8 rank Local State，执行隔离的、最多2个 optimizer step；唯一允许的输出是独立 /tmp 诊断 JSON、只读材料的摘要/见证；**禁止写任何 DCP、正式 Namespace 或正式 latest**。这里的暂态目标 Local State 适配只是内存态数值比较，不叫迁移、不得发布新 checkpoint。

Gate M：**受控一次性持久化迁移**，只能在 Gate B PASS 且 Owner 另行授权、迁移代码单独审查后执行；写入全新 Namespace 的合法 Packed128 DCP，再执行真实 Strict Resume 验证。正式 iter1301 续训仍是后续独立 Owner 授权。

不使用原方案中不能成立的 --phase resume --job-name gateb_index8_ref/gateb_packed128_target 命令：正式入口只会查同 job latest，Packed Sidecar 原 digest 必不兼容；--stop-after-iter 仅允许 fresh。也不把目标持久化 Checkpoint 迁移当成 Gate B 前置条件。

## 3. Gate B0 — Comparator Harness 的设计及先行 CPU Gate

**拟议文件（尚不存在，需设计批准后由 GPT 实现）：**tools/gates/v3_packed128_gateb_compare.py；诊断支持代码与测试均须明确划入独立 Gate/隔离分支，production Model/Trainer/Checkpoint/正式 Gitlink 一律不改。此设计命名只是后续实现契约，不代表路径当前可执行。

单 leg 启动分布式8进程；SOURCE 和 TARGET 各自使用与其 Root/Child 一致的隔离 checkout/venv import path，互不在同一 Python 进程混用代码。Harness 调用真实 Model、native Local scan、Grouped Window、native collate/forward/backward、Optimizer/Scheduler，并仅在诊断的内存态加载路径及随机见证中使用隔离钩子；不得用自写 surrogate loss / 假 FSDP / 假 optimizer 代替真实调用。**须证明此 direct train_step/Hook 时序与原 trainer 成功 GA2 时序一致**（Begin → GA0 scan+native+backward → GA1 scan+native+backward → finite/optimizer → Frontier/Sidecar commit → zero_grad）。不得运行会定期/退出时保存 DCP 的普通 Trainer.train()，不得绕过其执行语义仅声称模型等价。

### B0 合约（CPU 优先）

1. 可读取原始 source .metadata/CRC/8 rank sidecar 的权威只读清单；全部源文件 sha256 快照。与旧静态验收对照；不凭文件存在推断 GPU load 成功。
2. **B0 仅 CPU 静态与 API/mock 合同**：审查官方 DCP 组件读取接口、metadata/schema、source shard CRC/文件权限与无写入的模拟调用；不要求在 CPU Gate 上实例化或真实加载 4B/FSDP8 Model+Optimizer。model/optim/scheduler/trainer 的 **真实8rank H100 DCP Load** 明确属于授权后的 **B1**：必须检查 loaded-key 覆盖、FQN、dtype/shape/shard、optimizer moment/LR/GradScaler/Trainer RNG/iteration，不因 ModelWrapper 可能 strict=False 就默许 missing/unexpected key。失败即 BLOCKED，不能靠创建迁移 DCP 解决。
3. **B0 CPU** 只读检查 source dataloader/rank_*.pkl：旧 digest、十个精确顶层键、17字段 rank profile、frontier/committed scheduler、各 active record provenance 和四个 fp32 Fast State 的 schema/值/哈希；可用 lightweight CPU Window 运行生产 restore_grouped_local_state 负例，但须标注模拟 Runtime。**B1 真实8rank Model/FSDP** 才能认证生产 Local restore 与 rank-local Fast State 的真实 ABI/设备行为。
4. TARGET 在内存中 deep-clone 经过 SOURCE 校验的状态，**仅**重建顶层 config_digest 及每个活跃记录的 SegmentProvenance.config_digest 为通过新 authority 独立计算的 TARGET digest；不增加 sidecar 键。**B0 用 CPU fixture 测试负例及原生产 restore API；B1 用真实8rank FSDP Runtime 调用生产 restore_grouped_local_state 严格验证**。旧→新映射只在审计 JSON 另记，不改源、不得写出“可 resume 的 DCP”。其他 Profile/Identity/Frontier/Scheduler/fast state 值一一相同；如 source/target Local 类型/ABI/state-shape 不兼容，直接 BLOCKED。
5. 从恢复的每 rank Frontier **纯函数**推导连续两个预定 GA2 window 的 Consumer 清单和 candidate frontier。SOURCE/TARGET 按同一 slot、episode.uid、source_digest、binding_epoch、segment_id、cursor、absolute_step 顺序及相同 Raw/Action/State/Video Latent 内容执行；plan.member_counts/有效数一致，记录每 rank 每 member 的实际 n_g。检查是否含 terminal partial。若 SOURCE Index8 的各 rank active_indices 不同，先标记 COLLECTIVE_RHYTHM_BLOCKED，不得冒险进行8卡 FSDP；必须有安全可审的处理方法。
6. 隔离 CPU 负面测试：错误 SHA/digest、错 rank/profile、旧 sidecar 新字段、遗漏任意嵌套 digest 翻译、Consumer 缺失或重排、额外 RNG 调用、含 NaN Fast State、Checkpoint 保存调用，都必须 fail-closed；检查源 SHA256 前后不变。
7. 对 Harness 的模型、optimizer、scheduler、FSDP 初始化及 native DCP Load 的调用顺序做准确 Source-to-call 对照；此步完成独立代码审核后，才能申请 Owner GPU Gate B。

## 4. Canonical Consumer Witness 与 RNG 控制（R2）

Comparator 采用 **专属测试态 per-consumer witness**，不是正式 Full Prefetch consumer_keyed_v1，也**不改变**正式训练数据增强语义/config_digest。

CanonicalKey = (source_checkpoint_fingerprint, rank, global_completed_iteration_before, GA member, slot_id, episode_uid, source_digest, binding_epoch, segment_id, segment_cursor, absolute_source_step, modality, view_or_item_index, stochastic_site, subindex)；以版本化、长度前缀的 canonical encoding + SHA256 派生 64bit seed，各 RNG 域独立。不能仅以 GA/index-major/slot-major 的数组位置作为随机身份。Consumer 身份必须完整、唯一且先由 plan 验证。

**Transform/CFG：** RoboCasa getter cfg_dropout_rate=0.1；cosmos_framework/data/generator/augmentors/text_tokenizer.py 原生确实调用 Python random.random。CPU witness provider 在每次对应的 _transform 调用期间使用受作用域保护的 per-consumer Python RNG（try/finally 恢复主线程 RNG）；主线程单 worker (nw=0)，捕获实际 CFG 决策、caption hash、token ids、action/state/latent 输入 shape/dtype/hash。两腿匹配同一 Consumer 的 mask 和 token bytes。对 transform 的所有实际随机调用位置做审计；遗漏者不能视为通过。JSON Prompt 的 IdleFrames 独立 Dropout 并非本 recipe 的已启用行为。

**Model sigma/noise：** RectifiedFlow.sample_train_time 在启用 deterministic_algorithms 且有 iteration 时基于 (iteration*65536+rank) 局部 Generator 采样；omni_mot_model._add_noise_to_input 又从 (iteration*65536+rank+32768) 的 Generator 按每次 Native batch 顺序为 vision/action 等生成 epsilon；**两者在 Index8 多调用 vs Packed128 单调用时均不会自然逐 Consumer 对齐**。Provider 预先以同一 CanonicalKey 构造每个 Consumer（及 vision item / action item / frame）的实际 shape/dtype 匹配的 sigma、epsilon；可有两个不混淆的测试 profile：
- P0 FIXED：sigma=0.5；epsilon 用明确冻结的常量或固定 canonical-key 正态样本；CFG mask/transform 输入配对一致；检验纯布局数值。
- P1 MATCHED_STOCHASTIC：用生产对应的 sigma 分布/shift 逐 Consumer keyed 采样，用 keyed 正态产生 epsilon；训练模式保持一致，逐 Consumer 注入并证明与隔离组件期望 shape、mask 和归约权重一致。这验证受控相同随机输入下的布局数值等价，**不代表**两种正式布局自然的 RNG 后继序列会相同。

**仅允许诊断钩子：** 为每次 native training_step 给出按当前 native batch 排列的 CanonicalKey 队列；在 model._get_train_noise_level_vision/_action（如真实配置启用）与 _add_noise_to_input 的原生随机边界使用严格调用点 scoped adapter / witnessed RNG，记录输入输出 Tensor Hash、顺序/张量数量及全部随机调用site。任何不在白名单的 rand/randn/dropout/CFG draw、shape/path 差异或注入覆盖不足 -> BLOCKED；不可直接全局 monkeypatch torch.random 而不做站点/线程隔离和误调用计数。诊断注入要保持原来的 interpolation、packing、FSDP forward、loss 及 backward；不能改写 loss 公式来“制造”等价。

**RNG 判断：**相同 Consumer 的决策/随机张量数值完全一致；每个 leg 的同模式重复运行需可重复；跨布局 native Torch/Python 全局 RNG 的 step-end state 不要求 BIT_EXACT（更改了调用形状，bitwise 后继不是 frozen 合同）。源 iter1300 原 RNG 必须被完整保留用于未来迁移；受控 Comparator 并不证明真实续训 RNG 等价。所有 P0/P1 witness 种子、算法、schema 事前锁定，随机源位置及未命中的 RNG 探针显示0。

## 5. Loss/梯度/Local State 的严格目标（R4）

SOURCE 原生逐 index：
    L_Index8 = sum_g sum_t (n_g,t / N) * L_native(g,t)
TARGET 每 GA member 1次 packed：
    L_Packed = sum_g (n_g / N) * L_native_packed(g)
N = 本 rank 当前窗口 sum_g n_g，不使用全8rank作为本地目标分母。
只有原生 L_native 中的每项是按 Consumer 平均且与 Batch 构造无关时，上面两项才能数学等价。

默认源码说明 sample_level_loss_averaging=False，LBL method=local，coeff_und/coeff_gen=None（aux 默认 OFF）；这仍**不是运行时证明**。Harness 各 leg 在模型 fully resolved Config 下记录上述实际值、normalize_loss_by_active、exclude_fully_conditioned_items、independent_action_schedule、diffusion_forcing、loss weights、MoE aux 的真实启用状态和实际 output 键。若 aux_loss_gen/und 非零或 sample/global batch-level 损失/scale 存在，则必须证明单独归约及其梯度等价；做不到即 BLOCKED，不得只把 whole-loss 按 n/N 乘一下就宣称通过。

分别记录：native scalar total、flow_matching_loss_vision、flow_matching_loss_action（乘以 config 权重前后）、其他真实活跃分项、aux_loss_*、GA/step 加权聚合；Local-TTT inner loss 单独作为内循环适配诊断，并**不预先假定 inner_loss 以简单加数进入 Outer Total**。记录真实 loss 成分重建误差；若非 sample-additive 或遗漏分项则失败。

**Slow gradient**：采集真实 optimizer allowlist 对应的全部 trainable FQN，分 generation/action/local 三组（不可仅比 global grad_norm 或若干示例 FQN）。每个 FQN 比较 shape/dtype、None 及非有限、rank-local DTensor shards；有代表性的各组同时对全 tensor gather 做一致性见证。Gradient 采样点为完整 GA2 之后、optimizer.step 之前、unscale 完毕，且双方时点一致。每一组和每个 FQN 的 Norm2、L2rel、cos、maxabs、是否 near-zero 单独输出；遗漏 FQN/梯度即 FAIL。

**Local-TTT**：相同初始 fast state、evidence、每 consumer 的 Local prefix（包括 S0 必须 None）、higher-order chain 可到 slow Local params，GA0/GA1 后 candidate Fast State、成功 Optimizer 之后 committed Frontier/Sidecar/Scheduler、失败时无 publish；四个 Fast-State fp32 张量按真实 fp32 标准比较。实际 TTT 内循环 loss/更新亦逐 member 记录。Optimizer 一次更新后的 selected 参数、moment、scheduler LR、step 计数对比；第二步验证从已提交的新 fast state 连续演化。对权重更新差值 DeltaWeight 而不是只比较原始巨大初值（避免小更新被初始权重掩盖）。

## 6. 数值 Comparator 的预注册规则（R5）

**以下是 GPT 提议的候选阈值，Owner 应在任何新 Gate B GPU 输出产生前确认冻结。不是已经观察到的新 Pair 误差。**按实际比较梯度 dtype，不按 model forward BF16 假设全部梯度都是 BF16。所有张量先转换 fp64 做 metric（不参与模型训练）。同模式 run2run 只证明稳定性，不用于事后放宽阈值；当噪声包络为零时也不要求跨布局 bitwise，而按下面的固定数值底限。

定义 A=SOURCE、B=TARGET、d=B-A、n=numel。per-FQN:
- relL2 = norm2(d) / max(norm2(A), norm2(B), epsilon_dtype * sqrt(n))；
- maxAbs = max_i |d_i|，elemPASS = 对每个 i: |d_i| <= atol_dtype + rtol_dtype*|A_i|；
- normal = 两侧 norm2 > epsilon_dtype*sqrt(n)。normal 时 cos = dot(A,B)/(normA*normB)，必须比较；两侧 near-zero 时 cos=N/A，要求 maxAbs <= atol_dtype 且 RMS(d) <= epsilon_dtype；仅一侧 near-zero 直接 FAIL。None vs tensor 直接 FAIL，双方 None 对于原本要求有梯度的 optimizer FQN 同样 FAIL；NaN/Inf 直接 FAIL。

**候选独立数值上限（需 Owner 冻结，统一按 per-FQN AND per-family 通过，不允许按平均掩盖失败）：**

| 比较项 | FP32/FP64 已归一化输出 | BF16 梯度 |
|---|---|---|
| Loss scalar | atol=1e-6, rtol=1e-5 | atol=2e-2, rtol=2e-2 |
| 梯度 elementwise | atol=1e-6, rtol=1e-4 | atol=2e-2, rtol=2e-2 |
| relL2 (normal) | <=2e-3 | <=3e-2 |
| cos (normal) | >=0.9999 | >=0.999 |
| epsilon_dtype for norm-floor | 1e-7 | 2e-5 |

**注意：**BF16 elementwise atol=0.02 在微小梯度上十分宽松，因此它**绝不能单独构成 PASS**；需同过 relL2、cos、near-zero 及 group coverage。FP32/FP64 此处指真实比较张量/标量的归一化 dtype，不代表所有 4B 模型都需要 full FP32 GPU 重跑。GradScaler/optimizer weight/moment 的 dtype 与不同数值敏感性必须在 GPU 执行前独立冻结适配判据；如果实现者认为统一表不足以判断小权重更新，请在**见到 GPU 对照残差之前**提交数学依据和具体数值阈值，经 Owner 另行审定，禁止实验后改阈值。Terminal, prefix, identity, cfg mask 等离散合同则必须精确相等，不使用浮点容差。

对低梯度 FQN（尤其稀疏路由/零梯度），报告是否激活、原始 norm、zero-status，避免 cosine NaN 产生假 FAIL/假 PASS。对 trainable parameters 若因实际模型 conditional branch 获得 true zero tensor，应作为双方均 zero 的明确激活覆盖证据，不得默默视作缺失而过滤。每组报告所有 FQN 的 worst relL2/maxAbs/cos 及对应 FQN，不只平均数。

重复2次/leg：P0/P1 中与相同 witness 同模式重跑必须在表中相应限内，否则 Gate B 本身不具备判别能力，标记 BLOCKED_UNSTABLE；不能以 run2run K=3 倍噪声包络作为事后补偿。旧 V2 A2 ~2.4% Relative L2 只是设计背景，**不是**本 Gate 默认通过依据。

## 7. Full/Terminal 的几何和 FSDP 节律（R6）

CPU read-only plan preflight 从 iter1300 八个源 frontier 推导连续2个窗口。记录 per-rank/per-member n_g，segment final/valid mask，以及 SOURCE Index8 每 GA member 的 active_indices 和 Packed Native call count。要求:
- 每 rank 0<n_g<=128，0<N<=256；actual rank-sum <=2048；所有实际 Consumer 在两腿数量/身份/顺序内容完全一致（允许原生 native flatten 不同，但 canonical consumer bag+per-identity payload 一致）。
- Packed 成功 GA2 恰好 2 forwards + 2 backwards；若任何 n_g=0，当前生产代码合同不支持空 member，必须 BLOCKED 而非伪造2次调用。
- SOURCE Index8 各 rank active_indices 的长度/调用节律必须与 distributed FSDP collectives 安全匹配。若有不同，不能在8 H100 上直接跑此 witness，先审查 rank-safe 方案；不能静默挑选更方便的 consumers 并称作 iter1301。
- 如果两个真实窗口无 terminal partial，单独规划至少一例独立 terminal partial 的配对证据（可先利用既有 Gate A CPU negative/terminal tests；要关闭 real-GPU terminal parity 时需用经审核的 rank-safe isolated fixture）。不把 synthetic fixture 的结果冒充真实 iter1300 后继。

## 8. Gate B1 真实 8×H100 实验与证据矩阵（仅将来 Owner 授权后）

固定：8×H100，各卡 memory.free >= 20480 MiB 的原资源门；世界大小8，B8 T16 GA2 K4，nw0，Dense OFF/OFF，原始 dataset catalog/cache/source 和冻结 model/optim/scheduler 配置；HF_HUB_OFFLINE=1；不降 Batch、GA、消费者数量。每 leg 先进行审计无写入的 native 4组件加载、RNG/profile/sidecar transient 验证，再执行2个 optimizer step。为建立重复性，SOURCE/TARGET 分别2 runs；P0/P1 若分开执行，记录实际运行次数及资源开销，未授权不得增跑。训练迭代应区分“已完成1300”、内部调用 iteration 参数和外部“执行1301、1302”的标签，不能出现显示上的 1/101 式偏移。

| 编号 | 验证 | PASS 合同 |
|---|---|---|
| B0 | Harness/CPU gate | read-only、源码绑定、两个窗口 plan+schema+random hook负例全绿 |
| B1 | 原始组件加载 | source DCP四组件数据成功读入两腿，同 FQN/step/optimizer state、8rank无 missing/unexpected |
| B2 | State/plan | SOURCE 严格 sidecar验证、TARGET 内存临时翻译严格验证、8rank Consumer/frontier两窗口一致 |
| B3 | stochastic | P0/P1每 Consumer CFG/sigma/noise/payload hash 精确一致；无未监测 stochastic site |
| B4 | native shape | SOURCE原生 index calls，TARGET成功 GA2 2F/2B；相同有效 Consumer；无假 padding |
| B5 | loss | vision/action/total/真实 aux 分量按冻结数学规则及阈值一致 |
| B6 | gradients | 全 selected FQN + 各组 local DTensor/all-gather witness 满足 §6；无缺失/nonfinite |
| B7 | TTT | prefix、四 fast tensors、outer→Local slow grad chain、frontier/commit/abort合同满足 |
| B8 | optimizer | 每完整GA2 step1 optimizer/scheduler；参数增量、moments和LR匹配；连续两步有效 |
| B9 | CUDA/资源 | 无 OOM/NCCL hang/非有限；逐卡 alloc/reserved/peak、wall/call count记录，**本轮不判断提速** |
| B10 | repeatability | 同模式同 witness重复符合冻结阈值；非决定性变化必须先分类 |
| B11 | terminal | 真实或独立 rank-safe fixture覆盖末段缩短 consumer，无 silent drop |
| B12 | immutability | 源 DCP文件清单/sha256 before=after；正式工作树/latest未变化；未创建目标 migration namespace |

失败时输出首个失败 rank、step、GA、FQN/consumer、site、实际值/容差、traceback、CPU/GPU内存；安全终止全部 ranks 并保留 isolated logs，**不得自动 retry、缩 batch、修改源码或改阈值**。报告 literal 只允许 PASS / FAIL / BLOCKED 逐项，并由 GPT 独立审核给 Gate B 正式 verdict。CPU B0 不等于 GPU B1 PASS。

## 9. 未来 Harness CLI 合同（拟议；**命令当前不可执行、GPU 未授权**）

拟新增独立入口 tools/gates/v3_packed128_gateb_compare.py，要求 parser 包含：
- --mode cpu-plan-only / paired-run；--leg index8 / packed128；--source-checkpoint（唯一 iter1300 绝对路径）；--source-config-digest；--target-config-digest；--root-worktree；--expected-root；--expected-child；
- --dataset-index-root、--source-root、--cache-root、--edge、--vae、--base-checkpoint；--witness-manifest、--witness-profile P0/P1、--steps 2、--output-dir（仅 /tmp 非正式 Namespace）；--no-checkpoint-write（必须为真）。
- --rank0-resolved-config-witness、--expect-consumer-identity-match、--fail-on-unknown-rng，禁止普通 --phase resume 或旧 --stop-after-iter 被混入。

分别运行原 source pair 与 target pair 的分布式隔离进程；先只读 CPU 生成/冻结 per-rank canonical plan 和 witness manifest，两腿消费同一 witness 约定并各自以相同 key 生出本地张量，严格校验 sha256 后进行 native train_step；以 JSON 汇总 exact FQN 对照，不交换 FSDP rank0 的不完整碎片当作 full gradient。命令和模块需在完成真正 Harness 实现+验证并得到 Owner 单独授权后才成为可执行指令。不得复用旧 §9.1 的 --phase resume 模板。

## 10. Gate M — 后置 iter1300 → Packed128 一次性持久化迁移（R3）

M 是独立设计/实现/CPU/真实 DCP Load/Strict Resume Gate，**不属于 Gate B**。只有 Gate B 独立 PASS + Owner 批准后 GPT 才实现和审查迁移代码。

- **Source 认证：**8 rank× source sidecar、原始四组件 DCP metadata/shards、源 Root/Child/digest（70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37）、8 rank 17-field profile、CRC/sha256、trainer/scheduler/optimizer state 都匹配。原 DCP/指针永远只读。
- **目标授权配置：**Packed128 Base exact Root/Child 独立推导新 Digest（包含 native_batch_layout）；不得使用 Full Prefetch/consumer_keyed_v1。SOURCE 和 TARGET digest 必须是不同、真实 authority；不得把 target 冒充旧 Digest 或直接禁用 strict 校验。
- **Sidecar 翻译：**原始10个顶层键**一个不增减**。先 source strictly validate 后，在独立对象中将 top-level config_digest 和每个活跃 slot 记录的 SegmentProvenance.config_digest 显式更新为新 digest；原 Identity/manifest/source/segment_id/frontier/committed/fast fp32 values 均精确保存、逐值和 checksum 比对。迁移来源只写在**外置** MIGRATION_MANIFEST.json（绝不加到 rank_*.pkl 新 key）。恢复后用未放宽的 target restore_grouped_local_state 真正验证每 rank。
- **DCP 保存：**Model/Optimizer/Scheduler/Trainer 四组件使用经验证的 DCP state loader/writer 在新 TEMP Namespace 创建自洽 target checkpoint；能否直接复制原分片需以真实 FSDP metadata/loader 证明，不可擅自 hand-copy 元数据或遗漏 optimizer moments/RNG/GradScaler。对比源的全 FQN/state counters/8 rank RNG，除目标 digest/provenance，模型与连续状态不得发生语义变化。
- **原子发布：**在同一文件系统的新临时 Namespace 全部生成 config/manifest/checkpoints/iter_000001300/latest_checkpoint.txt，验证实际 target Strict Load（8 rank、Iteration=1300），校验所有文件和权限及源不变；提交 READY 记录后通过同文件系统原子 rename 整个**尚不存在**的新 Namespace，任一 fail 删除/隔离 temp，绝不发布 latest。不能把“写入了 iter1300 目录”误当作可 resume。
- **后续真实续训验收：**新 Namespace 的生产 --phase resume 严格启动、目标 first step 显示 iter1301，Model/Optimizer/Scheduler/RNG/8 rank frontier/fast state 与 Gate B 已认证的迁移前状态一致；之后可保存、再次 Strict Resume。**自然生产 RNG 后续调用映射随布局改变，因此不得宣称 Index8 与 Packed128 迭代1301以后的随机轨迹 bitwise 相同**；只保证完整恢复源状态与 Gate B受控随机输入的数值布局等价。
- **回滚：**新 Namespace 完全隔离；旧 iter1300 DCP/latest 保持源快照 sha256 原值，源权限/正式训练工作树不改。失败不推进 Formal30k、不使用 iter1400。

独立迁移报告必须包含：完整原/目标 Root+Child、旧/新 digest、所有 source/target文件 SHA、10-key/8rank profile/各 nested provenance、actual DCP Load结果、FQN/Optimizer/Trainer RNG/Frontier state 对照、首次1301日志、Strict Resume复验以及 atomic publish/rollback证据。

## 11. Owner 决策点与当前权限（R7）

请 Owner 仅裁决以下设计事项：
1. 是否采用 **单独 Comparator Gate B**、随后 **独立持久化迁移 Gate M** 的方案（推荐采用）。
2. 是否批准 **先做 Harness 实现与隔离 CPU Gate B0**（不是GPU授权），以及 §6 的候选数值阈值在看见新 GPU 数据前作为正式阈值冻结。
3. 是否需要将真实 terminal partial GPU witness 作为 Gate B 正式关闭必需项；本案按必需项设计。

裁决前：DS 只读；GPT 可提交 docs-only 提案；没有 GPU/torchrun/Nsight、真正 DCP load、生产/测试代码变更、migration publish、真实训练/推理、正式 Namespace/latest/原始 DCP 操作授权。Full Segment Prefetch 性能实验不阻塞 Formal30k 恢复的关键路径。

**下一步不是启动 Gate B**，而是 Owner 对本设计作出明确裁决；然后 GPT 实现隔离 Harness，并由 DS 验收 B0，之后单独申请 B1 GPU。
