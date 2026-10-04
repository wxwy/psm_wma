# PSM-WMA V3 Corrected — Phase 4 Local-TTT Integration Design v1.2

日期：2026-10-05
状态：GPT frozen design authority；Phase4 production implementation 仍被 Phase3.5 REAL_PARITY_PASS 阻塞。
本 v1.2 supersede 未提交的 v1.1/v1.0 草稿。

## 1. Phase4 目标

在 Phase1A / Phase1B / Phase2 / Phase3 已关闭的 Corrected V3 数据与 policy 路径上，恢复 V2 已验证的 Local-TTT 语义：

    exact cache current z0
    + previous exact executed/recorded raw15 transition
        -> V2 visual96
        -> Local evidence encoder
        -> continual fast-weight update
        -> K_local Local tokens
        -> native Cosmos Local prefix action path
        -> native outer policy loss
        -> gradients to Local slow params + allowed host trainables

Phase4 分两步：

Phase4A
- exact-window Local evidence
- corrected producer
- exact-window episode view
- corrected planner/frontier

Phase4B
- B_stream batched Local scan
- dynamic T / B_stream / active_ga grouped window
- candidate/live transaction
- per-row telemetry parity

Phase4 不做：
- formal trainer/DCP/resume wiring
- optimizer inventory/final launcher
- online inference
- simulator/eval

这些属于 Phase5 / Phase6。

## 2. Hard prerequisite

Phase4 implementation 只有在 Phase3.5 thresholded REAL_PARITY_PASS 后允许开始。

当前 Phase3.5：

    BLOCKED_ASSET_PATH

编码服务器缺少显式：
- CACHE_ROOT
- SOURCE_ROOT
- WAN_VAE_PATH
- PARITY_OUT

这不是 source/code FAIL，也不是 parity FAIL。

因此：
- 本文可以冻结；
- cx 可以只读复核本文；
- cx 不得开始 Phase4 production；
- ds 不得绕过资产 Gate 猜路径或全盘搜索。

## 3. Parent authority

Phase4 必须继承：

- Corrected V3 detailed design v3.0
- Phase0 implementation mapping
- Phase1A cache catalog closure
- Phase1B cache->flat-source binding closure
- Phase2 raw15/state15/H_pred16 closure
- Phase3 cached-latent SFT + cache-hit closure
- Phase3.5 final REAL_PARITY_PASS Evidence
- V2 donor e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92 的 Local chronology / visual96 / fast-state semantics

Phase3 frozen facts：

- corpus authority = exact_window_v1 cache
- raw sample authority = RoboCasaExactWindowCachedDataset
- policy video_latent = exact z0..z4
- Local current visual必须来自同一个 exact z0
- B1 separate-camera / endpoint / mean-RMS route = historical only

## 4. KEEP / RETIRE / ADAPT

### 4.1 KEEP current Local core

保留：

1. LocalEvidenceEncoder
   - visual_dim=96
   - action_dim=15
   - visual_proj
   - action_proj
   - LayerNorm
   - no state/dt/age

2. ContinualTTTLocalMemoryCore
   - learned W0
   - key/query/value projections
   - slot_queries
   - fast MLP
   - inner_lr
   - step_many
   - scan_segment_masked_encoded_many
   - fp32 fast state
   - create_graph=True training / False online

3. current TTT math
   - row-independent update
   - row MSE mean then sum across active rows
   - inner_lr不除B
   - W0/slow gradients有效

4. model-owned FSDP scan method
   - Cosmos3VFMNetwork.scan_local_memory

5. Local prefix action path
   - local_memory2llm
   - local_memory_modality_embed
   - attach_local_prefixes
   - native attention prefix K/V
   - native action path

6. transaction concept
   - SegmentBatch
   - SegmentIdentity / SegmentProvenance
   - LocalMemorySegmentSidecar
   - RankLocalSegmentScheduler
   - optimizer-success publication boundary

### 4.2 RETIRE from corrected active route

历史保留但 corrected route 不得 import/use：

- robocasa_latent_evidence.py
- RoboCasaLatentReader
- latent_to_visual96 mean48 + RMS48
- causal endpoint/floor mapping
- robocasa_causal_evidence.py active path
- StageARoboCasaEpisodeBinder
- historical RoboCasaSegmentProducer
- historical RoboCasaEpisodeCatalog
- chunk32 / consumer33 geometry
- iter500/B1 checkpoint

### 4.3 ADAPT

必须适配：

- visual96 回到 V2 adaptive pool
- producer 改为 Phase3 exact-window raw dataset
- corrected planner不依赖 historical grouped catalog
- grouped scan从逐 slot改为 B_stream batch
- T runtime configurable，default16
- B_stream runtime configurable，default8
- active_ga runtime configurable，default2
- telemetry在 batching 后保持 per-row含义
- FSDP mixed fresh/continuation state assembly进入 model-owned scan

## 5. Canonical visual96

唯一 helper，例如：

    robocasa_current_latent_to_visual96(z0)

输入：

    fp32 z0 [48,H,W]

公式必须逐值等于 V2：

    adaptive_avg_pool2d(
        z0.unsqueeze(0),
        output_size=(1,2)
    ).flatten()

输出：

    fp32 [96]

硬要求：

- finite
- channel=48
- no mean/RMS
- no left/wrist separate
- no z1..z4
- no learned projection
- helper不detach

Formal test必须和 V2 donor公式逐值相等。

Phase6 inference必须复用同一个 helper。

## 6. Local evidence chronology

exact-window episode：

    window_count = F - 16

consumer step：

    s = 0 .. window_count-1

consumer s 使用 exact window start=s。

s=0：
- no previous evidence
- no fast update
- prefix=None

s>0：

    previous raw exact item start=s-1
        previous z0
        -> visual96

    previous raw exact item action[1]
        -> exact previous raw15 transition

    (visual96_{s-1}, action15_{s-1})
        -> fast update
        -> W_s
        -> Local prefix_s
        -> current consumer s policy forward

因此 canonical chronology：

    (z_{s-1}, a_{s-1}) -> W_s -> prefix_s -> policy_s

禁止：

- z_s + a_{s-1}
- current predicted action
- future action chunk
- state15 row0
- padded64 action
- B1 endpoint latent

训练 evidence action authority：

    previous Phase3 raw item action[1]

并要求逐值等于：

    previous Phase2 transition action15[0]

## 7. Phase3 dataset 是唯一 raw authority

Phase4 producer必须接：

    ActionSFTDataset
    whose _dataset is RoboCasaExactWindowCachedDataset

不得新建第三套 cache/source/raw dataset。

对 flat exact index i：

    raw_item = wrapped_sft._dataset[i]

raw item同时含：

- video_latent [5,48,H,W]
- cached_latent_required=True
- action [17,15] = state15 + 16 raw15
- task_class
- episode_index
- start_frame
- global_row_indices
- window_frame_indices
- latent_source_frame_indices
- cache_corpus_digest
- source_binding_digest

consumer payload 与 Local evidence必须从同一个 raw item capability 派生。

## 8. Consumer transform 与 nesting

每个有效 consumer只 transform一次：

    payload = wrapped_sft._transform(
        dict(raw_item),
        wrapped_sft._resolution
    )

保持 Phase3 ABI：

single sample：
    video_latent [5,48,H,W]

collate：
    [B,5,48,H,W]

Packing split：
    [1,5,48,H,W]

packed model batch：
    list[B] of [1,5,48,H,W]

Phase4 producer不得：

- 把 video_latent预包成 list
- 复制 V2 MULTI_ITEM_KEYS
- 修改 custom_collate_fn
- 修改 PackingDataLoader ABI

## 9. Producer I/O dedup

一次 produce 建 ephemeral raw map。

需要 starts：

- current consumers
- 若 segment start>0，再需要 start-1 作为第一条 previous evidence

读取集合：

    max(0,start-1) .. start+valid_count-1

terminal PAD不读 raw item。

一次 produce中：
- 每个 exact window raw dataset __getitem__ 最多一次；
- 同一 raw item可同时作为 current consumer与下一 consumer的 previous evidence；
- ephemeral map不跨 segment；
- 不进入 DCP。

## 10. Corrected segment geometry

T：

    T = runtime.core.ttt_tbptt_steps

default：
    T=16

支持：
    T=32
    其它正整数实验值

valid consumer count：

    F - 16

segment_count：

    ceil(valid_consumer_count / T)

per-slot SegmentBatch width：

    T

terminal不足T：
- consumer_valid前缀 true
- PAD tail false
- PAD payload=None
- PAD无 raw read
- PAD无 evidence

consumer_step：
    episode-local absolute consumer step

evidence_valid：
    consumer_valid AND consumer_step>0

evidence_source_step：
    consumer_step-1 else -1

segment boundary：
- committed W_t detach
- memory不reset

episode terminal：
- sidecar runtime state移除
- 新 episode从 trained W0开始

## 11. Exact-window planner authority

Phase4创建新 exact-window planner family，不复用 historical catalog types。

建议：

- ExactWindowLocalEpisode
- ExactWindowSlotFrontier
- ExactWindowCatalogFrontier
- ExactWindowSegmentRequest
- ExactWindowGroupedPlan
- ExactWindowRankPlanner

GroupedPlan.members：

    tuple[tuple[SegmentRequest,...], ...]

长度：

    active_ga

每 member requests：

    b_stream

禁止固定 2 / 8。

episode view至少：

- ExactWindowEpisodeKey
- stable uid
- task_class
- flat_start
- window_count
- segment_count
- source_digest

flat_start来自 Phase3 cache-driven get_shuffle_blocks cumulative layout。

source_digest至少绑定：

- cache corpus_digest
- source_binding_digest
- task_class
- episode_index
- window_count
- first exact global-row witness
- terminal exact global-row witness

不得包含 machine absolute path。

## 12. Stable slots / rank partition / GA

planner参数：

- world_size
- rank
- b_stream default8
- active_ga default2
- seed
- T

slot_id：

    rank * b_stream + local_slot

rank partition必须 deterministic，例如：

    sha256(episode.uid) % world_size == rank

禁止 Python process hash。

world_size=1必须合法。

若 rank episodes < b_stream：
- fail-closed
- 不复制 episode凑 batch

task-balanced queue：
- 只用 cache实际 task class
- per-task deterministic shuffle
- round-robin interleave
- seed至少绑定 seed|epoch|task_class|rank

stable slot：
- same episode
- same W_t chain
- cursor segment-by-segment
- terminal后才rebind
- rebind cursor0/W0

同一个 optimizer grouped window：
- 同 slot可跨 member continuation同 episode
- 同 episode不能 fresh-bind到两个 slots
- terminal后 fresh rebind不能与 window内其它 active/fresh episode冲突

T / b_stream / active_ga 完全独立。

## 13. B_stream batched Local scan

historical：

    for slot:
        scan_local_memory([1,T])

Corrected每 member只调用一次：

    model.net.scan_local_memory(
        visual [B,T,96],
        action [B,T,15],
        valid [B,T],
        state_in [B,...] | None,
        continuation_mask [B] | None,
        create_graph=True
    )

B normal = b_stream。

### 13.1 Per-row provenance不合并

每 slot仍拥有独立：

- SegmentBatch
- SegmentIdentity
- SegmentProvenance
- LocalMemoryTransaction

batch adapter只临时 stack：

- visual
- action
- valid
- continuation state
- continuation mask

scan后按 row拆回。

不得创建共享 provenance SegmentBatch。

### 13.2 BatchedLocalMemorySegmentAdapter

保留 CanonicalLocalMemorySegmentAdapter 单 slot语义。

新增：

    BatchedLocalMemorySegmentAdapter

输入：

- per-slot SegmentBatch tuple
- aligned SegmentIdentity tuple
- aligned LocalMemoryTransaction tuple
- candidate sidecar
- model-owned scan callable

职责：

1. 每 row identity/provenance/scheduler validate
2. 每 row sidecar.read
3. fresh row得到 None
4. continuation row得到 detached [1,...] fast state
5. adapter不得读取 W0
6. adapter不得调用 core.initial_state
7. all-fresh：state_in=None, continuation_mask=None
8. all-continuation：stack detached state, continuation_mask=None
9. mixed：stack continuation rows + fresh zero placeholders，构造 continuation_mask
10. 单次 model-owned scan
11. row split tokens/present/state_out
12. 原 SegmentBatch.gather_consumers
13. 每 row独立 pending capability
14. backward成功后只 commit candidate overlay

### 13.3 FSDP blocker fix：model-owned mixed state assembly

W0 是 Local slow Parameter。

FSDP2 下 W0 可能处于 sharded/non-materialized 状态。

当前唯一注册 Local 参数物化 hook 的 method：

    Cosmos3VFMNetwork.scan_local_memory

因此：

adapter / grouped driver 禁止调用：

    runtime.core.initial_state(...)
    runtime.core.scan...

v1.2允许最小修改：

    cosmos3_vfm_network.py

只扩展现有 scan_local_memory：

新增 kw-only：

    continuation_mask: Tensor | None = None

method name保持不变。

#### A. all fresh

输入：

    state_in=None
    continuation_mask=None

保持现有行为：
core scan内部 initial_state(B)。

#### B. all continuation

输入：

    state_in = detached batched continuation
    continuation_mask=None

直接使用 continuation。
不得调用 initial_state。
这样 continuation-only member不会人为构造 W0 zero-grad graph。

#### C. mixed

输入：

    state_in [B,...]
    continuation_mask [B] bool

要求：
- mask same device
- mask同时含 True/False
- True = continuation
- False = fresh
- state_in fresh rows只含 finite zero placeholder

在 model-owned/FSDP-materialized scan method内部：

    W0_batch = runtime.core.initial_state(B)

然后每个 fast-state tensor做 out-of-place selection：

    mixed =
        continuation_mask ? detached_cont_state : W0_batch

mask只沿 batch dim广播。

再调用：

    runtime.core.scan_segment_masked_encoded_many(
        ...,
        state_in=mixed,
        create_graph=True
    )

保证：
- fresh row gradient连到 W0
- continuation row不连 W0
- continuation row不连上一 TBPTT graph
- mixed batch只一次 model-owned scan
- all-continuation完全不触碰 W0
- 无 in-place Parameter mutation

禁止：
- mixed assembly放在 adapter外
- adapter读 W0
- fresh继承 continuation
- continuation重新W0
- 新增第二个 FSDP scan method

### 13.4 Fresh placeholder

mixed batch需要 fresh placeholder对齐 shape。

placeholder只能：
- 从 detached continuation tensor new_zeros
- 或等价普通 tensor元数据构造

不得：
- 从 W0取模板值
- 访问 Local Parameter内容

model-owned method必须忽略 fresh placeholder数值。

formal test：
把 placeholder改成不同 finite值，mixed output与 W0 gradient不变。

若 member无 continuation：
adapter必须走 all-fresh state_in=None。

### 13.5 FSDP registration

继续复用：

    register_fsdp_forward_method(model, "scan_local_memory")

parallelize_vfm_network.py：

    formal diff必须为空

不新增第二 method，不新增 registration。

## 14. Row independence / inner math

必须保持：

- batched update == independent row update
- active row MSE mean per row
- rows sum为 inner scalar
- inner_lr不除B
- T serial
- B parallel

## 15. local_evidence.py 允许的两类 patch

Phase4B 只允许：

A. K_local=1 V2 init
- K=1：slot_queries exact zero
- K>1：保持 current normal init std=1/sqrt(ttt_dim)

B. batched telemetry per-row invariance

current batch telemetry需改为 row invariant：

- row_inner_loss vector
- inner scalar = row_inner_loss.sum()
- telemetry记录每个 active row scalar
- fast_state_norm按 row
- fast_update_norm按 row

drain telemetry：
- sum
- count
- max

必须等于相同 rows逐 slot执行再合并。

B=1 inference telemetry必须不变。

除此之外不改：
- W0定义
- K/Q/V math
- fast MLP
- step_many update公式
- inner_lr
- create_graph

## 16. Scalar vs batched proof

必须比较：

- every-step Local tokens
- present mask
- final four fast-state tensors
- W0 gradient
- evidence encoder gradients
- K/Q/V gradients
- slot query gradient
- inner telemetry sum/count/max
- state norm sum/count/max
- update norm sum/count/max

并证明：
- no inner_lr dilution
- continuation row W0 gradient contribution = 0
- fresh rows W0 gradient == scalar fresh rows gradient sum

## 17. Grouped result split

scan后按 row拆：

- tokens[row:row+1]
- present[row:row+1]
- each state tensor[row:row+1]
- original payload/identity

每 slot保持自己的 pending capability与 transaction。

## 18. Candidate/live transaction

begin复制 live：
- frontier
- sidecar
- scheduler

形成 candidate。

member backward成功后：
- per-slot detached state可进入 candidate
- candidate可继续给下一个 GA member使用

但 live不变。

发生：
- native forward fail
- backward fail
- nonfinite
- later GA fail
- optimizer/scaler skip

则整个 candidate丢弃。

只有 optimizer step成功：

    live = candidate

一次引用切换发布整个 grouped window。

## 19. Same-index native callback

每 member local index i：

1. 选 consumer_valid[:,i]
2. 取原 Phase3 transformed payload
3. 取 row对应 Local prefix
4. 调 native_loss(payloads,prefixes,index)

S0 prefix：
    None

有 evidence：
    [K_local, local_dim]

每 index最多一次 callback。

不得把一个 slot完整T consumers一次性送 native forward。

Phase4不得修改 Phase3 video_latent nesting/collate ABI。

## 20. Outer weighting

一个 grouped optimizer window：

    N_window = 所有 active_ga members 的有效 consumer总数

same-index callback：
- n_i = 当前 index有效 samples
- native mean loss = L_i

weighted backward：

    L_i * n_i / N_window

不得再除 active_ga。

PAD通过 n_i自然排除。

## 21. Outer gradients

Phase4必须证明 outer native loss gradient到：

Local slow：
- encoder.visual_proj
- encoder.action_proj
- encoder.norm
- key_proj
- query_proj
- value_proj
- slot_queries
- W0 four tensors
- local_memory2llm
- local_memory_modality_embed

Reasoner：
    frozen

host generation/action optimizer inventory：
    Phase5冻结

TBPTT：
- continuation segment从 detached W_t继续
- 不回连更早 segment
- fresh segment从 W0建 graph

这是设计语义。

## 22. Policy visual vs Local visual

Policy consumer payload：

    z0..z4

Local：

    同一 raw item z0 -> visual96

不得：
- 改 payload video_latent
- 把 visual96写回 dataset
- Local读 z1..z4
- 改 Policy vision path

## 23. Implementation files

只有 Phase3.5 REAL_PARITY_PASS 后才能实施。

### Phase4A

ADD：

    cosmos_framework/model/generator/mot/robocasa_exact_window_local.py

ADD test：

    robocasa_exact_window_local_test.py

职责：
- visual96 helper
- Phase3 raw capability access
- corrected episode view
- corrected planner/frontier/request
- exact segment producer
- same-index gather helper

### Phase4B

MODIFY：

    local_evidence.py

只允许：
- K1 zero-init
- per-row telemetry compatibility

MODIFY：

    cosmos3_vfm_network.py

只允许：
- existing scan_local_memory新增 continuation_mask
- model-owned mixed fresh/continuation state assembly
- method name不变

MODIFY：

    local_memory_segment_adapter.py

- 保留 single adapter
- 新增 batched adapter
- adapter不得读 W0 / 调 core.initial_state

MODIFY：

    local_memory_grouped_window.py

- corrected planner types
- dynamic T/B/GA
- one model-owned B scan/member
- same-index callback
- candidate/live transaction

明确不改：

- parallelize_vfm_network.py
- memory_prefix.py
- attention
- OmniMoT Local prefix seam
- Phase1A/1B/2/3 datasets
- Phase3 cache-hit seam
- trainer/DCP/resume
- inference/server/eval
- historical B1 files

超范围必须 fresh review。

## 24. Historical import prohibition

corrected Phase4 active modules不得 import：

- robocasa_latent_evidence
- RoboCasaLatentReader
- StageARoboCasaEpisodeBinder
- historical RoboCasaSegmentProducer
- historical CatalogFrontier
- historical RankLocalGroupedPlanner

历史文件/tests可保留。

## 25. Phase4A formal tests

至少：

1. visual96逐值等于 V2 adaptive pool
2. wrong channel/dtype/nonfinite reject
3. only z0 used
4. previous s-1 z0 + previous action[1]
5. action[1] == Phase2 previous transition action15[0]
6. S0 no evidence
7. evidence action不是state15/padded64/future prediction
8. raw capability来自 Phase3 dataset
9. transform once/consumer
10. per-produce raw exact window最多读取一次
11. transformed payload保持 Phase3 marker/video_latent/action ABI
12. current collate/Packing nesting regression
13. valid_consumer_count = F-16
14. T16 geometry
15. T32 geometry
16. terminal PAD fixed width且不读 raw
17. identity/digest mismatch fail
18. source_digest machine-path independent
19. cache实际 task membership
20. world_size=1
21. deterministic rank partition
22. stable continuation/terminal/rebind
23. b_stream configurable
24. active_ga configurable
25. same optimizer window不重复 episode
26. no B1 imports
27. Phase1A/1B/2/3 regression

## 26. Phase4B formal tests

至少：

1. K1 init exact zero
2. K4 init regression
3. batched adapter per-row provenance/identity/transaction
4. one model-owned scan/member
5. input shapes B,T,96 / B,T,15 / B,T
6. continuation state detached
7. fresh W0 gradient path
8. all-fresh兼容旧 state_in=None
9. all-continuation不调用 core.initial_state
10. mixed只在 model-owned scan内调用一次 core.initial_state(B)
11. batched adapter从不调用 core.initial_state
12. placeholder finite值变化不影响 output/gradient
13. mixed W0 gradient == fresh scalar rows gradient sum
14. continuation row对W0 gradient为0
15. every-step tokens scalar-vs-batched parity
16. final W_t parity
17. no inner_lr dilution
18. slow-gradient parity
19. inner_loss telemetry sum/count/max parity
20. fast_state_norm telemetry parity
21. fast_update_norm telemetry parity
22. B=1 telemetry regression
23. T16
24. T32
25. B_stream !=8 CPU
26. active_ga !=2 CPU
27. member count == active_ga
28. rows/member == b_stream
29. same-index callback order
30. S0 prefix None
31. continuation prefix present
32. Phase3 payload nesting unchanged
33. outer weighting n_i/N_window
34. member failure rollback
35. later-GA rollback
36. optimizer skip rollback
37. successful optimizer single live publish
38. live unchanged before optimizer
39. FSDP guard method name仍 scan_local_memory
40. parallelize_vfm_network.py formal diff empty
41. memory-prefix/native action-path regression

## 27. Phase5 boundary

Phase4 closure后仍不直接长训。

Phase5负责：

- corrected GroupedLocalMemoryTrainer wiring
- planner/producer binder
- DCP resume schema bump
- dynamic T/B/GA
- H_pred16/obs17 profile
- cache/source/config digest binding
- direct-DROID initialization
- optimizer inventory
- rank0 corpus/local logging
- CPU/CUDA readiness
- 10-step GPU readiness
- same-job resume
- formal launcher

## 28. Resume future requirement

historical local_memory_grouped_resume.py：
- old frontier
- GA2
- chunk32
- consumer33

Phase4不改。

Phase5必须：
- schema bump
- corrected frontier/planner
- H_pred16/obs17
- dynamic T/B/GA
- per-slot W_t continuation state
- exact cache/source/config digest

## 29. Phase3.5 dependency

Phase4 production authorization必须绑定 Phase3.5：

    REAL_PARITY_PASS

即：
- matching exact cache
- matching flat source
- same Wan VAE
- offline Encode17[0] vs runtime current Encode1
- thresholded parity通过

在此之前：
- design可冻结
- source implementation不允许开始

## 30. Final Phase4 sentence

Corrected Phase4 的唯一目标：

在 exact cache / raw15 / state15 / H_pred16 / cached-latent policy 路径上，
用与 Policy 同源的 current z0 和 previous executed raw15，
按 V2 chronology 持续更新 per-episode fast weight；
T串行、B_stream并行；
fresh W0必须在现有 FSDP-registered model-owned scan 内初始化；
continuation W_t必须 detached；
Local prefix必须真实进入 native Cosmos action path。