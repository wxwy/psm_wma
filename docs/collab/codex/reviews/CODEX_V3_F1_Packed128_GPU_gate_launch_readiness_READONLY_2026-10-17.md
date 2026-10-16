# V3 Packed128 GPU 启动路径与监控可行性：只读准备报告

日期：2026-10-17（Asia/Shanghai）。作者：Codex。任务依据：GPT `26a9eeb1` 的同日 READONLY preparation 指令；并行 DS S0 指令 `11b36b7e`。本报告只核对启动能力、证据覆盖和运行方案，不重复 F0/F1 技术审核或 CPU 验收。

**结论：静态启动路径 READY；实际 G0/G1/G2 仍 BLOCKED，待 DS S0 容量/配置结果、明确的 GPU 证据采集方案及逐阶段 Owner 授权。推荐独立 G0 bounded3 → G1 Fresh100 → G2 same-job Resume500，三个 GPU 启动、两个 Job Namespace。现有 G0 审计不能直接关闭全部全 Rank 数值更新和 Action 因果性证据。没有发现本轮必须立即修改 F1 生产实现的新明确违约，不申请扩大修改范围。**

本轮只读 Git 对象和源文件、写此一份报告；未执行项目 Python、Launcher、CPU/GPU 测试、Config/preflight、模型/DCP 载入或训练，未连接训练服务器，未创建正式 Job/Evidence 目录。文中的命令均为 **NOT EXECUTED / 待授权模板**，不是执行指令或已测结果。

## 1. 版本与已有裁决

| 项目 | 精确值与用途 |
| --- | --- |
| Formal Implementation Root | `6ebf8998a7935f2ad690bb547c5db5e5a4322e6d` |
| Child / Root Gitlink | `2d128ed5a07601cdd424974f99b67832eafeeb41`，两者一致 |
| 隔离分支 | `v3-f1-checkpoint-rng-20261016` |
| 该分支远端 docs HEAD | `ccfd900bc35fcd39ca9953aa7aa55b85398300ad`，不是训练 Root |
| 本轮读取的 V3 远端 | `cb7c607c8d32f9dc844ac74cdab377719660b2fc`；本轮未合并 |
| F1 CPU 关闭权威 | `docs/collab/chatgpt/reviews/2026-10-17_V3_F1_6ebf8998_2d128ed5_EVID03_EVID05_CPU_gate_closeout.md`，`708d420eec489f883e10bb29ab4d1320c88355a6`，`APPROVE_TO_CLOSE`，CPU ONLY |

Root Launcher 从 formal Git 对象核对；本地 Child HEAD 就是上述 Child，读取的源文件未修改。F1 的实际配置工厂/序列化与受影响回归已由正式 closeout 接受，本轮不重新运行、不要求重新技术审核同 Pair。`Config.validate()` 在 CPU 的 BLOCKED 已正式转交未来 GPU HARD_P0，不在此改判 PASS。旧 B1 数值 FAIL、冻结 Source/Target 与原 iter1300 不变。

下文引用均按上述 Child 行号；Root Launcher 按上述 Formal Root。简称：

- P5：`cosmos-framework/examples/psm_wma_robocasa_corrected_phase5.py`。
- OBS：`cosmos-framework/examples/psm_wma_robocasa_corrected_telemetry.py`。
- TRAIN：`cosmos-framework/cosmos_framework/trainer/local_memory_grouped.py`。
- WINDOW：`cosmos-framework/cosmos_framework/model/generator/mot/local_memory_grouped_window.py`。
- DCP：`cosmos-framework/cosmos_framework/checkpoint/dcp.py`。

## 2. 真实启动链与模式边界

`scripts/train_v3_packed128_staged.sh:4–29` 检查两个位置参数及十个必要环境变量，设置 offline/PYTHONPATH，进入 Child，以 `${PYTHON:-python} -m torch.distributed.run --standalone --nproc_per_node=8` 唯一调用 corrected Phase5。它不调用旧 H3F，不透传额外 CLI，**不能在命令末尾附加 audit/preflight flag**。

| 契约 | 真实源码 / 能力 |
| --- | --- |
| 正式预算 | Launcher 固定 T16/B8/GA2/K4、world8、workers0、max30000/warmup500/save100；只把 `fresh 100` / `resume 500` 转为 formal-execution-until。P5:707–742 拒绝 formal 与 bounded/audit 混用 |
| Packed128 默认 | P5:132 固定 `v2_a2_member_packed_slot_major_v1`；TRAIN:273–308、WINDOW:162–208 每 GA member 一次 packed Native forward/backward。Full 为每 member 128，每 update 两次 forward/backward、256 consumers/rank；terminal 按真实 counts。没有此入口的 Index8 选择或自动回退 |
| GA=2 | 本次冻结训练配方及 GPT G0 指令优先于旧 AGENTS 通用 smoke GA=1；不得把 G0 改成 GA1 后宣称覆盖 GA2 |
| Prefetch/RNG 默认 | P5:891–917 默认 workers0、full-segment-prefetch=False、transform RNG=`legacy_global`。Launcher 没有开启 keyed RNG 或 full prefetch；不临时更改 |
| FSDP/优化器 | P5:554–594 叠加 Local，shard=world8、replicate1、Grouped Trainer GA2、精确 optimizer allowlist/action multiplier、strict=True/async=False/SafeLocal。真实 resolved precision/LR/seed/Aux/模型并行仍由 DS world8 配置报告提供，不从名称猜测 |
| Fresh 初始化 | 同上：`load_training_state=False`、DROID model-only，跳过新 Local/EMA 权重，Local 新参数走模型初始化；不读取旧 iter1300 训练状态 |
| Namespace/身份 | P5:142–185,226–340；Fresh 原子独占新 Namespace，Resume 校验旧身份/规范配置，不覆盖规范快照；Root/Child、布局、参数语义、数据/资产绝对路径、RNG 策略都进入身份 |
| 两种预检 | P5:942–945 的 `--preflight` 是 CPU 只读准备；P5:946–958 在真实分布式 init 后调用 `_agree_preflight()`，后者 P5:343–360 调用 `config.validate()`、freeze、全 Rank 错误/摘要一致性检查，然后才创建 Trainer/Job 写入 |
| GPU validate | `cosmos_framework/utils/config.py:529–546` 建 world communicator，创建 CUDA byte tensor 并 broadcast；CPU preflight 不代表这一项通过。未来每次 G0/G1/G2 启动都需成功 |
| 保存/结束 | `trainer/__init__.py:425–465` 只在完整 optimizer/Local 边界保存，逢100保存，退出非整100再保存；G0产生iter3，G1结束100/G2结束500不额外重复保存该整百迭代。DCP:1663–1703 完整发布后才更新 latest，无自动 retention |

布局进入身份，不能跨布局/跨 Pair Resume；Root/Child 未变也不能随意移动 source/cache/index/模型路径或改变 precision/seed 等身份字段。旧 Formal30k 的冻结 digest 不适用于这个新 Job；既有两 Rank CPU 配置摘要也不能冒充 DS 本次 world8 摘要。

## 3. 命令模板：全部未执行

### 3.1 DS/Owner 必须先补全的输入

`F1_ROOT` 必须是 **clean detached** 的 formal Root 工作区，其 Child 同样锁精确 SHA。下列 `DS_*` 是未赋值的占位变量，均需 DS S0 真实报告确认：输出持久卷、source/cache/已验收 index、官方 Edge/DROID DCP/VAE、完整训练 Python、外部可写缓存、八张 H100 分配、外部 Evidence 目录。不能把本 Codex CPU venv 当作训练环境。

以下仅为未来 shell 环境模板；本次未 export、mkdir、领取 namespace 或预订 GPU：

```bash
export EXPECTED_ROOT=6ebf8998a7935f2ad690bb547c5db5e5a4322e6d
export EXPECTED_CHILD=2d128ed5a07601cdd424974f99b67832eafeeb41
export PYTHON="$DS_TRAIN_PYTHON"
export OUTPUT_ROOT="$DS_OUTPUT_ROOT"
export SOURCE_ROOT="$DS_SOURCE_ROOT"
export CACHE_ROOT="$DS_LATENT_CACHE_ROOT"
export DATASET_INDEX_ROOT="$DS_ACCEPTED_INDEX_ROOT"
export EDGE_POLICY_CHECKPOINT="$DS_EDGE_POLICY_CHECKPOINT"
export WAN_VAE_PATH="$DS_WAN_VAE_PATH"
export BASE_CHECKPOINT_PATH="$DS_OFFICIAL_DROID_DCP"
export HF_HOME="$DS_RUNTIME_CACHE/huggingface"
export MPLCONFIGDIR="$DS_RUNTIME_CACHE/matplotlib"
export XDG_CACHE_HOME="$DS_RUNTIME_CACHE/xdg"
export PYTHONPYCACHEPREFIX="$DS_RUNTIME_CACHE/pycache"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$F1_ROOT/cosmos-framework"
export CUDA_VISIBLE_DEVICES="$DS_APPROVED_EIGHT_GPU_IDS"
```

十个 Launcher 必填变量为 OUTPUT_ROOT、SOURCE_ROOT、CACHE_ROOT、DATASET_INDEX_ROOT、EDGE_POLICY_CHECKPOINT、WAN_VAE_PATH、BASE_CHECKPOINT_PATH、JOB_NAME、EXPECTED_ROOT、EXPECTED_CHILD；PYTHON 可选但实际必须锁已验收完整环境。不要继承旧 Job 的 PYTHONPATH、checkpoint path 或未经记录的诊断/RNG/precision 环境覆盖。GPU 型号、rank→device、NCCL/Gloo、Torch/驱动、可用显存、持久 FS/quota 都是服务器先决事实，本机未测。

### 3.2 G0：独立 bounded3，不走 formal Launcher

Owner 单独授权后，用新 `bounded_` 名称与独立外部 G0_EVID，直接调用同一个 corrected Phase5；下例仅为 **NOT EXECUTED** 模板：

```bash
cd "$F1_ROOT/cosmos-framework"
"$PYTHON" -m torch.distributed.run --standalone --nproc_per_node=8 \
  --log-dir "$G0_EVID/torchrun" --redirects 3 --tee 3 \
  examples/psm_wma_robocasa_corrected_phase5.py \
  --phase fresh --stop-after-iter 3 --audit-missing-grads \
  --root-worktree "$F1_ROOT" --expected-root "$EXPECTED_ROOT" --expected-child "$EXPECTED_CHILD" \
  --output-root "$OUTPUT_ROOT" --job-name "$OWNER_NEW_BOUNDED_JOB_NAME" \
  --source-root "$SOURCE_ROOT" --cache-root "$CACHE_ROOT" --dataset-index-root "$DATASET_INDEX_ROOT" \
  --edge "$EDGE_POLICY_CHECKPOINT" --vae "$WAN_VAE_PATH" --base-checkpoint "$BASE_CHECKPOINT_PATH" \
  --num-workers 0 --world-size 8 --t 16 --b 8 --ga 2 --k 4 \
  --max-iter 30000 --warmup 500 --save-iter 100
```

`OWNER_NEW_BOUNDED_JOB_NAME` 必须匹配 `bounded_*` 且 Namespace 不存在。预期三次完整 update、每 Rank 六次 Native forward/backward、最多768个 consumer/rank；不是三次 microstep。应保留8个进程日志、24份 rank×iteration 缺梯度报告、Rank0 JSONL、diag-only身份、iter3完整标记/八份Local sidecar/四个DCP组件及退出码；不能因日志缺失就补写 PASS。`diagnostic_only_do_not_resume=True` 和 prefix 保护阻止该 DCP 进入正式恢复链；G1 仍从官方 DROID Fresh。

### 3.3 G1、G2：同一正式 Job，分别授权

```bash
# G1 — NOT EXECUTED；JOB_NAME 是全新且非 bounded_ 的 Owner 批准名称
export JOB_NAME="$OWNER_NEW_FORMAL_JOB_NAME"
bash "$F1_ROOT/scripts/train_v3_packed128_staged.sh" fresh 100

# 人工审核 G1 / 空间 / iter100完整性并取得 G2 授权后，另一次进程启动：
# G2 — NOT EXECUTED；保持同一工作区、上述身份环境与 JOB_NAME
bash "$F1_ROOT/scripts/train_v3_packed128_staged.sh" resume 500
```

未来执行方应在新外部 Evidence 中保留 console/进程退出码，避免依赖终端滚屏；Launcher 本身不接受 per-rank log CLI，可在批准的运行编排中保存其全部输出，不修改 Launcher。CPU S0 preflight 应直接调用 P5 `--preflight`，由 DS 按已发布指令执行；不要运行 Launcher 期待得到 CPU dry-run。

G2 使用 same-job latest，G2准入时必须确认其为新Job iter100，而非迭代号相同的其它作业或旧iter1300。若 latest 有变、身份不一致、预算已达到则停止；不修指针绕过。当前 `resume 500` **不会在101等待人工确认**，亦没有全 Rank 语义硬门。要在首步异常时停止，需要事先批准的外部监控/终止流程；不能声称零延迟阻止102。若要求精确101暂停/内部硬门，属于新执行设计/代码 Gate，不能偷偷用额外101保存代替原三次启动方案。

## 4. 前三步观测能力：A/B 选择与剩余证据

| 选项 | 能做什么 | 空白/成本 | 建议 |
| --- | --- | --- | --- |
| A：现有独立 bounded3 + allrank audit | 原样F1，world8、GA2、DROID Fresh，真实三次训练更新；全Rank调用计数硬检查，所有Rank缺梯度清单，Rank0 loss/Local/grad组范数，独立iter3保存 | 额外一次GPU启动、独立诊断DCP；审计是报告，没有全FQN数值非零硬门，没有全Rank优化器变化或Action因果干预输出 | **推荐**。先用最少新代码取得有边界的功能证据；人工逐项裁决，未采到的必需语义仍保持未通过 |
| B：正式 Fresh100 内首三步强制门 | 可设计为三步内所有Rank自动停止/确认，再继续同Job | 至少 P5 放开正式有界见证入口、OBS收集全Rank摘要并全Rank判定；若需精确pre/post optimizer tensor witness，还需TRAIN已有观察点接入。新Child/Root、聚焦CPU负例、DS独立Gate/GPT Fresh Review，再授权GPU。不是简单去掉audit互斥检查 | 本轮不实施；仅在Owner坚持两次GPU启动且接受新代码/Gate成本时选 |

### 4.1 不能混淆的四种检查

1. **现有硬门：**WINDOW:200–208 检查 scalar outer finite；TRAIN:187–206、365–368 在 hook 前后两次检查现有梯度有限性，并全 Rank归约。它检查“全局存在至少某些梯度且所有被检查的现有梯度有限”，不是每Rank/每个eligible FQN完整性；`grad=None`被跳过。OBS:620–629 检查每 Rank Native调用数等于GA members。
2. **全 Rank presence 报告：**OBS:314–378 对选中参数采集grad=None、group、缺失者的global/local numel、DTensor placements；采集在pre_optimizer，发出在post_commit。`AUDIT_OK`仅无采集/迭代错误，**即使missing列表非空也可出现**。OBS:638–646 是被动遥测，异常不转成生产训练硬失败；因此必须外部验证完整24份报告及错误字段，不凭退出码/状态字符串单独PASS。
3. **数值及参数变化：**OBS:282–312、389–415、461–585 仅Rank0分片有grad组范数、Local inner/fast汇总；参数范数采样G0为每3步、formal每100步，采在pre_optimizer，并非参数delta。其它Rank仅presence不含范数。`training_audit.py:225–238` 的Consumer/state/memory audit也只Rank0，optimizer memory bytes不等于非零moment或真实参数更新。
4. **功能因果：**WINDOW:51–95 检查slot/time/episode/S0-prefix对应、不detach；TRAIN:291传入Native，`model/generator/omni_mot_model.py:1389–1400` attach prefix，证明静态接线。非零总Loss、grad存在、fast norm变化仍不能单独证明Action依赖Local。原生模型还存在无有效Action时的dummy零梯度连接（同文件:1967–1977），须核对真实Action有效mask/count。后续同输入/seed的Local干预及短Simulator ABI Gate不可由Loss下降代替。

**A 的验收边界应写实：**可关闭8Rank运行、packed调用、presence/结构、Rank0分片数值观察与diag-save；不能直接签“所有Rank Local/Generation/Action真实更新、CUDA RNG恢复或Local→Action因果性已证实”。若GPT将全Rank数值见证列为G1前硬前置，需要在G0同一授权资源内另行批准具体只读证据采集工具/工具版本和验收方法，或选择B的新实现。当前没有能一键输出这些全部证据的CLI，本报告不实现外部hook、不假造现成工具。

### 4.2 空分片与 W0 例外必须精确归类

- `DTensor.to_local().numel()==0` 是合法eligibility排除，不能把local0当作FQN全局缺梯度；须跨8Rank聚合所属分片及placements。空张量也不能算作“非零梯度”的成功证据。
- All-continuation 行用已提交fast state，不重新读W0；mixed/fresh需区别。现有 `mot/local_memory_fsdp_scan_test.py:175–211` 明确 all-continuation W0 **zero、非None** 的参与契约；不能把它推广成任意Local FQN均可None/zero。该测试本轮未重跑，也不能代替DROID Fresh H100实证。
- 对其它非空、实际参与该损失/consumer的eligible分片，持续None/全零或无optimizer delta需定位，不因总体loss下降、其它组非零或“FSDP常这样”而放行。不要要求每个tensor每个元素都非零；聚合与例外按FQN/子组和实际执行分支裁决。

## 5. 未来 GPU 见证与停止规则

这些是**待测清单**，不是本次追加执行授权。

| 关口 | 必须见证 | 当前可见性与人工准入 |
| --- | --- | --- |
| 每次启动首项 | exact clean Pair/world8/H100设备映射、NCCL world communicator、真实Config.validate/freeze、同rank配置摘要 | P5调用顺序已具备；GPU未测。失败不得继续Trainer训练 |
| G0 原生 batch/loss | 每Rank每GA n_member/n_window，Full[128,128]、实际遇到的Terminal Partial；slot-major payload/prefix/mask同序；raw15/state15/action64有效15维、17帧/H16、left_wrist/use_state；Action/Vision/Outer、Aux条件及权重 | Window真实计数加权：如[122,128]为122/250、128/250；不能固定各1/2。三步没遇到Partial就如实记未覆盖，不额外重跑旧B1。Rank0 Loss不得冒充全局valid-consumer mean；跨Rank counts/归约口径需引用已冻结目标并核对 |
| G0 Local/FSDP | S0无prefix，continuation有past-only committed证据；encoder/core/local2llm/modality_embed、Generation/Action的eligible slow梯度与实际optimizer更新；fresh/continuation/W0分类 | stock audit覆盖presence，数值allRank/update缺口见§4；inner/fast norm需有限且在有证据更新的分支具合理变化，不机械要求每个S0值非零 |
| G1 iter100 | 所有8Rank完整退出；新Job四DCP组件、八Local sidecar、完整标记/latest、trainer100、Local frontier；实际C100、写入峰值和延迟 | F1 CPU契约已闭，真实GPU/FSDP保存与容量仍待测；不能只看rank0 latest文件出现。大body无需为此重新全量hash |
| G2 load→101 | 每RankCUDA/CPU/Python/NumPy RNG恢复且无reseed；模型/优化器moments/scheduler/scaler/Local slot/frontier/下一Consumer身份一致，101第一次更新连续 | stock CLI不直接给全套pre-consumer CUDA RNG/optimizer numeric见证；需事先批准采集方案。Loss100≈Loss101既不充分也非必要；消费输入/噪声不同，不要求两步Loss相等 |
| G2 101→500 | 既定调度连续、无状态重置；异常监控有效，完整保存200/300/400/500；500后人工门 | 不是30k授权，不自动继续2000或30k |
| 后续少量任务闭环 | 同身份Action解码raw15→env12、安全horizon、Local on/off功能影响、实际短rollout/失败视频证据 | 单独GPU/Simulator授权；训练Loss不能代替。正式18-task汇总还受E1可靠性Gate限制 |

**立即停止/不批准下一Gate：**配置/资产/身份或rank不一致、CUDA/NCCL/Gloo错误、OOM、非有限loss/grad/state、调用计数或mask/prefix/consumer对应错误、任意必需审计缺失/AUDIT_ERROR、无法解释的eligible梯度缺失、optimizer失败、Local错误commit、DCP保存/完整性/RNG恢复失败、磁盘/inode/quota达到批准的安全阈值。失败证据保留，禁止fallback或修指针后强行继续。

**允许带记录观察：**有限Loss前期波动、学习率warmup趋势、已证明无Aux分支的缺少Aux字段、S0无prefix、按分支证明的W0零梯度/合法空分片、吞吐波动。未知/未采样字段不填0；必需见证拿不到就是该子门BLOCKED。Wall吞吐来自OBS:464先于post-commit遥测开销，只作趋势；容量/运行时限应使用外部总耗时，不为此改遥测实现。

## 6. 存储：当前无清理方案与候选有界方案要分开

实际卷free/quota/inode、`C_old`、可用输出路径均由DS S0独立读取，本机没有训练服务器事实。旧iter1300仅作统计估值锚，不保证等于新F1 Fresh C；也不使用旧B1 rank*.pt捕获大小推算。新G0三步也可能已分配完整optimizer状态，其DCP不会因只有三步就缩到Fresh100的3%。

令 `D` 为保留的G0完整诊断DCP尺寸，`C_i` 为新正式iteri的完整DCP尺寸，`W` 为明确预算的日志/视频/共享卷增长缓冲，`R` 为批准的失败stage/orphan应急余量（不得假定无限重试仍安全）。

| 执行方式 | 容量事实/预算 |
| --- | --- |
| 现有代码G0→G1、禁止删除 | 至少D + C100 + W，另计可能留下的R；在真实C100测出前使用有根据的保守估计，否则STORAGE_UNCERTAIN |
| 现有代码一次Resume100→500、不清理 | iter100/200/300/400/500五份全部留下；正常完成预算为 `D + Σ(C100,C200,C300,C400,C500) + W`，再加R。迭代500写stage时已有前四份，stage即第五份，目录rename本身不复制出第六份；额外失败预算应明确另列 |
| 未来已授权latest+previous滚动保留 | 无里程碑/评测pin时可按 `3C_est + W + R` 估下一次写入峰值，**还要加D及额外被pin的唯一checkpoint集合**；必须真有已批准且可靠的保留执行机制，才可用这个预算 |
| 不清理直到30000 | 正常整百共300份正式DCP，约300C_est + D + W + R；非整百退出会增加保存点。不据此猜TB数字 |

**推荐最简单的眼下方案：**先由DS确认独立G0/G1容量；G1后测C100及写入成本，再为一次Resume500预留五份正式DCP及D/W/R。若卷不够，则G2 BLOCKED，由Owner选择新增持久容量、批准未来新Job保留工具及对应Gate，或改变执行分段增加人工停止点。不能只写下“保留三份”就假设当前Launcher会自动执行，也不把清理任务偷偷加入本轮。

**未来候选保留策略（只设计）：**保护latest、previous、Owner选定milestone与正在评测引用的DCP；以唯一集合计数，不重复计latest也是milestone的同一份。新complete+latest及全部Rank保存成功后才考虑旧完整副本；评测引用/恢复读者须受保护。删除前输出明确路径/大小/身份清单取得Owner授权，仅限未来新Fresh Job。hidden staging/final orphan另列，先人工诊断，禁止自动复用、移动或删除。原iter1300、595GB历史Evidence及旧缓存永不进入此新Job候选清理集合。本批不提供或安装pruner。

## 7. 正式版本、评测与最少启动顺序

**推荐直接在原始formal Pair的clean detached worktree训练。** 不需要为训练先合并V3；外部Evidence和报告从docs分支读取，放在外部运行目录，不能把报告commit当训练Root。原工作区、所有未提交内容和旧checkpoint保留。不能用本报告所在docs分支HEAD配合expected-root=6ebf8998启动；P5:670–704会拒绝Root SHA不一致。

若Owner以后要求Promote：先明确允许哪些F0/F1祖先/实现变更、保留V3全部后续文档与他人提交，走非force合并/集成；生成**新的真实Root SHA**并核对Child/Gitlink与训练源码/Launcher差异，只做新Root/身份/增量的窄审核及相应CPU证据，不重审未变F1核心技术。若Child也变，则按真实diff新Gate。新的Root进入training_identity，不能给已在6ebf8998建立的正式Job冒充同身份Resume；训练后需保持原Pair工作区，Promote并不改变旧Job身份。本轮无merge/cherry-pick或生产Promote。

E1评测可靠性是独立阻塞：旧18-task Queue的worker错误保全及模拟器整体deadline问题已有正式裁决（`2026-10-15_V3_production_six_findings_static_triage_2f4dec43_1d56320c.md`）。本报告不宣称E1已验收或把另一分支的修复拼进此Pair；在有明确新评测Pair和独立Gate前，不发布18-task完整SR。不因此阻止已另获授权的初始模型训练；少量Simulator验证也须单独确定受控入口/失败证据。Index8显式可选功能仍是独立P1，不删除、不隐式回退、不重开B1等价实验。

最少顺序及人工决策点：

1. DS S0报告：真实容量与world8只读preflight/数据身份；GPT裁决容量、观测缺口和选择A/B，Owner逐阶段授权。尚无本报告可引用的DS S0结果，不代填PASS。
2. **G0启动1、Namespace D：**独立bounded3；先真实GPU Config.validate，再三次更新与diagnostic iter3保存。人工判24份audit/结构/数值证据覆盖及磁盘成本；未测的全Rank功能项明确保留。不能直接转Resume。
3. **G1启动2、Namespace F：**官方DROID Fresh至100，真正的第一份正式完整DCP；人工核全部Rank保存、实际C100、后续五份容量和G2采集计划，再单独批准G2。
4. **G2启动3、仍Namespace F：**same-job100→500；iter101观测连续性，硬错误按批准流程停止；500正常退出，人工裁决后续训练/保留/小规模任务闭环。没有额外100→101启动或额外iter101 DCP。

三个启动是最低的A路线编排数量，不保证所有未知风险三次内都能关闭；例如自然三步未出现terminal partial、未能采到要求的allRank数值或G2 CUDA RNG见证，不能为了维持次数而宣布通过。新增采集/补测须独立界定范围与授权，优先同一已授权G0/G2资源窗口中的小型功能见证，避免重跑已关闭的F0/F1/B0/B1。

**交付状态：READONLY_PREPARATION_COMPLETE；实际GPU就绪：BLOCKED_PENDING_S0_EVIDENCE_AND_OWNER_GATES。** F0/F1 CPU关闭继续有效，无生产修改请求、无自动清理或训练推进授权。
