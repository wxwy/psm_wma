# Local Memory A2 实现设计 v0.2 — ChatGPT 构建接手

日期：2026-09-18。依据：用户明确委托接手构建；review_adjudication_2026-09-18.md §3 选 A2。
本文件替代 member-shape v0.1 中 A1/A2 未决与错误的前向次数算术；不覆盖其他已冻结文件。
交付边界：Local Memory 当前阶段的可运行训练链路、恢复、回归和运行证据；不声称训练效果或完整 PSM-WMA 已完成。

## 1. 形状、单位与选择权威
- SegmentIdentity 保持单 slot/episode/cursor；SegmentBatch 保持原有 [B,T] ABI。
- B_stream 可配置；T=ttt_tbptt_steps（默认16）；GA 表示一次 optimizer update 的 grouped-member 数。
- A2 默认 B_stream=8、GA=16：16 次 native forward × 128 consumers = 2048 consumers/update。
- A1 若一次只处理8个 consumer，等工作量需256次 native forward，不使用该路线。
- 保留 ActiveLocalMemoryWindowDriver.freeze_window 的 scalar 调度、category deficit、slot 轮转与逐 slot epoch 语义。
- 先冻结 B_stream*GA 个 scalar segments；每 B_stream 个连续 segments 组成一个 grouped member，原始选择序列不变。
- 正常均衡区间一个 group 包含8个不同slot；供给受限区间可能重复slot，不能宣称始终8个不同slot。
- 对重复slot采用依赖分层：每层只含各slot最早未处理segment，层内并行，层间按该slot因果顺序推进。
- 各层的 Local token 按原 scalar 顺序合并，最终仍一次 native forward；不得为凑齐8个不同slot改变数据分布。
- 不把跨slot的“同index”解释为同一个物理时刻；episode-local cursor 与 consumer_step 分别保留。

## 2. 批量 authority 与状态
- 新建 grouped member/plan 类型，移植 MicrobatchPlanMember 的逐行 identity/count/chronology 验证语义。
- 不直接复用其 global QueueEpochSnapshot：active 已冻结 per-slot epoch，不能重新引入全局epoch权威。
- 每组读取 sidecar 的逐slot detached fast state；fresh episode 初始化当前 slow W0；continued episode 严格接前一cursor。
- 使用现有 scan_segment_masked_encoded_many 执行 [B,T] scan；T顺序、不同slot独立。
- 同组重复slot的后段使用前段数值的 detached shadow，保留每T步TBPTT截断；真实sidecar尚不提交。
- 整组预先构建候选 scheduler 和 detached sidecar；完成 native forward、loss validation、outer backward 后才原子发布。
- 任一行/inner/forward/backward失败：不提交本组任何行、不增加本组exposure，清空本window所有可训练参数梯度。
- 先前成功组的fast commits保留；不能静默全episode重跑。只允许精确第一组显式source-transient的一次同bytes重试。

## 3. Loss 与 optimizer
- 一个group的planned_n_valid=sum(row counts)，一个window的N=sum(group counts)；默认128/2048。
- 唯一outer缩放为group valid/N；trainer不得再次除GA。auxiliary在group层按GA平均，禁止默认为inner loss。
- native reduction与多模态均值是否保持原目标必须单独验证；不得把合并forward自动等同数值等价。
- D025使用pristine Nano7 + canonical TTT4（各一次）。fast state不属于optimizer；所有选择外参数保持冻结。
- 数值层可将逐row inner MLP改为batched matmul，但inner loss按row分别归一化再求和，禁止多除B。
- vectorization须与原始逐row数值/fast-state/所有slow参数梯度比较；不变更MSE、inner_lr或post-write readout。
- 成功optimizer一步才推进LR scheduler；GradScaler skip保留此前fast commit但不推进slow/LR。

## 4. 恢复与生命周期
- 沿用active的catalog digests、_slot_epoch重排、driver frontier与owner snapshot。
- 新快照记录member_layout、group_size、logical segments/update、TBPTT width；不同几何或legacy/A2跨模式恢复拒绝。
- 只在IDLE且全部组提交、slow resolution结束后存盘；本轮运行不支持mid-group checkpoint。
- load先stage/validate所有字段再apply，校验失败不得修改live数据游标或sidecar。
- 在线推理只携带每episode的fast state，不携带GA/训练group；首帧Local absent，done按行reset。

## 5. 分层验收
1. selector exact-list/禁止参数/当前recipe回归；历史stale测试与本次变更归因分开。
2. grouped vs scalar同计划、同数据：所有payload身份、tokens、fast state和slow梯度等价。
3. fresh/continued/terminal/rebind、同组重复slot、source失败/outer失败/重试、原子commit/零突变load测试。
4. B_stream=4/8/12几何（至少suite数）；logical consumers/update= B_stream*T*GA，参数变化如实标注。
5. 实际CPU cache取数、单GPU真实128-consumer forward/backward、计数/显存/有限性、save→resume匹配。
6. 新20-step预算和性能证据；机器可读root/child、配置与输入digest绑定；不继承旧20-step的READY。
7. 推理/评测兼容性检查，Local开关对照入口可复现；只在实际验证后记录完成。
失败时停止该次运行保留证据，再定向修复；不启动14天长训代替短链路定位。

## 6. 交付记录
代码作者：ChatGPT；自测与独立review分开。DS/MM对新实现独立审核，不由作者自授APPROVE。
旧审阅文档不改写；状态汇总只指向本次真实产物。每个未完成/未执行阶段保留明确状态。
